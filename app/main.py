import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional

from app.email_utils import send_email
from app.email_schema import EmailRequest, EmailAttachment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Advanced Email Sending API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/send-email/")
@limiter.limit("5/minute")
async def send_email_endpoint(
    request: Request,
    email_data: EmailRequest,
    background_tasks: BackgroundTasks
):
    """
    Send emails with advanced features:
    - Multiple recipients
    - File attachments
    - Embedded links
    - CC and BCC support
    """
    try:
        # Validate recipients
        if not email_data.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient is required")

        # Add task to background
        background_tasks.add_task(
            send_email, 
            subject=email_data.subject,
            body=email_data.body,
            recipients=email_data.recipients,
            attachments=email_data.attachments,
            embedded_links=email_data.embedded_links,
            cc=email_data.cc,
            bcc=email_data.bcc
        )

        return {
            "message": f"Email is being sent to {len(email_data.recipients)} recipients",
            "recipients_count": len(email_data.recipients)
        }
    
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-attachments/")
async def upload_attachments(files: List[UploadFile] = File(...)):
    """
    Endpoint to upload attachments before sending email
    Supports multiple file uploads
    """
    attachments = []
    for file in files:
        # Read file content
        content = await file.read()
        
        attachment = EmailAttachment(
            filename=file.filename,
            content=content,
            mime_type=file.content_type or 'application/octet-stream'
        )
        attachments.append(attachment)
    
    return {
        "message": f"Successfully uploaded {len(attachments)} files",
        "attachments": [{"filename": a.filename, "mime_type": a.mime_type} for a in attachments]
    }