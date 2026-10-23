"""AI provider configuration and status API routes."""
from fastapi import APIRouter, Depends, HTTPException
from app.core.config import settings

router = APIRouter()


@router.get("/status")
async def ai_provider_status():
    """Get status of configured AI providers."""
    providers = []
    
    # Gemini
    providers.append({
        "name": "Google Gemini",
        "provider": "gemini",
        "configured": bool(settings.GEMINI_API_KEY),
        "model": "gemini-1.5-flash",
        "priority": 1,
        "free_tier": True,
        "status": "ready" if settings.GEMINI_API_KEY else "not_configured",
    })
    
    # Groq
    providers.append({
        "name": "Groq",
        "provider": "groq",
        "configured": bool(settings.GROQ_API_KEY),
        "model": "llama-3.1-70b-versatile",
        "priority": 2,
        "free_tier": True,
        "status": "ready" if settings.GROQ_API_KEY else "not_configured",
    })
    
    # OpenRouter
    providers.append({
        "name": "OpenRouter",
        "provider": "openrouter",
        "configured": bool(settings.OPENROUTER_API_KEY),
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "priority": 3,
        "free_tier": True,
        "status": "ready" if settings.OPENROUTER_API_KEY else "not_configured",
    })
    
    return {
        "providers": providers,
        "active_provider": next((p["provider"] for p in providers if p["configured"]), None),
    }


@router.post("/test/{provider}")
async def test_ai_provider(provider: str):
    """Test an AI provider connection."""
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=400, detail="Gemini API key not configured")
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Say 'ApplyPilot AI connected' in one sentence.")
            return {"status": "success", "response": response.text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini test failed: {str(e)}")
    
    elif provider == "groq":
        if not settings.GROQ_API_KEY:
            raise HTTPException(status_code=400, detail="Groq API key not configured")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                    json={
                        "model": "llama-3.1-70b-versatile",
                        "messages": [{"role": "user", "content": "Say 'ApplyPilot AI connected' in one sentence."}],
                        "max_tokens": 50,
                    },
                )
            if resp.status_code == 200:
                return {"status": "success", "response": resp.json()["choices"][0]["message"]["content"]}
            else:
                raise HTTPException(status_code=500, detail=f"Groq test failed: {resp.text}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Groq test failed: {str(e)}")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
