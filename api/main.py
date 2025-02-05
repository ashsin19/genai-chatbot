
import os
import openai
from utils import *
import pandas as pd
# server.py

from fastapi import FastAPI, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Create FastAPI instance
app = FastAPI()
actions = Actions()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow your React app's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Define the request body structure
class Message(BaseModel):
    username: str
    message: str

@app.get("/api/data")
async def get_data():
    columns=['Payment Method','Count']
    sql_query = "SELECT PaymentMethod, count(*) FROM customer_sales_record GROUP BY PaymentMethod"    
    sql_output = actions.execute_query(actions.DATABASE_NAME,sql_query)
    data = []
    if isinstance(sql_output, list):
        for item in sql_output:
            row = [item[0]['Value'],item[1]['Value']]
            data.append(row)
        data_df = pd.DataFrame(data,columns=columns)
        json_columns = data_df.to_json(orient='index')
    return JSONResponse(content=json_columns)

            

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = actions.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = actions.create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Define a route for handling POST requests
@app.post("/api/messages")
async def get_message(message: Message, current_user: str = Depends(oauth2_scheme)):
    user_message = message.message
    # Simple response, you can integrate chatbot logic here
    source_filepath=os.path.join(os.path.dirname(__file__))
    desc_filename=os.getenv("TBL_DESC")
    openai.api_key = os.getenv("OPENAI_KEY")
    query_input = user_message.lower()
    table_details=actions.get_table_details(f"{source_filepath}//{desc_filename}")
    # Generate SQL query
    sql_query = actions.generate_sql_query(table_details,query_input)
    sql_query = actions.extract_text_between_backtick(sql_query)
    print(sql_query)
    sql_output = actions.execute_query(actions.DATABASE_NAME,sql_query)
    sql_output = json.dumps(sql_output)
    prompt = f"Convert the following JSON data into readable natural language:\n\n{sql_output} Query Instructions: If a response has multiple json elements, then make sure that the response is understandable and cohesive"
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # or "gpt-4" if you have access
    messages=[
        {"role": "user", "content": prompt}
    ],
    max_tokens=150,  # Adjust based on expected response length
    )
    response = response['choices'][0]['message']['content']   
    return {"response": response}

@app.get("/protected")
async def protected_route(current_user: dict = Depends(Actions().get_current_user)):
    return {"msg": f"Hello, {current_user['username']}. You are authenticated."}

@app.get("/redirect")
async def redirect_route(current_user: dict = Depends(Actions().get_current_user)):
    # Redirect to the protected route after successful validation
    return RedirectResponse(url="/protected")

# Optional: A root endpoint for testing
@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Chatbot API"}