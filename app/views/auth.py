from fastapi import FastAPI, HTTPException, status, Body, APIRouter
from datetime import datetime
# Remove the bcrypt import since we're not using hashing anymore
from pymongo import MongoClient

auth_router = APIRouter()

# MongoDB connection
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']
users_collection = db.users
documents_collection = db.documents

# Remove the check_password function since we're not using hashing anymore
# def check_password(password, hashed_password):
#     return password == hashed_password

@auth_router.post("/login")
async def login(request: dict = Body(...)):
    email = request.get("email")
    password = request.get("password")
    try:
        print('hi')
        user = users_collection.find_one({"email": email})
        print(user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if 'admin_id' in user and 'admin' in user.get('roles', []):
            if user['active_status'] == 'true' and password == user['password']:
                return {"message": "Admin login successful", "role": user.get('roles', []), "admin_id": user['admin_id'], "status": 200}
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin account is inactive or invalid credentials")
            
        elif 'signer_id' in user and 'signer' in user.get('roles', []):
            credentials = users_collection.find_one({"signer_id": user['signer_id']})
            if credentials and password == credentials['password'] and datetime.now() <= credentials['expiration']:
                associated_documents = documents_collection.find({"signers.signer_id": user['signer_id']}, {"_id": 0, "document_id": 1, "signers.$": 1})
                documents = list(associated_documents)

                return {
                    "message": "Signer login successful",
                    "role": user.get('roles', []),
                    "signer_id": user['signer_id'],
                    "assigned_documents": documents,
                    "status": 200
                }
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired password")
             
            
        elif user and password == user['password']:
            if 'superadmin' in user.get('roles', []):
                return {"message": "Superadmin login successful", "role": user.get('roles', []), "status": 200}
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied, not an authorized role")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
