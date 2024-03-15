from fastapi import APIRouter, HTTPException, Body, Depends, requests
from uuid import uuid4
from pydantic import BaseModel, conint
from app.services.email_service import send_email
from app.services.otp_service import generate_otp, verify_otp
from app.utils.db_utils import get_next_sequence
from app.utils.auth_utils import get_current_user
from app.dependencies.auth_logic import verify_user_role
from pymongo import MongoClient
from app.utils.file_utils import save_document
from typing import List
import random
from app.utils.gen_doc_id import generate_next_number

admin_router = APIRouter()
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']
temp_storage = {}  # Temporary storage for admin data during OTP process

class CreateAdminRequest(BaseModel):
    name: str
    email: str
    password: str
    phone_number: str
    superadmin_email: str

class VerifyOTPRequest(BaseModel):
    admin_email: str
    otp: str

class AdminStatusUpdateRequest(BaseModel):
    admin_id: str
    active_status: bool

# class SubmitDocumentRequest(BaseModel):
#     agreement_name: str
#     agreement_type: str
#     document: str
#     signers: List[dict]
#     watchers: List[dict]
#     admin_id: conint(ge=1)

class VerifyDocumentRequest(BaseModel):
    email: str
    otp: str

@admin_router.post('/create_admin')
async def create_admin(request: CreateAdminRequest):
    superadmin_email = request.superadmin_email
    email = request.email

    otp = generate_otp(email)
    email_body = f"Your OTP for admin creation is: {otp}"
    send_email(superadmin_email, "OTP Verification", email_body)

    # Temporarily store the admin data
    temp_storage[email] = request.dict(exclude_unset=True, exclude_none=True)

    return {"message": "OTP sent to superadmin for verification", "status code": 200}

@admin_router.post('/verify_otp')
async def verify_admin_creation_otp(request: VerifyOTPRequest):
    admin_email = request.admin_email
    otp = request.otp
    
    if verify_otp(admin_email, otp):
        admin_data = temp_storage.pop(admin_email, None)
        if not admin_data:
            raise HTTPException(status_code=404, detail="Admin data not found")

        admin_id = get_next_sequence(db, 'adminid')
        user = {
            "admin_id": admin_id,
            "email": admin_data['email'],
            "password": admin_data['password'],  # Store password directly
            "roles": ['admin'],
            "name": admin_data['name'],
            "phone_number": admin_data['phone_number'],
            "active_status": "true"
        }
        db.users.insert_one(user)

        email_body = f"Your Admin ID: {admin_id}\nYou are added as an admin in DigiSign application.\nYour credentials are as follows:\nUsername: {admin_data['email']}\nPassword: {admin_data['password']}"
        send_email(admin_data['email'], "Admin Account Created", email_body)

        return {"message": "Admin created successfully", "admin_id": admin_id, "status code": 201}
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

@admin_router.get('/get_admins')
async def get_admins():
    admin_records = db.users.find({"roles": "admin"}, {"password": 0})
    admins = []
    for record in admin_records:
        record['_id'] = str(record['_id'])
        admins.append(record)
    return admins

@admin_router.post('/update_admin_status')
async def update_admin_status(request: AdminStatusUpdateRequest):
    admin_id = int(request.admin_id)  # Convert admin_id to integer
    active_status = request.active_status

    # Update admin status in the database
    check = db.users.update_one({"admin_id": admin_id}, {"$set": {"active_status": active_status}})
    
    if check.modified_count == 1:
        return {"message": "Admin status updated", "active_status": active_status, "status": 200}
    else:
        return {"message": "Admin not found or status not updated", "status": 404}
    

def get_admin_email(admin_id: str):
    admin_record = db.users.find_one({"admin_id": admin_id})
    if not admin_record:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin_record['email']


@admin_router.post("/admin/{admin_email}/submit_document")
async def submit_document(admin_email: str, data: dict = Body(...)):
    agreement_name = data.get('agreement_name')
    agreement_type = data.get('agreement_type')
    document_base64 = data.get('document')
    signers = data.get('signers', [])
    watchers = data.get('watchers', [])
    admin_id = data.get('admin_id')

    admin_record = db.users.find_one({"admin_id": admin_id})
    if not admin_record:
        raise HTTPException(status_code=404, detail="Admin not found")

    admin_email = admin_record['email']

    # document_id = str(uuid4())
    document_id = get_next_sequence(db,'documentid')
    document_path = save_document(document_base64, document_id)  # Implement this function

    for i, signer in enumerate(signers):
        signer['status'] = 'in_progress' if i == 0 else 'pending'

    otp = generate_otp(admin_email)
    send_email(admin_email, "OTP Verification", f"Your OTP: {otp}")

    temp_storage[admin_email] = {
        "admin_id": admin_id,
        "document_id": document_id,
        "agreement_name": agreement_name,
        "agreement_type": agreement_type,
        "signers": signers, 
        "watchers": watchers,
        "document_path": document_path,
        "document_base64": document_base64
    }

    return {"message": "Details submitted. OTP sent for verification.", "document_id": document_id, "status": 200}




@admin_router.post('/verify_and_store_document')
async def verify_and_store_document(request: dict = Body(...)):

    admin_id = request.get('admin_id')
    email = request.get('email')
    otp = request.get('otp')
    print("otp",otp)
    document_id = request.get('document_id')
    if verify_otp(email, otp):
        document_data = temp_storage.pop(email, None)
        if document_data:
            for signer in document_data['signers']:
                signer['signer_id'] = get_next_sequence(db, 'signerid')
            for watcher in document_data['watchers']:
                watcher['watcher_id'] = get_next_sequence(db, 'watcherid')

            db.documents.insert_one(document_data)
            return {"message": "Document and details stored successfully","status": 200}
        else:
            raise HTTPException(status_code=404, detail="Session expired or invalid request")
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

@admin_router.get('/get_documents')
async def get_admin_documents(admin_id: str):
    try:
        documents = list(db.documents.find({"admin_id": int(admin_id)}))
        for doc in documents:
            doc.pop('_id', None)

        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def protected_resource(user: dict = Depends(get_current_user)):
    verify_user_role(user)
