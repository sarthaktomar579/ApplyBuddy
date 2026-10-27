"""
ApplyPilot AI - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.resume import router as resume_router
from app.api.preferences import router as preferences_router
from app.api.jobs import router as jobs_router
from app.api.applications import router as applications_router
from app.api.emails import router as emails_router
from app.api.recruiters import router as recruiters_router
from app.api.dashboard import router as dashboard_router
from app.api.integrations import router as integrations_router
from app.api.gmail import router as gmail_router
from app.api.ai_providers import router as ai_providers_router
from app.services.seed_data import seed_default_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    await seed_default_user()
    print(f"[OK] {settings.APP_NAME} backend started")
    yield
    # Shutdown
    await close_db()
    print(f"[STOP] {settings.APP_NAME} backend stopped")


app = FastAPI(
    title=settings.APP_NAME,
    description="Find better jobs. Apply smarter. Spend less time on forms.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend and Chrome extensions
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Register API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile_router, prefix="/api/profile", tags=["Profile"])
app.include_router(resume_router, prefix="/api/resumes", tags=["Resume"])
app.include_router(preferences_router, prefix="/api/preferences", tags=["Preferences"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications_router, prefix="/api/applications", tags=["Applications"])
app.include_router(emails_router, prefix="/api/emails", tags=["Emails"])
app.include_router(recruiters_router, prefix="/api/recruiters", tags=["Recruiters"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(integrations_router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(ai_providers_router, prefix="/api/ai", tags=["AI Providers"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    }
