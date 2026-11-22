# AnimeVerse AI — Database Architecture & Schema Specification

This document details the relational database design, entity relationships, model specifications, and storage configurations of **AnimeVerse AI**.

---

## 1. Storage Engines & Environment Strategy

AnimeVerse AI supports a dual-engine architecture:

| Environment | Database Engine | Configuration | Use Case |
|---|---|---|---|
| **Local Development** | SQLite 3 | Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), foreign keys enabled | Rapid local prototyping with zero external dependency |
| **Testing / CI** | SQLite 3 | In-memory / isolated file database (`--keepdb` supported) | Fast, isolated automated regression suites |
| **Staging / Production** | PostgreSQL 16 | Managed SSL connection pool via `dj-database-url` | High-concurrency production deployments |

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    User ||--o{ UserAnimeList : tracks
    User ||--o{ EpisodeProgress : logs
    User ||--o{ RyukMessage : chats
    User ||--o{ CommunityPost : authors
    User ||--o{ Comment : writes
    User ||--o{ PostLike : likes
    User ||--o{ CommentLike : likes
    User ||--o{ PollVote : casts
    User ||--o{ Report : flags
    User ||--o{ Notification : receives
    User ||--o{ NotificationPreference : configures
    User ||--|| UserPreferences : configures
    User ||--o{ UserFollow : initiates_follow
    User ||--o{ UserFollow : receives_follow

    Anime ||--o{ UserAnimeList : referenced_in
    Anime ||--o{ EpisodeProgress : has_progress
    Anime ||--o{ FranchiseEntry : belongs_to
    Anime ||--o{ StreamingLanguageTrack : available_on
    Anime ||--o{ CommunityPost : tagged_in

    Franchise ||--o{ FranchiseEntry : contains

    CommunityPost ||--o{ Comment : has_replies
    CommunityPost ||--o{ PostLike : receives_likes
    CommunityPost ||--o{ Poll : contains_poll
    CommunityPost ||--o{ Report : subject_of

    Comment ||--o{ Comment : parent_of_child
    Comment ||--o{ CommentLike : receives_likes
    Comment ||--o{ Report : subject_of

    Poll ||--o{ PollOption : contains_choices
    PollOption ||--o{ PollVote : selected_in

    User {
        int id PK
        string session_token UK
        string display_name
        string avatar_url
        string bio
        string role
        boolean is_staff
        datetime created_at
        datetime updated_at
    }

    Anime {
        int id PK
        int mal_id UK
        string title
        string title_japanese
        string poster_url
        string banner_url
        string synopsis
        string anime_type
        int total_episodes
        string status
        float score
        string rating
        json genres
        json studios
        json season
        int year
        datetime created_at
    }

    Franchise {
        int id PK
        string name UK
        string description
        string slug UK
    }

    FranchiseEntry {
        int id PK
        int franchise_id FK
        int anime_id FK
        string relation_type
        int sequence_order
    }

    StreamingLanguageTrack {
        int id PK
        int anime_id FK
        string platform_name
        string region_code
        string audio_language
        boolean is_verified
        string deep_link_url
    }

    UserAnimeList {
        int id PK
        int user_id FK
        int anime_id FK
        string status
        int score
        int progress_episodes
        datetime started_at
        datetime completed_at
        datetime updated_at
    }

    EpisodeProgress {
        int id PK
        int user_id FK
        int anime_id FK
        int episode_number
        boolean is_completed
        datetime updated_at
    }

    CommunityPost {
        int id PK
        int author_id FK
        int anime_id FK
        string title
        string content
        string topic_tag
        boolean is_spoiler
        boolean is_hidden
        int like_count
        int comment_count
        datetime created_at
    }

    Comment {
        int id PK
        int post_id FK
        int author_id FK
        int parent_id FK
        string content
        boolean is_spoiler
        boolean is_hidden
        datetime created_at
    }

    Poll {
        int id PK
        int post_id FK
        string question
        boolean is_multiple_choice
        datetime expires_at
    }

    PollOption {
        int id PK
        int poll_id FK
        string option_text
        int vote_count
    }

    PollVote {
        int id PK
        int user_id FK
        int option_id FK
        datetime voted_at
    }

    Notification {
        int id PK
        int recipient_id FK
        string category
        string title
        string message
        string action_url
        boolean is_read
        datetime created_at
    }

    UserPreferences {
        int id PK
        int user_id FK,UK
        json preferred_genres
        json preferred_formats
        json excluded_genres
        string recommendation_diversity
        boolean enable_personalized_recommendations
        boolean enable_dashboard_personalization
        boolean enable_discovery_personalization
        datetime updated_at
    }

    UserFollow {
        int id PK
        int follower_id FK
        int followed_id FK
        datetime created_at
    }
```

---

## 3. Core Relational Constraints & Indexing Strategy

1. **Session Resolution**: `User.session_token` carries a unique index (`db_index=True`, `unique=True`) ensuring sub-millisecond session lookup on every inbound request.
2. **Watchlist Uniqueness**: `UserAnimeList` enforces `unique_together = ('user', 'anime')`, preventing duplicate tracking rows per user.
3. **Episode Progress Uniqueness**: `EpisodeProgress` enforces `unique_together = ('user', 'anime', 'episode_number')`, guaranteeing deterministic progress calculations.
4. **Poll Vote Integrity**: `PollVote` enforces `unique_together = ('user', 'option')` and transaction-isolated checks to reject duplicate ballot submissions.
5. **Streaming Language Provenance**: `StreamingLanguageTrack` indexes `('anime', 'platform_name', 'region_code')` to rapidly resolve territory-specific licensing queries.
6. **User Preferences Isolation**: `UserPreferences` enforces strict OneToOne cardinality with `User` (`OneToOneField(User, related_name='preferences')`), providing secure, isolated personalization controls per user session.
7. **Follow Relationship Uniqueness & Performance**: `UserFollow` enforces `UniqueConstraint(fields=['follower', 'followed'], name='unique_user_follow_pair')` to reject duplicate follow links and self-following, while indexing `follower_id` and `followed_id` for efficient following feed queries and count aggregations.
8. **Watchlist Query & Invalidation Indexing (Phase 14)**: `UserAnimeList` defines compound indexes:
   - `user_anime_status_idx`: `('user', 'status')` for rapid watchlist status filtering.
   - `user_anime_updated_idx`: `('user', '-updated_at')` for sub-millisecond cache version checks and recent activity ordering.
   - `anime_status_idx`: `('anime', 'status')` for anime-centric engagement calculations.
9. **Community Feed Indexing (Phase 14)**: `CommunityPost` defines compound indexes:
   - `comm_post_hidden_created_idx`: `('is_hidden', '-created_at')` for main feed pagination without full table scans.
   - `comm_post_cat_created_idx`: `('category', '-created_at')` for category-specific feed queries.
   - `comm_post_anime_created_idx`: `('anime', '-created_at')` for anime detail discussion feeds.
   - `comm_post_user_created_idx`: `('user', '-created_at')` for user profile post histories.
10. **Comment & Discussion Hierarchy Indexing (Phase 14)**: `Comment` defines compound indexes:
    - `comm_comment_post_idx`: `('post', 'is_hidden', 'created_at')` for thread reply fetching.
    - `comm_comment_parent_idx`: `('parent', 'created_at')` for nested reply trees.
11. **Review Query Indexing (Phase 14)**: `Review` defines compound indexes:
    - `rev_anime_hidden_created_idx`: `('anime', 'is_hidden', '-created_at')` for anime review listings.
    - `rev_user_created_idx`: `('user', '-created_at')` for user profile review history.
