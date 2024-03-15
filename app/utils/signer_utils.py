from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from app.services.email_service import send_email, send_otp_to_signer
from app.utils.auth_utils import generate_temp_password
from datetime import datetime, timedelta

app = FastAPI()

# mongo_uri = os.getenv("MONGO_URI")
# mongo_uri = "mongodb+srv://yosuvaberry:yosuvaberry@cluster0.mnf3k57.mongodb.net/?retryWrites=true&w=majority"
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']


def find_next_signer(document, current_signer_id):
    signers = sorted(document.get('signers', []), key=lambda x: x['order'])
    current_index = next((i for i, s in enumerate(signers) if s['signer_id'] == current_signer_id), None)

    if current_index is not None and current_index + 1 < len(signers):
        return signers[current_index + 1]

    return None


def initiate_signing_for_signer(document_id, signer_id):
    # Fetch the document and find the specific signer   
    document = db.documents.find_one({"document_id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    signer = next((s for s in document['signers'] if s['signer_id'] == signer_id), None)
    if not signer:
        raise HTTPException(status_code=404, detail="Signer not found")

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
    send_email_to_signer(signer['email'], "Document Signing Credentials", email_body)

    return "Email sent to the signer"


def send_email_to_signer(signer_email, subject, message):
    send_email_to_user(signer_email, subject, message)


def send_email_to_admin(admin_id, message):
    # Fetch admin's details from the database
    admin = db.users.find_one({"admin_id": admin_id})
    if admin:
        email = admin.get('email')
        if email:
            subject = "Document Signing Status"
            send_email_to_user(email, subject, message)
        else:
            print("Email address not found for admin.")
    else:
        print("Admin not found in the database.")


def send_email_to_user(email, subject, message):
    # Send email to the user
    send_email(email, subject, message)


