# from pyprojroot import here
from dotenv import load_dotenv
from dataclasses import dataclass
from langgraph.types import Command

# from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.runtime import get_runtime
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import ToolMessage
from utils.sql_utils import get_db, get_usable_tables, customer_exists
from langgraph.checkpoint.memory import InMemorySaver
from langchain_community.utilities import SQLDatabase
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.agents.middleware.types import ModelRequest, dynamic_prompt
from langchain.agents.middleware import wrap_model_call
from utils.prompts import (
    SQL_EXECUTION_AGENT_PROMPT_TEMPLATE,
    execute_sql_tool_description,
)

load_dotenv()
gemini_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


@dataclass
class RuntimeContext:
    db: SQLDatabase
    user_first_name: str
    user_last_name: str
    has_valid_name: bool


@tool(
    name_or_callable="execute_sql",
    description=execute_sql_tool_description,
)
def execute_sql(query: str):
    "Executes a read-only SQL query on the connected Chinook database and returns the query result as structured rows."
    runtime = get_runtime(RuntimeContext)
    db = runtime.context.db
    try:
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"


@tool
def update_user_name(
    new_first_name: str,
    new_last_name: str,
    runtime: ToolRuntime,
) -> Command:
    """Update the user's name in the Runtime Context."""
    if customer_exists(new_first_name, new_last_name):
        return Command(
            update={
                "user_first_name": new_first_name,
                "user_last_name": new_last_name,
                "has_valid_name": True,
                "messages": [
                    ToolMessage(
                        content=f"Updated user name to {new_first_name} {new_last_name}.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"{new_first_name.title()} {new_last_name.title()} is not a valid name in the database. Ask the user for a name that actually exists in the database. Dont call the user {new_first_name}",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest):
    runtime = get_runtime(RuntimeContext)
    firstname = runtime.context.user_first_name
    lastname = runtime.context.user_last_name
    return SQL_EXECUTION_AGENT_PROMPT_TEMPLATE.format(
        available_tables=get_usable_tables(),
        user_first_name=firstname,
        user_last_name=lastname,
    )


@wrap_model_call
def require_valid_name(request: ModelRequest, handler):
    """Gate all behavior until a valid Customer name is set.

    While has_valid_name is False, allow only the update_user_name tool and
    guide the model to collect and validate the user's name. Do not answer
    any other questions.
    """
    runtime = request.runtime
    if not runtime.context.has_valid_name:  # type: ignore
        # Restrict toolset and force clear instruction to collect name only
        request.tools = [update_user_name]
        request.system_prompt = (
            "You must first collect the user's first and last name that exist in the Chinook Customer table. "
            "Ask for their full name if missing or invalid. When a name is provided, call the update_user_name tool "
            "with parsed first_name and last_name. Do not answer any other questions and do not call any other tools "
            "until the name is validated. Be concise and polite."
        )
    return handler(request)


agent = create_agent(
    name="sql_agent",
    model=gemini_model,
    tools=[execute_sql, update_user_name],
    context_schema=RuntimeContext,
    checkpointer=InMemorySaver(),
    middleware=[
        require_valid_name,  # type: ignore
        dynamic_system_prompt,  # type: ignore
    ],
)

db = get_db()

# Only run CLI when script is executed directly, not when imported
if __name__ == "__main__":
    question = input("\n\nWhat's up:\t")
    while question != "exit":
        for step in agent.stream(
            input={"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": "1"}},
            context=RuntimeContext(
                db=db, user_first_name="", user_last_name="", has_valid_name=False
            ),
            stream_mode="values",
        ):
            step["messages"][-1].pretty_print()
        question = input("\n\nWhat's up:\t")


"""
What's up:im frank harris
================================ Human Message =================================

im frank harris
================================== Ai Message ==================================
Tool Calls:
  update_user_name (95732890-d8d9-4e30-9ba0-44deb9bcc04c)
 Call ID: 95732890-d8d9-4e30-9ba0-44deb9bcc04c
  Args:
    new_last_name: Harris
    new_first_name: Frank
  PydanticSerializationUnexpectedValue(Expected `none` - serialized value may not be as expected [field_name='context', input_value=RuntimeContext(db=<langch...e='', user_last_name=''), input_type=RuntimeContext])
  return self.__pydantic_serializer__.to_python(
================================= Tool Message =================================
Name: update_user_name

Updated user name to Frank Harris.
================================== Ai Message ==================================

Hello Frank! How can I help you today?


What's up:what was my most cheap purchase?
================================ Human Message =================================

what was my most cheap purchase?
================================== Ai Message ==================================
Tool Calls:
  execute_sql (a5c0202f-795f-4dfd-ae94-4980276847b0)
 Call ID: a5c0202f-795f-4dfd-ae94-4980276847b0
  Args:
    query: SELECT i.InvoiceId, i.Total FROM Invoice i JOIN Customer c ON i.CustomerId = c.CustomerId WHERE c.FirstName = 'Frank' AND c.LastName = 'Harris' ORDER BY i.Total ASC LIMIT 1;
================================= Tool Message =================================
Name: execute_sql

[(13, 0.99)]
================================== Ai Message ==================================

Frank, your most inexpensive purchase was Invoice ID 13, totaling $0.99.


What's up:what about the most expensive?
================================ Human Message =================================

what about the most expensive?
================================== Ai Message ==================================
Tool Calls:
  execute_sql (b389d6e0-aabd-46ca-bc79-5d9423c4dbb7)
 Call ID: b389d6e0-aabd-46ca-bc79-5d9423c4dbb7
  Args:
    query: SELECT i.InvoiceId, i.Total FROM Invoice i JOIN Customer c ON i.CustomerId = c.CustomerId WHERE c.FirstName = 'Frank' AND c.LastName = 'Harris' ORDER BY i.Total DESC LIMIT 1;
================================= Tool Message =================================
Name: execute_sql

[(145, 13.86)]
================================== Ai Message ==================================

Frank, your most expensive purchase was Invoice ID 145, totaling $13.86.


What's up:exit
"""
