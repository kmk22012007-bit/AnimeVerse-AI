# AnimeVerse AI — Complete API Documentation

Base URL: `http://127.0.0.1:8000/api`

All endpoints accept and return `application/json` unless otherwise stated. Authentication is handled transparently via the `animeverse_session` session cookie.

---

## 1. Authentication & User Profile

### `GET /api/profile/`
Returns the current user profile, watchlist summary, role, and favorite anime.

**Response (200 OK):**
```json
{
  "id": 73,
  "display_name": "Levi Ackerman",
  "bio": "Captain of the Survey Corps",
  "is_public": true,
  "role": "moderator",
  "is_staff": true,
  "is_moderator": true,
  "joined_at": "2026-11-20T17:00:00Z",
  "stats": {
    "total_anime": 15,
    "completed_count": 8,
    "total_episodes_watched": 240,
    "average_rating": 8.5
  },
  "status_counts": { "watching": 3, "completed": 8, "plan_to_watch": 4, "on_hold": 0, "dropped": 0 },
  "recent_activity": [...],
  "favorites": [...]
}
```

### `PATCH /api/profile/`
Updates user profile fields (`display_name`, `bio`, `is_public`).
**Security Rule**: Attempts to modify `role`, `is_staff`, or `is_superuser` are rejected with **400 Bad Request**.

---

## 2. Anime Catalog, Search & Discovery

### `GET /api/anime/discovery/filters/`
Returns dynamically available filters, including verified audio languages derived from confirmed database records.

**Response (200 OK):**
```json
{
  "genres": [...],
  "formats": ["tv", "movie", "ova", "ona", "special"],
  "statuses": ["airing", "complete", "upcoming"],
  "sort_options": [
    { "value": "-score", "label": "Highest Rated" },
    { "value": "score", "label": "Lowest Rated" },
    { "value": "-start_date", "label": "Newest Release" },
    { "value": "start_date", "label": "Oldest Release" },
    { "value": "-episodes", "label": "Most Episodes" },
    { "value": "title", "label": "Title (A-Z)" },
    { "value": "relevance", "label": "Relevance" }
  ],
  "available_audio_languages": ["Tamil", "Hindi", "Telugu", "Japanese", "English", "Malayalam"],
  "available_countries": ["IN"]
}
```

### `GET /api/anime/browse/`
Advanced parametric anime discovery.

**Query Parameters:**
- `q`: Search keyword (matched against title/Japanese title).
- `genres`: Comma-separated list of included genres.
- `exclude_genres`: Comma-separated list of excluded genres.
- `format`: `tv`, `movie`, `ova`, `ona`, `special`.
- `year` / `year_from` / `year_to`: Release year bounds.
- `min_score` / `max_score`: Minimum and maximum score (strictly omits unrated anime).
- `status`: `airing`, `complete`, `upcoming`.
- `min_episodes` / `max_episodes`: Episode count bounds.
- `audio_language`: Confirmed audio language (e.g. `Tamil`, `Hindi`).
- `country`: Country ISO code (default `IN`).
- `sort`: Sort mode (e.g. `-score`, `-start_date`).
- `page`: Page index (default `1`).

### `GET /api/anime/{mal_id}/`
Retrieves detailed anime metadata, characters, studio info, ratings, and synopsis.
**Content Safety**: Blocked hentai / adult IDs return **404 Not Found**.

### `GET /api/anime/{mal_id}/franchise/`
Returns verified franchise relationship hierarchy (sequels, prequels, spin-offs).

### `GET /api/anime/{mal_id}/watch-options/`
Returns streaming providers and verified audio/subtitle tracks for the specified territory.

---

## 3. Watchlist & Progress Tracking

### `GET /api/watchlist/`
Returns the user's personal anime list with status, progress, ratings, and personal notes.

### `POST /api/watchlist/`
Adds an anime to the user's watchlist.
**Payload:**
```json
{
  "anime_id": 16498,
  "status": "watching",
  "watched_episodes": 5,
  "rating": 9,
  "personal_notes": "Masterpiece pacing"
}
```

### `PATCH /api/watchlist/{id}/`
Updates progress, status, or rating.

### `DELETE /api/watchlist/{id}/`
Removes an entry from the user's watchlist.

---

## 4. RYUK AI Recommendation Engine

### `GET /api/ryuk/recommendations/`
Generates personalized anime recommendations tailored to user watchlist preferences, ratings, and genre affinities. Excludes completed and currently watching anime.

**Response (200 OK):**
```json
{
  "recommendations": [
    {
      "anime_id": 16498,
      "title": "Attack on Titan",
      "poster_url": "https://...",
      "genres": ["Action", "Suspense"],
      "explanation": "Because you rated dark military anime highly...",
      "confidence": 0.94,
      "recommendation_type": "personalized",
      "available_on": ["Crunchyroll", "Netflix"]
    }
  ],
  "engine": "gemini-3.5-flash-lite",
  "user_context": { "total_tracked": 12, "top_genre": "Action" }
}
```

### `POST /api/ryuk/chat/`
Interactive conversational anime assistant.
**Payload:** `{ "message": "Suggest a thriller like Death Note" }`

---

## 5. Advanced Analytics

### `GET /api/analytics/overview/`
Computes real-time personal analytics from database records.
- Total watch time in hours and days.
- Watch status breakdown (watching, completed, plan to watch, dropped).
- Genre distribution percentages.
- Mean score and rating histogram.
- 30-day activity trend.

---

## 6. Notifications System

### `GET /api/notifications/`
Returns paginated user notifications.

### `GET /api/notifications/unread-count/`
Returns `{ "unread_count": 3 }`.

### `PATCH /api/notifications/{id}/read/`
Marks a specific notification as read.

### `POST /api/notifications/mark-all-read/`
Marks all notifications as read for the user.

### `DELETE /api/notifications/{id}/`
Deletes a specific notification.

### `DELETE /api/notifications/clear-read/`
Clears all read notifications.

### `GET /api/notifications/preferences/` & `PATCH /api/notifications/preferences/`
Manages notification toggles (anime releases, community likes, comments, etc.).

---

## 7. Community, Polls & Moderation

### `GET /api/community/posts/`
Returns community feed sorted by `latest`, `trending`, `popular`, or `discussed`. Supports filtering by `anime_id`, `category`, and `tag`.

### `POST /api/community/posts/`
Creates a new post with optional anime reference, tags, spoiler flag, and embedded poll.

### `GET /api/community/posts/{id}/`
Returns post details, attached poll status, and nested threaded comments.

### `POST /api/community/posts/{id}/like/` & `DELETE /api/community/posts/{id}/like/`
Toggles like on a post.

### `POST /api/community/posts/{id}/comments/`
Adds a root comment or a reply (`parent_id`).

### `POST /api/community/polls/{id}/vote/`
Casts a single vote on a poll option. Duplicate votes return **409 Conflict**.

### `POST /api/community/reports/`
Submits a user report for a post, comment, review, or poll.

### `GET /api/community/moderation/reports/`
**Staff / Moderator Only**. Lists pending and resolved reports. Normal users receive **403 Forbidden**.

### `PATCH /api/community/moderation/reports/{id}/`
**Staff / Moderator Only**. Actions a report (`content_hidden`, `content_deleted`, `dismissed`).

### `GET /api/anime/{mal_id}/reviews/`
Lists reviews for an anime with sorting by `recent`, `helpful`, `highest_rating`, `lowest_rating`.

### `POST /api/anime/{mal_id}/reviews/`
Submits a review with score (1–10), optional title, body, and spoiler flag.

### `POST /api/reviews/{id}/helpful/`
Toggles helpful vote on a review.
