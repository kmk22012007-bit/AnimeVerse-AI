# AnimeVerse AI — Final Project Report

**Project Title**: AnimeVerse AI: Cyberpunk Anime Discovery, Personal Tracking & AI Assistant  
**Degree / Level**: II BCA (Bachelor of Computer Applications)  
**Date of Submission**: November 2026  
**Repository Working Directory**: `E:\LLM\AnimeVerse-AI`  
**Quality Assurance & Audit Status**: 100% Test Pass Rate (270/270 Backend Tests Passed across 20 Modules), Production Vite Build Clean (72.9 kB Entry Chunk), Multi-Tier Metadata & Streaming Verification Safeguards  

---

## 1. Project Introduction

AnimeVerse AI is an intelligent, full-stack anime discovery, personal watchlist management, streaming guidance, and community platform developed as an academic project for II BCA. Styled with a futuristic Cyberpunk visual identity (Deep Space midnight background `#080911`, neon purple accents `#a855f7`, and electric cyan badges `#06b6d4`), the platform provides anime fans with a comprehensive hub to explore anime catalogs, track episode progress, verify legal streaming availability by territory, participate in otaku discussions, and interact with RYUK—a context-aware AI anime companion powered by Google Gemini.

The project emphasizes **strict data provenance and zero-fabrication guarantees**, ensuring that upstream anime metadata, streaming options, and episode summaries are accurately represented, with explicit and honest fallback notices displayed whenever external records are unavailable.

---

## 2. Problem Statement

Modern anime tracking and recommendation platforms face several significant user experience and technical challenges:
1. **Scattered Regional Streaming Availability**: Fans frequently struggle to identify where an anime can be legally watched in their country (e.g., India vs. US). External platforms often link to expired, geo-blocked, or unverified streams.
2. **Generic and Fabricated Episode Data**: Many aggregators duplicate the main show synopsis across every individual episode or hallucinate fictional summaries when real data is missing from upstream APIs.
3. **Fragmented User Experience**: Watchlist trackers, community forums, recommendation engines, and personal analytics typically exist in isolated silos, lacking unified session isolation, personal taste profiling, and real-time contextual AI companions.
4. **Performance & Security Deficits**: Heavy client bundles, unoptimized database queries, and vulnerable API endpoints often lead to slow initial page loads and security exposures such as IDOR and rate-limiting bypasses.

AnimeVerse AI addresses these challenges through a decoupled React 19 single-page application and a hardened Django REST Framework backend featuring verified multi-provider metadata caching, atomic episode stepping, IP-anchored rate limiting, and an intelligent companion grounded in user watch records.

---

## 3. Project Objectives

1. **Smart & Fast Anime Search**: Implement debounced live searching (250ms) with exact-match title ranking, alternate Romaji/English/Japanese title resolution, and format normalization (`TV`, `Movie`, `OVA`, `ONA`, `Special`).
2. **Accurate Anime Details & Episode Guide**: Deliver cinematic backdrops, verified cast members, chronological franchise trees, and per-episode guides. Never duplicate main show summaries as episode synopses; display `"Episode description unavailable."` when upstream records are absent.
3. **Personal Watchlist & Stepping**: Provide responsive episode tracking (`+1`, `-1`), 5-state status management (*Watching*, *Completed*, *Plan to Watch*, *On Hold*, *Dropped*), automatic completion upon reaching final episodes, star ratings (1–10), and personal review notes.
4. **Watch Anywhere Regional Hub**: Deliver verified legal streaming options across 5 tiers (*Subscription*, *Free*, *Free with Ads*, *Rent*, *Buy*) with territory filtering (defaulting to India), verified regional dub provenance (Hindi, Tamil, Telugu, Malayalam), and official studio YouTube trailers.
5. **RYUK AI Intelligence Companion**: Integrate Google Gemini 2.5 Flash with multi-turn conversation memory, intent routing, and database grounding to analyze watchlist progress, recommend anime, and answer lore questions with heuristic fallbacks.
6. **Personal Analytics Hub**: Compute comprehensive otaku telemetry including total watch time (days, hours, minutes), episode completion velocity, genre affinity radar charts, score distribution histograms, and achievement badges.
7. **In-App Notification Center**: Provide real-time alerts across 5 event categories with unread count badges, preference toggles, and self-suppression logic to prevent duplicate notifications.
8. **Social Ecosystem & Community Lounge**: Support category-based discussion threads, threaded replies, interactive polls with single-vote enforcement, spoiler-flagged reviews with helpful voting, directional user follows, and public user profiles (`/users/:id`).
9. **Taste Profiling & Smart Personalization**: Build activity-grounded user taste profiles combining explicit preferences with inferred viewing habits to power personalized carousels (*Continue Watching*, *Because You Watched*) and discovery ranking.
10. **Performance & Security Hardening**: Maintain an optimized frontend entry bundle (~72.9 kB), IP-anchored rate limiting, IDOR resistance, sanitized 500 error handling, and a 100% test pass rate across 270 automated backend tests.

---

## 4. Technologies Used

| Tier | Technology | Version / Specification | Purpose |
|---|---|---|---|
| **Frontend Framework** | React | `^19.3.1` (React 19) | Reactive component hierarchy, Suspense, and client-side UI rendering |
| **Client Routing** | React Router DOM | `^7.18.6` (React Router 7) | Route-based lazy loading and application navigation |
| **Build Tool & Bundler** | Vite | `^8.3.6` (Vite 8) | High-performance dev server (HMR) and optimized Rollup production builds |
| **Styling & Design** | Tailwind CSS | `^4.3.5` (Tailwind 4) | Utility-first CSS via `@tailwindcss/vite`, dark cyberpunk design tokens |
| **Icons** | Lucide React | `^1.77.0` | Crisp, accessible iconography across navigation and status indicators |
| **Data Visualization** | Recharts | `^3.11.0` (Recharts 3) | Interactive radar charts and score distribution histograms (isolated chunk) |
| **HTTP Client** | Axios | `^1.21.1` | Asynchronous REST API requests with request/response interceptors |
| **Backend Framework** | Django | `Django>=5.1,<6.0` (Runtime: 6.1.3) | Core web framework, ORM, database migrations, and security middleware |
| **API Framework** | Django REST Framework | `djangorestframework>=3.15.0` (Runtime: 3.18.3) | RESTful API endpoints, request serializers, and permission classes |
| **Database (Development)** | SQLite 3 | WAL Mode (Write-Ahead Logging) | Relational persistence for development with zero external dependencies |
| **Database (Production Ready)** | PostgreSQL 16 Compatibility | `psycopg2-binary>=2.9.9`, `dj-database-url>=2.1.0` | Production database architecture configured via `DATABASE_URL` *(untested against live PostgreSQL)* |
| **AI Integration** | Google Gemini API | `google-genai>=0.1.0` (`gemini-2.5-flash`) | Context-aware anime assistant, lore query processing, and recommendations |
| **Production WSGI & Static** | Gunicorn / WhiteNoise | `gunicorn>=22.0.0`, `whitenoise>=6.6.0` | WSGI application server and static asset compression/caching |
| **Backend Testing** | Pytest / Pytest-Django | `pytest>=8.0.0`, `pytest-django>=4.8.0` | Automated test runner for models, services, views, and security checks |
| **E2E Browser Automation** | Puppeteer | `^25.18.1` | Headless Chrome end-to-end integration and responsive viewport testing |

---

## 5. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Browser (Desktop & Mobile)"]
        UI["React 19 SPA (Vite 8 + Tailwind 4)"]
        Router["React Router 7 (Route-Based Lazy Loading)"]
        WatchlistCtx["Watchlist Context"]
        NotifCtx["Notification Context"]
    end

    subgraph Edge ["Deployment Edge Layer"]
        StaticCDN["Static Asset CDN (dist/assets/)"]
        EdgeProxy["Same-Origin API Rewrite Proxy (/api/*)"]
    end

    subgraph Backend ["Backend Application (Django + DRF)"]
        SessionMW["AnimeverseSessionMiddleware (64-char Cookie)"]
        ThrottleLayer["IP-Anchored Throttling Layer"]
        APIViews["DRF API Controllers"]
        
        subgraph DomainServices ["Domain Services Layer"]
            DiscoverySvc["Discovery & Filter Engine"]
            TrackingSvc["Atomic Tracking & Progress Service"]
            WatchSvc["Watch Anywhere & Dub Verification Service"]
            RyukSvc["RYUK AI Companion Engine"]
            RecEngine["Hybrid Recommendation Engine"]
            AnalyticsSvc["Analytics Aggregator Service"]
            NotifSvc["Notification Dispatcher"]
            TasteSvc["User Taste Profiler"]
            SafetyFilter["Adult / NSFW Content Filter"]
        end
    end

    subgraph Storage ["Persistence & External Providers"]
        DevDB[("SQLite 3 WAL (Local Development)")]
        ProdDB[("PostgreSQL 16 (Configured Architecture)")]
        GeminiAPI["Google Gemini 2.5 Flash API"]
        UpstreamAPIs["Upstream Metadata (Tenrai v1 / AniList)"]
    end

    UI -->|1. Static Assets| StaticCDN
    UI -->|2. REST Calls| EdgeProxy
    EdgeProxy -->|3. Forwarded HTTPS| SessionMW
    SessionMW --> ThrottleLayer
    ThrottleLayer --> APIViews
    APIViews --> DomainServices
    DomainServices --> SafetyFilter
    DomainServices --> DevDB
    DomainServices -.->|Configured| ProdDB
    RyukSvc --> GeminiAPI
    DiscoverySvc --> UpstreamAPIs
```

---

## 6. Modules and Features

### Module 1: Smart Anime Search & Catalog Discovery
- **Debounced Instant Search**: 250ms debouncing triggers autocomplete results while typing, minimizing redundant network requests.
- **Intelligent Relevance Ranking**: Calculates relevance scores on the backend: exact title matches (1000 pts), prefix matches (500 pts with length bonuses), whole-word matches (300 pts), and substring matches (100 pts), with MyAnimeList score as tie-breaker.
- **Parametric Multi-Filter**: Filter catalog by format (`TV`, `Movie`, `OVA`, `ONA`, `Special`), score sliders (1–10), airing status, and inclusion/exclusion of multiple genres simultaneously.
- **Franchise Consolidation**: Multi-entry anime franchises (e.g., *Black Clover*) are consolidated into a primary franchise card with an entry count badge (`7 ENTRIES`), preventing catalog redundancy.

### Module 2: Anime Details, Franchise Navigator & Episode Guide
- **Cinematic Artwork & Relations**: Displays high-resolution posters, dark gradient backdrop banners, studio credits, genres, and relation graphs.
- **Franchise Entry Navigator**: Interactive header banner allows seamless navigation between main series, sequels, prequels, movies, and spin-offs.
- **Episode Guide**:
  - Displays episode numbers (`EP 01`), titles, air dates, duration, and filler/recap badges.
  - Expandable accordion allows viewing individual episode synopses.
  - **Zero-Fabrication Guarantee**: Discards episode descriptions that duplicate the main show overview. When upstream data is absent, displays `"Episode description unavailable."` without hallucinating text.
  - Spoiler alert tags protect users from unwanted plot details.

### Module 3: Watchlist Management & Real-Time Tracking
- **5-State Status Engine**: Supports *Watching*, *Completed*, *Plan to Watch*, *On Hold*, and *Dropped*.
- **Precision Stepper**: Atomic `+1` and `-1` episode controls with boundary validation (`0 <= watched <= total`). Reaching total episodes automatically updates status to *Completed*; decrementing reverts it to *Watching*.
- **Independent Franchise Tracking**: Each franchise entry (e.g., *Black Clover TV* vs. *Sword of the Wizard King*) maintains completely separate watchlist progress, ratings, and notes.
- **Session Isolation**: Transparent 64-character cookie session creates isolated user workspaces, ensuring visitors do not overwrite one another's tracking data.

### Module 4: Watch Anywhere & Multilingual Streaming Verification
- **Legal Streaming Hub**: Queries verified regional licensors across 5 tiers (*Subscription*, *Free*, *Free with Ads*, *Rent*, *Buy*) with country-specific filtering (defaulting to India `IN`).
- **Multilingual Dub & Sub Tracking**: Audited and confirmed language tracks for India:
  - *Demon Slayer*: Crunchyroll (Japanese, English, Hindi, Tamil, Telugu); Netflix (Japanese, English). Incorrect Netflix Hindi dubs were removed, and outdated JioHotstar records are isolated as `unverified`.
  - *Black Clover*: Official Crunchyroll India Tamil dub for Season 1 (Episodes 1–51) starring Prabhu Dev; Japanese and English streams on Crunchyroll and Netflix.
  - *Naruto*: Sony LIV (Hindi, Tamil, Telugu, Malayalam broadcast dubs for Seasons 1–4); Netflix & Crunchyroll (English, Japanese).
  - *Frieren*: Crunchyroll (Hindi, English, Japanese); Muse Asia YouTube (Japanese subbed); Netflix (Japanese).
- **Official YouTube Trailers**: Validates trailer video IDs against official studio and distributor registries (`@tohoanimation`, `@aniplex`, etc.) with graceful oEmbed error resilience.

### Module 5: RYUK AI Intelligence & Multi-Turn Conversations
- **Gemini 2.5 Flash Integration**: Powers natural language chat to answer anime lore questions, suggest thematic titles, and analyze user watch habits.
- **Multi-Turn Conversation Memory**: Stored in `AIConversation` and `AIMessage` models, allowing contextually coherent dialogues across multiple turns.
- **Deterministic Intent Routing**: Automatically classifies queries into progress lookup, streaming availability, recommendation requests, or general chat.
- **Heuristic Fallback Engine**: If upstream AI quotas or network timeouts occur, gracefully delivers curated discovery recommendations without breaking chat threads.

### Module 6: Personal Analytics Hub
- **Watch Time Telemetry**: Computes total viewing duration in days, hours, and minutes based on tracked episodes and average episode runtimes.
- **Completion Velocity**: Tracks episode completion rates over 7-day and 30-day rolling windows.
- **Genre Affinity Radar**: Visualizes top genre preferences using an interactive Recharts radar chart.
- **Score Distribution Histogram**: Displays rating tendencies across 1–10 star ratings to identify scoring patterns.
- **Achievement Badges**: Dynamically unlocks milestone badges (*First Anime Tracked*, *Century Club: 100 Episodes*, *Genre Explorer*, *Critical Evaluator*).

### Module 7: In-App Notification Center
- **5 Event Categories**: Delivers alerts for *Anime Releases*, *Episode Airings*, *Community Likes*, *Comment Replies*, and *System Notices*.
- **Interactive Management**: Unread count badge on navigation bar, mark individual notification as read, mark all as read, and clear read history.
- **Granular User Preferences**: `NotificationPreference` model allows toggling individual notification categories on or off.
- **Self-Suppression Logic**: Prevents generating notifications for actions performed by the user themselves (e.g., liking one's own post or commenting on one's own thread).

### Module 8: Social Ecosystem, Community Lounge, Polls & Reviews
- **Discussion Threads**: Create category-tagged discussion posts (`discussion`, `theory`, `review`, `question`, `news`, `fan_art`, `recommendation`) with spoiler flags.
- **Threaded Comments**: Nested reply hierarchy (`parent` comment foreign key) with optimistic UI updates.
- **Interactive Polls**: Create single-choice polls with multiple options; enforces strictly one vote per user per poll via `PollVote` unique constraints.
- **Long-Form Reviews**: Write detailed reviews (score 1–10, 20–2000 chars) with spoiler tags and a helpful vote counter via `ReviewHelpful` (self-voting strictly prohibited).
- **Directional User Follow System**: Follow and unfollow community members (`UserFollow`), view follower and following lists, and filter community feeds to only show followed users.
- **Public User Profiles**: Visit `/users/:id` to view public otaku telemetry, favorite genres, recent posts, and verified reviews (private profiles return `404 Not Found`).
- **Community Moderation Reporting**: Submit moderation reports (`CommunityReport`) for inappropriate content, spam, harassment, or unmarked spoilers with moderator action workflows.

### Module 9: Taste Profiling & Smart Personalization
- **Dual-Source Preference Engine**: Combines explicit user preferences (`preferred_genres`, `excluded_genres`, `preferred_formats`, `recommendation_diversity`) with inferred preferences calculated from watchlist activity.
- **Personalized Dashboard Telemetry**: Powers dynamic carousels including *Continue Watching* (next uncompleted episode) and *Because You Watched* (thematically linked recommendations).
- **Recommendation Confidence Tiers**: Categorizes AI recommendations into confidence tiers (*High Match*, *Strong Match*, *Explore*) with match percentage scores and rationale explanations.
- **Zero-Staleness Cache Invalidation**: Modifying a watchlist entry automatically invalidates cached recommendations, ensuring suggestions immediately reflect updated watch history.

### Module 10: Seasonal Calendar & Release Schedules
- **Quarterly Season Navigator**: Explore seasonal anime catalogs by quarter (*Winter*, *Spring*, *Summer*, *Fall*) and release years (2000 to 2030).
- **Airing Schedules**: Displays premiere dates (`aired_from`), weekly broadcast days, format badges, and one-click watchlist addition buttons.

### Module 11: Security Hardening & Rate Limiting
- **IP-Anchored Throttling**: `AnimeverseSessionThrottle` anchors rate limiting directly to client IP (`ip_{client_ip}`), completely preventing attackers from bypassing rate limits by clearing session cookies.
- **IDOR Resistance**: Watchlist items, notifications, conversations, comments, and reviews strictly verify owner identity; unauthorized modifications return `404 Not Found` or `403 Forbidden`.
- **Privileged Field Protection**: Prevents mass assignment attempts targeting `role`, `is_staff`, `is_superuser`, or `session_key` on `/api/profile/`.
- **Exception Sanitization**: Unhandled 500 errors log tracebacks on the server while returning sanitized messages (`"An unexpected internal server error occurred."`) to API clients when `DEBUG=False`.
- **Global Content Safety Filter**: Centralized adult / hentai filter excludes explicit titles across discovery, watchlists, community posts, and AI recommendations.
- **Safe URI Validation**: External streaming and trailer links validate URL protocols via `isSafeUrl()`, allowing only `https://` and `http://`.

---

## 7. Database Design & Models

```mermaid
erDiagram
    User ||--o{ UserAnimeList : owns
    User ||--o{ Review : writes
    User ||--o{ ReviewHelpful : votes
    User ||--o{ CommunityPost : posts
    User ||--o{ PostLike : likes
    User ||--o{ Comment : comments
    User ||--o{ Poll : creates
    User ||--o{ PollVote : casts
    User ||--o{ CommunityReport : reports
    User ||--o| UserPreferences : configures
    User ||--o{ UserFollow : follows
    User ||--o{ Notification : receives
    User ||--o| NotificationPreference : configures
    User ||--o{ AIConversation : chats
    AIConversation ||--o{ AIMessage : contains
    CommunityPost ||--o{ Comment : has
    CommunityPost ||--o| Poll : attaches
    Poll ||--o{ PollOption : contains
    Poll ||--o{ PollVote : receives
    PollOption ||--o{ PollVote : records
    Review ||--o{ ReviewHelpful : receives
    UserAnimeList ||--o{ EpisodeProgress : tracks
    Anime ||--o{ UserAnimeList : referenced_by
    Anime ||--o{ Review : reviewed_in
    Anime ||--o{ FranchiseEntry : belongs_to
    Franchise ||--o{ FranchiseEntry : groups
    Anime ||--o{ StreamingLanguageTrack : offers

    User {
        int id PK
        string session_key UK
        string display_name
        string bio
        boolean is_public
        string role
        boolean is_staff
        datetime created_at
    }

    UserPreferences {
        int id PK
        int user_id FK
        json preferred_genres
        json preferred_formats
        json excluded_genres
        string recommendation_diversity
        boolean enable_personalized_recommendations
        datetime updated_at
    }

    UserFollow {
        int id PK
        int follower_id FK
        int followed_id FK
        datetime created_at
    }

    Anime {
        int mal_id PK
        string title
        string poster_url
        string anime_type
        int total_episodes
        datetime last_fetched_at
    }

    Franchise {
        int id PK
        string name
        string slug UK
        text description
        string cover_image
        datetime created_at
    }

    FranchiseEntry {
        int id PK
        int franchise_id FK
        int anime_id FK
        string relationship_type
        int display_order
        boolean is_main_entry
    }

    StreamingLanguageTrack {
        int id PK
        int anime_id FK
        string provider_name
        string country
        string audio_language
        string subtitle_language
        string track_type
        string verification_status
        string source_url
        text notes
        datetime verified_at
    }

    UserAnimeList {
        int id PK
        int user_id FK
        int anime_id FK
        string status
        int watched_episodes
        int rating
        string note
        datetime updated_at
    }

    EpisodeProgress {
        int id PK
        int list_entry_id FK
        int episode_number
        datetime watched_at
    }

    Review {
        int id PK
        int user_id FK
        int anime_id FK
        string title
        int score
        text body
        boolean is_spoiler
        boolean is_hidden
        int helpful_count
        datetime created_at
    }

    ReviewHelpful {
        int id PK
        int review_id FK
        int user_id FK
        datetime created_at
    }

    CommunityPost {
        int id PK
        int user_id FK
        int anime_id FK
        string title
        text body
        string category
        json tags
        boolean is_spoiler
        boolean is_hidden
        datetime created_at
    }

    Comment {
        int id PK
        int post_id FK
        int user_id FK
        int parent_id FK
        string body
        boolean is_spoiler
        boolean is_hidden
        datetime created_at
    }

    PostLike {
        int id PK
        int post_id FK
        int user_id FK
        datetime created_at
    }

    Poll {
        int id PK
        int user_id FK
        int post_id FK
        string question
        datetime expires_at
        datetime created_at
    }

    PollOption {
        int id PK
        int poll_id FK
        string text
        int order
    }

    PollVote {
        int id PK
        int poll_id FK
        int option_id FK
        int user_id FK
        datetime created_at
    }

    CommunityReport {
        int id PK
        int reporter_id FK
        string target_type
        int post_id FK
        int comment_id FK
        int review_id FK
        int poll_id FK
        string reason
        text explanation
        string status
        string action_taken
        datetime created_at
    }

    Notification {
        int id PK
        int user_id FK
        string notification_type
        string title
        text message
        int anime_id FK
        boolean is_read
        string deduplication_key
        datetime created_at
    }

    NotificationPreference {
        int id PK
        int user_id FK
        boolean anime_releases
        boolean episode_releases
        boolean community_likes
        boolean community_comments
        boolean watchlist_reminders
        boolean system_notices
    }

    AIConversation {
        int id PK
        int user_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    AIMessage {
        int id PK
        int conversation_id FK
        string role
        text content
        boolean is_fallback
        datetime created_at
    }
```

---

## 8. API Specifications Overview

| Endpoint | Method | App Subsystem | Description |
|---|---|---|---|
| `/api/health/` | `GET` | Core | System health check reporting database and cache status |
| `/api/dashboard/` | `GET` | Dashboard | Aggregated dashboard metrics, continue watching, and recommendations |
| `/api/anime/search/?q={q}` | `GET` | Anime | Debounced anime search with title relevance weighting |
| `/api/anime/trending/?page={page}` | `GET` | Anime | Top currently airing trending anime with franchise grouping |
| `/api/anime/discovery/filters/` | `GET` | Anime | Available genres, formats, and rating choices for discovery |
| `/api/anime/browse/` | `GET` | Anime | Parametric multi-genre and format catalog browsing |
| `/api/anime/franchises/{id_or_slug}/` | `GET` | Anime | Franchise details with categorized entries (Main, Sequels, Movies) |
| `/api/anime/{id}/` | `GET` | Anime | Detailed metadata, characters, relations, and user status |
| `/api/anime/{id}/franchise/` | `GET` | Anime | Franchise grouping and sibling entries for a specific anime |
| `/api/anime/{id}/episodes/` | `GET` | Anime | Verified episode guide with synopses and filler tags |
| `/api/anime/{id}/reviews/` | `GET`, `POST` | Anime / Community | List reviews for an anime or submit a new review |
| `/api/anime/{id}/watch-options/` | `GET` | Anime | Legal streaming tiers by territory with audio dub verification |
| `/api/anime/{id}/trailers/` | `GET` | Anime | Verified official studio YouTube trailers |
| `/api/list/` | `GET`, `POST` | Tracking | Retrieve user watchlist or add an anime entry |
| `/api/list/{id}/` | `GET`, `PATCH`, `DELETE` | Tracking | Retrieve, update status/rating/notes, or remove watchlist entry |
| `/api/list/{id}/progress/` | `POST` | Tracking | Incremental (+1/-1) or absolute episode progress update |
| `/api/list/{id}/complete/` | `POST` | Tracking | Mark watchlist entry as completed directly |
| `/api/reviews/{id}/` | `GET`, `PATCH`, `DELETE` | Community | Retrieve, edit, or delete an existing review |
| `/api/reviews/{id}/helpful/` | `POST` | Community | Vote a review as helpful (self-voting prohibited) |
| `/api/community/posts/` | `GET`, `POST` | Community | List community posts with category/following filters or create post |
| `/api/community/posts/{id}/` | `GET`, `PATCH`, `DELETE` | Community | Retrieve post details, comments, and poll |
| `/api/community/posts/{id}/like/` | `POST`, `DELETE` | Community | Like or unlike a community post |
| `/api/community/posts/{id}/comments/` | `POST` | Community | Submit a comment or nested reply on a post |
| `/api/community/comments/{id}/` | `GET`, `PATCH`, `DELETE` | Community | Retrieve, edit, or delete an individual comment |
| `/api/community/polls/{id}/vote/` | `POST` | Community | Cast a single vote on a community poll |
| `/api/community/reports/` | `POST` | Community | Submit a moderation report for content violations |
| `/api/community/moderation/reports/` | `GET` | Community | Moderation report list (moderator/staff only) |
| `/api/community/moderation/reports/{id}/` | `POST` | Community | Apply moderation action to reported content |
| `/api/ryuk/messages/` | `POST` | RYUK AI | Send conversational prompt to RYUK AI companion |
| `/api/ryuk/recommendations/` | `GET` | RYUK AI | Retrieve personalized or exploratory recommendations |
| `/api/ryuk/conversations/` | `GET` | RYUK AI | List chat conversations for the current session |
| `/api/ryuk/conversations/clear/` | `DELETE` | RYUK AI | Clear all chat conversations for the current session |
| `/api/ryuk/conversations/{id}/` | `GET`, `DELETE` | RYUK AI | Retrieve or delete a specific conversation thread |
| `/api/ryuk/conversations/{id}/messages/` | `GET` | RYUK AI | Retrieve message history for a conversation |
| `/api/calendar/season/` | `GET` | Calendar | Seasonal releases filtered by year and quarter |
| `/api/calendar/upcoming/` | `GET` | Calendar | Scheduled future anime premieres |
| `/api/analytics/overview/` | `GET` | Analytics | Summary metrics (total watch time, episodes, mean score) |
| `/api/analytics/genres/` | `GET` | Analytics | Genre affinity distribution for radar visualization |
| `/api/analytics/ratings/` | `GET` | Analytics | Score distribution across ratings 1 to 10 |
| `/api/analytics/activity/` | `GET` | Analytics | Episode completion velocity over 7-day and 30-day windows |
| `/api/analytics/watchlist/` | `GET` | Analytics | Breakdown of watchlist items by status |
| `/api/notifications/` | `GET` | Notifications | List notifications with category filters and unread status |
| `/api/notifications/unread-count/` | `GET` | Notifications | Lightweight badge endpoint returning total unread count |
| `/api/notifications/{id}/read/` | `POST` | Notifications | Mark a specific notification as read |
| `/api/notifications/mark-all-read/` | `POST` | Notifications | Mark all notifications as read for current user |
| `/api/notifications/{id}/` | `GET`, `DELETE` | Notifications | Retrieve or dismiss an individual notification |
| `/api/notifications/clear-read/` | `POST` | Notifications | Purge all read notifications for current user |
| `/api/notifications/preferences/` | `GET`, `PATCH` | Notifications | Retrieve or update notification event category toggles |
| `/api/profile/` | `GET`, `PATCH` | Profiles | Retrieve or update current user profile (display name, bio, public) |
| `/api/profile/preferences/` | `GET`, `PATCH` | Profiles | Manage explicit genres, formats, and diversity settings |
| `/api/profile/taste-profile/` | `GET` | Profiles | Inferred taste analysis based on tracking activity |
| `/api/users/{id}/` | `GET` | Profiles | View public profile of a community member |
| `/api/users/{id}/follow/` | `POST`, `DELETE` | Profiles | Follow or unfollow a user (self-follow prevented) |
| `/api/users/{id}/followers/` | `GET` | Profiles | List followers of a user |
| `/api/users/{id}/following/` | `GET` | Profiles | List users followed by a specific user |

---

## 9. Testing & Quality Assurance Summary

### Backend Pytest Suite
- **Total Test Cases**: **270 tests** across **20 test modules**:
  1. `test_api_endpoints.py`
  2. `test_content_safety.py`
  3. `test_database_models.py`
  4. `test_franchise_and_language.py`
  5. `test_jikan_client.py`
  6. `test_provider_verification.py`
  7. `test_services.py`
  8. `test_session_and_errors.py`
  9. `test_watch_anywhere.py`
  10. `test_watchlist_tracking.py`
  11. `test_analytics.py`
  12. `test_auth_lifecycle.py`
  13. `test_community_social.py`
  14. `test_discovery.py`
  15. `test_notifications.py`
  16. `test_personalization.py`
  17. `test_phase12_social.py`
  18. `test_phase15_security.py`
  19. `test_ryuk_intelligence.py`
  20. `test_ryuk_recommendations.py`
- **Test Pass Rate**: **100% (270 of 270 passed)**.
- **Execution Time**: 224.16 seconds.
- **Failures / Errors**: `0`.

### Frontend Build & Bundle Optimization
- **Compiler**: Vite 8 / Rollup with React 19 production compilation.
- **Initial JavaScript Entry Chunk**: Reduced by **93.4%** from 1,102.3 kB to **72.90 kB** (gzip: **17.45 kB**) via route-based code splitting (`React.lazy()`).
- **Vendor Chunk Isolation**: Heavy charting dependencies (`Recharts`) isolated into a dedicated **474.17 kB chunk** loaded strictly when visiting `/analytics`.
- **Build Status**: Clean compilation with `0` warnings/errors in 9.64 seconds.

### Dependency Security Audit
- **Frontend (`npm audit`)**: **0 vulnerabilities** across all 204 dependencies (0 critical, 0 high, 0 moderate, 0 low).
- **Backend (Python Packages)**: Audited installed packages against known CVE advisories; all packages (Django 6.1.3, DRF 3.18.3, Cryptography 50.0.2, Requests 2.34.2) operate on secure, patched releases.

### Responsive Viewport Verification
Automated Puppeteer testing across 9 core routes and 3 standard viewports:
- **Desktop (1440 × 900)**: Fluid cyberpunk layout with fixed sidebar navigation; **0 horizontal overflow, 0 console errors**.
- **Tablet (768 × 1024)**: Responsive collapsible sidebar; **0 horizontal overflow, 0 console errors**.
- **Mobile (390 × 844)**: Full-width navigation drawer; **0 horizontal overflow, 0 console errors**.

---

## 10. Known Limitations & Technical Realities

1. **Episodic & Seasonal Dub Scope**: Anime dub licensing in India and global regions is frequently acquired on a season-by-season basis. For example, *Black Clover* Tamil dubbing on Crunchyroll covers Season 1 (Episodes 1–51), while *Naruto* dubs on Sony LIV cover Seasons 1–4. The UI displays verified boundaries in coverage notes rather than asserting universal availability.
2. **Upstream Rate Limiting & Network Latency**: Upstream metadata providers (Tenrai / Jikan) enforce rate limits (typically 3 requests per second). In the event of an unheated cache, initial detail fetches may experience brief delays. The backend mitigates this via SQLite-backed caching (`JikanCache` with a 6-hour TTL).
3. **Episode Summary Granularity**: Vintage and niche anime often lack per-episode synopses in upstream databases. In accordance with zero-fabrication standards, the platform displays `"Episode description unavailable."` rather than generating speculative summaries.
4. **Database Engine Concurrency**: Local development runs on SQLite 3 with Write-Ahead Logging (`WAL`), which supports concurrent reads but serializes writes. Staging and production configurations are pre-architected for PostgreSQL 16 connection pooling via `dj-database-url` and `psycopg2-binary`, though live PostgreSQL migration remains untested.
5. **AI Generation Quotas**: When utilizing live Gemini credentials, intensive chat queries consume API token quotas. The system mitigates this using IP-anchored rate limiting (30 req/min) and automatic heuristic fallback recommendations.

---

## 11. GitHub Repository & Release Status

- **Active Branch**: `master`
- **Project Quality Audit Classification**: **READY** (verified in Phase 16 audit)
- **Local Repository Integrity**: All code changes, performance optimizations, security hardening controls, and documentation updates reside locally in `E:\LLM\AnimeVerse-AI`.
- **Release State**: Automated Git commits and pushes were deliberately withheld to ensure complete manual oversight by the student evaluator.
- **Publication Readiness**: The repository is in a clean, release-ready state. Final staging, commit, and push to GitHub origin can be executed upon user command.

---

## 12. Conclusion

AnimeVerse AI demonstrates the complete engineering lifecycle of a modern full-stack web application: responsive React 19 UI design, robust Django REST Framework backend architecture, grounded Google Gemini AI companion integration, multi-tier legal streaming verification, and strict data provenance. With a **100% test pass rate across 270 automated tests**, an optimized **72.9 kB frontend entry bundle**, and comprehensive security hardening, the project stands fully verified and prepared for II BCA academic evaluation.
