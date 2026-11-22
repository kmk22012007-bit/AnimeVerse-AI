import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from apps.profiles.models import User
from apps.anime.models import Anime, StreamingLanguageTrack
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.ryuk.models import AIConversation, AIMessage
from apps.ryuk.recommendation_service import RyukRecommendationEngine, STARTER_GATEWAY_ANIME
from apps.ryuk.services import RyukService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_a(db):
    return User.objects.create(
        session_key="a" * 64,
        display_name="UserAlpha",
        is_public=True
    )

@pytest.fixture
def user_b(db):
    return User.objects.create(
        session_key="b" * 64,
        display_name="UserBeta",
        is_public=True
    )

@pytest.mark.django_db
class TestRyukIntelligenceUpgrade:

    def test_recommendations_schema_and_confidence_tiers(self, api_client, user_a):
        """Verifies recommendation response contains confidence_tier and mode."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert 'recommendations' in data
        assert 'mode' in data
        assert data['mode'] == 'personalized'
        assert 'available_modes' in data
        assert len(data['recommendations']) > 0

        first_rec = data['recommendations'][0]
        assert 'confidence_tier' in first_rec
        assert first_rec['confidence_tier'] in [
            'Very High Affinity', 'High Affinity', 'Strong Match', 'Curated Match'
        ]
        assert 'match_percentage' in first_rec
        assert 70 <= first_rec['match_percentage'] <= 100
        assert 'why_recommended' in first_rec
        assert len(first_rec['why_recommended']) > 10

    def test_exploratory_discovery_mode(self, api_client, user_a):
        """Verifies mode='different' triggers exploratory discovery."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.get('/api/ryuk/recommendations/?mode=different')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['mode'] == 'different'
        assert len(data['recommendations']) > 0

    def test_strict_exclusion_of_completed_and_watching(self, api_client, user_a):
        """Completed and currently watching titles must never be recommended."""
        anime1 = Anime.objects.create(
            mal_id=1535,
            title="Death Note",
            poster_url="https://example.com/deathnote.jpg",
            anime_type="TV",
            total_episodes=37
        )
        anime2 = Anime.objects.create(
            mal_id=5114,
            title="Fullmetal Alchemist: Brotherhood",
            poster_url="https://example.com/fmab.jpg",
            anime_type="TV",
            total_episodes=64
        )
        UserAnimeList.objects.create(
            user=user_a,
            anime=anime1,
            status=WatchStatus.COMPLETED,
            watched_episodes=37,
            rating=10
        )
        UserAnimeList.objects.create(
            user=user_a,
            anime=anime2,
            status=WatchStatus.WATCHING,
            watched_episodes=15,
            rating=9
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == status.HTTP_200_OK
        rec_ids = [r['mal_id'] for r in response.json()['recommendations']]
        assert 1535 not in rec_ids
        assert 5114 not in rec_ids

    def test_cold_start_starter_recommendations(self, api_client, user_a):
        """Zero-watchlist users receive curated gateway titles."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.get('/api/ryuk/recommendations/')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['user_profile_summary']['has_watch_history'] is False
        assert data['user_profile_summary']['total_tracked'] == 0

        rec_ids = [r['mal_id'] for r in data['recommendations']]
        gateway_ids = [s['mal_id'] for s in STARTER_GATEWAY_ANIME]
        assert any(gid in rec_ids for gid in gateway_ids)

    def test_chat_grounded_progress_summary(self, api_client, user_a):
        """'Summarize my progress' returns exact database calculations."""
        anime = Anime.objects.create(
            mal_id=99991,
            title="Grounded Quest",
            anime_type="TV",
            total_episodes=24
        )
        UserAnimeList.objects.create(
            user=user_a,
            anime=anime,
            status=WatchStatus.COMPLETED,
            watched_episodes=24,
            rating=10
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.post('/api/ryuk/messages/', {'message': 'Summarize my progress'})

        assert response.status_code == status.HTTP_201_CREATED
        reply = response.json()['reply']
        assert "Completed: 1 series" in reply
        assert "Total Episodes Watched: 24 episodes" in reply
        assert "Average Score: 10.0/10" in reply

    def test_chat_grounded_specific_title_progress(self, api_client, user_a):
        """User asking about a specific anime receives verified progress."""
        anime = Anime.objects.create(
            mal_id=38000,
            title="Demon Slayer",
            anime_type="TV",
            total_episodes=26
        )
        UserAnimeList.objects.create(
            user=user_a,
            anime=anime,
            status=WatchStatus.WATCHING,
            watched_episodes=12,
            rating=9
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.post(
            '/api/ryuk/messages/',
            {'message': 'What episode am I on for Demon Slayer?'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        reply = response.json()['reply']
        assert "Demon Slayer" in reply
        assert "Episode 12 of 26" in reply
        assert "Watching" in reply

    def test_chat_grounded_streaming_guidance(self, api_client, user_a):
        """Asking where to watch pulls verified StreamingLanguageTrack records."""
        anime = Anime.objects.create(
            mal_id=38001,
            title="Demon Slayer: Kimetsu no Yaiba",
            anime_type="TV",
            total_episodes=26
        )
        from apps.anime.models import VerificationStatus
        StreamingLanguageTrack.objects.create(
            anime=anime,
            provider_name="Crunchyroll",
            country="US",
            audio_language="English",
            verification_status=VerificationStatus.LICENSOR_CONFIRMED
        )
        StreamingLanguageTrack.objects.create(
            anime=anime,
            provider_name="Netflix",
            country="IN",
            audio_language="Hindi",
            verification_status=VerificationStatus.LICENSOR_CONFIRMED
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.post(
            '/api/ryuk/messages/',
            {'message': 'Where can I watch Demon Slayer: Kimetsu no Yaiba with dubs?'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        reply = response.json()['reply']
        assert "Crunchyroll" in reply
        assert "Netflix" in reply
        assert "English" in reply
        assert "Hindi" in reply

    def test_conversation_deletion_and_idor_protection(self, api_client, user_a, user_b):
        """User A can delete their own conversation; User B cannot delete User A's conversation."""
        convo_a = AIConversation.objects.create(user=user_a, title="Alpha Private Chat")

        # 1. User B attempts to delete User A's conversation -> 404 (IDOR defense)
        api_client.cookies['animeverse_session'] = user_b.session_key
        res_b = api_client.delete(f'/api/ryuk/conversations/{convo_a.id}/')
        assert res_b.status_code == status.HTTP_404_NOT_FOUND
        assert AIConversation.objects.filter(id=convo_a.id).exists()

        # 2. User A deletes their own conversation -> 200 OK
        api_client.cookies['animeverse_session'] = user_a.session_key
        res_a = api_client.delete(f'/api/ryuk/conversations/{convo_a.id}/')
        assert res_a.status_code == status.HTTP_200_OK
        assert not AIConversation.objects.filter(id=convo_a.id).exists()

    def test_conversation_clear_all_endpoint(self, api_client, user_a):
        """POST /api/ryuk/conversations/clear/ purges all conversations for authenticated user."""
        AIConversation.objects.create(user=user_a, title="Chat 1")
        AIConversation.objects.create(user=user_a, title="Chat 2")
        assert AIConversation.objects.filter(user=user_a).count() == 2

        api_client.cookies['animeverse_session'] = user_a.session_key
        response = api_client.post('/api/ryuk/conversations/clear/')

        assert response.status_code == status.HTTP_200_OK
        assert AIConversation.objects.filter(user=user_a).count() == 0

    def test_gemini_fallback_in_chat(self, api_client, user_a):
        """When AI provider fails or is unconfigured, chat returns 503 with fallback suggestions."""
        api_client.cookies['animeverse_session'] = user_a.session_key

        with patch('apps.ryuk.services.AIClientFactory.get_provider', return_value=None):
            response = api_client.post('/api/ryuk/messages/', {'message': 'Tell me about anime history'})

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data['error'] == 'ai_unavailable'
            assert data['is_fallback'] is True
            assert 'suggestions' in data

    def test_gemini_fallback_in_recommendations(self, api_client, user_a):
        """When Gemini API raises TimeoutError, recommendation engine falls back gracefully."""
        mock_provider = MagicMock()
        mock_provider.generate_response.side_effect = TimeoutError("Gemini timed out")

        with patch('apps.ryuk.recommendation_service.AIClientFactory.get_provider', return_value=mock_provider):
            api_client.cookies['animeverse_session'] = user_a.session_key
            response = api_client.get('/api/ryuk/recommendations/')

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data['recommendations']) > 0
            for rec in data['recommendations']:
                assert rec['is_ai_rationale'] is False
                assert rec['rationale_source'] == 'ryuk_heuristics'
                assert len(rec['why_recommended']) > 10
