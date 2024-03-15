# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# from app.services.otp_service import generate_otp
# from fastapi import FastAPI, BackgroundTasks
# from app.models.email_signer import SignerEmail


# def send_otp_to_signer(signer_email: SignerEmail, background_tasks: BackgroundTasks):
#     otp = generate_otp(signer_email.email)
#     background_tasks.add_task(send_otp_email, signer_email.email, otp)
#     return {"message": "OTP sent successfully"}

# def send_otp_email(signer_email: str, otp: str):
#     subject = "OTP Verification"
#     body = f"Your OTP: {otp}"
#     send_email(signer_email, subject, body)

# def send_email(to_address, subject, body):
#     # Your email configuration
#     from_address = "lokesh.ksn@mind-graph.com"
#     password = "ttyx npiw jpku oxeo3"

#     # Create message container - the correct MIME type is multipart/alternative.
#     msg = MIMEMultipart()
#     msg['From'] = from_address
#     msg['To'] = to_address
#     msg['Subject'] = subject

#     # Attach body to the email
#     msg.attach(MIMEText(body, 'plain'))

#     # Start the SMTP session
#     server = smtplib.SMTP('smtp.gmail.com', 587)  # Change according to your email provider
#     server.starttls()
#     server.login(from_address, password)

#     # Convert the message to a string and send it
#     text = msg.as_string()
#     server.sendmail(from_address, to_address, text)

#     # Close the SMTP session
#     server.quit()


from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from .otp_service import generate_otp
from app.config import settings

app = FastAPI()

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

conf = ConnectionConfig(
    MAIL_USERNAME = "lokeshreddyneelapu@gmail.com",
    MAIL_PASSWORD = "ttyx npiw jpku oxeo",
    MAIL_FROM = "lokesh.ksn@mind-graph.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_SSL_TLS = True , # Specify whether SSL/TLS should be used for email
    USE_CREDENTIALS = True,
    MAIL_STARTTLS=True
)


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

def send_email(receiver_email: str, subject: str, body: str):
    # Create message container
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USERNAME
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Add body to email
    msg.attach(MIMEText(body, 'plain'))

    # Send the message via our SMTP server
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)

    print("Email sent successfully to", receiver_email)


async def send_otp_to_signer(signer_email: str):
    otp = generate_otp(signer_email)
    await send_email(signer_email, "OTP Verification", f"Your OTP: {otp}")
    return {"message": "OTP sent successfully", "otp": otp}