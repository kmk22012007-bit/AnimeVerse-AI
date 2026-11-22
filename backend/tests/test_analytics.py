import pytest
from datetime import datetime, timezone as dt_timezone
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.anime.models import Anime, JikanCache
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_a(db):
    return User.objects.create(
        session_key="a" * 64,
        display_name="OtakuPrime",
        is_public=True
    )

@pytest.fixture
def user_b(db):
    return User.objects.create(
        session_key="b" * 64,
        display_name="CasualWatcher",
        is_public=True
    )

@pytest.mark.django_db
class TestAnalyticsAPI:

    def test_analytics_overview_empty_history(self, api_client, user_a):
        """Verifies clean response and has_data=False when user has no tracked anime."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get('/api/analytics/overview/')

        assert res.status_code == 200
        data = res.json()

        assert data['has_data'] is False
        assert data['user']['display_name'] == "OtakuPrime"
        assert data['stats']['total_tracked'] == 0
        assert data['stats']['completed_count'] == 0
        assert data['stats']['average_rating'] is None
        assert data['genres']['distribution'] == []
        assert data['ratings']['rated_count'] == 0
        assert data['ratings']['average_rating'] is None
        assert data['activity']['timeline'] == []
        assert data['recently_completed'] == []
        assert len(data['insights']) >= 1
        assert data['insights'][0]['id'] == 'empty_history'

    def test_analytics_multiple_statuses_and_ratings(self, api_client, user_a):
        """Tests comprehensive aggregation with diverse statuses, ratings, and episodes."""
        anime1 = Anime.objects.create(mal_id=1535, title="Death Note", anime_type="TV", total_episodes=37)
        anime2 = Anime.objects.create(mal_id=5114, title="Fullmetal Alchemist: Brotherhood", anime_type="TV", total_episodes=64)
        anime3 = Anime.objects.create(mal_id=199, title="Spirited Away", anime_type="Movie", total_episodes=1)
        anime4 = Anime.objects.create(mal_id=38000, title="Demon Slayer", anime_type="TV", total_episodes=26)

        from django.utils import timezone
        exp = timezone.now() + timezone.timedelta(days=1)
        # Cache metadata with genres and community scores
        JikanCache.objects.create(
            cache_key="anime:1535:full",
            payload={'data': {'genres': [{'name': 'Psychological'}, {'name': 'Supernatural'}], 'score': 8.62}},
            expires_at=exp
        )
        JikanCache.objects.create(
            cache_key="anime:5114:full",
            payload={'data': {'genres': [{'name': 'Action'}, {'name': 'Adventure'}, {'name': 'Fantasy'}], 'score': 9.10}},
            expires_at=exp
        )
        JikanCache.objects.create(
            cache_key="anime:199:full",
            payload={'data': {'genres': [{'name': 'Adventure'}, {'name': 'Supernatural'}], 'score': 8.78}},
            expires_at=exp
        )
        JikanCache.objects.create(
            cache_key="anime:38000:full",
            payload={'data': {'genres': [{'name': 'Action'}, {'name': 'Fantasy'}], 'score': 8.48}},
            expires_at=exp
        )

        # User A entries
        e1 = UserAnimeList.objects.create(user=user_a, anime=anime1, status=WatchStatus.COMPLETED, watched_episodes=37, rating=10)
        e2 = UserAnimeList.objects.create(user=user_a, anime=anime2, status=WatchStatus.WATCHING, watched_episodes=30, rating=9)
        e3 = UserAnimeList.objects.create(user=user_a, anime=anime3, status=WatchStatus.COMPLETED, watched_episodes=1, rating=8)
        e4 = UserAnimeList.objects.create(user=user_a, anime=anime4, status=WatchStatus.PLAN_TO_WATCH, watched_episodes=0, rating=None)

        # Add EpisodeProgress records for e2
        EpisodeProgress.objects.create(list_entry=e2, episode_number=1, watched_at=datetime(2026, 10, 15, tzinfo=dt_timezone.utc))
        EpisodeProgress.objects.create(list_entry=e2, episode_number=2, watched_at=datetime(2026, 11, 1, tzinfo=dt_timezone.utc))

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get('/api/analytics/overview/')

        assert res.status_code == 200
        data = res.json()

        assert data['has_data'] is True
        stats = data['stats']
        assert stats['total_tracked'] == 4
        assert stats['completed_count'] == 2
        assert stats['watching_count'] == 1
        assert stats['plan_to_watch_count'] == 1
        assert stats['total_episodes_watched'] == 68  # 37 + 30 + 1 + 0
        # Average rating: (10 + 9 + 8) / 3 = 9.0 (unrated anime4 must NOT be treated as 0)
        assert stats['average_rating'] == 9.0
        assert stats['rated_count'] == 3
        assert stats['unrated_count'] == 1
        assert stats['completion_rate'] == 50.0

        # Genre analytics
        genres = data['genres']
        genre_names = [g['name'] for g in genres['distribution']]
        assert 'Supernatural' in genre_names
        assert 'Action' in genre_names
        assert 'Adventure' in genre_names

        # Rating distribution
        ratings = data['ratings']
        dist_map = {item['rating']: item['count'] for item in ratings['distribution']}
        assert dist_map[10] == 1
        assert dist_map[9] == 1
        assert dist_map[8] == 1
        assert dist_map[7] == 0
        assert ratings['average_rating'] == 9.0
        assert len(ratings['highest_rated']) == 1
        assert ratings['highest_rated'][0]['mal_id'] == 1535
        assert len(ratings['lowest_rated']) == 1
        assert ratings['lowest_rated'][0]['mal_id'] == 199

        # Community comparison
        assert ratings['community_comparison'] is not None
        assert ratings['community_comparison']['average_personal_score'] == 9.0

        # Activity timeline
        activity = data['activity']
        assert len(activity['timeline']) >= 1
        assert activity['most_active_month'] is not None

        # Watchlist breakdown
        watchlist = data['watchlist']
        assert watchlist['plan_to_watch_backlog'] == 1
        assert len(watchlist['currently_watching_progress']) == 1
        assert watchlist['currently_watching_progress'][0]['mal_id'] == 5114

        # Insights generated
        insights = data['insights']
        assert len(insights) >= 2
        insight_cats = [i['category'] for i in insights]
        assert 'genre' in insight_cats or 'progress' in insight_cats

    def test_user_data_isolation(self, api_client, user_a, user_b):
        """Strictly ensures User B cannot see User A's tracking analytics."""
        anime = Anime.objects.create(mal_id=1535, title="Death Note", anime_type="TV", total_episodes=37)
        UserAnimeList.objects.create(user=user_a, anime=anime, status=WatchStatus.COMPLETED, watched_episodes=37, rating=10)

        # User B queries analytics
        api_client.cookies['animeverse_session'] = user_b.session_key
        res = api_client.get('/api/analytics/overview/')

        assert res.status_code == 200
        data = res.json()
        assert data['user']['display_name'] == "CasualWatcher"
        assert data['has_data'] is False
        assert data['stats']['total_tracked'] == 0

    def test_adult_anime_excluded_from_analytics(self, api_client, user_a):
        """Ensures hentai / adult titles never leak into user analytics."""
        normal_anime = Anime.objects.create(mal_id=1535, title="Death Note", anime_type="TV", total_episodes=37)
        adult_anime = Anime.objects.create(mal_id=99999, title="Adult Hentai Title", anime_type="OVA", total_episodes=2)

        from django.utils import timezone
        # Mark adult in cache
        JikanCache.objects.create(
            cache_key="anime:99999:full",
            payload={'data': {'genres': [{'mal_id': 12, 'name': 'Hentai'}], 'rating': 'Rx - Hentai'}},
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )

        UserAnimeList.objects.create(user=user_a, anime=normal_anime, status=WatchStatus.COMPLETED, watched_episodes=37, rating=10)
        UserAnimeList.objects.create(user=user_a, anime=adult_anime, status=WatchStatus.WATCHING, watched_episodes=2, rating=10)

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get('/api/analytics/overview/')

        assert res.status_code == 200
        data = res.json()
        # Adult anime must be strictly excluded!
        assert data['stats']['total_tracked'] == 1
        assert data['stats']['watching_count'] == 0

    def test_sub_endpoints_return_200(self, api_client, user_a):
        """Tests individual granular analytics endpoints."""
        anime = Anime.objects.create(mal_id=1535, title="Death Note", anime_type="TV", total_episodes=37)
        UserAnimeList.objects.create(user=user_a, anime=anime, status=WatchStatus.COMPLETED, watched_episodes=37, rating=10)

        api_client.cookies['animeverse_session'] = user_a.session_key

        genres_res = api_client.get('/api/analytics/genres/')
        assert genres_res.status_code == 200
        assert 'distribution' in genres_res.json()
        assert 'explanation' in genres_res.json()

        ratings_res = api_client.get('/api/analytics/ratings/')
        assert ratings_res.status_code == 200
        assert 'distribution' in ratings_res.json()
        assert ratings_res.json()['average_rating'] == 10.0

        activity_res = api_client.get('/api/analytics/activity/')
        assert activity_res.status_code == 200
        assert 'timeline' in activity_res.json()
        assert 'scope_disclaimer' in activity_res.json()

        watchlist_res = api_client.get('/api/analytics/watchlist/')
        assert watchlist_res.status_code == 200
        assert 'status_distribution' in watchlist_res.json()

    def test_missing_ratings_never_treated_as_zero(self, api_client, user_a):
        """Ensures titles with no rating (None) do not skew average personal rating down to 0."""
        anime1 = Anime.objects.create(mal_id=1535, title="Death Note", anime_type="TV", total_episodes=37)
        anime2 = Anime.objects.create(mal_id=5114, title="Fullmetal Alchemist", anime_type="TV", total_episodes=64)

        # e1 has rating 8, e2 has rating None
        UserAnimeList.objects.create(user=user_a, anime=anime1, status=WatchStatus.COMPLETED, watched_episodes=37, rating=8)
        UserAnimeList.objects.create(user=user_a, anime=anime2, status=WatchStatus.PLAN_TO_WATCH, watched_episodes=0, rating=None)

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get('/api/analytics/overview/')

        assert res.status_code == 200
        data = res.json()
        # Average rating must be 8.0, NOT (8 + 0)/2 = 4.0!
        assert data['stats']['average_rating'] == 8.0
        assert data['stats']['rated_count'] == 1
        assert data['stats']['unrated_count'] == 1

    def test_multi_genre_accounting_and_explanation(self, api_client, user_a):
        """Tests that anime with multiple genres are accounted for in appearances with disclaimer."""
        anime = Anime.objects.create(mal_id=9253, title="Steins;Gate", anime_type="TV", total_episodes=24)
        from django.utils import timezone
        JikanCache.objects.create(
            cache_key="anime:9253:full",
            payload={'data': {'genres': [{'name': 'Sci-Fi'}, {'name': 'Suspense'}, {'name': 'Psychological'}], 'score': 9.07}},
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )
        UserAnimeList.objects.create(user=user_a, anime=anime, status=WatchStatus.COMPLETED, watched_episodes=24, rating=10)

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get('/api/analytics/genres/')

        assert res.status_code == 200
        data = res.json()
        assert data['total_appearances'] == 3
        assert data['unique_genres_count'] == 3
        assert 'appearances' in data['explanation'].lower()

