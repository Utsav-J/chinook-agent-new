"""
FastAPI backend for Chinook Data Speech Agent.

This module exposes the SQL agent as a REST API with:
- Session management via thread_id
- Simple HTTP responses (no streaming)
- Thread creation and management
- Message history retrieval
- Conversation metadata
- Request timeout handling
"""

import uuid
import asyncio

# import traceback
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# from collections import defaultdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, ToolMessage

from agent import agent, RuntimeContext, db as agent_db

# Thread registry to track active threads (since InMemorySaver doesn't expose list)
# Structure: {thread_id: {"created_at": datetime, "last_activity": datetime, "title": str, "messages": List[BaseMessage]}}
thread_registry: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# Pydantic Models for API
# ============================================================================


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message to send to the agent")
    thread_id: Optional[str] = Field(
        default=None,
        description="Thread ID for session continuity. If not provided, a new thread is created.",
    )


class MessageModel(BaseModel):
    """Model for a single message."""

    id: Optional[str] = Field(None, description="Message ID")
    role: str = Field(..., description="Message role (user/assistant/tool)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")


class ToolCallInfo(BaseModel):
    """Metadata about a tool call."""

    tool_name: str = Field(..., description="Name of the tool called")
    args: Dict[str, Any] = Field(..., description="Arguments passed to the tool")
    tool_call_id: str = Field(..., description="Unique ID of the tool call")
    output: Optional[str] = Field(None, description="Output from the tool")


class AgentDebugInfo(BaseModel):
    """Debug information about the agent execution."""

    step_count: int = Field(..., description="Number of steps in the execution")
    tool_calls: List[ToolCallInfo] = Field(..., description="List of tools invoked")
    model_name: Optional[str] = Field(None, description="Name of the model used")


class ChatResponse(BaseModel):
    """Response model for chat."""

    response: str = Field(..., description="Agent response")
    thread_id: str = Field(..., description="Thread ID for this conversation")
    message_id: Optional[str] = Field(None, description="Message ID if available")
    timestamp: Optional[str] = Field(
        None, description="Response timestamp (ISO format)"
    )
    debug_info: Optional[AgentDebugInfo] = Field(
        None, description="Debug information about the agent execution"
    )


class ThreadCreate(BaseModel):
    """Request model for creating a new thread."""

    thread_id: Optional[str] = Field(
        default=None,
        description="Custom thread ID. If not provided, a UUID is generated.",
    )
    title: Optional[str] = Field(None, description="Optional thread title")


class ThreadInfo(BaseModel):
    """Response model for thread information."""

    thread_id: str = Field(..., description="Thread identifier")
    created_at: Optional[str] = Field(
        None, description="Thread creation timestamp (ISO format)"
    )
    last_activity: Optional[str] = Field(
        None, description="Last activity timestamp (ISO format)"
    )
    title: Optional[str] = Field(None, description="Thread title")
    message_count: Optional[int] = Field(
        None, description="Number of messages in thread"
    )


class ThreadListResponse(BaseModel):
    """Response model for listing threads."""

    threads: List[ThreadInfo] = Field(..., description="List of threads")
    total: int = Field(..., description="Total number of threads")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class MessagesResponse(BaseModel):
    """Response model for message history."""

    messages: List[MessageModel] = Field(..., description="List of messages")
    thread_id: str = Field(..., description="Thread identifier")
    total: int = Field(..., description="Total number of messages")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    agent_name: str = Field(..., description="Agent name")


# ============================================================================
# Application Setup
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    print("Starting FastAPI backend for Chinook Data Speech Agent...")
    print(f"Agent name: {agent.name if hasattr(agent, 'name') else 'sql_agent'}")
    yield
    print("Shutting down FastAPI backend...")


app = FastAPI(
    title="Chinook Data Speech Agent API",
    description="REST API for the Chinook SQL agent with session management",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Helper Functions
# ============================================================================


def get_default_context() -> RuntimeContext:
    """Get default runtime context for new threads."""
    return RuntimeContext(
        db=agent_db,
        user_first_name="",
        user_last_name="",
        has_valid_name=False,
    )


def extract_message_content(message) -> str:
    """Extract string content from a message, handling various formats."""
    if message is None:
        return "No response generated"

    content = getattr(message, "content", None)

    if content is None:
        return "No response generated"

    # Handle string content
    if isinstance(content, str):
        return content

    # Handle list content (e.g., from Gemini models)
    if isinstance(content, list):
        # Extract text from list items
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Handle dict with 'text' key
                if "text" in item:
                    text_parts.append(str(item["text"]))
                # Handle dict with 'type' and 'text'
                elif item.get("type") == "text" and "text" in item:
                    text_parts.append(str(item["text"]))
                else:
                    # Fallback: convert dict to string
                    text_parts.append(str(item))
            elif isinstance(item, str):
                text_parts.append(item)
            else:
                text_parts.append(str(item))
        return " ".join(text_parts) if text_parts else "No response generated"

    # Fallback: convert to string
    return str(content)


def serialize_message(message: BaseMessage) -> MessageModel:
    """Serialize a LangChain message to MessageModel."""
    content = extract_message_content(message)

    # Determine role
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    else:
        role = getattr(message, "type", "unknown").replace("_message", "")

    # Get message ID if available
    message_id = getattr(message, "id", None)
    if message_id:
        message_id = str(message_id)

    # Get timestamp (use current time if not available)
    timestamp = datetime.now(timezone.utc).isoformat()

    return MessageModel(
        id=message_id,
        role=role,
        content=content,
        timestamp=timestamp,
    )


def generate_thread_title(first_message: str) -> str:
    """Generate a thread title from the first message."""
    # Clean up the message
    title = first_message.strip()

    # Limit length
    if len(title) > 50:
        title = title[:47] + "..."

    # Capitalize first letter
    if title:
        title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()

    return title or "New Conversation"


def get_thread_messages_from_registry(thread_id: str) -> List[BaseMessage]:
    """Retrieve messages from thread registry for a thread."""
    if thread_id in thread_registry:
        return thread_registry[thread_id].get("messages", [])
    return []


def update_thread_registry(
    thread_id: str,
    title: Optional[str] = None,
    is_new: bool = False,
    messages: Optional[List[BaseMessage]] = None,
):
    """Update thread registry with activity."""
    now = datetime.now(timezone.utc)

    if thread_id not in thread_registry or is_new:
        thread_registry[thread_id] = {
            "created_at": now,
            "last_activity": now,
            "title": title or "New Conversation",
            "messages": messages or [],
        }
    else:
        thread_registry[thread_id]["last_activity"] = now
        if title:
            thread_registry[thread_id]["title"] = title
        if messages is not None:
            thread_registry[thread_id]["messages"] = messages


def get_thread_metadata(thread_id: str) -> Dict[str, Any]:
    """Get metadata for a thread."""
    messages = get_thread_messages_from_registry(thread_id)
    registry_entry = thread_registry.get(thread_id, {})

    return {
        "thread_id": thread_id,
        "created_at": registry_entry.get("created_at"),
        "last_activity": registry_entry.get(
            "last_activity", registry_entry.get("created_at")
        ),
        "title": registry_entry.get("title", "New Conversation"),
        "message_count": len(messages),
    }


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health check."""
    return HealthResponse(
        status="healthy",
        agent_name=getattr(agent, "name", "sql_agent"),
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        agent_name=getattr(agent, "name", "sql_agent"),
    )


@app.post("/threads", response_model=ThreadInfo, status_code=201)
async def create_thread(thread_data: Optional[ThreadCreate] = None):
    """
    Create a new conversation thread.

    Returns a thread_id that can be used for subsequent chat requests.
    """
    thread_id = (
        thread_data.thread_id
        if thread_data and thread_data.thread_id
        else str(uuid.uuid4())
    )
    title = thread_data.title if thread_data else None

    update_thread_registry(thread_id, title=title, is_new=True)

    metadata = get_thread_metadata(thread_id)
    return ThreadInfo(
        thread_id=metadata["thread_id"],
        created_at=(
            metadata["created_at"].isoformat() if metadata["created_at"] else None
        ),
        last_activity=(
            metadata["last_activity"].isoformat() if metadata["last_activity"] else None
        ),
        title=metadata["title"],
        message_count=metadata["message_count"],
    )


@app.get("/threads", response_model=ThreadListResponse)
async def list_threads(
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of threads to return"
    ),
    offset: int = Query(0, ge=0, description="Number of threads to skip"),
):
    """
    List all conversation threads with pagination.

    Returns threads sorted by last activity (most recent first).
    """
    # Get all threads from registry
    all_threads = list(thread_registry.keys())

    # Sort by last activity (most recent first)
    sorted_threads = sorted(
        all_threads,
        key=lambda tid: thread_registry[tid].get(
            "last_activity", datetime.min.replace(tzinfo=timezone.utc)
        ),
        reverse=True,
    )

    # Apply pagination
    paginated_threads = sorted_threads[offset : offset + limit]

    # Get metadata for each thread
    thread_infos = []
    for thread_id in paginated_threads:
        metadata = get_thread_metadata(thread_id)
        thread_infos.append(
            ThreadInfo(
                thread_id=metadata["thread_id"],
                created_at=(
                    metadata["created_at"].isoformat()
                    if metadata["created_at"]
                    else None
                ),
                last_activity=(
                    metadata["last_activity"].isoformat()
                    if metadata["last_activity"]
                    else None
                ),
                title=metadata["title"],
                message_count=metadata["message_count"],
            )
        )

    return ThreadListResponse(
        threads=thread_infos,
        total=len(all_threads),
        limit=limit,
        offset=offset,
    )


@app.get("/threads/{thread_id}", response_model=ThreadInfo)
async def get_thread(thread_id: str):
    """
    Get metadata for a specific thread.
    """
    metadata = get_thread_metadata(thread_id)

    return ThreadInfo(
        thread_id=metadata["thread_id"],
        created_at=(
            metadata["created_at"].isoformat() if metadata["created_at"] else None
        ),
        last_activity=(
            metadata["last_activity"].isoformat() if metadata["last_activity"] else None
        ),
        title=metadata["title"],
        message_count=metadata["message_count"],
    )


@app.get("/threads/{thread_id}/messages", response_model=MessagesResponse)
async def get_thread_messages(
    thread_id: str,
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of messages to return"
    ),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
):
    """
    Retrieve message history for a thread with pagination.

    Returns messages in chronological order (oldest first).
    """
    messages = get_thread_messages_from_registry(thread_id)

    if not messages:
        return MessagesResponse(
            messages=[],
            thread_id=thread_id,
            total=0,
            limit=limit,
            offset=offset,
        )

    # Serialize messages
    serialized_messages = [serialize_message(msg) for msg in messages]

    # Apply pagination
    paginated_messages = serialized_messages[offset : offset + limit]

    return MessagesResponse(
        messages=paginated_messages,
        thread_id=thread_id,
        total=len(serialized_messages),
        limit=limit,
        offset=offset,
    )


@app.delete("/threads/{thread_id}", status_code=200)
async def delete_thread(thread_id: str):
    """
    Delete a thread and its associated state.

    Note: With InMemorySaver, this removes from registry but may not fully clear checkpointer state.
    """
    try:
        # Remove from registry
        if thread_id in thread_registry:
            del thread_registry[thread_id]

        # Note: InMemorySaver doesn't expose delete method
        # In production, you'd use a checkpointer (like PostgresSaver) with delete support

        return {
            "thread_id": thread_id,
            "status": "deleted",
            "message": "Thread deleted successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete thread: {str(e)}"
        )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the agent.

    Returns the complete agent response after processing.
    Includes timeout handling (30 seconds max).
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    context = get_default_context()

    # Generate title if this is a new thread
    is_new_thread = thread_id not in thread_registry
    if is_new_thread:
        title = generate_thread_title(request.message)
        update_thread_registry(thread_id, title=title, is_new=True)
    else:
        update_thread_registry(thread_id)

    try:
        # Apply timeout (30 seconds)
        # agent.stream() is synchronous, so we run it in a thread pool
        def process_agent():
            last_message = None
            all_messages = []

            # Process the agent response
            # stream_mode="values" returns full state at each step
            for step in agent.stream(
                input={"messages": [{"role": "user", "content": request.message}]},
                config={"configurable": {"thread_id": thread_id}},
                context=context,
                stream_mode="values",
            ):
                step_messages = step.get("messages", [])
                if step_messages:
                    # Each step contains all messages up to that point
                    all_messages = step_messages
                    last_message = step_messages[-1]

            return last_message, all_messages

        try:
            last_message, all_messages = await asyncio.wait_for(
                asyncio.to_thread(process_agent), timeout=30.0
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Request timeout. The agent took too long to respond. Please try again.",
            )

        # Store messages in registry for history retrieval
        # The all_messages list from the stream contains all messages in the conversation
        # We'll use the latest state as the source of truth
        updated_messages = all_messages

        # --- Extract Debug Info & Response ---

        # 1. Find the start of this turn (the user's message)
        turn_messages = []
        found_start = False
        for msg in reversed(all_messages):
            if isinstance(msg, HumanMessage) and msg.content == request.message:
                found_start = True
                turn_messages.append(msg)
                break
            turn_messages.append(msg)

        if found_start:
            turn_messages.reverse()  # Now in chronological order
        else:
            # Fallback if specific message not matched: just use all messages
            # (Though logic dictates it should be there)
            turn_messages = all_messages

        # 2. Extract Tool Calls Metadata
        tool_calls_map = {}  # id -> ToolCallInfo
        step_count = len(turn_messages)

        for msg in turn_messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
                for tc in msg.tool_calls:
                    tc_id = tc.get("id")
                    if tc_id:
                        tool_calls_map[tc_id] = ToolCallInfo(
                            tool_name=tc.get("name", "unknown"),
                            args=tc.get("args", {}),
                            tool_call_id=tc_id,
                            output=None,
                        )

            if isinstance(msg, ToolMessage):
                tc_id = msg.tool_call_id
                if tc_id in tool_calls_map:
                    tool_calls_map[tc_id].output = str(msg.content)

        debug_info = AgentDebugInfo(
            step_count=step_count,
            tool_calls=list(tool_calls_map.values()),
            model_name=getattr(
                agent_db, "name", None
            ),  # Attempt to get some name or fallback
        )

        # Try to get better model name if available on the agent object
        # agent is a CompiledGraph, usually doesn't expose model directly easily
        # but we can try referencing the global gemini_model if strictly needed,
        # or just leave as None/Generic.
        try:
            # Importing gemini_model from agent module to get the model name if possible
            from agent import gemini_model

            debug_info.model_name = getattr(gemini_model, "model", "gemini-2.5-flash")
        except ImportError:
            pass

        # Extract the final response - look for the last AIMessage
        response_content = "No response generated"
        response_message_id = None

        if last_message:
            # Try to find the last AIMessage in the messages
            for msg in reversed(all_messages):
                if isinstance(msg, AIMessage):
                    response_content = extract_message_content(msg)
                    response_message_id = getattr(msg, "id", None)
                    if response_message_id:
                        response_message_id = str(response_message_id)
                    break
            else:
                # If no AIMessage found, extract from last message
                response_content = extract_message_content(last_message)
                response_message_id = getattr(last_message, "id", None)
                if response_message_id:
                    response_message_id = str(response_message_id)

        # Validate response is a string (Pydantic requirement)
        if not isinstance(response_content, str):
            response_content = str(response_content)

        # Update thread activity and store messages
        update_thread_registry(thread_id, messages=updated_messages)

        # Generate timestamp
        timestamp = datetime.now(timezone.utc).isoformat()

        return ChatResponse(
            response=response_content,
            thread_id=thread_id,
            message_id=response_message_id,
            timestamp=timestamp,
            debug_info=debug_info,
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Handle validation errors gracefully
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except Exception as e:
        # Log the error for debugging
        error_details = str(e)

        # Provide more helpful error messages based on error type
        if "validation error" in error_details.lower():
            raise HTTPException(
                status_code=500,
                detail="The agent generated an unexpected response format. Please try again or use a different thread_id.",
            )

        # Check if it's a content extraction issue
        if (
            "string_type" in error_details
            or "Input should be a valid string" in error_details
        ):
            raise HTTPException(
                status_code=500,
                detail="The agent response could not be processed. Please try again with a new thread_id or rephrase your question.",
            )

        # Generic error with details for debugging
        raise HTTPException(status_code=500, detail=f"Agent error: {error_details}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_backend:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
