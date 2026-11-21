# AnimeVerse AI — Cyberpunk Anime Discovery & Tracking Platform

Welcome to **AnimeVerse AI**, an intelligent, full-stack anime tracking and discovery platform built with Django REST Framework, React Vite, and Google Gemini AI.

---

## 1. System Requirements

- **Python**: 3.10, 3.11, or 3.12+ (Python 3.14 compatible)
- **Node.js**: v18.0.0 or higher (v20+ recommended)
- **Package Managers**: `pip` (Python) and `npm` (Node)
- **Database**: SQLite 3 (included with Python)
- **Operating System**: Windows, macOS, or Linux

---

## 2. Project Architecture

```
AnimeVerse-AI/
├── backend/                  # Django REST Framework Backend
│   ├── apps/
│   │   ├── anime/            # Anime discovery, episodes, search, streaming options
│   │   ├── tracking/         # Watchlist and episode tracking services
│   │   ├── profiles/         # User demo session and profile management
│   │   ├── community/        # Reviews and user interaction
│   │   ├── ryuk/             # RYUK Gemini AI conversational assistant
│   │   └── core/             # Custom exceptions, pagination, middleware
│   ├── config/               # Django settings, ASGI/WSGI, routing
│   ├── tests/                # 95 passing pytest test cases
│   ├── requirements.txt      # Python dependencies
│   ├── manage.py
│   └── .env                  # Backend environment configuration
├── frontend/                 # React 18 + Vite SPA
│   ├── src/
│   │   ├── api/              # Axios clients for anime, watchlist, RYUK
│   │   ├── components/       # Common, layout, and watchlist components
│   │   ├── context/          # WatchlistContext and ThemeContext
│   │   └── pages/            # Dashboard, Discover, Details, My List, Watch Anywhere, RYUK
│   ├── package.json
│   └── vite.config.js
├── screenshots/              # Verified application screenshots for submission
├── FINAL_PROJECT_REPORT.md   # Comprehensive BCA submission project report
├── FINAL_TEST_REPORT.md      # Pytest, build, and E2E test report
└── README.md                 # Setup and startup instructions
```

---

## 3. Environment Variables Setup

### Backend Environment Configuration
Create or inspect `backend/.env`:

```env
# Django Settings
DEBUG=True
SECRET_KEY=django-insecure-animeverse-ai-college-submission-key-2026
ALLOWED_HOSTS=127.0.0.1,localhost

# Upstream Anime Providers
JIKAN_BASE_URL=https://api.tenrai.org/v1

# Google Gemini AI Integration
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Optional Partner Streaming API
WATCHMODE_API_KEY=
```

> **Security Note**: Never commit actual API keys to public source repositories.

---

## 4. Installation & Setup Instructions

### Step 1: Clone or Navigate to Project
```bash
cd E:\LLM\AnimeVerse-AI
```

### Step 2: Backend Setup & Migrations
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Return to root
cd ..
```

### Step 3: Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Return to root
cd ..
```

---

## 5. Startup Commands

Run both servers concurrently in two separate terminal windows:

### Terminal 1 — Start Backend Server (Port 8000)
```bash
cd backend
python manage.py runserver 127.0.0.1:8000
```
*Backend API available at: `http://127.0.0.1:8000/`*

### Terminal 2 — Start Frontend Server (Port 5173)
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
*Frontend web application available at: `http://127.0.0.1:5173/`*

---

## 6. Running Tests & Quality Verification

### Run Backend Pytest Suite
```bash
pytest backend/ -v
```

### Run Franchise Grouping & Verified Language Test Suite
```bash
pytest backend/tests/test_franchise_and_language.py -v
```

### Run Content Safety & Exclusion Suite
```bash
pytest backend/tests/test_content_safety.py -v
```

### Run Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 7. Key Features Walkthrough

1. **Franchise Grouping System**:
   - Related sequels, prequels, movies, OVAs, ONAs, and specials are automatically consolidated under a single primary franchise card in Search and Discover.
   - For example, searching **Black Clover** displays one primary franchise card indicating `7 Entries` instead of cluttering results with 7 duplicate cards.
   - Opening the franchise displays categorized entries: Main Series (170 episodes continuous run, without invented seasons), Sequels (Season 2), Movies (*Sword of the Wizard King*), OVAs (*Jump Festa 2016*), Specials, and Spin-offs (*Squishy! Black Clover*).
   - Selecting any entry opens its dedicated anime page with independent watch progress, status, and episode tracking. An interactive Franchise Navigator banner enables swift navigation across franchise entries.
   - API endpoints:
     - `GET /api/anime/franchises/{id_or_slug}/`
     - `GET /api/anime/{mal_id}/franchise/`

2. **Watch Anywhere — Verified Language Filter**:
   - Filter streaming options by territory (default: India `IN`), audio language (Tamil, English, Japanese, Hindi, Telugu, Malayalam), and subtitle language.
   - Provenance guarantee: Language availability is never inferred from platform name or general catalogue. Only officially verified audio/sub tracks (licensor confirmed or provider reported) are displayed.
   - If an audio language is not confirmed for a title (e.g. Tamil for Black Clover in India), AnimeVerse AI honestly displays: *"No verified Tamil audio option found for this title in India."*
   - Unverified providers display honest disclosure: *"Platform available — audio language unconfirmed."*
   - API endpoint:
     - `GET /api/anime/{mal_id}/watch-options/?country=IN&audio=tam&sub=eng`

3. **Global Content Safety & Hentai Exclusion**:
   - Centralized rule engine (`backend/apps/anime/content_filter.py`) excludes all hentai and explicit adult content across Search, Browse, Trending, Calendar, Dashboard, Watch Anywhere, RYUK, Community, and Watchlist.
   - Protects legitimate non-hentai mature titles (*Berserk*, *Attack on Titan*, *Psycho-Pass*) and broadcast ecchi (*High School DxD*).
   - Stored database rows remain safe, but never leak into visible results or user statistics.

4. **Smart Live Search**:
   - Type in the top navigation search bar. Results appear instantly with debouncing, format badges (`TV`, `Movie`, `OVA`), franchise indicators, and MAL scores. Exact title matches are ranked at the top.

5. **Anime Details & Episode Guide**:
   - Navigate to any anime (e.g. *Sousou no Frieren* or *Demon Slayer*).
   - View backdrop art, synopsis, cast characters, and verified related sequels.
   - Expand any episode to read its genuine description with spoiler warnings.

6. **My List & Stepper Tracking**:
   - Add anime directly to your personal list.
   - Step episodes with `+1` / `-1` buttons.
   - Set 1-10 star scores and personal notes.
   - Watchlist state and statistics are preserved across browser refreshes via session isolation.

7. **RYUK AI Assistant**:
   - Open the **RYUK AI** tab to ask questions about anime story arcs, character analyses, or personalized recommendations powered by Gemini.

---

## 8. Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `CORS Error in Browser` | Backend server not running or wrong origin | Verify backend is running on `127.0.0.1:8000` and frontend on `127.0.0.1:5173`. |
| `Rate Limit 429 from Upstream` | Too many external requests per second | Wait 2 seconds. The built-in rate limiter and SQLite cache handle caching automatically. |
| `Episode description unavailable` | Niche/older anime lacks per-episode summary | This is an intentional data integrity rule; fictional summaries are never invented. |
| `RYUK shows fallback suggestions` | Gemini API key quota reached or offline | Check `GEMINI_API_KEY` in `backend/.env`. RYUK automatically provides curated fallback recommendations. |
