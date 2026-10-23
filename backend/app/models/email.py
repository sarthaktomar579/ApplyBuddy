"""Email model for drafts, sent emails, and tracking."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    
    # Idempotency key to prevent duplicate sends
    idempotency_key = Column(String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Email content
    to_email = Column(String(255), nullable=False)
    to_name = Column(String(255))
    from_email = Column(String(255))
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    body_html = Column(Text)  # Optional HTML version
    
    # Attachment
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    attachment_filename = Column(String(255))
    
    # Status
    status = Column(String(50), default="draft", nullable=False)
    # Statuses: draft, awaiting_approval, approved, sending, sent, failed, cancelled
    
    # Recipient verification
    recipient_verified = Column(Boolean, default=False)
    recipient_source = Column(String(500))  # Where we found this email
    
    # Send tracking
    gmail_message_id = Column(String(255))  # Gmail API message ID
    gmail_thread_id = Column(String(255))
    sent_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Scheduling
    scheduled_for = Column(DateTime)
    
    # Metadata
    generation_model = Column(String(100))  # Which AI model generated this
    is_personalized = Column(Boolean, default=False)
    personalization_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    job = relationship("Job", back_populates="emails")
    attachments = relationship("EmailAttachment", back_populates="email", cascade="all, delete-orphan")


class EmailAttachment(Base):
    __tablename__ = "email_attachments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    filepath = Column(String(1000), nullable=False)
    mime_type = Column(String(100), default="application/pdf")
    file_size = Column(Integer)  # bytes
    
    email = relationship("Email", back_populates="attachments")
