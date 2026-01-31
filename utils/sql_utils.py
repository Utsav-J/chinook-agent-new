import ast
from pyprojroot import here
from langchain_community.utilities import SQLDatabase
from sqlalchemy.sql import true
db_path = here("Chinook.db")
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

def get_usable_tables():
    return db.get_usable_table_names()

def get_db():
    return db

def customer_exists(first_name:str, last_name:str)->bool:
    query=f'''
    SELECT 
    EXISTS (
        SELECT 1 
        FROM Customer
        WHERE FirstName = '{first_name.title()}' 
          AND LastName = '{last_name.title()}'
    ) AS CustomerExists;
    '''
    res = ast.literal_eval(db.run(query))
    bool_result = res[0][0]
    print(bool_result)
    return False if bool_result==0 else True

if __name__ == "__main__":
    ans = customer_exists("frank","harris")   
    print(ans)