"""Gmail OAuth and email sending API routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.integration import Integration

router = APIRouter()


@router.get("/connect")
async def gmail_connect():
    """Redirect to Google OAuth consent screen."""
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="Gmail OAuth is not configured. Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in your .env file."
        )
    
    # Build OAuth URL
    scopes = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly"
    oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GMAIL_CLIENT_ID}&"
        f"redirect_uri={settings.GMAIL_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"auth_url": oauth_url}


@router.get("/callback")
async def gmail_callback(code: str = None, error: str = None, db: AsyncSession = Depends(get_db)):
    """Handle Google OAuth callback."""
    if error:
        # Redirect to frontend with error
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail_error={error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
    
    try:
        import httpx
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GMAIL_CLIENT_ID,
                    "client_secret": settings.GMAIL_CLIENT_SECRET,
                    "redirect_uri": settings.GMAIL_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_response.text}")
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        # Get user email
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(
                "https://www.googleapis.com/gmail/v1/users/me/profile",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        
        gmail_email = ""
        if profile_response.status_code == 200:
            gmail_email = profile_response.json().get("emailAddress", "")
        
        # Save integration
        result = await db.execute(
            select(Integration).where(Integration.user_id == 1, Integration.provider == "gmail")
        )
        integration = result.scalar_one_or_none()
        
        if integration:
            integration.access_token = access_token
            integration.refresh_token = refresh_token or integration.refresh_token
            integration.is_connected = True
            integration.connected_email = gmail_email
            integration.last_error = None
        else:
            integration = Integration(
                user_id=1,
                provider="gmail",
                is_connected=True,
                is_enabled=True,
                access_token=access_token,
                refresh_token=refresh_token,
                connected_email=gmail_email,
            )
            db.add(integration)
        
        await db.commit()
        
        # Redirect to frontend with success
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail_connected=true")
    
    except Exception as e:
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail_error={str(e)}")


@router.get("/status")
async def gmail_status(db: AsyncSession = Depends(get_db)):
    """Check Gmail connection status."""
    result = await db.execute(
        select(Integration).where(Integration.user_id == 1, Integration.provider == "gmail")
    )
    integration = result.scalar_one_or_none()
    
    return {
        "configured": bool(settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET),
        "connected": integration.is_connected if integration else False,
        "email": integration.connected_email if integration else None,
        "last_error": integration.last_error if integration else None,
    }


@router.post("/disconnect")
async def gmail_disconnect(db: AsyncSession = Depends(get_db)):
    """Disconnect Gmail integration."""
    result = await db.execute(
        select(Integration).where(Integration.user_id == 1, Integration.provider == "gmail")
    )
    integration = result.scalar_one_or_none()
    
    if integration:
        integration.is_connected = False
        integration.access_token = None
        integration.refresh_token = None
        integration.connected_email = None
    
    return {"message": "Gmail disconnected"}


@router.post("/send/{email_id}")
async def send_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Send an approved email via Gmail API."""
    from app.models.email import Email
    from app.models.resume import Resume
    import base64
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.application import MIMEApplication
    from datetime import datetime, timezone
    import os
    
    # Check Gmail connection
    gmail_result = await db.execute(
        select(Integration).where(Integration.user_id == 1, Integration.provider == "gmail")
    )
    gmail = gmail_result.scalar_one_or_none()
    if not gmail or not gmail.is_connected:
        raise HTTPException(status_code=400, detail="Gmail is not connected. Please connect your Gmail account first.")
    
    # Get email record
    email_result = await db.execute(select(Email).where(Email.id == email_id, Email.user_id == 1))
    email_record = email_result.scalar_one_or_none()
    if not email_record:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email_record.status not in ("approved",):
        raise HTTPException(status_code=400, detail=f"Email must be approved before sending. Current status: {email_record.status}")
    
    # Check for duplicate send (idempotency)
    if email_record.gmail_message_id:
        raise HTTPException(status_code=409, detail="This email has already been sent")
    
    try:
        # Build email message
        msg = MIMEMultipart()
        msg["To"] = email_record.to_email
        msg["From"] = gmail.connected_email or settings.GMAIL_REDIRECT_URI
        msg["Subject"] = email_record.subject
        msg.attach(MIMEText(email_record.body, "plain"))
        
        # Attach resume if specified
        if email_record.resume_id:
            resume_result = await db.execute(select(Resume).where(Resume.id == email_record.resume_id))
            resume = resume_result.scalar_one_or_none()
            if resume and os.path.exists(resume.filepath):
                with open(resume.filepath, "rb") as f:
                    attachment = MIMEApplication(f.read(), _subtype="pdf")
                    attachment.add_header("Content-Disposition", "attachment", filename=resume.filename)
                    msg.attach(attachment)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        
        # Send via Gmail API
        import httpx
        
        # Refresh token if needed
        access_token = gmail.access_token
        
        async with httpx.AsyncClient() as client:
            send_response = await client.post(
                "https://www.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"raw": raw_message},
            )
        
        if send_response.status_code == 401:
            # Token expired, try refresh
            async with httpx.AsyncClient() as client:
                refresh_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GMAIL_CLIENT_ID,
                        "client_secret": settings.GMAIL_CLIENT_SECRET,
                        "refresh_token": gmail.refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
            
            if refresh_response.status_code == 200:
                new_tokens = refresh_response.json()
                gmail.access_token = new_tokens["access_token"]
                access_token = new_tokens["access_token"]
                
                # Retry send
                async with httpx.AsyncClient() as client:
                    send_response = await client.post(
                        "https://www.googleapis.com/gmail/v1/users/me/messages/send",
                        headers={"Authorization": f"Bearer {access_token}"},
                        json={"raw": raw_message},
                    )
            else:
                gmail.is_connected = False
                gmail.last_error = "Token refresh failed. Please reconnect Gmail."
                email_record.status = "failed"
                email_record.error_message = "Gmail token expired. Please reconnect."
                raise HTTPException(status_code=401, detail="Gmail token expired. Please reconnect your Gmail account.")
        
        if send_response.status_code == 200:
            result_data = send_response.json()
            email_record.status = "sent"
            email_record.gmail_message_id = result_data.get("id")
            email_record.gmail_thread_id = result_data.get("threadId")
            email_record.sent_at = datetime.now(timezone.utc)
            email_record.from_email = gmail.connected_email
            
            return {
                "message": "Email sent successfully",
                "gmail_message_id": result_data.get("id"),
                "sent_at": email_record.sent_at.isoformat(),
            }
        else:
            email_record.status = "failed"
            email_record.error_message = send_response.text
            email_record.retry_count += 1
            raise HTTPException(status_code=500, detail=f"Gmail API error: {send_response.text}")
    
    except HTTPException:
        raise
    except Exception as e:
        email_record.status = "failed"
        email_record.error_message = str(e)
        email_record.retry_count += 1
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
