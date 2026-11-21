from django.db.models import Sum, Avg
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.tracking.services import TrackingService
from apps.anime.jikan_client import JikanClient
from apps.anime.content_filter import is_excluded_adult_anime, filter_anime_list
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    """
    Computes live dashboard statistics and aggregated lists per SRS Module 1 (FR-1.1 to FR-1.7).
    Never uses hardcoded sample data or demo values (NFR-3).
    """

    def __init__(self, jikan_client=None):
        self.jikan_client = jikan_client or JikanClient()

    def get_dashboard_data(self, user):
        # 1. Welcome message with user display_name
        welcome = {
            'display_name': user.display_name or "Guest"
        }

        # 2. Anime currently watching with episode progress (strictly non-excluded)
        all_user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
            .order_by('-updated_at')
        )
        valid_entries = [e for e in all_user_entries if not is_excluded_adult_anime(e.anime)]

        watching = [
            TrackingService.serialize_entry(e)
            for e in valid_entries
            if e.status == WatchStatus.WATCHING
        ]

        # 3. Calculate statistics from database records (strictly non-excluded)
        completed_count = sum(1 for e in valid_entries if e.status == WatchStatus.COMPLETED)
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

        # 4. Five most recently updated anime in user's list (strictly non-excluded)
        recent = [
            TrackingService.serialize_entry(e)
            for e in valid_entries[:5]
        ]

        # 5. Trending anime strip fetched from Jikan top-anime endpoint (FR-1.7)
        trending = []
        trending_available = True
        try:
            trending_res = self.jikan_client.get_trending_anime(page=1)
            if trending_res and trending_res.get('data'):
                trending = [
                    self.jikan_client.normalize_poster_card(item)
                    for item in trending_res['data']
                    if not is_excluded_adult_anime(item)
                ][:10]
            else:
                trending_available = False
        except Exception as e:
            logger.warning(f"Trending fetch failed for dashboard: {e}")
            trending = []
            trending_available = False

        return {
            'welcome': welcome,
            'watching': watching,
            'stats': stats,
            'recent': recent,
            'trending': trending,
            'trending_available': trending_available
        }
