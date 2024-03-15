from fastapi import Depends, FastAPI, HTTPException, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pymongo import MongoClient
import os
import string
import random

app = FastAPI()

security = HTTPBasic()

def generate_temp_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    user_id = int(credentials.username)  # Assuming the user's ID is provided in the username
    print("userId: ", user_id)
    
    # Connect to MongoDB and query user
    try:
        mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
        client = MongoClient(mongo_uri)
        db = client['CLMDigiSignDB']
        
        user = db.users.find_one({"admin_id": user_id})
        print("user ", user)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # Convert _id to string
        user['_id'] = str(user.get('_id'))
            
        return user
    
    except Exception as e:
        print("Error fetching user:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user data. Please check server logs for more details.",
        )
