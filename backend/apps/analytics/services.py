import logging
from collections import Counter, defaultdict
from datetime import datetime
from django.db.models import Sum, Avg, Count, Min, Max
from django.utils import timezone
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus
from apps.anime.models import Anime, JikanCache
from apps.anime.content_filter import is_excluded_adult_anime
from apps.anime.jikan_client import JikanClient
from apps.ryuk.ai_client import AIClientFactory

logger = logging.getLogger(__name__)

# Fallback metadata for common anime if cache is absent
KNOWN_ANIME_METADATA = {
    1535: {'genres': ['Supernatural', 'Suspense', 'Psychological'], 'score': 8.62},
    5114: {'genres': ['Action', 'Adventure', 'Drama', 'Fantasy'], 'score': 9.10},
    16498: {'genres': ['Action', 'Drama', 'Suspense', 'Mystery'], 'score': 8.55},
    52991: {'genres': ['Adventure', 'Drama', 'Fantasy'], 'score': 9.30},
    9253: {'genres': ['Drama', 'Sci-Fi', 'Suspense', 'Psychological'], 'score': 9.07},
    199: {'genres': ['Adventure', 'Award Winning', 'Supernatural', 'Fantasy'], 'score': 8.78},
    38000: {'genres': ['Action', 'Fantasy', 'Historical'], 'score': 8.48},
    32281: {'genres': ['Drama', 'Supernatural', 'Romance'], 'score': 8.84},
    20: {'genres': ['Action', 'Adventure', 'Fantasy'], 'score': 8.00},
    21: {'genres': ['Action', 'Adventure', 'Fantasy'], 'score': 8.73},
    34572: {'genres': ['Action', 'Comedy', 'Fantasy'], 'score': 7.91},
    30276: {'genres': ['Action', 'Comedy', 'Sci-Fi', 'Supernatural'], 'score': 8.50},
    11061: {'genres': ['Action', 'Adventure', 'Fantasy'], 'score': 9.04},
}

# Color palette for charts
CYBERPUNK_PALETTE = [
    '#a855f7',  # Purple
    '#06b6d4',  # Cyan
    '#ec4899',  # Pink / Magenta
    '#10b981',  # Emerald
    '#f59e0b',  # Amber
    '#8b5cf6',  # Violet
    '#3b82f6',  # Blue
    '#f43f5e',  # Rose
    '#14b8a6',  # Teal
    '#6366f1',  # Indigo
]

STATUS_COLORS = {
    WatchStatus.WATCHING: '#06b6d4',      # Cyan
    WatchStatus.COMPLETED: '#10b981',     # Emerald
    WatchStatus.PLAN_TO_WATCH: '#a855f7', # Purple
    WatchStatus.ON_HOLD: '#f59e0b',       # Amber
    WatchStatus.DROPPED: '#f43f5e',       # Rose
}


class AnalyticsService:
    """
    Calculates detailed personal anime statistics, genre distribution,
    rating metrics, and activity timelines from actual user database records.
    Strictly excludes adult anime and never fabricates missing data.
    """

    def __init__(self, jikan_client=None):
        self.jikan_client = jikan_client or JikanClient()

    def get_valid_user_entries(self, user):
        """
        Retrieves all UserAnimeList entries for the user,
        strictly filtering out excluded adult titles.
        """
        all_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
            .order_by('-updated_at')
        )
        return [e for e in all_entries if not is_excluded_adult_anime(e.anime)]

    def _extract_anime_metadata(self, anime_id):
        """Retrieves genres and community score from JikanCache or known fallback."""
        cached = JikanCache.objects.filter(cache_key=f"anime:{anime_id}:full").first()
        if cached and isinstance(cached.payload, dict) and 'data' in cached.payload:
            data = cached.payload['data']
            raw_genres = data.get('genres', [])
            genres = [
                g.get('name') if isinstance(g, dict) else str(g)
                for g in raw_genres
                if (g.get('name') if isinstance(g, dict) else str(g)).lower() not in ('hentai', 'erotica')
            ]
            score = data.get('score')
            return genres, score

        # Check known fallback
        if anime_id in KNOWN_ANIME_METADATA:
            meta = KNOWN_ANIME_METADATA[anime_id]
            return meta['genres'], meta.get('score')

        return [], None

    def get_personal_stats(self, valid_entries):
        """Calculates core summary counts and averages."""
        total_tracked = len(valid_entries)
        completed = sum(1 for e in valid_entries if e.status == WatchStatus.COMPLETED)
        watching = sum(1 for e in valid_entries if e.status == WatchStatus.WATCHING)
        plan_to_watch = sum(1 for e in valid_entries if e.status == WatchStatus.PLAN_TO_WATCH)
        on_hold = sum(1 for e in valid_entries if e.status == WatchStatus.ON_HOLD)
        dropped = sum(1 for e in valid_entries if e.status == WatchStatus.DROPPED)

        total_episodes = sum(e.watched_episodes or 0 for e in valid_entries)

        rated_entries = [e for e in valid_entries if e.rating is not None]
        if rated_entries:
            avg_rating = round(sum(e.rating for e in rated_entries) / len(rated_entries), 2)
        else:
            avg_rating = None

        completion_rate = round((completed / total_tracked * 100), 1) if total_tracked > 0 else 0.0

        # Formats breakdown
        format_counts = Counter(e.anime.anime_type or 'TV' for e in valid_entries)
        most_watched_format = format_counts.most_common(1)[0][0] if format_counts else None

        # Genres explored
        all_genres = set()
        for e in valid_entries:
            genres, _ = self._extract_anime_metadata(e.anime.mal_id)
            all_genres.update(genres)

        return {
            'total_tracked': total_tracked,
            'completed_count': completed,
            'watching_count': watching,
            'plan_to_watch_count': plan_to_watch,
            'on_hold_count': on_hold,
            'dropped_count': dropped,
            'total_episodes_watched': total_episodes,
            'average_rating': avg_rating,
            'rated_count': len(rated_entries),
            'unrated_count': total_tracked - len(rated_entries),
            'completion_rate': completion_rate,
            'total_genres_explored': len(all_genres),
            'most_watched_format': most_watched_format,
            'format_counts': dict(format_counts),
        }

    def get_genre_analytics(self, valid_entries):
        """
        Analyzes user's genre distribution and rating affinity.
        Explains that counts represent appearances across multi-genre anime.
        """
        genre_counter = Counter()
        genre_ratings = defaultdict(list)
        genre_anime_list = defaultdict(list)

        for e in valid_entries:
            genres, _ = self._extract_anime_metadata(e.anime.mal_id)
            for g in genres:
                genre_counter[g] += 1
                genre_anime_list[g].append(e.anime.title)
                if e.rating is not None:
                    genre_ratings[g].append(e.rating)

        total_genre_appearances = sum(genre_counter.values())

        genre_chart_data = []
        for idx, (genre, count) in enumerate(genre_counter.most_common(10)):
            pct = round((count / total_genre_appearances * 100), 1) if total_genre_appearances > 0 else 0.0
            color = CYBERPUNK_PALETTE[idx % len(CYBERPUNK_PALETTE)]
            genre_chart_data.append({
                'name': genre,
                'count': count,
                'percentage': pct,
                'color': color,
            })

        # Strongest genre preferences (highest average rating with at least 1 rated title)
        genre_affinity = []
        for genre, ratings in genre_ratings.items():
            if ratings:
                avg = round(sum(ratings) / len(ratings), 2)
                genre_affinity.append({
                    'genre': genre,
                    'average_rating': avg,
                    'rated_count': len(ratings),
                    'total_count': genre_counter[genre],
                })
        genre_affinity.sort(key=lambda x: (x['average_rating'], x['total_count']), reverse=True)

        return {
            'distribution': genre_chart_data,
            'total_appearances': total_genre_appearances,
            'unique_genres_count': len(genre_counter),
            'strongest_preferences': genre_affinity[:5],
            'explanation': 'Genre counts represent genre tag appearances across tracked titles, as anime frequently encompass multiple genres.',
        }

    def get_rating_analytics(self, valid_entries):
        """
        Calculates personal rating distribution (1-10) and
        compares personal ratings to external community scores.
        """
        rating_counter = Counter()
        # Pre-populate 1 to 10 with 0
        for i in range(1, 11):
            rating_counter[i] = 0

        rated_entries = [e for e in valid_entries if e.rating is not None]
        for e in rated_entries:
            rating_counter[e.rating] += 1

        rating_chart_data = [
            {'rating': score, 'count': rating_counter[score], 'label': f"{score}★"}
            for score in range(1, 11)
        ]

        if rated_entries:
            avg_personal = round(sum(e.rating for e in rated_entries) / len(rated_entries), 2)
            max_score = max(e.rating for e in rated_entries)
            min_score = min(e.rating for e in rated_entries)

            highest_rated = [
                {
                    'mal_id': e.anime.mal_id,
                    'title': e.anime.title,
                    'poster_url': e.anime.poster_url,
                    'rating': e.rating,
                    'status': e.status,
                }
                for e in rated_entries if e.rating == max_score
            ][:5]

            lowest_rated = [
                {
                    'mal_id': e.anime.mal_id,
                    'title': e.anime.title,
                    'poster_url': e.anime.poster_url,
                    'rating': e.rating,
                    'status': e.status,
                }
                for e in rated_entries if e.rating == min_score
            ][:5]
        else:
            avg_personal = None
            highest_rated = []
            lowest_rated = []

        # Comparison with community scores
        comparison_list = []
        community_scores = []
        personal_scores_for_comparison = []

        for e in rated_entries:
            _, comm_score = self._extract_anime_metadata(e.anime.mal_id)
            if comm_score is not None:
                delta = round(float(e.rating) - float(comm_score), 2)
                comparison_list.append({
                    'mal_id': e.anime.mal_id,
                    'title': e.anime.title,
                    'personal_rating': e.rating,
                    'community_score': round(float(comm_score), 2),
                    'delta': delta,
                })
                community_scores.append(float(comm_score))
                personal_scores_for_comparison.append(float(e.rating))

        comparison_summary = None
        if comparison_list:
            avg_comm = round(sum(community_scores) / len(community_scores), 2)
            avg_pers = round(sum(personal_scores_for_comparison) / len(personal_scores_for_comparison), 2)
            overall_delta = round(avg_pers - avg_comm, 2)
            comparison_summary = {
                'average_community_score': avg_comm,
                'average_personal_score': avg_pers,
                'delta': overall_delta,
                'compared_titles_count': len(comparison_list),
                'top_divergences': sorted(comparison_list, key=lambda x: abs(x['delta']), reverse=True)[:5],
            }

        return {
            'distribution': rating_chart_data,
            'average_rating': avg_personal,
            'rated_count': len(rated_entries),
            'unrated_count': len(valid_entries) - len(rated_entries),
            'highest_rated': highest_rated,
            'lowest_rated': lowest_rated,
            'community_comparison': comparison_summary,
        }

    def get_activity_analytics(self, user, valid_entries):
        """
        Builds monthly and yearly activity timeline using actual database timestamps.
        Never fabricates dates.
        """
        monthly_activity = defaultdict(lambda: {'episodes': 0, 'completed': 0})
        yearly_activity = defaultdict(lambda: {'episodes': 0, 'completed': 0})

        # 1. Episodes watched from EpisodeProgress timestamps
        episodes_qs = (
            EpisodeProgress.objects.filter(list_entry__user=user)
            .values('watched_at')
        )
        has_episode_timestamps = episodes_qs.exists()

        if has_episode_timestamps:
            for ep in episodes_qs:
                w_at = ep['watched_at']
                if w_at:
                    m_key = w_at.strftime('%Y-%m')
                    y_key = w_at.strftime('%Y')
                    monthly_activity[m_key]['episodes'] += 1
                    yearly_activity[y_key]['episodes'] += 1
        else:
            # Fall back to entry updated_at/created_at if EpisodeProgress timestamps are absent
            for e in valid_entries:
                if (e.watched_episodes or 0) > 0 and e.updated_at:
                    m_key = e.updated_at.strftime('%Y-%m')
                    y_key = e.updated_at.strftime('%Y')
                    monthly_activity[m_key]['episodes'] += (e.watched_episodes or 0)
                    yearly_activity[y_key]['episodes'] += (e.watched_episodes or 0)

        # 2. Completed anime from UserAnimeList timestamps
        for e in valid_entries:
            if e.status == WatchStatus.COMPLETED and e.updated_at:
                m_key = e.updated_at.strftime('%Y-%m')
                y_key = e.updated_at.strftime('%Y')
                monthly_activity[m_key]['completed'] += 1
                yearly_activity[y_key]['completed'] += 1

        # Format timeline list sorted chronologically
        timeline_data = []
        for m_key in sorted(monthly_activity.keys()):
            try:
                dt = datetime.strptime(m_key, '%Y-%m')
                label = dt.strftime('%b %Y')
            except ValueError:
                label = m_key

            timeline_data.append({
                'month': m_key,
                'label': label,
                'episodes': monthly_activity[m_key]['episodes'],
                'completed': monthly_activity[m_key]['completed'],
            })

        # Yearly breakdown list
        yearly_data = []
        for y_key in sorted(yearly_activity.keys()):
            yearly_data.append({
                'year': y_key,
                'episodes': yearly_activity[y_key]['episodes'],
                'completed': yearly_activity[y_key]['completed'],
            })

        # Most active month
        most_active_month = None
        if timeline_data:
            most_active = max(timeline_data, key=lambda x: (x['episodes'], x['completed']))
            if most_active['episodes'] > 0 or most_active['completed'] > 0:
                most_active_month = most_active

        # Recent activity log
        recent_activity = [
            {
                'mal_id': e.anime.mal_id,
                'title': e.anime.title,
                'poster_url': e.anime.poster_url,
                'status': e.status,
                'watched_episodes': e.watched_episodes,
                'total_episodes': e.anime.total_episodes,
                'rating': e.rating,
                'date': e.updated_at.strftime('%Y-%m-%d %H:%M') if e.updated_at else None,
            }
            for e in valid_entries[:6]
        ]

        return {
            'timeline': timeline_data,
            'yearly': yearly_data,
            'most_active_month': most_active_month,
            'recent_activity': recent_activity,
            'scope_disclaimer': 'Timeline reflects recorded activity in this AnimeVerse session. Unrecorded historical periods are omitted.',
        }

    def get_watchlist_insights(self, valid_entries):
        """Calculates status distribution and in-progress overview."""
        status_counts = Counter(e.status for e in valid_entries)
        total_tracked = len(valid_entries)

        status_distribution = []
        for status_val in WatchStatus.values:
            count = status_counts[status_val]
            pct = round((count / total_tracked * 100), 1) if total_tracked > 0 else 0.0
            status_distribution.append({
                'status': status_val,
                'count': count,
                'percentage': pct,
                'color': STATUS_COLORS.get(status_val, '#a855f7'),
            })

        # Currently watching progress items
        currently_watching = [
            {
                'mal_id': e.anime.mal_id,
                'title': e.anime.title,
                'poster_url': e.anime.poster_url,
                'watched_episodes': e.watched_episodes or 0,
                'total_episodes': e.anime.total_episodes,
                'progress_percentage': (
                    round(((e.watched_episodes or 0) / e.anime.total_episodes * 100), 1)
                    if e.anime.total_episodes and e.anime.total_episodes > 0
                    else None
                ),
            }
            for e in valid_entries if e.status == WatchStatus.WATCHING
        ]

        # Average episodes per title where total_episodes is known
        episodes_with_total = [e.anime.total_episodes for e in valid_entries if e.anime.total_episodes]
        avg_episodes_per_title = (
            round(sum(episodes_with_total) / len(episodes_with_total), 1)
            if episodes_with_total else None
        )

        return {
            'status_distribution': status_distribution,
            'currently_watching_progress': currently_watching,
            'plan_to_watch_backlog': status_counts[WatchStatus.PLAN_TO_WATCH],
            'average_episodes_per_title': avg_episodes_per_title,
        }

    def generate_personal_insights(self, valid_entries, stats, genres, ratings, activity):
        """
        Derives meaningful mathematical observations from real statistics.
        All statements are strictly backed by calculation.
        """
        insights = []

        if not valid_entries:
            return [{
                'id': 'empty_history',
                'category': 'system',
                'title': 'Begin Your Tracking Journey',
                'text': 'Track anime in your personal watchlist to unlock deep analytics, genre preferences, and viewing habits.',
                'is_ai_generated': False,
            }]

        # 1. Top genre insight
        if genres['distribution']:
            top_genre = genres['distribution'][0]
            insights.append({
                'id': 'top_genre',
                'category': 'genre',
                'title': f"{top_genre['name']} Dominance",
                'text': f"{top_genre['name']} is your most explored genre, appearing in {top_genre['count']} tracked titles ({top_genre['percentage']}% of all genre tags).",
                'is_ai_generated': False,
            })

        # 2. Genre rating preference
        if genres.get('strongest_preferences'):
            top_affinity = genres['strongest_preferences'][0]
            overall_avg = stats.get('average_rating')
            if overall_avg and top_affinity['average_rating'] > overall_avg:
                delta = round(top_affinity['average_rating'] - overall_avg, 1)
                insights.append({
                    'id': 'genre_affinity',
                    'category': 'rating',
                    'title': f"Affinity for {top_affinity['genre']}",
                    'text': f"You score {top_affinity['genre']} titles {delta} points higher than your overall personal average ({top_affinity['average_rating']}/10 vs {overall_avg}/10).",
                    'is_ai_generated': False,
                })

        # 3. Completion rate insight
        if stats['total_tracked'] >= 2:
            insights.append({
                'id': 'completion_rate',
                'category': 'progress',
                'title': f"{stats['completion_rate']}% Completion Efficiency",
                'text': f"You have conquered {stats['completed_count']} out of {stats['total_tracked']} tracked anime series, maintaining a {stats['completion_rate']}% finish rate.",
                'is_ai_generated': False,
            })

        # 4. Community comparison insight
        if ratings.get('community_comparison'):
            comp = ratings['community_comparison']
            delta = comp['delta']
            if abs(delta) >= 0.2:
                tendency = "more generous than" if delta > 0 else "more critical than"
                insights.append({
                    'id': 'community_contrast',
                    'category': 'rating',
                    'title': f"Perspective: {abs(delta)}★ {'Above' if delta > 0 else 'Below'} Global Consensus",
                    'text': f"Your personal average rating ({comp['average_personal_score']}/10) is {abs(delta)} points {tendency} the global anime community score ({comp['average_community_score']}/10).",
                    'is_ai_generated': False,
                })

        # 5. Backlog insight
        if stats['plan_to_watch_count'] > 0:
            insights.append({
                'id': 'backlog_queue',
                'category': 'habit',
                'title': 'Queue Readiness',
                'text': f"You have {stats['plan_to_watch_count']} titles waiting in your Plan to Watch backlog ready for your next viewing session.",
                'is_ai_generated': False,
            })

        return insights

    def get_overview(self, user):
        """Aggregates all analytics modules into a single payload."""
        valid_entries = self.get_valid_user_entries(user)
        has_data = len(valid_entries) > 0

        stats = self.get_personal_stats(valid_entries)
        genres = self.get_genre_analytics(valid_entries)
        ratings = self.get_rating_analytics(valid_entries)
        activity = self.get_activity_analytics(user, valid_entries)
        watchlist = self.get_watchlist_insights(valid_entries)
        insights = self.generate_personal_insights(valid_entries, stats, genres, ratings, activity)

        # Recently completed anime list
        recently_completed = [
            {
                'mal_id': e.anime.mal_id,
                'title': e.anime.title,
                'poster_url': e.anime.poster_url,
                'rating': e.rating,
                'total_episodes': e.anime.total_episodes,
                'completed_at': e.updated_at.strftime('%Y-%m-%d') if e.updated_at else None,
            }
            for e in valid_entries if e.status == WatchStatus.COMPLETED
        ][:6]

        return {
            'has_data': has_data,
            'user': {
                'id': user.id,
                'display_name': user.display_name,
            },
            'stats': stats,
            'genres': genres,
            'ratings': ratings,
            'activity': activity,
            'watchlist': watchlist,
            'insights': insights,
            'recently_completed': recently_completed,
            'disclaimer': 'All analytics are computed dynamically from authenticated tracking records in your database session.',
        }
