# ApplyPilot AI

**Find better jobs. Apply smarter. Spend less time on forms.**

ApplyPilot AI is a personal AI-powered job-search and application agent that helps you discover relevant software engineering jobs, find recruiter contacts, prepare tailored applications, send emails via Gmail, and track your entire job search process.

## Features

- 🔍 **Job Discovery** — Find relevant jobs from public sources + manual entry
- 🎯 **AI Matching** — Score and rank jobs against your profile (0-100)
- 👤 **Recruiter Discovery** — Find HR/recruiter contacts from public sources
- ✉️ **Gmail Integration** — Send personalized application emails with resume attachment
- 📊 **Application Tracker** — Track every application from discovery to offer
- 📝 **Resume Studio** — Upload, parse, and tailor resumes
- 🤖 **AI-Powered** — Gemini API with fallback providers (Groq, OpenRouter)
- 🔒 **Privacy-First** — Approval required before any email is sent

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Google Gemini API, Groq (fallback) |
| Email | Gmail API (OAuth 2.0) |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

## Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

- `GEMINI_API_KEY` — Google Gemini API key (required for AI features)
- `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET` — For email sending
- `SECRET_KEY` — Change to a random string for JWT security

## Project Structure

```
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
├── backend/           # Python + FastAPI
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Config, DB, security
│   │   ├── models/    # SQLAlchemy models
│   │   ├── services/  # Business logic
│   │   └── main.py
│   ├── uploads/       # Resume PDFs
│   └── requirements.txt
```

## License

Private — Personal use only.
