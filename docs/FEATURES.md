# AnimeVerse AI — Complete Feature Catalog

This document details all functional capabilities and subsystem features implemented across **AnimeVerse AI**.

---

## 1. Global Content Safety & Adult Exclusion Filter

- **Core Module**: `backend/apps/anime/content_filter.py`
- **Objective**: Prevent explicit adult (hentai, erotica, and non-mainstream adult animation) titles from leaking into public feeds, search results, recommendations, community threads, or user lists, while safely preserving mainstream mature seinen anime (e.g., *Berserk*, *Monster*, *Psycho-Pass*).
- **Multi-Layer Exclusion Logic**:
  - Excludes explicit genres and themes (`Hentai`, `Erotica`).
  - Filters titles by age rating (`Rx - Hentai`).
  - Evaluates keyword heuristics on synopsis and title fields.
- **Enforcement Points**:
  - Parametric discovery search.
  - Quick-search debounced autocomplete.
  - RYUK AI recommendation candidate pool.
  - Airing calendar schedule.
  - Watchlist addition validation.

---

## 2. Watch Anywhere & Streaming Language Provenance

- **Core Module**: `backend/apps/anime/watch_service.py`
- **Objective**: Provide verified, territory-specific streaming availability with strict provenance tracking to avoid misleading users regarding dub and sub availability.
- **Capabilities**:
  - **Verified Platform Integration**: Displays confirmed platforms (Crunchyroll, Netflix, Hulu, Disney+, Prime Video, Muse Asia) with official icons.
  - **Audio Track Verification**: Explicit confirmation of original Japanese, English, and regional dubs (e.g. Hindi, Tamil, Telugu, Spanish, Portuguese).
  - **Unverified Fallback Rule**: If an audio track is not officially corroborated by verified distributors, the platform renders an explicit *Unconfirmed* status rather than guessing.

---

## 3. Franchise Grouping & Chronological Hierarchy

- **Core Module**: `backend/apps/anime/franchise_service.py`
- **Objective**: Organize sprawling anime properties (prequels, sequels, OVAs, movies, spin-offs) into structured franchise trees.
- **Capabilities**:
  - **Franchise Tree Navigator**: Visual hierarchical view showing parent franchise, main canon series, side stories, and theatrical movies.
  - **Search De-Cluttering**: Option to group search results by franchise rather than flooding the catalog with individual seasonal entries.
  - **Watch Order Guidance**: Chronological and release-order indicators to guide newcomers through long-running sagas.

---

## 4. RYUK AI Context-Aware Companion & Hybrid Recommendation Engine (Phase 10 Upgrade)

- **Core Module**: `backend/apps/ryuk/`
- **Objective**: Provide a context-aware conversational anime intelligence companion and explainable hybrid recommendation engine.
- **Capabilities**:
  - **Context-Aware Conversational Companion**: Understands the user's personal watchlist, completed titles, ratings, and current episode progress.
  - **Grounded Intent Handling**:
    - Progress summaries calculated from database records.
    - Specific anime progress lookups (e.g. *"What episode am I on for Demon Slayer?"*).
    - Verified streaming availability guidance (e.g. *"Where can I watch Demon Slayer in Hindi?"*).
  - **Multi-Turn Dialogue Memory**: Retains conversational context across recent message turns.
  - **Explainable Hybrid Recommendations**:
    - Multi-signal scoring combining genre affinity, studio affinity, user ratings, and community score.
    - `confidence_tier` classification (*Very High Affinity*, *High Affinity*, *Strong Match*, *Curated Match*).
    - Dual modes: `mode='personalized'` (aligned with top tastes) and `mode='different'` (serendipitous exploration of unexplored genres).
  - **Negative Filtering**: Automatically excludes completed and watching titles.
  - **Hallucination Guard**: Never fabricates release dates, episode numbers, or unverified audio tracks.
  - **Deterministic Offline Fallback**: Fully functional heuristic fallback when external AI is unconfigured or unreachable.
  - **Conversation Management**: Delete individual conversations or clear chat history with strict IDOR defense.

---

## 5. Advanced Analytics & Personal Watch Statistics

- **Core Module**: `backend/apps/analytics/`
- **Objective**: Transform raw watch history into insightful visualizations and gamified milestones.
- **Capabilities**:
  - **Watch Time Computation**: Accurate breakdown of total time invested in anime, converted into days, hours, and minutes.
  - **Completion Metrics**: Real-time completion velocity, series completion rate, and average score calculations.
  - **Genre Affinity Radar**: Dynamic multi-axis radar chart mapping top genre preferences from 5-star ratings.
  - **Score Distribution Histogram**: Bar chart illustrating user rating distribution from 1 to 10.
  - **Achievement Badges**: Dynamically calculated milestones (e.g., *Century Club*, *Shonen Veteran*, *Eclectic Viewer*).

---

## 6. Intelligent In-App Notification Hub

- **Core Module**: `backend/apps/notifications/`
- **Objective**: Deliver real-time, non-intrusive activity updates and alerts.
- **Capabilities**:
  - **5 Event Categories**:
    - `EPISODE_RELEASE`: Notifications when followed airing titles drop a new episode.
    - `ANIME_UPDATE`: Status or license changes on watchlisted items.
    - `COMMUNITY_REPLY`: Alerts when another member replies to your post or comment.
    - `RECOMMENDATION`: Periodic tailored alerts from the RYUK AI engine.
    - `SYSTEM_ALERT`: Platform updates and announcements.
  - **Self-Suppression & Anti-Spam**: Suppresses notifications triggered by the user's own actions and coalesces duplicate alerts.
  - **Spoiler-Safe Snippets**: Truncates and sanitizes comment notifications containing spoilers.
  - **Notification Drawer**: Unread badge counters, instant mark-all-read action, and category preference toggles.

---

## 7. Parametric Anime Discovery Engine

- **Core Module**: `backend/apps/anime/discovery_service.py`
- **Objective**: High-speed, multi-criteria anime exploration.
- **Capabilities**:
  - **Multi-Genre Filter**: Include and exclude genres simultaneously.
  - **Media Formats**: Filter by `TV`, `Movie`, `OVA`, `ONA`, and `Special`.
  - **Airing Status & Season**: Filter by currently airing, finished, or upcoming seasons.
  - **Score Sliders**: Set minimum and maximum community score thresholds.
  - **Sort Modes**: Sort by popularity, score, release date, or title.
  - **Debounced Search**: Instant live search queries with local caching to prevent redundant upstream requests.

---

## 8. Cyberpunk Community Hub, Polls & Moderation

- **Core Module**: `backend/apps/community/`
- **Objective**: Foster a vibrant, spoiler-safe community space for anime discussions.
- **Capabilities**:
  - **Rich Post Feeds**: Markdown-formatted posts, anime card attachments, and topic tags.
  - **Collapsible Spoiler Tags**: Community content containing spoilers is masked behind interactive reveal buttons.
  - **Interactive Polls**: Fraud-resistant community voting engine enforcing single-vote rules (`409 Conflict` on duplicates).
  - **Nested Comment Trees**: Multi-level discussions with upvoting.
  - **Staff Moderation Console**: Role-guarded dashboard (`/community/moderation`) allowing staff to review user reports, dismiss false flags, or purge infringing content.

---

## 9. Frictionless Session Authentication & Profile System

- **Core Module**: `backend/apps/core/middleware.py` & `backend/apps/profiles/`
- **Objective**: Instant guest onboarding with persistent session identity and zero forced registration friction.
- **Capabilities**:
  - **Automatic Cookie Provisioning**: Generates a 64-character cryptographic token on first visit.
  - **Identity Persistence**: Preserves watchlists, analytics, votes, and notification preferences across browser sessions.
  - **Profile Customization**: Users can personalize display names, bios, and avatar selections.
  - **Mass-Assignment Defense**: Enforces strict serializer whitelists preventing unauthorized escalation of user roles or staff permissions.

---

## 10. Anime Personalization & Smart User Experience (Phase 11)

- **Core Modules**: `backend/apps/profiles/services.py`, `backend/apps/dashboard/services.py`, `backend/apps/anime/discovery_service.py`, `backend/apps/ryuk/services.py`
- **Objective**: Deliver a customized, activity-grounded user experience that cleanly distinguishes behavioral inferred taste signals from user-configured explicit preferences.
- **Capabilities**:
  - **Personal Anime Taste Profile**:
    - Analyzes real user tracking history, episode velocity, and completion rate.
    - Classifies user rating tendencies (*Enthusiastic & Generous*, *Balanced & Measured*, *Discerning & Critical*).
    - Extracts top inferred genres and studios with evidence chips (e.g. `Action (6 titles, avg 8.8/10)`).
    - Produces grounded, human-readable natural language taste summaries.
    - Cold-start calibration for new users with 0–2 tracked series.
  - **Personalized Dashboard Upgrade**:
    - `continue_watching` with progress percentage bars and quick episode steppers.
    - `recently_completed` showcase strip of finished series.
    - `because_you_watched` carousels seeded from the user's highest rated completed anime.
    - `recommended_for_you` powered by the RYUK recommendation engine.
    - `explore_new_genres` highlighting top-rated anime outside the user's comfort zone.
    - `your_anime_journey` live telemetry summary (hours watched, completion rate %, top genre).
  - **Smart Discovery Personalization**:
    - Optional `personalized=true` toggle boosting preferred and inferred genres without breaking normal sorting.
    - Optional `hide_tracked=true` toggle filtering out watched and in-progress anime.
    - Automatic exclusion of user's `excluded_genres`.
    - Recommendation reason chips (e.g., *"Matches your affinity for Sci-Fi"*).
  - **User Preference Controls**:
    - Dedicated preference management via `GET`/`PUT` `/api/profile/preferences/`.
    - Granular feature toggles (`enable_personalized_recommendations`, `enable_dashboard_personalization`, `enable_discovery_personalization`).
    - Recommendation diversity selector (`focused`, `balanced`, `exploratory`).
    - Multi-select genre inclusion and exclusion lists with server-side validation.
  - **RYUK Taste Intelligence Integration**:
    - Natural language queries like *"Explain my anime taste"* grounded in real profile telemetry.
    - Genre departure queries like *"Recommend a different genre"* recommending unexplored styles.
    - Strict adherence to explicit exclusions and preferences over inferred signals.

---

## 11. Advanced Social & Community Experience (Phase 12)

- **Core Modules**: `backend/apps/profiles/models.py`, `backend/apps/profiles/views.py`, `backend/apps/community/views.py`, `backend/apps/notifications/services.py`, `frontend/src/pages/CommunityPage.jsx`, `frontend/src/pages/ProfilePage.jsx`
- **Objective**: Provide a complete social layer with directional user follows, personalized community feeds, threaded discussions, safe user mentions, review feedback, and comprehensive public profiles.
- **Capabilities**:
  - **User Follow System**:
    - Directional follow/unfollow API via `POST` & `DELETE` `/api/users/<id>/follow/`.
    - Paginated followers and following user lists via `GET /api/users/<id>/followers/` and `GET /api/users/<id>/following/`.
    - Live follower and following counts integrated directly into user profile endpoints.
    - Strict validation rejecting self-following (`400 Bad Request`) and database `UniqueConstraint` preventing duplicate relationships.
    - Automatic in-app notification dispatching (`NotificationType.SYSTEM`) when a user gains a follower.
  - **Personalized Community Feed**:
    - "Following" feed mode (`sort=following` or `feed=following`) displaying posts strictly from followed authors.
    - Genre-based community filtering (`genre=<genre>`) matching discussion tags and anime references.
    - Seamless tab bar navigation with "Latest", "Following", "Trending", "Most Liked", and "Most Discussed".
  - **Social Interactions & Mentions**:
    - Threaded discussion comments and nested replies with spoiler protection.
    - Like/unlike toggles on community posts.
    - Helpful review voting via `POST /api/reviews/<id>/helpful/` with real-time feedback tally.
    - Safe `@username` mention detection in posts and comments, dispatching in-app notifications (`NotificationType.COMMUNITY_COMMENT`) with self-mention suppression and deduplication.
  - **Enhanced Public User Profiles**:
    - Public user view at `/users/:id` showing avatar, display name, bio, join date, and follow status.
    - Follow/Unfollow action button with immediate UI reflection.
    - Click-to-open Followers & Following modal with in-modal follow toggles.
    - Public Anime Activity summary (completed count, episodes watched, mean rating, top favorite genres).
    - Community Activity summary (discussion count, comment count, review count) and recent public post cards.

---

## 12. Premium UI/UX & Visual Experience (Phase 13)

- **Core Modules**: `frontend/src/index.css`, `frontend/src/components/layout/`, `frontend/src/components/common/`, `frontend/src/pages/`, `docs/DESIGN_SYSTEM.md`
- **Objective**: Establish an accessible, production-grade design system and elevate the platform's visual quality, responsiveness, usability, and accessibility across all screen sizes.
- **Capabilities**:
  - **Comprehensive Design System**:
    - Semantic CSS tokens for colors, typography scale, spacing, border radius, shadows, and elevation layers.
    - Cohesive dark anime aesthetic featuring midnight black (`#080911`), deep panel backgrounds (`#0e101d`), elevated cards (`#131627`), and restrained purple accents without disorienting neon saturation.
    - Documented thoroughly in `docs/DESIGN_SYSTEM.md`.
  - **Upgraded Navigation Experience**:
    - **Sidebar**: Active navigation route vertical pill indicator (`w-1 h-5 bg-gradient-to-b from-purple-400 to-cyan-400`), ergonomic touch targets (`min-h-[44px]`), accessible ARIA navigation landmarks, and keyboard shortcut cue.
    - **Top Navigation**: Responsive mobile search drawer button for screens `< 640px`, accessible interactive user profile route link, and notification bell.
    - **Search Bar**: Global `/` keyboard shortcut, keyboard arrow navigation (`ArrowDown`/`ArrowUp`) with `Enter` selection across suggestion items, `Escape` key dismissal, and combobox ARIA roles (`role="combobox"`, `role="listbox"`, `role="option"`, `aria-selected`).
  - **Page-by-Page Visual Refinement**:
    - **Dashboard**: High-contrast hero banner vignette, live journey telemetry metrics, unified glass telemetry cards with subtle border gradients, and responsive carousels.
    - **Discover**: Advanced filter matrix panel, active filter chips strip with single-click removal, score slider, format buttons, and responsive grid (`grid-cols-2` up to `grid-cols-5`).
    - **Anime Details**: Seamless hero backdrop transition into midnight canvas, prominent watchlist tracking bar with episode steppers and modal actions, legal streaming cards with verified badge styling, and spoiler warning tags.
    - **RYUK AI Intelligence Hub**: Elevated message bubbles (gradient for user, midnight glass with border glow for assistant), glowing bot avatar, grounded prompt suggestion chips with hover scale feedback, and responsive input with Enter-to-send support.
    - **Watch Anywhere & Watchlist**: Accessible status filter pill strips, platform cards with verified audio track labels, and responsive episode steppers.
  - **Full Accessibility & Viewport Compliance (WCAG 2.1 AA)**:
    - Global accessible `:focus-visible` indicators with 2px purple outline and 2px offset.
    - Built-in `@media (prefers-reduced-motion: reduce)` disabling non-essential transitions for motion-sensitive users.
    - Minimum 4.5:1 text contrast across all midnight card surfaces and high-contrast badges.
    - Verified responsive behavior across 6 viewports: 360px (ultra-compact mobile), 390px (mobile), 768px (tablet), 1024px (laptop), 1440px (desktop), and 1920px (large desktop).

