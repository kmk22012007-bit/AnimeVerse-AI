# AnimeVerse AI — Security Model & Threat Mitigation

This document details the security architecture, authentication mechanisms, privilege boundaries, and vulnerability mitigations implemented across **AnimeVerse AI**.

---

## 1. Threat Model & Defense-in-Depth Strategy

AnimeVerse AI implements defense-in-depth across six distinct protective layers:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Edge & Transport: TLS 1.3 / First-Party API Proxying     │
├─────────────────────────────────────────────────────────────┤
│ 2. Session Integrity: Cryptographic Tokens & SameSite=Lax   │
├─────────────────────────────────────────────────────────────┤
│ 3. Authorization & IDOR: Strict Ownership Resolution        │
├─────────────────────────────────────────────────────────────┤
│ 4. Privilege Boundary: Mass-Assignment Defense              │
├─────────────────────────────────────────────────────────────┤
│ 5. Content Safety: Zero-Tolerance Adult / NSFW Exclusion    │
├─────────────────────────────────────────────────────────────┤
│ 6. Data Sanitization: Zero-Leak Fixture & Production Guard  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication & Session Cookie Architecture

Traditional third-party cross-domain cookies fail in modern browsers due to Safari Intelligent Tracking Prevention (ITP), Firefox Enhanced Tracking Protection (ETP), and Chrome Incognito cookie sandboxing.

### The First-Party Edge Proxy Solution
- The client talks to `/api/...` directly on `animeverse-ai.vercel.app`.
- The `animeverse_session` cookie is issued under the frontend's own origin with:
  - `HttpOnly`: Inaccessible to JavaScript, neutralizing XSS credential theft.
  - `SameSite=Lax`: Defends against Cross-Site Request Forgery (CSRF).
  - `Secure`: Transmitted solely over HTTPS connections in production.
- Vercel rewrites `/api/:match*` server-to-server to the Render backend, preserving cookies and headers without client-side cross-origin leakage.

---

## 3. Privilege Escalation & Mass-Assignment Defense

The `User` model defines administrative attributes:
- `role`: Member role (`member`, `moderator`, `admin`).
- `is_staff`: Django administrative access flag.

### Mitigations
In `backend/apps/profiles/serializers.py`:
- `ProfileUpdateSerializer` explicitly whitelists only mutable personal fields: `display_name`, `bio`, and `avatar_url`.
- Any inbound request containing `role`, `is_staff`, or `is_superuser` is strictly ignored by DRF serializer validation.
- Unit tests (`test_auth_lifecycle.py`) systematically verify that non-staff users cannot elevate privileges through API payloads.

---

## 4. Insecure Direct Object Reference (IDOR) Protection

All state-modifying endpoints authenticate the requesting session and query records scoped strictly to that session identity:
- **Watchlist & Tracking**: A user can only view, add, or alter `UserAnimeList` and `EpisodeProgress` records where `user_id == request.user_profile.id`.
- **Community Posts & Comments**: Editing and deletion privileges are restricted to the verified author or authenticated staff moderators.
- **Poll Balloting**: The poll voting engine enforces transaction-isolated checks (`unique_together = ('user', 'option')`) ensuring users cannot tamper with ballot counts or submit duplicate votes (`HTTP 409 Conflict`).

---

## 5. Content Safety & Adult Exclusion

- **Centralized Engine**: `apps/anime/content_filter.py`.
- **Systemic Enforcement**: Querysets across Discovery, Watch Anywhere, Airing Calendar, and RYUK AI are automatically filtered to exclude adult and hentai records.
- **Protection of Mature Seinen**: Mature themes (violence, psychological drama) are distinguished from explicit erotica to avoid false-positive censorship of acclaimed series.

---

## 6. Secret Hygiene & Data Protection

- **Zero-Secret Commitment Policy**: Neither private API keys, database passwords, nor session tokens exist in tracked Git files.
- **Sanitized Staging Data**: `backend/scripts/export_sanitized_staging_data.py` replaces real session keys with synthetic demonstration accounts, guaranteeing zero exposure of private user data.

---

## 7. Advanced Security Hardening (Phase 15)

In Phase 15, the platform implemented targeted hardening controls across the API, AI, and presentation layers:

1. **Scoped API Throttling (`backend/apps/core/throttling.py`)**:
   - `RyukMessageThrottle`: 30 requests/min per session/IP to protect LLM token budgets.
   - `RyukRecommendationThrottle`: 40 requests/min per session/IP.
   - `CommunityActionThrottle`: 40 requests/min per session/IP on post creation, report submission, and polls to prevent automated spam.
   - Returns standardized `HTTP 429 Too Many Requests` envelope.
2. **Error Message Sanitization (`backend/apps/core/exceptions.py`)**:
   - Unhandled internal server exceptions log complete stack traces securely to backend application logs while returning a generic sanitized error message (`"An unexpected internal server error occurred."`) to external callers when `DEBUG=False`.
3. **Review Self-Helpful Prevention (`backend/apps/community/views.py`)**:
   - In `ReviewHelpfulView`, authors are prohibited from voting helpful on their own reviews, preventing score inflation.
4. **Input Array Bounds & Whitespace Validation**:
   - `UserPreferencesSerializer`: list fields (`preferred_genres`, `preferred_formats`, `excluded_genres`) capped at `max_length=30`.
   - String fields across RYUK chat, community posts, reviews, and comments reject empty or solely whitespace payloads.
5. **RYUK Prompt Injection Boundary Guards (`backend/apps/ryuk/services.py`)**:
   - Enhanced `RYUK_SYSTEM_INSTRUCTION` with explicit boundary guards directing the model to ignore and reject any user attempts to overwrite, alter, bypass, or reveal system instructions or role identities.
6. **Frontend External Link Defense-in-Depth (`frontend/src/utils/security.js`)**:
   - External links in `AnimeDetailsPage` and `WatchAnywherePage` validate URLs with `isSafeUrl()`, enforcing strict `https://` / `http://` protocols and neutralizing pseudo-protocol attacks (`javascript:`, `data:`).
