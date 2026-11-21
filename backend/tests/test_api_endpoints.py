import pytest
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.anime.models import Anime
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus
from apps.community.models import Review, CommunityPost, Comment, PostLike
from apps.ryuk.models import AIConversation, AIMessage
from apps.core.middleware import SESSION_COOKIE_NAME

@pytest.fixture
def client_with_session():
    client = APIClient()
    user = User.objects.create(session_key="a" * 64, display_name="OtakuPrime")
    client.cookies[SESSION_COOKIE_NAME] = user.session_key
    client.user = user
    return client

@pytest.fixture
def other_client():
    client = APIClient()
    user = User.objects.create(session_key="b" * 64, display_name="OtherUser")
    client.cookies[SESSION_COOKIE_NAME] = user.session_key
    client.user = user
    return client


@pytest.mark.django_db
class TestSRSSpecifiedAPICases:
    """
    Validates SRS specified API test cases:
    API-01, API-02, API-03, API-04, API-05, API-06
    """

    def test_api_01_search_query_too_short(self, client_with_session):
        """API-01: GET /api/anime/search/?q=a -> 400 with details.q"""
        res = client_with_session.get('/api/anime/search/?q=a')
        assert res.status_code == 400
        assert res.data['error'] == 'validation_error'
        assert 'q' in res.data['details']

    def test_api_02_duplicate_watchlist_post(self, client_with_session):
        """API-02: POST /api/list/ with {mal_id: 1535, status: 'Watching'} twice -> 201 first, 409 second"""
        # Ensure anime exists in DB for test
        Anime.objects.get_or_create(mal_id=1535, defaults={'title': 'Death Note', 'total_episodes': 37})

        payload = {'mal_id': 1535, 'status': 'Watching'}
        res1 = client_with_session.post('/api/list/', payload, format='json')
        assert res1.status_code == 201
        assert res1.data['mal_id'] == 1535

        res2 = client_with_session.post('/api/list/', payload, format='json')
        assert res2.status_code == 409
        assert res2.data['error'] == 'duplicate_resource'
        assert UserAnimeList.objects.filter(user=client_with_session.user, anime_id=1535).count() == 1

    def test_api_03_patch_list_invalid_rating(self, client_with_session):
        """API-03: PATCH /api/list/{id}/ with {rating: 11} -> 400 with details.rating"""
        anime = Anime.objects.create(mal_id=20, title='Naruto', total_episodes=220)
        entry = UserAnimeList.objects.create(user=client_with_session.user, anime=anime, status=WatchStatus.WATCHING)

        res = client_with_session.patch(f'/api/list/{entry.id}/', {'rating': 11}, format='json')
        assert res.status_code == 400
        assert res.data['error'] == 'validation_error'
        assert 'rating' in res.data['details']

    def test_api_04_patch_list_owned_by_another_session(self, client_with_session, other_client):
        """API-04: PATCH /api/list/{id}/ for an entry owned by another session -> 404 No data returned"""
        anime = Anime.objects.create(mal_id=30, title='Neon Genesis Evangelion', total_episodes=26)
        entry = UserAnimeList.objects.create(user=other_client.user, anime=anime, status=WatchStatus.WATCHING)

        res = client_with_session.patch(f'/api/list/{entry.id}/', {'rating': 9}, format='json')
        assert res.status_code == 404
        assert res.data['error'] == 'not_found'

    def test_api_05_put_progress_updates_episodes(self, client_with_session):
        """API-05: PUT /api/list/{id}/progress/ with {watched_episodes: 5} -> 200, watched_episodes is 5"""
        anime = Anime.objects.create(mal_id=40, title='Fullmetal Alchemist', total_episodes=51)
        entry = UserAnimeList.objects.create(user=client_with_session.user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=2)

        res = client_with_session.put(f'/api/list/{entry.id}/progress/', {'watched_episodes': 5}, format='json')
        assert res.status_code == 200
        assert res.data['watched_episodes'] == 5

        entry.refresh_from_db()
        assert entry.watched_episodes == 5
        assert EpisodeProgress.objects.filter(list_entry=entry).count() == 5

    def test_api_06_get_private_user_profile(self, client_with_session, other_client):
        """API-06: GET /api/users/{id}/ for a private profile -> 404 No profile fields in body"""
        other_client.user.is_public = False
        other_client.user.save()

        res = client_with_session.get(f'/api/users/{other_client.user.id}/')
        assert res.status_code == 404
        assert 'display_name' not in res.data


@pytest.mark.django_db
class TestCoreEndpointsWorkflow:
    """
    Tests full API flows:
    Dashboard, Watchlist, Reviews, Community, Calendar, Profiles, RYUK.
    """

    def test_dashboard_endpoint(self, client_with_session):
        anime = Anime.objects.create(mal_id=50, title='Steins;Gate', total_episodes=24)
        UserAnimeList.objects.create(
            user=client_with_session.user,
            anime=anime,
            status=WatchStatus.COMPLETED,
            watched_episodes=24,
            rating=10
        )

        res = client_with_session.get('/api/dashboard/')
        assert res.status_code == 200
        assert res.data['welcome']['display_name'] == 'OtakuPrime'
        assert res.data['stats']['completed_count'] == 1
        assert res.data['stats']['total_episodes_watched'] == 24
        assert res.data['stats']['average_rating'] == 10.0
        assert 'trending' in res.data
        assert 'trending_available' in res.data

    def test_watchlist_complete_and_delete(self, client_with_session):
        anime = Anime.objects.create(mal_id=60, title='Mob Psycho 100', total_episodes=12)
        entry = UserAnimeList.objects.create(user=client_with_session.user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=4)

        # Complete
        res_comp = client_with_session.post(f'/api/list/{entry.id}/complete/')
        assert res_comp.status_code == 200
        assert res_comp.data['status'] == 'Completed'
        assert res_comp.data['watched_episodes'] == 12

        # Delete
        res_del = client_with_session.delete(f'/api/list/{entry.id}/')
        assert res_del.status_code == 204
        assert not UserAnimeList.objects.filter(id=entry.id).exists()

    def test_reviews_crud_and_permissions(self, client_with_session, other_client):
        anime = Anime.objects.create(mal_id=70, title='Vinland Saga')

        # 1. Create review
        body = "An absolute masterpiece of historical drama and character growth."
        res = client_with_session.post(f'/api/anime/{anime.mal_id}/reviews/', {'score': 10, 'body': body}, format='json')
        assert res.status_code == 201
        review_id = res.data['id']
        assert res.data['score'] == 10

        # 2. Duplicate review by same user fails (409)
        res_dup = client_with_session.post(f'/api/anime/{anime.mal_id}/reviews/', {'score': 8, 'body': body}, format='json')
        assert res_dup.status_code == 409

        # 3. Other user attempts to edit -> 403 Forbidden
        res_forbidden = other_client.patch(f'/api/reviews/{review_id}/', {'score': 5}, format='json')
        assert res_forbidden.status_code == 403

        # 4. Owner edits -> 200 OK
        new_body = "Updated thoughts: still a 10/10 masterpiece with unmatched score."
        res_edit = client_with_session.patch(f'/api/reviews/{review_id}/', {'body': new_body}, format='json')
        assert res_edit.status_code == 200
        assert res_edit.data['body'] == new_body

        # 5. Owner deletes -> 204
        res_del = client_with_session.delete(f'/api/reviews/{review_id}/')
        assert res_del.status_code == 204

    def test_community_post_like_comment(self, client_with_session, other_client):
        # Create post
        res_post = client_with_session.post('/api/community/posts/', {
            'title': 'What are your top 3 anime this season?',
            'body': 'Drop your favorites below and let us discuss!'
        }, format='json')
        assert res_post.status_code == 201
        post_id = res_post.data['id']

        # Like post
        res_like = other_client.post(f'/api/community/posts/{post_id}/like/')
        assert res_like.status_code == 200
        assert res_like.data['liked'] is True
        assert res_like.data['like_count'] == 1

        # Comment on post
        res_comm = other_client.post(f'/api/community/posts/{post_id}/comments/', {
            'body': 'Frieren is definitely number one for me.'
        }, format='json')
        assert res_comm.status_code == 201
        assert res_comm.data['body'] == 'Frieren is definitely number one for me.'

        # Get post detail
        res_detail = client_with_session.get(f'/api/community/posts/{post_id}/')
        assert res_detail.status_code == 200
        assert res_detail.data['post']['like_count'] == 1
        assert len(res_detail.data['comments']) == 1

    def test_profile_update_and_public_view(self, client_with_session, other_client):
        # Update current profile
        res_update = client_with_session.patch('/api/profile/', {
            'display_name': 'HokageMaster',
            'bio': 'Watching anime since 2005.',
            'is_public': True
        }, format='json')
        assert res_update.status_code == 200
        assert res_update.data['display_name'] == 'HokageMaster'
        assert res_update.data['is_public'] is True

        # Other user can now view public profile
        res_view = other_client.get(f'/api/users/{client_with_session.user.id}/')
        assert res_view.status_code == 200
        assert res_view.data['display_name'] == 'HokageMaster'
        assert res_view.data['bio'] == 'Watching anime since 2005.'

    def test_ryuk_progress_summary_and_messages(self, client_with_session):
        # 1. Progress summary (handled from DB records)
        res_sum = client_with_session.post('/api/ryuk/messages/', {'message': 'Summarize my progress'}, format='json')
        assert res_sum.status_code == 201
        assert res_sum.data['is_fallback'] is False
        assert 'journey so far' in res_sum.data['reply']

        # 2. General conversation with RYUK (real AI configured returns 201)
        res_ai = client_with_session.post('/api/ryuk/messages/', {'message': 'Recommend some cyberpunk anime'}, format='json')
        if res_ai.status_code == 201:
            assert res_ai.data['is_fallback'] is False
            assert len(res_ai.data['reply']) > 0
        else:
            # Fallback path if quota/network blocks
            assert res_ai.status_code == 503
            assert res_ai.data['is_fallback'] is True
            assert 'suggestions' in res_ai.data

        # 3. Check conversation history
        res_convos = client_with_session.get('/api/ryuk/conversations/')
        assert res_convos.status_code == 200
        assert len(res_convos.data['results']) >= 1

    def test_anime_episodes_endpoint(self, client_with_session):
        """GET /api/anime/52991/episodes/ returns verified episode list with actual descriptions."""
        res = client_with_session.get('/api/anime/52991/episodes/')
        assert res.status_code == 200
        assert 'episodes' in res.data
        assert 'pagination' in res.data
        assert res.data['metadata_source'] in ['tenrai', 'anilist', 'jikan']
        if res.data['episodes']:
            ep1 = res.data['episodes'][0]
            assert 'episode_number' in ep1
            assert 'title' in ep1
            assert 'filler' in ep1
            assert 'synopsis' in ep1
            assert 'has_description' in ep1

    def test_search_ranking_exact_match_priority(self, client_with_session):
        """Search query ranks exact match ahead of related matches."""
        res = client_with_session.get('/api/anime/search/?q=Sousou no Frieren')
        assert res.status_code == 200
        assert 'results' in res.data
        if len(res.data['results']) > 0:
            top_result = res.data['results'][0]
            assert 'frieren' in (top_result['title'] or '').lower() or 'frieren' in (top_result['title_english'] or '').lower()

    def test_episode_normalizer_never_repeats_main_synopsis(self):
        """Ensures normalize_episode strips any synopsis that duplicates the main anime synopsis."""
        from apps.anime.jikan_client import JikanClient
        client = JikanClient()
        main_syn = "This is the overarching synopsis of the entire show."
        
        # Test case 1: Raw episode synopsis duplicates main synopsis
        dupe_raw = {'mal_id': 1, 'title': 'Prologue', 'synopsis': "This is the overarching synopsis of the entire show."}
        normalized = client.normalize_episode(dupe_raw, main_synopsis=main_syn)
        assert normalized['synopsis'] is None
        assert normalized['has_description'] is False

        # Test case 2: Episode has genuine specific synopsis
        real_raw = {'mal_id': 1, 'title': 'Prologue', 'synopsis': "Frieren meets Fern in the ancient woods."}
        normalized_real = client.normalize_episode(real_raw, main_synopsis=main_syn)
        assert normalized_real['synopsis'] == "Frieren meets Fern in the ancient woods."
        assert normalized_real['has_description'] is True
