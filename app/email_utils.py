import os
import asyncio
import logging
from typing import List, Optional
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from aiosmtplib import send

from app.email_schema import EmailAttachment

# Load environment variables
load_dotenv()

# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_multipart_message(
    subject: str, 
    body: str, 
    sender: str, 
    recipients: List[str],
    attachments: Optional[List[EmailAttachment]] = None,
    embedded_links: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> MIMEMultipart:
    """
    Create a multipart email message with advanced features
    """
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ', '.join(recipients)
    
    # Add CC and BCC if provided
    if cc:
        message['Cc'] = ', '.join(cc)
    if bcc:
        message['Bcc'] = ', '.join(bcc)
    
    message['Subject'] = subject

    # Add body
    body_with_links = body
    if embedded_links:
        body_with_links += "\n\nAdditional Links:\n"
        body_with_links += "\n".join(embedded_links)
    
    message.attach(MIMEText(body_with_links, 'html'))

    # Add attachments
    if attachments:
        for attachment in attachments:
            if attachment.mime_type.startswith('image/'):
                part = MIMEImage(attachment.content, name=attachment.filename)
            elif attachment.mime_type.startswith('application/'):
                part = MIMEApplication(attachment.content, name=attachment.filename)
            else:
                part = MIMEApplication(attachment.content, name=attachment.filename)
            
            part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
            message.attach(part)

    return message

async def send_individual_email(
    recipient: str, 
    message: MIMEMultipart
) -> bool:
    """Send individual email with robust error handling"""
    try:
        await send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False

async def send_email(
    subject: str, 
    body: str, 
    recipients: List[str],
    attachments: Optional[List[EmailAttachment]] = None,
    embedded_links: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
):
    """
    Send emails concurrently with advanced features
    """
    # Combine all recipients
    all_recipients = recipients.copy()
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    # Create multipart message
    message = create_multipart_message(
        subject=subject,
        body=body,
        sender=SMTP_USER,
        recipients=recipients,
        attachments=attachments,
        embedded_links=embedded_links,
        cc=cc,
        bcc=bcc
    )

    # Limit concurrent tasks
    semaphore = asyncio.Semaphore(10)

    async def send_with_semaphore(recipient):
        async with semaphore:
            return await send_individual_email(recipient, message)

    # Send emails concurrently
    results = await asyncio.gather(
        *[send_with_semaphore(recipient) for recipient in all_recipients],
        return_exceptions=True
    )

    # Log results
    successful = sum(1 for result in results if result is True)
    failed = len(all_recipients) - successful
    logger.info(f"Email send summary: Successful: {successful}, Failed: {failed}")