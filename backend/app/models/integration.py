"""Integration settings model for Gmail, AI providers, etc."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.core.database import Base


class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=1)
    
    # Integration type
    provider = Column(String(100), nullable=False)  # gmail, gemini, groq, openrouter, ollama
    
    # Status
    is_connected = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)
    
    # OAuth tokens (encrypted at rest in production)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    
    # Provider-specific config
    config = Column(Text)  # JSON: model name, quotas, etc.
    
    # Usage tracking
    daily_usage = Column(Integer, default=0)
    daily_limit = Column(Integer)
    last_reset_date = Column(String(10))  # "2026-10-23"
    
    # Status info
    last_error = Column(Text)
    last_used = Column(DateTime)
    connected_email = Column(String(255))  # For Gmail: which account
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
