import json
import os
import requests
import base64
from dotenv import load_dotenv
import openai
import re
from pydantic import BaseModel
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette.responses import RedirectResponse
from datetime import datetime, timedelta
import bcrypt

class Token(BaseModel):
    access_token: str
    token_type: str

# User model for token payload
class TokenData(BaseModel):
    username: str | None = None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Actions():
    def __init__(self):
        load_dotenv()
        self.table_name=os.getenv("TBL_NAME")
        self.API_KEY=os.getenv("SQLITE_KEY")
        self.DATABASE_NAME = os.getenv("DB_NAME")
        self.OWNER_NAME = os.getenv("DB_OWNER")
        self.BASE_URL = os.getenv("DB_BASEURL")
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM")
        self.LOGIN_DB = "user_authentication.db"
        

    def verify_password(self,plain_password: str, hashed_password: str):
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
    
    def create_access_token(self,data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    
    def get_user_from_db(self,username: str):
        cursor=self.execute_query(self.LOGIN_DB,f"SELECT username, password FROM users WHERE username = '{username}'")
        for item in cursor:
            result = True
            if result:
                return {"username": item[0]['Value'], "hashed_password": item[1]['Value']}
        return None
    
    def authenticate_user(self,username: str, password: str):
        user = self.get_user_from_db(username)
        if user is None:
            return False
        if not self.verify_password(password, user['hashed_password'].encode('utf-8')):
            return False
        return user
    
    async def get_current_user(self,token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        user = self.get_user_from_db(token_data.username)
        if user is None:
            raise credentials_exception
        return user

    def iterate_json(self,json_data):
        """Iterate through the loaded JSON and print keys and values."""
        if isinstance(json_data, dict):  # JSON object
            for key, value in json_data.items():
                # If the value is another dictionary or list, you can recursively iterate over it
                if isinstance(value, list):
                    table_details = f"Table Name: {self.table_name} \nTable Schema and its column description\n"
                    for item in value:
                        table_details = table_details + "Column: " + item['column_name'] + "\tData Type: "+ item['data_type'] + "\tDescription: " +   item['description'] + "\n\n"
                    return table_details             

    def get_table_details(self,file_path):
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)  # Load the JSON content
                table_details=self.iterate_json(data)
                return table_details
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
        except json.JSONDecodeError:
            print("Error: The file is not a valid JSON.")
        except Exception as e:
            print(f"An error occurred: {e}")


    def execute_query(self,DB_NAME,sql_query):
        """Execute a SQL query against DBHub.io."""
        url = f"{self.BASE_URL}/query"
        query_bytes = sql_query.encode("ascii") 
        query_base64 = base64.b64encode(query_bytes) 
        # Prepare the payload
        params = {
            'apikey': self.API_KEY,
            'dbowner': self.OWNER_NAME,
            'dbname': DB_NAME,
            'sql': query_base64
        }
        # Make the POST request
        response = requests.post(url, params)

        # Check if the response is successful
        if response.status_code == 200:
            return response.json()  # Return the JSON response if successful
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
        

    def generate_sql_query(self,context,query):
        """Convert natural language text to SQL query using a custom prompt."""
        
        # Define the context about the database schema
        context = f"""
        Database Schema: \n
        {context}
        """
        # Define the custom prompt, including the context
        prompt = f"""
        You are a SQL expert. Your task is to convert natural language descriptions into SQL queries.
        Please follow these guidelines:
        1. Only provide the SQL query as the response.
        2. Ensure the SQL syntax is correct.
        3. If the request is ambiguous or incomplete, ask for clarification.
        4. If the user asks about product type or product, then include lower in the where clause for product type
        5. You should always assign an alias

        Context: {context}

        Example and its SQL query:
        1. XXXX buy YYYY
        SQL: ```sql SELECT customerid, sum(quantity) as `Number of Items` FROM table WHERE customerid in (XXXX) AND lower(producttype)='YYYY'```

        Natural Language: "{query}"
        
        SQL Query:
        """
        
        # Make a request to the OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the GPT-3.5 model
            messages=[
                {"role": "system", "content": "You are a SQL expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,  # Adjust as needed
            temperature=0.3,  # Lower temperature for more deterministic output
        )
        
        # Extract and return the generated SQL query
        sql_query = response.choices[0].message['content'].strip()
        return sql_query
    
    def extract_text_between_backtick(self,text):
        pattern = r'```(.*?)```'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            extracted_text = match.group(1).replace("sql","")
        else:
            print("No text found between triple backticks.")
        return extracted_text