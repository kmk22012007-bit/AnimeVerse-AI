# AnimeVerse AI — Developer & Contributor Guide

This guide provides instructions for setting up, developing, testing, and verifying the **AnimeVerse AI** platform locally.

---

## 1. System Prerequisites

Before beginning local development, verify your workstation has the following tools installed:
- **Python**: Version 3.10, 3.11, or 3.12 (`python --version`).
- **Node.js**: Version 18.x or 20.x LTS (`node --version`).
- **Package Manager**: `npm` (v9 or higher).
- **Git**: For version control (`git --version`).

---

## 2. Local Environment Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/kmk22012007-bit/AnimeVerse-AI.git
cd AnimeVerse-AI
```

### Step 2: Backend Setup
Create and activate an isolated Python virtual environment:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run initial migrations
python manage.py migrate

# Return to root
cd ..
```

### Step 3: Frontend Setup
Install frontend npm dependencies:

```bash
cd frontend
npm install
cd ..
```

---

## 3. Environment Configuration

Copy the example environment template:
```bash
cp .env.example .env
```

Ensure the following default values are present in `.env` or `backend/.env`:
```env
DJANGO_SECRET_KEY=local-dev-secret-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Optional: Add Google Gemini API key for live AI companion responses
GEMINI_API_KEY=
AI_PROVIDER=gemini
AI_MODEL_NAME=gemini-2.5-flash

# Upstream metadata API mirror
JIKAN_BASE_URL=https://api.tenrai.org/v1
```

> **Note**: If `GEMINI_API_KEY` is left blank, the application automatically engages its deterministic offline recommendation fallback engine.

---

## 4. Running the Development Servers

Open two terminal windows to run both servers concurrently:

### Terminal 1 — Backend REST API
```bash
cd backend
python manage.py runserver 127.0.0.1:8000
```
- REST API Root: `http://127.0.0.1:8000/api/`
- Health Probe: `http://127.0.0.1:8000/api/health/`
- Django Admin: `http://127.0.0.1:8000/admin/`

### Terminal 2 — Frontend Single-Page Application
```bash
cd frontend
npm run dev
```
- Web Application: `http://127.0.0.1:5173/`

Vite is configured with a development proxy forwarding `/api` requests to `http://127.0.0.1:8000`, matching production behavior without CORS complications.

---

## 5. Verification & Testing

### Running Backend Tests
Execute the complete automated regression test suite:
```bash
pytest backend/tests/ -v
```

Execute individual test suites:
```bash
# Authentication & Session Lifecycle (10 stages)
pytest backend/tests/test_auth_lifecycle.py -v

# Community, Polls & Social Feeds
pytest backend/tests/test_community_social.py -v

# Content Safety & Adult Exclusion Filter
pytest backend/tests/test_content_safety.py -v

# Franchise Grouping & Verified Language Tracks
pytest backend/tests/test_franchise_and_language.py -v

# Analytics & RYUK AI Recommendations
pytest backend/tests/test_ryuk_recommendations.py backend/tests/test_analytics.py -v
```

### Validating Frontend Production Build
Verify that the frontend builds cleanly without bundler or syntax errors:
```bash
npm --prefix frontend run build
```

### Database Parity Verification
Verify database referential integrity and orphan-free status:
```bash
python backend/scripts/verify_db_parity.py
```
