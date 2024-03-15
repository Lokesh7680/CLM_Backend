from fastapi import FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.views.auth import auth_router
from app.views.admin import admin_router
from app.views.document import documents_router
from app.views.signers import signer_router
from fastapi.middleware.cors import CORSMiddleware
from app.config import Settings
from fastapi.staticfiles import StaticFiles  # Import StaticFiles

def get_connection_config(settings: Settings):
    return ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USERNAME,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.EMAIL_FROM,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_SERVER,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        USE_CREDENTIALS=settings.USE_CREDENTIALS
    )

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'static' directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mail setup
settings = Settings()
mail_conf = get_connection_config(settings)
mail = FastMail(mail_conf)

# Define a simple route for testing
@app.get('/')
def hello_world():
    return 'Hello, World!'

# Add other route routers and configurations here
app.include_router(auth_router, prefix='/auth')
app.include_router(admin_router, prefix='/admin')
app.include_router(documents_router, prefix='/documents')
app.include_router(signer_router, prefix='/signers')
