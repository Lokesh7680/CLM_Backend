from fastapi import APIRouter, HTTPException, Depends, FastAPI, BackgroundTasks, Request, status,Body
from fastapi.responses import JSONResponse
from app.models.user import User
from app.services.email_service import send_email, send_otp_to_signer
from app.services.document_processing import process_signature_and_update_document
from app.services.otp_service import generate_otp, verify_otp
from app.utils.db_utils import get_next_sequence
from app.utils.auth_utils import generate_temp_password
from app.utils.file_utils import save_document, save_jpeg_image, save_png_image
# from app.utils.decorators import role_required
from app.services.digital_signature_service import process_signature
from app.utils.signer_utils import find_next_signer,initiate_signing_for_signer
from pymongo import MongoClient
from datetime import datetime,timedelta
import uuid
import base64
import os

signer_router = APIRouter()

# mongo_uri = "mongodb+srv://yosuvaberry:yosuvaberry@cluster0.2fstg6g.mongodb.net/?retryWrites=true&w=majority"
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo/"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']
temp_storage = {}  # Temporary storage for admin data during OTP process


@signer_router.post('/initiate_signing_process')
async def initiate_signing_process(data: dict):
    document_id = data.get('document_id')

    # Fetch the document details
    document_data = db.documents.find_one({"document_id": document_id})
    if not document_data:
        raise HTTPException(status_code=404, detail="Document not found")

    # Find the first signer with 'in_progress' status
    signer = next((s for s in document_data['signers'] if s['status'] == 'in_progress'), None)
    if not signer:
        raise HTTPException(status_code=404, detail="No signer in progress")

    # Generate a temporary password
    temp_password = generate_temp_password()
    password_expiration = datetime.now() + timedelta(days=5)

    # Store the credentials
    db.users.insert_one({
        "email": signer['email'],
        "phone_number": signer['phone_number'],
        "signer_id": signer['signer_id'],
        "roles": ["signer"],
        "password": temp_password,
        "expiration": password_expiration
    })

    # Send email to the signer
    email_body = f"You are a part of signing a document. Your credentials are below:\nUsername: {signer['email']}\nPassword: {temp_password}"
    send_email(signer['email'], "Document Signing Credentials", email_body)

    return {"message": "Email sent to the signer", "signer_id": signer['signer_id'], "status": 200}
    


@signer_router.post('/signer_login')
async def signer_login(data: dict = Body(...)):
    email = data.get('email')
    password = data.get('password')

    # Check if user exists and has the role 'signer'
    user = db.users.find_one({"email": email, "roles": "signer"})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized access, not a signer")

    # Check if the password matches and is still valid
    credentials = db.users.find_one({"signer_id": user['signer_id']})
    # email_content = f"Please check your credentials:\nSigner ID: {user['signer_id']}\nEmail: {credentials['email']}\nPassword: {credentials['password']}"
    # send_email(user['email'], "Please check your credentials",email_content)
    if not credentials or datetime.now() > credentials['expiration']:
        raise HTTPException(status_code=401, detail="Invalid or expired password")

    if password == credentials['password']:
        return {"message": "Signer login successful", "signer_id": user['signer_id'], "role": user['roles'],
                "status": 200}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    

# @signer_router.post('/signer_login')
# async def signer_login(data: dict = Body(...)):
#     email = data.get('email')
#     password = data.get('password')

#     # Check if user exists and has the role 'signer'
#     user = db.users.find_one({"email": email, "roles": "signer"})
#     if not user:
#         raise HTTPException(status_code=401, detail="Unauthorized access, not a signer")

#     # Check if the password matches and is still valid
#     credentials = db.users.find_one({"signer_id": user['signer_id']})
#     if not credentials or datetime.now() > credentials['expiration']:
#         raise HTTPException(status_code=401, detail="Invalid or expired password")

#     if password == credentials['password']:
#         return {"message": "Signer login successful", "signer_id": user['signer_id'], "role": user['roles'],
#                 "status": 200}
#     else:
#         raise HTTPException(status_code=401, detail="Invalid credentials")


@signer_router.post('/upload_video')
async def upload_video(data: dict):
    signer_id = data.get('signer_id')
    video_string = data.get('video')
    document_id = data.get('document_id')

    db.signerdocuments.update_one(
        {"signer_id": signer_id, "document_id": document_id},
        {"$set": {"video": video_string}},
        upsert=True
    )
    return {"message": "Video uploaded successfully", "status": 200}


@signer_router.post('/upload_photo')
async def upload_photo(data: dict):
    signer_id = data.get('signer_id')
    photo_string = data.get('photo')
    document_id = data.get('document_id')

    db.signerdocuments.update_one(
        {"signer_id": signer_id, "document_id": document_id},
        {"$set": {"photo": photo_string}},
        upsert=True
    )
    return {"message": "Photo uploaded successfully", "status": 200}


@signer_router.post('/upload_govt_id')
async def upload_govt_id(data: dict):
    signer_id = data.get('signer_id')
    govt_id_string = data.get('govt_id')
    document_id = data.get('document_id')

    db.signerdocuments.update_one(
        {"signer_id": signer_id, "document_id": document_id},
        {"$set": {"govt_id": govt_id_string}},
        upsert=True
    )
    return {"message": "Government ID uploaded successfully", "status": 200}


@signer_router.post('/upload_signature')
async def upload_signature(data: dict):
    signer_id = data.get('signer_id')
    signature_string = data.get('signature')
    document_id = data.get('document_id')

    db.signerdocuments.update_one(
        {"signer_id": signer_id, "document_id": document_id},
        {"$set": {"signature": signature_string}},
        upsert=True
    )
    return {"message": "Signature uploaded successfully", "status": 200}

@signer_router.post('/submit_details')
async def submit_details(data: dict):
    signer_id = data.get('signer_id')
    document_id = data.get('document_id')

    # Fetch the signer's details
    signer = db.users.find_one({"signer_id": signer_id})
    if not signer:
        raise HTTPException(status_code=404, detail="Signer not found")

    # Send OTP to signer's email
    otp = generate_otp(signer['email'])
    send_email(signer['email'], "OTP Verification", f"Your OTP: {otp}")

    return {"message": "Submit successful, OTP sent for verification", "status": 200}


@signer_router.post('/verify_otp')
async def verify_signer_otp(data: dict):
    signer_id = data.get('signer_id')
    otp = data.get('otp')
    signer = db.users.find_one({"signer_id": signer_id})
    # OTP verification logic
    if verify_otp(signer['email'], otp):  # Implement your OTP verification logic
        # Update signer's status to 'submitted'
        db.documents.update_one(
            {"signers.signer_id": signer_id, "signers.status": "in_progress"},
            {"$set": {"signers.$.status": "submitted"}}
        )
        return {"message": "OTP verified, submission confirmed"}, 200
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")


@signer_router.post('/process_signature')
async def process_digital_signature(data: dict):
    signer_id = data.get('signer_id')
    document_id = data.get('document_id')

    # Retrieve signature and PDF paths from the database
    signer_document = db.signerdocuments.find_one({"signer_id": signer_id})
    document = db.documents.find_one({"document_id": document_id})
    if not signer_document or not document:
        raise HTTPException(status_code=404, detail="Document or signer not found")

    signature_base64 = signer_document['signature']
    signature_format = signer_document['signature_format']
    pdf_path = document['document_path']
    signers = document['signers']
    signer = next((s for s in signers if s.get('signer_id') == signer_id), None)

    # Process signature and update document
    message, status_code = process_signature_and_update_document(
        pdf_path,
        "Yosuva",  # Assuming signer's name is stored here
        signature_base64,
        signer_id
    )
    return {"message": message}, status_code

@signer_router.post('/accept_signer_status')
async def accept_signer_status(request: dict = Body(...)):

    document_id = request.get('document_id')
    signer_id = request.get('signer_id')
    action = request.get('action')

    if not document_id or not signer_id or not action:
        return JSONResponse({"message": "Document ID, Signer ID, and Action are required"}, status_code=400)

    try:
        document_id_int = int(document_id)
        signer_id_int = int(signer_id)

        if action == 'accept':
            db.documents.update_one(
                {"document_id": document_id_int, "signers.signer_id": signer_id_int},
                {"$set": {"signers.$.status": "success"}}
            )
            send_email_to_signer(signer_id_int, "Your signature has been verified.")

            document = db.documents.find_one({"document_id": document_id_int})
            next_signer = find_next_signer(document, signer_id_int)

            if next_signer:
                db.documents.update_one(
                    {"document_id": document_id_int, "signers.signer_id": next_signer['signer_id']},
                    {"$set": {"signers.$.status": "in_progress"}}
                )
                initiate_signing_for_signer(document_id_int, next_signer['signer_id'])
            else:
                send_email_to_admin(document['admin_id'], "All signatures completed for document.")

        return JSONResponse({"message": "Signer status updated successfully"}, status_code=200)

    except Exception as e:
        return JSONResponse({"message": str(e)}, status_code=500)

def send_email_to_signer(signer_id, message):
    # Example implementation: Send email using send_email service
    # Assuming you have a send_email service implemented
    signer_email = get_signer_email(signer_id)  # Assuming you have a function to get signer's email
    if signer_email:
        send_email(signer_email, "Signature Verification", message)

def send_email_to_admin(admin_id, message):
    # Example implementation: Send email using send_email service
    # Assuming you have a send_email service implemented
    admin_email = get_admin_email(admin_id)  # Assuming you have a function to get admin's email
    if admin_email:
        send_email(admin_email, "Document Signed", message)

def get_signer_email(signer_id):
    # Example function to get signer's email from the database
    # You should replace this with your actual logic to fetch signer's email
    signer = db.signers.find_one({"signer_id": signer_id})
    if signer:
        return signer.get("email")
    return None

def get_admin_email(admin_id):
    # Example function to get admin's email from the database
    # You should replace this with your actual logic to fetch admin's email
    admin = db.admins.find_one({"admin_id": admin_id})
    if admin:
        return admin.get("email")
    return None