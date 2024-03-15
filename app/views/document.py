from fastapi import FastAPI, APIRouter, Request, HTTPException,Body
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from app.services.email_service import send_email, send_otp_to_signer
from app.utils.signer_utils import find_next_signer, initiate_signing_for_signer

documents_router = APIRouter()

documents_router = APIRouter()
mongo_uri = "mongodb+srv://loki_user:loki_password@clmdemo.1yw93ku.mongodb.net/?retryWrites=true&w=majority&appName=Clmdemo"
client = MongoClient(mongo_uri)
db = client['CLMDigiSignDB']

@documents_router.get('/get_document')
async def get_document(document_id: int = None):
    if not document_id:
        return JSONResponse({"message": "Document ID is required"}, status_code=400)

    document = db.documents.find_one({"document_id": document_id})
    if document:
        return JSONResponse({"document_base64": document['document_base64']}, status_code=200)
    else:
        return JSONResponse({"message": "Document not found"}, status_code=404)

@documents_router.get('/get_document_details')
async def get_document_details(document_id: int = None):
    if not document_id:
        return JSONResponse({"message": "Document ID is required"}, status_code=400)

    try:
        document = db.documents.find_one({"document_id": document_id}, {"_id": 0})
        if not document:
            return JSONResponse({"message": "Document not found"}, status_code=404)

        eligible_signer_ids = [int(signer['signer_id']) for signer in document.get('signers', []) if
                               signer.get('status') in ['submitted', 'success']]

        signer_documents = list(
            db.signerdocuments.find({"signer_id": {"$in": eligible_signer_ids}, "document_id": document_id},
                                    {"_id": 0}))

        return JSONResponse({
            "document_details": document,
            "signer_documents": signer_documents
        }, status_code=200)
    except Exception as e:
        return JSONResponse({"message": str(e)}, status_code=500)

# @documents_router.post('/accept_signer_status')
# async def accept_signer_status(request: dict = Body(...)):

#     document_id = request.get('document_id')
#     signer_id = request.get('signer_id')
#     action = request.get('action')

#     if not document_id or not signer_id or not action:
#         return JSONResponse({"message": "Document ID, Signer ID, and Action are required"}, status_code=400)

#     try:
#         document_id_int = int(document_id)
#         signer_id_int = int(signer_id)

#         if action == 'accept':
#             db.documents.update_one(
#                 {"document_id": document_id_int, "signers.signer_id": signer_id_int},
#                 {"$set": {"signers.$.status": "success"}}
#             )
#             send_email_to_signer(signer_id_int, "Your signature has been verified.")

#             document = db.documents.find_one({"document_id": document_id_int})
#             next_signer = find_next_signer(document, signer_id_int)

#             if next_signer:
#                 db.documents.update_one(
#                     {"document_id": document_id_int, "signers.signer_id": next_signer['signer_id']},
#                     {"$set": {"signers.$.status": "in_progress"}}
#                 )
#                 initiate_signing_for_signer(document_id_int, next_signer['signer_id'])
#             else:
#                 send_email_to_admin(document['admin_id'], "All signatures completed for document.")

#         return JSONResponse({"message": "Signer status updated successfully"}, status_code=200)

#     except Exception as e:
#         return JSONResponse({"message": str(e)}, status_code=500)

# def send_email_to_signer(signer_id, message):
#     # Example implementation: Send email using send_email service
#     # Assuming you have a send_email service implemented
#     signer_email = get_signer_email(signer_id)  # Assuming you have a function to get signer's email
#     if signer_email:
#         send_email(signer_email, "Signature Verification", message)

# def send_email_to_admin(admin_id, message):
#     # Example implementation: Send email using send_email service
#     # Assuming you have a send_email service implemented
#     admin_email = get_admin_email(admin_id)  # Assuming you have a function to get admin's email
#     if admin_email:
#         send_email(admin_email, "Document Signed", message)

# def get_signer_email(signer_id):
#     # Example function to get signer's email from the database
#     # You should replace this with your actual logic to fetch signer's email
#     signer = db.signers.find_one({"signer_id": signer_id})
#     if signer:
#         return signer.get("email")
#     return None

# def get_admin_email(admin_id):
#     # Example function to get admin's email from the database
#     # You should replace this with your actual logic to fetch admin's email
#     admin = db.admins.find_one({"admin_id": admin_id})
#     if admin:
#         return admin.get("email")
#     return None