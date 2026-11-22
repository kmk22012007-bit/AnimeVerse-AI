import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.anime.models import Anime
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.ryuk.recommendation_service import RyukRecommendationEngine, STARTER_GATEWAY_ANIME

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def demo_user(db):
    user = User.objects.create(
        session_key="a" * 64,
        display_name="RyukTester",
        is_public=True
    )
    return user

@pytest.mark.django_db
class TestRyukRecommendationEngine:

    def test_recommendations_endpoint_schema_and_status(self, api_client, demo_user):
        """Verifies GET /api/ryuk/recommendations/ returns 200 and required schema."""
        api_client.cookies['animeverse_session'] = demo_user.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == 200
        data = response.json()

        assert 'recommendations' in data
        assert 'user_profile_summary' in data
        assert 'generated_by' in data
        assert 'disclaimer' in data
        assert isinstance(data['recommendations'], list)
        assert len(data['recommendations']) > 0

        first_rec = data['recommendations'][0]
        assert 'mal_id' in first_rec
        assert 'title' in first_rec
        assert 'poster_url' in first_rec
        assert 'genres' in first_rec
        assert 'match_percentage' in first_rec
        assert 'why_recommended' in first_rec
        assert 'is_ai_rationale' in first_rec
        assert 'rationale_source' in first_rec
        assert 'matched_reasons' in first_rec
        assert 'already_in_list' in first_rec
        assert 'verified_metadata' in first_rec
        assert 70 <= first_rec['match_percentage'] <= 100

    def test_recommendations_for_empty_watch_history(self, api_client, demo_user):
        """Verifies gateway starter recommendations when user has empty watchlist."""
        api_client.cookies['animeverse_session'] = demo_user.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == 200
        data = response.json()
        summary = data['user_profile_summary']

        assert summary['has_watch_history'] is False
        assert summary['total_tracked'] == 0
        assert summary['completed_count'] == 0
        assert summary['watching_count'] == 0

        # Starter gateway titles must be present in recommendations
        rec_ids = [r['mal_id'] for r in data['recommendations']]
        starter_ids = [s['mal_id'] for s in STARTER_GATEWAY_ANIME]
        assert any(sid in rec_ids for sid in starter_ids)

    def test_recommendations_excludes_completed_and_watching_anime(self, api_client, demo_user):
        """Strictly verifies that completed and watching anime are never recommended."""
        anime_completed = Anime.objects.create(
            mal_id=1535,
            title="Death Note",
            poster_url="https://example.com/deathnote.jpg",
            anime_type="TV",
            total_episodes=37
        )
        anime_watching = Anime.objects.create(
            mal_id=5114,
            title="Fullmetal Alchemist: Brotherhood",
            poster_url="https://example.com/fmab.jpg",
            anime_type="TV",
            total_episodes=64
        )

        UserAnimeList.objects.create(
            user=demo_user,
            anime=anime_completed,
            status=WatchStatus.COMPLETED,
            watched_episodes=37,
            rating=10
        )
        UserAnimeList.objects.create(
            user=demo_user,
            anime=anime_watching,
            status=WatchStatus.WATCHING,
            watched_episodes=15,
            rating=9
        )

        api_client.cookies['animeverse_session'] = demo_user.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == 200
        data = response.json()

        rec_ids = [r['mal_id'] for r in data['recommendations']]
        assert 1535 not in rec_ids, "Completed anime Death Note must NOT be recommended!"
        assert 5114 not in rec_ids, "Currently watching anime FMAB must NOT be recommended!"

        summary = data['user_profile_summary']
        assert summary['has_watch_history'] is True
        assert summary['total_tracked'] == 2
        assert summary['completed_count'] == 1
        assert summary['watching_count'] == 1

    def test_recommendations_global_adult_content_safety(self, api_client, demo_user):
        """Ensures hentai and explicit adult titles (genre 12, 49) are never in recommendations."""
        api_client.cookies['animeverse_session'] = demo_user.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == 200
        data = response.json()

        for rec in data['recommendations']:
            genres_lower = [str(g).lower() for g in rec.get('genres', [])]
            assert 'hentai' not in genres_lower
            assert 'erotica' not in genres_lower
            assert rec['mal_id'] not in (12, 49)

    def test_recommendations_gemini_failure_graceful_fallback(self, api_client, demo_user):
        """Verifies that if Gemini AI fails or times out, RYUK falls back to heuristic rationales without 500 error."""
        mock_provider = MagicMock()
        mock_provider.generate_response.side_effect = TimeoutError("Gemini gateway timeout")

        with patch('apps.ryuk.recommendation_service.AIClientFactory.get_provider', return_value=mock_provider):
            api_client.cookies['animeverse_session'] = demo_user.session_key
            response = api_client.get('/api/ryuk/recommendations/')

            assert response.status_code == 200
            data = response.json()
            assert len(data['recommendations']) > 0

            for rec in data['recommendations']:
                # Must provide a valid rationale even on AI failure
                assert len(rec['why_recommended']) > 15
                assert rec['is_ai_rationale'] is False
                assert rec['rationale_source'] == 'ryuk_heuristics'

    def test_recommendations_query_param_validation(self, api_client, demo_user):
        """Verifies query parameters validation (e.g. limit bounds)."""
        api_client.cookies['animeverse_session'] = demo_user.session_key

        # Invalid limit: negative
        res_neg = api_client.get('/api/ryuk/recommendations/?limit=-5')
        assert res_neg.status_code == 400

        # Invalid limit: above max 20
        res_max = api_client.get('/api/ryuk/recommendations/?limit=999')
        assert res_max.status_code == 400

        # Valid limit
        res_valid = api_client.get('/api/ryuk/recommendations/?limit=4')
        assert res_valid.status_code == 200
        assert len(res_valid.json()['recommendations']) <= 4

    def test_watchlist_integration_with_recommendations(self, api_client, demo_user):
        """Verifies that adding a recommended anime directly updates watchlist and reflects in recommendations."""
        api_client.cookies['animeverse_session'] = demo_user.session_key

        # 1. Fetch recommendations
        res1 = api_client.get('/api/ryuk/recommendations/?limit=5')
        assert res1.status_code == 200
        target_rec = res1.json()['recommendations'][0]
        target_mal_id = target_rec['mal_id']

        # 2. Add this anime to watchlist via standard POST /api/list/
        add_res = api_client.post('/api/list/', {'mal_id': target_mal_id, 'status': 'Plan to Watch'}, format='json')
        assert add_res.status_code == 201

        # 3. Fetch recommendations again
        res2 = api_client.get('/api/ryuk/recommendations/?limit=8')
        assert res2.status_code == 200

        # If it appears (because it's Plan to Watch, not completed/watching), already_in_list must be True
        for rec in res2.json()['recommendations']:
            if rec['mal_id'] == target_mal_id:
                assert rec['already_in_list'] is True
