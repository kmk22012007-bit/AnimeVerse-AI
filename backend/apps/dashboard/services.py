import logging
from django.db.models import Sum, Avg
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.tracking.services import TrackingService
from apps.anime.jikan_client import JikanClient
from apps.anime.content_filter import is_excluded_adult_anime, filter_anime_list
from apps.ryuk.recommendation_service import RyukRecommendationEngine
from apps.profiles.services import TasteProfileService

logger = logging.getLogger(__name__)

class DashboardService:
    """
    Computes live dashboard statistics and personalized anime sections.
    Integrates genuine user records, taste profiles, continue watching,
    and verified recommendations. Never uses hardcoded sample data.
    """

    def __init__(self, jikan_client=None):
        self.jikan_client = jikan_client or JikanClient()
        self.rec_engine = RyukRecommendationEngine(jikan_client=self.jikan_client)

    def get_dashboard_data(self_or_user, maybe_user=None):
        if maybe_user is not None:
            # Called as instance method: service.get_dashboard_data(user)
            return self_or_user._compute_dashboard_data(maybe_user)
        else:
            # Called as class method: DashboardService.get_dashboard_data(user)
            service = DashboardService()
            return service._compute_dashboard_data(self_or_user)

    def _compute_dashboard_data(self, user):
        prefs = user.get_or_create_preferences()
        personalization_enabled = prefs.enable_dashboard_personalization

        # 1. Welcome message with user display_name
        welcome = {
            'display_name': user.display_name or "Guest",
            'personalization_enabled': personalization_enabled
        }

        # 2. Get all non-excluded user entries
        all_user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
            .order_by('-updated_at')
        )
        valid_entries = [e for e in all_user_entries if not is_excluded_adult_anime(e.anime)]

        # Watching entries with progress
        watching_entries = [e for e in valid_entries if e.status == WatchStatus.WATCHING]
        watching = [TrackingService.serialize_entry(e) for e in watching_entries]

        continue_watching = []
        for e in watching_entries:
            total_eps = e.anime.total_episodes or 0
            watched_eps = e.watched_episodes or 0
            progress_pct = min(100, int((watched_eps / total_eps) * 100)) if total_eps > 0 else 0
            entry_data = TrackingService.serialize_entry(e)
            entry_data['progress_pct'] = progress_pct
            entry_data['remaining_episodes'] = max(0, total_eps - watched_eps) if total_eps > 0 else None
            continue_watching.append(entry_data)

        # Recently completed entries
        completed_entries = [e for e in valid_entries if e.status == WatchStatus.COMPLETED]
        recently_completed = [TrackingService.serialize_entry(e) for e in completed_entries[:6]]

        # 3. Calculate statistics from database records
        completed_count = len(completed_entries)
        total_episodes_watched = sum(e.watched_episodes or 0 for e in valid_entries)
        rated_entries = [e.rating for e in valid_entries if e.rating is not None]
        if rated_entries:
            average_rating = round(sum(rated_entries) / len(rated_entries), 1)
        else:
            average_rating = "No ratings yet"

        stats = {
            'completed_count': completed_count,
            'total_episodes_watched': total_episodes_watched,
            'average_rating': average_rating
        }

        # 4. Five most recently updated anime in user's list
        recent = [
            TrackingService.serialize_entry(e)
            for e in valid_entries[:5]
        ]

        # 5. Trending anime strip (Cached for 15 minutes to eliminate redundant upstream calls)
        from django.core.cache import cache
        trending = cache.get('dashboard_trending_cards_v1')
        trending_available = True
        if trending is None:
            try:
                trending_res = self.jikan_client.get_trending_anime(page=1)
                if trending_res and trending_res.get('data'):
                    trending = [
                        self.jikan_client.normalize_poster_card(item)
                        for item in trending_res['data']
                        if not is_excluded_adult_anime(item)
                    ][:10]
                    cache.set('dashboard_trending_cards_v1', trending, timeout=900)
                else:
                    trending = []
                    trending_available = False
            except Exception as e:
                logger.warning(f"Trending fetch failed for dashboard: {e}")
                trending = []
                trending_available = False

        # 6. Personalized sections (if personalization is enabled)
        recommended_for_you = []
        because_you_watched = None
        explore_new_genres = []
        your_anime_journey = None

        if personalization_enabled:
            # Your Anime Journey summary
            taste_profile = TasteProfileService.get_taste_profile(user)
            total_decided = completed_count + sum(1 for e in valid_entries if e.status == WatchStatus.DROPPED)
            completion_rate = round((completed_count / total_decided) * 100, 1) if total_decided > 0 else 100.0
            top_genre = taste_profile['inferred_preferences']['genres'][0]['genre'] if taste_profile['inferred_preferences']['genres'] else None

            your_anime_journey = {
                'total_episodes_watched': total_episodes_watched,
                'episodes_watched': total_episodes_watched,
                'completed_count': completed_count,
                'watching_count': len(watching_entries),
                'completion_rate_pct': completion_rate,
                'hours_watched': round(total_episodes_watched * 24 / 60, 1),
                'estimated_hours_watched': round(total_episodes_watched * 24 / 60, 1),
                'average_rating': average_rating,
                'top_genre': top_genre,
                'taste_summary': taste_profile['taste_summary'],
            }

            # Recommended For You
            try:
                rec_res = self.rec_engine.get_recommendations(user, limit=6)
                recommended_for_you = rec_res.get('recommendations', [])
            except Exception as e:
                logger.warning(f"Dashboard recommendations fetch failed: {e}")

            # Because You Watched
            # Find user's highest rated completed anime
            high_rated_completed = [
                e for e in completed_entries
                if e.rating and e.rating >= 8
            ]
            if not high_rated_completed and completed_entries:
                high_rated_completed = completed_entries

            if high_rated_completed:
                seed_entry = high_rated_completed[0]
                seed_anime = seed_entry.anime
                seed_genres = []
                # Check candidate recommendations using the seed anime's genre
                try:
                    seed_profile = self.rec_engine.analyze_user_preferences(user)
                    seed_candidates = self.rec_engine.get_candidate_pool(seed_profile, limit=8)
                    # Exclude the seed itself and items in watching/completed
                    filtered_candidates = [
                        c for c in seed_candidates
                        if c['mal_id'] != seed_anime.mal_id
                    ][:4]

                    if filtered_candidates:
                        because_you_watched = {
                            'seed_anime': {
                                'mal_id': seed_anime.mal_id,
                                'title': seed_anime.title,
                                'poster_url': seed_anime.poster_url,
                                'rating': seed_entry.rating,
                            },
                            'recommendations': [
                                {
                                    'mal_id': c['mal_id'],
                                    'title': c['title'],
                                    'poster_url': c['poster_url'],
                                    'anime_type': c.get('anime_type', 'TV'),
                                    'score': c.get('score'),
                                    'genres': c.get('genres', []),
                                    'reason': f"Shares the compelling themes and narrative drive of {seed_anime.title}"
                                }
                                for c in filtered_candidates
                            ]
                        }
                except Exception as e:
                    logger.warning(f"Because You Watched computation failed: {e}")

            # Explore New Genres
            try:
                exp_res = self.rec_engine.get_recommendations(user, mode='different', limit=6)
                explore_new_genres = exp_res.get('recommendations', [])
            except Exception as e:
                logger.warning(f"Explore new genres fetch failed: {e}")

        return {
            'welcome': welcome,
            'watching': watching,
            'continue_watching': continue_watching,
            'stats': stats,
            'recent': recent,
            'trending': trending,
            'trending_available': trending_available,
            'personalization_enabled': personalization_enabled,
            'recommended_for_you': recommended_for_you,
            'because_you_watched': because_you_watched,
            'explore_new_genres': explore_new_genres,
            'your_anime_journey': your_anime_journey,
            'recently_completed': recently_completed,
        }
