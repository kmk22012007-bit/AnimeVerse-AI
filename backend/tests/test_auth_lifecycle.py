"""
AnimeVerse AI — Authentication Lifecycle & Session Compatibility Test Suite.
Validates the full 10-step authentication lifecycle:
  1. Session cookie generation on initial access.
  2. User creation and session association.
  3. Session persistence across subsequent requests with the same cookie.
  4. Profile updates persisted to the session identity.
  5. Watchlist creation and episode stepping persisted to the session.
  6. Community post and comment author attribution.
  7. Fraud-resistant poll voting isolation (1 vote per session).
  8. Cross-session isolation (User A cannot view or modify User B's watchlist).
  9. Session reset when cookie is removed (new guest identity created).
 10. Privilege escalation defense (mass-assignment validation rejecting role/staff).
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from apps.profiles.models import User
from apps.anime.models import Anime, JikanCache
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.community.models import CommunityPost, Poll, PollOption, PollVote

SESSION_COOKIE_NAME = 'animeverse_session'

@pytest.fixture
def sample_anime(db):
    anime, _ = Anime.objects.get_or_create(
        mal_id=52991,
        defaults={
            'title': 'Sousou no Frieren',
            'anime_type': 'TV',
            'total_episodes': 28,
            'poster_url': 'https://example.com/frieren.jpg'
        }
    )
    JikanCache.objects.update_or_create(
        cache_key=f"details_{anime.mal_id}",
        defaults={
            'payload': {
                'data': {
                    'mal_id': anime.mal_id,
                    'title': anime.title,
                    'genres': [{'mal_id': 1, 'name': 'Action'}, {'mal_id': 2, 'name': 'Adventure'}]
                }
            },
            'expires_at': timezone.now() + timedelta(days=7)
        }
    )
    return anime

@pytest.fixture
def sample_poll(db, sample_anime):
    creator = User.objects.create(session_key='creator_' + 'a' * 56, display_name='Poll Creator')
    post = CommunityPost.objects.create(
        user=creator,
        anime=sample_anime,
        title='Best Opening Song?',
        body='Vote for your favorite OP track.',
        category='discussion'
    )
    poll = Poll.objects.create(user=creator, post=post, question='Best Opening?')
    opt1 = PollOption.objects.create(poll=poll, text='Track Alpha', order=1)
    opt2 = PollOption.objects.create(poll=poll, text='Track Beta', order=2)
    return poll, opt1, opt2

@pytest.mark.django_db
class TestAuthenticationLifecycle:

    def test_01_initial_request_generates_session_cookie(self, client):
        """Step 1: First request without cookies receives a 64-char hex session cookie and creates User."""
        response = client.get('/api/health/')
        assert response.status_code == status.HTTP_200_OK

        # Verify session cookie was generated
        assert SESSION_COOKIE_NAME in response.cookies
        cookie = response.cookies[SESSION_COOKIE_NAME]
        session_token = cookie.value
        assert len(session_token) == 64

        # Verify User record was created in database
        user = User.objects.filter(session_key=session_token).first()
        assert user is not None
        assert user.display_name == "Guest"
        assert user.role == "user"
        assert user.is_staff is False

    def test_02_session_persists_across_subsequent_requests(self, client):
        """Step 2 & 3: Subsequent requests presenting the cookie maintain the exact same User identity."""
        init_res = client.get('/api/health/')
        token = init_res.cookies[SESSION_COOKIE_NAME].value

        # Make another request with the cookie
        client.cookies[SESSION_COOKIE_NAME] = token
        second_res = client.get('/api/profile/')
        assert second_res.status_code == status.HTTP_200_OK
        assert second_res.data['display_name'] == "Guest"

        # Verify no duplicate user was created
        assert User.objects.filter(session_key=token).count() == 1

    def test_03_profile_update_persists_for_session(self, client):
        """Step 4: User updates their profile, persisting across requests."""
        init_res = client.get('/api/health/')
        token = init_res.cookies[SESSION_COOKIE_NAME].value
        client.cookies[SESSION_COOKIE_NAME] = token

        # Update profile
        patch_res = client.patch(
            '/api/profile/',
            {'display_name': 'Kagami', 'bio': 'Cyberpunk enthusiast'},
            content_type='application/json'
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.data['display_name'] == 'Kagami'

        # Refresh and verify
        get_res = client.get('/api/profile/')
        assert get_res.data['display_name'] == 'Kagami'
        assert get_res.data['bio'] == 'Cyberpunk enthusiast'

    def test_04_watchlist_persists_to_authenticated_session(self, client, sample_anime):
        """Step 5: Watchlist addition and episode stepping are tied strictly to the session user."""
        init_res = client.get('/api/health/')
        token = init_res.cookies[SESSION_COOKIE_NAME].value
        client.cookies[SESSION_COOKIE_NAME] = token

        # Add anime to watchlist using correct schema (mal_id and capitalized Status)
        add_res = client.post(
            '/api/list/',
            {'mal_id': sample_anime.mal_id, 'status': 'Watching'},
            content_type='application/json'
        )
        assert add_res.status_code == status.HTTP_201_CREATED
        entry_id = add_res.data['id']

        # Update progress
        prog_res = client.put(
            f'/api/list/{entry_id}/progress/',
            {'watched_episodes': 3},
            content_type='application/json'
        )
        assert prog_res.status_code == status.HTTP_200_OK
        assert prog_res.data['watched_episodes'] == 3

        # Fetch watchlist
        list_res = client.get('/api/list/')
        assert list_res.status_code == status.HTTP_200_OK
        results = list_res.data.get('results', list_res.data)
        assert len(results) == 1
        assert results[0]['mal_id'] == sample_anime.mal_id
        assert results[0]['watched_episodes'] == 3

    def test_05_community_interactions_attribute_to_session(self, client, sample_anime):
        """Step 6: Community posts are authored by the session identity."""
        init_res = client.get('/api/health/')
        token = init_res.cookies[SESSION_COOKIE_NAME].value
        client.cookies[SESSION_COOKIE_NAME] = token

        # Name user
        client.patch('/api/profile/', {'display_name': 'DiscussionLead'}, content_type='application/json')

        # Create post
        post_res = client.post(
            '/api/community/posts/',
            {'title': 'Cyber Discussion', 'body': 'Analyzing sound design.', 'anime_id': sample_anime.mal_id, 'category': 'discussion'},
            content_type='application/json'
        )
        assert post_res.status_code == status.HTTP_201_CREATED
        post_id = post_res.data['id']

        # Verify author attribution
        detail_res = client.get(f'/api/community/posts/{post_id}/')
        assert detail_res.data['post']['author']['display_name'] == 'DiscussionLead'

    def test_06_poll_voting_enforces_session_uniqueness(self, client, sample_poll):
        """Step 7: User can vote once per poll; second vote attempt is rejected with 409 Conflict."""
        poll, opt1, opt2 = sample_poll
        init_res = client.get('/api/health/')
        token = init_res.cookies[SESSION_COOKIE_NAME].value
        client.cookies[SESSION_COOKIE_NAME] = token

        # First vote succeeds
        vote_res = client.post(
            f'/api/community/polls/{poll.id}/vote/',
            {'option_id': opt1.id},
            content_type='application/json'
        )
        assert vote_res.status_code == status.HTTP_200_OK

        # Second vote is rejected with 409 Conflict
        repeat_vote = client.post(
            f'/api/community/polls/{poll.id}/vote/',
            {'option_id': opt2.id},
            content_type='application/json'
        )
        assert repeat_vote.status_code == status.HTTP_409_CONFLICT

    def test_07_cross_session_isolation(self, client, sample_anime):
        """Step 8: User A cannot see or mutate User B's private watchlist."""
        # User A session
        client_a = client
        res_a = client_a.get('/api/health/')
        token_a = res_a.cookies[SESSION_COOKIE_NAME].value
        client_a.cookies[SESSION_COOKIE_NAME] = token_a
        client_a.post('/api/list/', {'mal_id': sample_anime.mal_id, 'status': 'Completed'}, content_type='application/json')

        # User B session (different client)
        from django.test import Client
        client_b = Client()
        res_b = client_b.get('/api/health/')
        token_b = res_b.cookies[SESSION_COOKIE_NAME].value
        assert token_a != token_b
        client_b.cookies[SESSION_COOKIE_NAME] = token_b

        # User B's list should be empty
        list_b = client_b.get('/api/list/')
        results_b = list_b.data.get('results', list_b.data)
        assert len(results_b) == 0

    def test_08_session_clearing_resets_identity(self, client, sample_anime):
        """Step 9: When session cookie is removed, a brand new identity is assigned."""
        res1 = client.get('/api/health/')
        token1 = res1.cookies[SESSION_COOKIE_NAME].value
        client.cookies[SESSION_COOKIE_NAME] = token1
        client.patch('/api/profile/', {'display_name': 'EphemeralGuest'}, content_type='application/json')

        # Clear cookie
        del client.cookies[SESSION_COOKIE_NAME]

        # Request again
        res2 = client.get('/api/health/')
        token2 = res2.cookies[SESSION_COOKIE_NAME].value
        assert token1 != token2

        # Verify new user has default Guest name
        client.cookies[SESSION_COOKIE_NAME] = token2
        profile_res = client.get('/api/profile/')
        assert profile_res.data['display_name'] == "Guest"

    def test_09_privilege_escalation_rejected(self, client):
        """Step 10: Attempting to elevate role or staff status via public profile API is blocked."""
        res = client.get('/api/health/')
        token = res.cookies[SESSION_COOKIE_NAME].value
        client.cookies[SESSION_COOKIE_NAME] = token

        # Attempt to inject role="admin" and is_staff=True
        attack_res = client.patch(
            '/api/profile/',
            {'display_name': 'Hacker', 'role': 'admin', 'is_staff': True, 'is_superuser': True},
            content_type='application/json'
        )
        assert attack_res.status_code == status.HTTP_400_BAD_REQUEST

        # Confirm user role is unchanged
        user = User.objects.get(session_key=token)
        assert user.role == 'user'
        assert user.is_staff is False
