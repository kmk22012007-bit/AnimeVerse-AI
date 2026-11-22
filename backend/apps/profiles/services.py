import logging
from collections import Counter
from django.db.models import Avg, Count
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.anime.models import Anime, JikanCache
from apps.anime.content_filter import is_excluded_adult_anime

logger = logging.getLogger(__name__)

class TasteProfileService:
    """
    Intelligent anime taste profiling service.
    Analyzes verified user activity (watchlists, episode logs, ratings, completions)
    and cleanly separates inferred taste signals from explicit user preferences.
    """

    @classmethod
    def get_taste_profile(cls, user):
        """
        Computes a comprehensive, explainable taste profile for the authenticated user.
        """
        # Ensure preferences model exists
        prefs = user.get_or_create_preferences()

        all_user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
            .order_by('-updated_at')
        )
        valid_entries = [e for e in all_user_entries if not is_excluded_adult_anime(e.anime)]

        # Categorize by status
        completed = [e for e in valid_entries if e.status == WatchStatus.COMPLETED]
        watching = [e for e in valid_entries if e.status == WatchStatus.WATCHING]
        dropped = [e for e in valid_entries if e.status == WatchStatus.DROPPED]
        plan_to_watch = [e for e in valid_entries if e.status == WatchStatus.PLAN_TO_WATCH]

        # Ratings analysis
        rated = [e for e in valid_entries if e.rating is not None]
        avg_score = round(sum(e.rating for e in rated) / len(rated), 2) if rated else None

        if avg_score is not None:
            if avg_score >= 8.5:
                rating_tendency = "Enthusiastic & Generous (Scores 8.5+ on average)"
            elif avg_score <= 6.5:
                rating_tendency = "Discerning & Critical (Scores 6.5 or below on average)"
            else:
                rating_tendency = "Balanced & Measured (Moderate 7.0–8.4 average)"
        else:
            rating_tendency = "Unrated (No ratings logged yet)"

        # Completion rate
        total_decided = len(completed) + len(dropped)
        completion_rate_pct = round((len(completed) / total_decided) * 100, 1) if total_decided > 0 else 100.0

        # Genre & Studio Aggregation with evidence tracking
        genre_weights = Counter()
        genre_titles = {}  # genre -> list of (title, rating)
        studio_weights = Counter()
        studio_titles = {}  # studio -> list of (title, rating)
        format_counts = Counter()

        for entry in valid_entries:
            anime = entry.anime
            mal_id = anime.mal_id
            rating = entry.rating or 0

            # Weighting factors
            weight = 1
            if rating >= 9:
                weight = 3
            elif rating >= 7 or entry.status == WatchStatus.COMPLETED:
                weight = 2
            elif entry.status == WatchStatus.DROPPED:
                weight = -1

            # Format tracking
            fmt = (anime.anime_type or 'TV').upper()
            format_counts[fmt] += 1

            # Extract genres and studios from cached payload or anime model
            genres = []
            studios = []
            cached = (
                JikanCache.objects.filter(cache_key=f"anime:{mal_id}:full").first()
                or JikanCache.objects.filter(cache_key=f"details_{mal_id}").first()
            )
            if cached and isinstance(cached.payload, dict):
                d = cached.payload.get('data') or cached.payload
                raw_genres = d.get('genres', [])
                for g in raw_genres:
                    name = g.get('name') if isinstance(g, dict) else str(g)
                    if name and name.lower() not in ('hentai', 'erotica'):
                        genres.append(name)
                raw_studios = d.get('studios', [])
                for s in raw_studios:
                    name = s.get('name') if isinstance(s, dict) else str(s)
                    if name:
                        studios.append(name)
            else:
                # Fallback to model anime_type / title
                pass

            for g in genres:
                genre_weights[g] += weight
                if g not in genre_titles:
                    genre_titles[g] = []
                if rating >= 7 or entry.status == WatchStatus.COMPLETED:
                    genre_titles[g].append((anime.title, rating))

            for s in studios:
                studio_weights[s] += weight
                if s not in studio_titles:
                    studio_titles[s] = []
                if rating >= 7 or entry.status == WatchStatus.COMPLETED:
                    studio_titles[s].append((anime.title, rating))

        # Top Inferred Genres with explanations
        top_inferred_genres = []
        for g, score in genre_weights.most_common(5):
            if score <= 0:
                continue
            evidence = genre_titles.get(g, [])
            count = len(evidence)
            rated_vals = [r for _, r in evidence if r > 0]
            avg_rating = round(sum(rated_vals) / len(rated_vals), 1) if rated_vals else None

            if evidence:
                top_refs = [f"{t} ({r}/10)" if r > 0 else t for t, r in evidence[:2]]
                explanation = f"Inferred from your positive engagement with {', '.join(top_refs)} ({count} titles)"
            else:
                explanation = f"Inferred from your active watchlist tracking ({count} titles)"

            top_inferred_genres.append({
                'name': g,
                'genre': g,
                'count': count,
                'avg_rating': avg_rating,
                'affinity_score': score,
                'explanation': explanation,
                'evidence': explanation,
            })

        # Top Inferred Studios with explanations
        top_inferred_studios = []
        for s, score in studio_weights.most_common(3):
            if score <= 0:
                continue
            evidence = studio_titles.get(s, [])
            count = len(evidence)
            if evidence:
                top_refs = [f"{t} ({r}/10)" if r > 0 else t for t, r in evidence[:2]]
                explanation = f"Inferred from acclaimed titles you watched: {', '.join(top_refs)} ({count} titles)"
            else:
                explanation = f"Inferred from your watchlist history ({count} titles)"

            top_inferred_studios.append({
                'name': s,
                'studio': s,
                'count': count,
                'affinity_score': score,
                'explanation': explanation,
                'evidence': explanation,
            })

        # Preferred format
        top_format = format_counts.most_common(1)[0][0] if format_counts else "TV"

        # Construct Natural Language Taste Summary
        if len(valid_entries) == 0:
            taste_summary = "Welcome to AnimeVerse! No dominant watch patterns detected yet. Track titles or set explicit preferences below to calibrate your taste profile."
        elif len(valid_entries) < 3:
            top_genre_names = [g['name'] for g in top_inferred_genres[:2]]
            genres_str = f"early interest in {', '.join(top_genre_names)}" if top_genre_names else "curious tastes"
            taste_summary = f"Budding Explorer. Showing {genres_str}. Track a few more anime to sharpen your taste profile."
        else:
            top_genre_names = [g['name'] for g in top_inferred_genres[:2]]
            top_studios_names = [s['name'] for s in top_inferred_studios[:1]]
            studio_str = f" with strong appreciation for {top_studios_names[0]}" if top_studios_names else ""
            taste_summary = (
                f"You demonstrate a strong affinity for {', '.join(top_genre_names) or 'diverse storytelling'}{studio_str}. "
                f"Your completion rate is {completion_rate_pct}% with a preference for {top_format} format anime."
            )

        # Inferred vs Explicit Comparison
        inferred_genre_names = [g['name'] for g in top_inferred_genres]
        explicit_genre_names = prefs.preferred_genres or []

        return {
            'has_sufficient_history': len(valid_entries) >= 3,
            'total_tracked': len(valid_entries),
            'tracked_count': len(valid_entries),
            'completed_count': len(completed),
            'watching_count': len(watching),
            'dropped_count': len(dropped),
            'completion_rate_pct': completion_rate_pct,
            'average_rating': avg_score,
            'rating_tendency': rating_tendency,
            'taste_summary': taste_summary,
            'top_format': top_format,
            'format_breakdown': dict(format_counts),
            'top_inferred_genres': top_inferred_genres,
            'top_inferred_studios': top_inferred_studios,
            'inferred_preferences': {
                'genres': top_inferred_genres,
                'studios': top_inferred_studios,
                'format': top_format,
            },
            'explicit_preferences': {
                'preferred_genres': prefs.preferred_genres,
                'preferred_formats': prefs.preferred_formats,
                'excluded_genres': prefs.excluded_genres,
                'recommendation_diversity': prefs.recommendation_diversity,
                'enable_personalized_recommendations': prefs.enable_personalized_recommendations,
                'enable_dashboard_personalization': prefs.enable_dashboard_personalization,
                'enable_discovery_personalization': prefs.enable_discovery_personalization,
            },
            'effective_genres': explicit_genre_names if explicit_genre_names else inferred_genre_names,
            'updated_at': prefs.updated_at.isoformat() if prefs.updated_at else None,
        }
