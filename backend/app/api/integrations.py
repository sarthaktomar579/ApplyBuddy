"""Integration settings API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.integration import Integration

router = APIRouter()


@router.get("")
async def list_integrations(db: AsyncSession = Depends(get_db)):
    """List all integration statuses."""
    result = await db.execute(select(Integration).where(Integration.user_id == 1))
    integrations = result.scalars().all()
    
    # Also show provider availability from config
    providers = {
        "gmail": {
            "configured": bool(settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET),
            "connected": False,
            "email": None,
        },
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "connected": bool(settings.GEMINI_API_KEY),
            "model": "gemini-1.5-flash",
        },
        "groq": {
            "configured": bool(settings.GROQ_API_KEY),
            "connected": bool(settings.GROQ_API_KEY),
        },
        "openrouter": {
            "configured": bool(settings.OPENROUTER_API_KEY),
            "connected": bool(settings.OPENROUTER_API_KEY),
        },
    }
    
    # Overlay database records
    for integration in integrations:
        if integration.provider in providers:
            providers[integration.provider]["connected"] = integration.is_connected
            providers[integration.provider]["enabled"] = integration.is_enabled
            if integration.connected_email:
                providers[integration.provider]["email"] = integration.connected_email
    
    return providers


@router.get("/{provider}")
async def get_integration(provider: str, db: AsyncSession = Depends(get_db)):
    """Get specific integration details."""
    result = await db.execute(
        select(Integration).where(Integration.user_id == 1, Integration.provider == provider)
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        return {"provider": provider, "is_connected": False, "is_enabled": False}
    
    return {
        "provider": integration.provider,
        "is_connected": integration.is_connected,
        "is_enabled": integration.is_enabled,
        "connected_email": integration.connected_email,
        "daily_usage": integration.daily_usage,
        "daily_limit": integration.daily_limit,
        "last_error": integration.last_error,
        "last_used": integration.last_used.isoformat() if integration.last_used else None,
    }
