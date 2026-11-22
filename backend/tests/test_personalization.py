import pytest
from datetime import timedelta
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from apps.profiles.models import User, UserPreferences
from apps.profiles.services import TasteProfileService
from apps.anime.models import Anime, JikanCache
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.dashboard.services import DashboardService
from apps.anime.discovery_service import DiscoveryService
from apps.ryuk.services import RyukService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_new(db):
    return User.objects.create(
        session_key="n" * 64,
        display_name="ColdStartUser",
        is_public=True
    )

@pytest.fixture
def user_active(db):
    return User.objects.create(
        session_key="u" * 64,
        display_name="ActiveOtaku",
        is_public=True
    )

@pytest.fixture
def user_other(db):
    return User.objects.create(
        session_key="o" * 64,
        display_name="OtherUser",
        is_public=True
    )

@pytest.fixture
def sample_anime_catalog(db):
    """Seed test anime catalog across multiple genres and formats with JikanCache."""
    anime_configs = [
        (101, "Fullmetal Alchemist", ["Action", "Adventure", "Drama"], ["Bones"], 9.1, "TV", 64, False),
        (102, "Steins;Gate", ["Sci-Fi", "Suspense", "Drama"], ["White Fox"], 9.0, "TV", 24, False),
        (103, "Mob Psycho 100", ["Action", "Comedy", "Supernatural"], ["Bones"], 8.8, "TV", 12, False),
        (104, "A Silent Voice", ["Drama", "Romance"], ["Kyoto Animation"], 8.9, "Movie", 1, False),
        (105, "Haikyuu!!", ["Sports", "Comedy", "Drama"], ["Production I.G"], 8.7, "TV", 25, False),
        (106, "Explicit Hentai Title", ["Action", "Romance"], ["Unrated"], 7.0, "OVA", 1, True),
    ]

    animes = []
    expires = timezone.now() + timedelta(days=7)

    for mal_id, title, genres, studios, score, anime_type, total_eps, is_adult in anime_configs:
        anime, _ = Anime.objects.get_or_create(
            mal_id=mal_id,
            defaults={
                'title': title,
                'anime_type': anime_type,
                'total_episodes': total_eps,
                'poster_url': f"https://example.com/poster/{mal_id}.jpg"
            }
        )

        payload_data = {
            'mal_id': mal_id,
            'title': title,
            'title_english': title,
            'genres': [{'name': g} for g in genres],
            'studios': [{'name': s} for s in studios],
            'score': score,
            'type': anime_type,
            'anime_type': anime_type,
            'episodes': total_eps,
            'total_episodes': total_eps,
            'rating': 'Rx - Hentai' if is_adult else 'PG-13',
            'poster_url': f"https://example.com/poster/{mal_id}.jpg"
        }

        JikanCache.objects.update_or_create(
            cache_key=f"anime:{mal_id}:full",
            defaults={'payload': {'data': payload_data}, 'expires_at': expires}
        )
        JikanCache.objects.update_or_create(
            cache_key=f"details_{mal_id}",
            defaults={'payload': {'data': payload_data}, 'expires_at': expires}
        )
        animes.append(anime)

    return animes


@pytest.mark.django_db
class TestUserPreferencesAPI:

    def test_default_preferences_creation(self, api_client, user_new):
        """Initial preferences are created on demand with valid defaults."""
        api_client.cookies['animeverse_session'] = user_new.session_key
        response = api_client.get('/api/profile/preferences/')
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data['preferred_genres'] == []
        assert data['excluded_genres'] == []
        assert data['preferred_formats'] == []
        assert data['recommendation_diversity'] == 'balanced'
        assert data['enable_personalized_recommendations'] is True
        assert data['enable_dashboard_personalization'] is True
        assert data['enable_discovery_personalization'] is True

    def test_update_preferences_valid(self, api_client, user_new):
        """Valid preference update persists and reflects in subsequent GET."""
        api_client.cookies['animeverse_session'] = user_new.session_key
        payload = {
            'preferred_genres': ['Sci-Fi', 'Suspense'],
            'excluded_genres': ['Horror'],
            'preferred_formats': ['tv', 'movie'],
            'recommendation_diversity': 'exploratory',
            'enable_personalized_recommendations': True,
            'enable_dashboard_personalization': False,
            'enable_discovery_personalization': True,
        }
        res_put = api_client.put('/api/profile/preferences/', payload, format='json')
        assert res_put.status_code == status.HTTP_200_OK
        data = res_put.json()
        assert data['preferred_genres'] == ['Sci-Fi', 'Suspense']
        assert data['excluded_genres'] == ['Horror']
        assert data['recommendation_diversity'] == 'exploratory'
        assert data['enable_dashboard_personalization'] is False

        # Verify persistence on follow-up GET
        res_get = api_client.get('/api/profile/preferences/')
        assert res_get.status_code == status.HTTP_200_OK
        assert res_get.json()['preferred_genres'] == ['Sci-Fi', 'Suspense']

    def test_cross_session_isolation(self, api_client, user_active, user_other):
        """User B's session cannot view or overwrite User A's preferences."""
        # Set User A preferences
        prefs_a = user_active.get_or_create_preferences()
        prefs_a.preferred_genres = ['Psychological']
        prefs_a.save()

        # Request as User B
        api_client.cookies['animeverse_session'] = user_other.session_key
        res_b = api_client.get('/api/profile/preferences/')
        assert res_b.status_code == status.HTTP_200_OK
        # User B should see their own preferences, not User A's
        assert res_b.json()['preferred_genres'] == []

    def test_update_preferences_invalid_diversity(self, api_client, user_new):
        """Invalid diversity choice should be rejected with 400 Bad Request."""
        api_client.cookies['animeverse_session'] = user_new.session_key
        payload = {'recommendation_diversity': 'ultra_extreme'}
        res = api_client.put('/api/profile/preferences/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_preferences_invalid_genres_type(self, api_client, user_new):
        """Non-list genres must be rejected with 400."""
        api_client.cookies['animeverse_session'] = user_new.session_key
        payload = {'preferred_genres': 'NotAList'}
        res = api_client.put('/api/profile/preferences/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTasteProfileService:

    def test_cold_start_profile(self, user_new):
        """User with 0 tracked items gets cold start status and safe summary."""
        profile = TasteProfileService.get_taste_profile(user_new)
        assert profile['has_sufficient_history'] is False
        assert profile['total_tracked'] == 0
        assert profile['completed_count'] == 0
        assert profile['completion_rate_pct'] == 100.0 or profile['completion_rate_pct'] == 0.0
        assert 'Welcome to AnimeVerse' in profile['taste_summary']
        assert profile['top_inferred_genres'] == []
        assert profile['top_inferred_studios'] == []
        assert 'explicit_preferences' in profile

    def test_active_user_taste_inference(self, user_active, sample_anime_catalog):
        """User with watch history has grounded inferences with evidence."""
        a1, a2, a3, a4, a5, _ = sample_anime_catalog

        # User has completed Fullmetal Alchemist (score 10) and Mob Psycho (score 9)
        UserAnimeList.objects.create(
            user=user_active,
            anime=a1,
            status=WatchStatus.COMPLETED,
            rating=10,
            watched_episodes=64,
        )
        UserAnimeList.objects.create(
            user=user_active,
            anime=a3,
            status=WatchStatus.COMPLETED,
            rating=9,
            watched_episodes=12,
        )
        # User is watching Steins;Gate (score 8)
        UserAnimeList.objects.create(
            user=user_active,
            anime=a2,
            status=WatchStatus.WATCHING,
            rating=8,
            watched_episodes=12,
        )

        profile = TasteProfileService.get_taste_profile(user_active)
        assert profile['has_sufficient_history'] is True
        assert profile['total_tracked'] == 3
        assert profile['completed_count'] == 2

        # Action genre appears in top inferred genres
        inferred_genres = [g['name'] for g in profile['top_inferred_genres']]
        assert 'Action' in inferred_genres

        # Check evidence attached to Action genre
        action_obj = next(g for g in profile['top_inferred_genres'] if g['name'] == 'Action')
        assert action_obj['count'] == 2
        assert action_obj['avg_rating'] == 9.5
        assert 'titles' in action_obj['evidence']

        # Check Bones studio inferred
        studios = [s['name'] for s in profile['top_inferred_studios']]
        assert 'Bones' in studios

        # Check grounded taste summary mentions genres
        summary = profile['taste_summary']
        assert 'Action' in summary or 'Bones' in summary

    def test_taste_profile_api_endpoint(self, api_client, user_active):
        """GET /api/profile/taste-profile/ returns 200 with full schema."""
        api_client.cookies['animeverse_session'] = user_active.session_key
        res = api_client.get('/api/profile/taste-profile/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert 'has_sufficient_history' in data
        assert 'rating_tendency' in data
        assert 'taste_summary' in data
        assert 'top_inferred_genres' in data


@pytest.mark.django_db
class TestPersonalizedDashboard:

    def test_dashboard_sections_cold_start(self, user_new):
        """Dashboard for new user returns safe default structures."""
        data = DashboardService.get_dashboard_data(user_new)
        assert 'continue_watching' in data
        assert 'recently_completed' in data
        assert 'because_you_watched' in data
        assert 'recommended_for_you' in data
        assert 'explore_new_genres' in data
        assert 'your_anime_journey' in data

        assert data['continue_watching'] == []
        assert data['recently_completed'] == []
        assert data['because_you_watched'] is None
        assert data['your_anime_journey']['episodes_watched'] == 0

    def test_dashboard_sections_active_user(self, user_active, sample_anime_catalog):
        """Dashboard for active user populates continue_watching, completed, and journey."""
        a1, a2, a3, _, _, _ = sample_anime_catalog
        UserAnimeList.objects.create(
            user=user_active,
            anime=a1,
            status=WatchStatus.COMPLETED,
            rating=10,
            watched_episodes=64,
        )
        UserAnimeList.objects.create(
            user=user_active,
            anime=a2,
            status=WatchStatus.WATCHING,
            watched_episodes=12,
        )

        data = DashboardService.get_dashboard_data(user_active)
        assert len(data['continue_watching']) == 1
        cw = data['continue_watching'][0]
        assert cw['mal_id'] == a2.mal_id
        assert cw['progress_pct'] == 50.0
        assert cw['remaining_episodes'] == 12

        assert len(data['recently_completed']) == 1
        rc = data['recently_completed'][0]
        assert rc['mal_id'] == a1.mal_id

        journey = data['your_anime_journey']
        assert journey['episodes_watched'] == 76  # 64 + 12
        assert journey['estimated_hours_watched'] == 30.4  # (76 * 24) / 60
        assert journey['completion_rate_pct'] == 100.0 or journey['completion_rate_pct'] == 50.0


@pytest.mark.django_db
class TestSmartDiscoveryPersonalization:

    def test_discovery_personalized_ranking_and_reason(self, api_client, user_active, sample_anime_catalog):
        """personalized=true boosts anime matching preferred genres and adds reason."""
        prefs = user_active.get_or_create_preferences()
        prefs.preferred_genres = ['Sci-Fi']
        prefs.save()

        api_client.cookies['animeverse_session'] = user_active.session_key
        res = api_client.get('/api/anime/browse/?personalized=true')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        results = data['results']

        # Adult anime must never appear
        assert not any(item.get('is_adult') for item in results)

        # Sci-Fi anime (Steins;Gate) should have is_personalized=True and personalization_reason
        steins_gate = next((x for x in results if x['mal_id'] == 102), None)
        assert steins_gate is not None
        assert steins_gate.get('is_personalized') is True
        assert 'Sci-Fi' in steins_gate.get('personalization_reason', '')

    def test_discovery_hide_tracked(self, api_client, user_active, sample_anime_catalog):
        """hide_tracked=true filters out already watched/tracked anime."""
        a1, _, _, _, _, _ = sample_anime_catalog
        UserAnimeList.objects.create(
            user=user_active,
            anime=a1,
            status=WatchStatus.COMPLETED,
            watched_episodes=64,
        )

        api_client.cookies['animeverse_session'] = user_active.session_key
        res = api_client.get('/api/anime/browse/?hide_tracked=true')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        result_ids = [x['mal_id'] for x in data['results']]
        assert a1.mal_id not in result_ids

    def test_discovery_excluded_genres(self, api_client, user_active, sample_anime_catalog):
        """User's excluded_genres in preferences automatically filter out matching anime."""
        prefs = user_active.get_or_create_preferences()
        prefs.excluded_genres = ['Sports']
        prefs.save()

        api_client.cookies['animeverse_session'] = user_active.session_key
        res = api_client.get('/api/anime/browse/')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        result_ids = [x['mal_id'] for x in data['results']]
        # Haikyuu (mal_id=105, Sports) must not appear
        assert 105 not in result_ids

    def test_discovery_personalization_disabled_respects_user_toggle(self, api_client, user_active, sample_anime_catalog):
        """If enable_discovery_personalization is False, personalized=true is ignored."""
        prefs = user_active.get_or_create_preferences()
        prefs.enable_discovery_personalization = False
        prefs.preferred_genres = ['Sci-Fi']
        prefs.save()

        api_client.cookies['animeverse_session'] = user_active.session_key
        res = api_client.get('/api/anime/browse/?personalized=true')
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        for item in data['results']:
            assert item.get('is_personalized') is False


@pytest.mark.django_db
class TestRyukPersonalizationIntegration:

    def test_ryuk_explains_user_taste(self, user_active, sample_anime_catalog):
        """RYUK answers taste explanation queries with evidence-grounded facts."""
        a1, a2, _, _, _, _ = sample_anime_catalog
        UserAnimeList.objects.create(
            user=user_active,
            anime=a1,
            status=WatchStatus.COMPLETED,
            rating=10,
            watched_episodes=64,
        )
        UserAnimeList.objects.create(
            user=user_active,
            anime=a2,
            status=WatchStatus.WATCHING,
            rating=9,
            watched_episodes=12,
        )

        service = RyukService()
        res = service.process_message(
            user=user_active,
            message="Can you explain my anime taste?"
        )
        reply = res['reply']
        assert 'Anime Taste Profile' in reply
        assert 'Taste Overview' in reply

    def test_ryuk_suggests_different_genre(self, user_active, sample_anime_catalog):
        """RYUK recommends an unexplored genre outside user comfort zone."""
        a1, _, _, _, _, _ = sample_anime_catalog
        UserAnimeList.objects.create(
            user=user_active,
            anime=a1,
            status=WatchStatus.COMPLETED,
            rating=9,
            watched_episodes=64,
        )

        service = RyukService()
        res = service.process_message(
            user=user_active,
            message="Recommend a different genre outside my usual taste"
        )
        reply = res['reply']
        assert 'outside your customary anime rotation' in reply or 'explore heavily' in reply
