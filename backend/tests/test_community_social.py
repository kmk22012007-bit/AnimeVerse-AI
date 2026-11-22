import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.anime.models import Anime
from apps.community.models import (
    CommunityPost,
    Comment,
    PostLike,
    Poll,
    PollOption,
    PollVote,
    CommunityReport,
    Review,
    ReviewHelpful,
)
from apps.notifications.models import Notification, NotificationPreference


@pytest.fixture
def user_author(db):
    user = User.objects.create(session_key="a" * 64, display_name="AuthorUser", role="user")
    NotificationPreference.get_for_user(user)
    return user


@pytest.fixture
def user_viewer(db):
    user = User.objects.create(session_key="b" * 64, display_name="ViewerUser", role="user")
    NotificationPreference.get_for_user(user)
    return user


@pytest.fixture
def user_moderator(db):
    user = User.objects.create(session_key="m" * 64, display_name="ModUser", role="moderator", is_staff=True)
    NotificationPreference.get_for_user(user)
    return user


@pytest.fixture
def client_author(user_author):
    client = APIClient()
    client.cookies['animeverse_session'] = user_author.session_key
    return client


@pytest.fixture
def client_viewer(user_viewer):
    client = APIClient()
    client.cookies['animeverse_session'] = user_viewer.session_key
    return client


@pytest.fixture
def client_moderator(user_moderator):
    client = APIClient()
    client.cookies['animeverse_session'] = user_moderator.session_key
    return client


@pytest.fixture
def sample_anime(db):
    return Anime.objects.create(
        mal_id=16498,
        title="Attack on Titan",
        poster_url="https://cdn.myanimelist.net/images/anime/10/47347.jpg",
        anime_type="tv",
        total_episodes=25
    )


@pytest.fixture
def adult_anime(db):
    return Anime.objects.create(
        mal_id=999999,
        title="Explicit Adult Hentai Test",
        poster_url="https://example.com/hentai.jpg",
        anime_type="ova",
        total_episodes=2
    )


# ==========================================
# 1. COMMUNITY FEED & SORTING TESTS
# ==========================================
@pytest.mark.django_db
class TestCommunityFeedAndSorting:
    def test_feed_latest_sorting(self, client_viewer, user_author):
        p1 = CommunityPost.objects.create(user=user_author, title="Post 1", body="Old body")
        p2 = CommunityPost.objects.create(user=user_author, title="Post 2", body="New body")

        res = client_viewer.get('/api/community/posts/?sort=latest')
        assert res.status_code == 200
        titles = [p['title'] for p in res.data['results']]
        assert titles[0] == "Post 2"
        assert titles[1] == "Post 1"

    def test_feed_popular_sorting(self, client_viewer, user_author, user_viewer):
        p_unpopular = CommunityPost.objects.create(user=user_author, title="Unpopular", body="body")
        p_popular = CommunityPost.objects.create(user=user_author, title="Popular", body="body")
        PostLike.objects.create(post=p_popular, user=user_author)
        PostLike.objects.create(post=p_popular, user=user_viewer)

        res = client_viewer.get('/api/community/posts/?sort=popular')
        assert res.status_code == 200
        results = res.data['results']
        assert results[0]['id'] == p_popular.id
        assert results[0]['like_count'] == 2

    def test_feed_discussed_sorting(self, client_viewer, user_author, user_viewer):
        p_quiet = CommunityPost.objects.create(user=user_author, title="Quiet", body="body")
        p_discussed = CommunityPost.objects.create(user=user_author, title="Discussed", body="body")
        Comment.objects.create(post=p_discussed, user=user_author, body="c1")
        Comment.objects.create(post=p_discussed, user=user_viewer, body="c2")

        res = client_viewer.get('/api/community/posts/?sort=discussed')
        assert res.status_code == 200
        results = res.data['results']
        assert results[0]['id'] == p_discussed.id
        assert results[0]['comment_count'] == 2

    def test_feed_trending_sorting_with_decay(self, client_viewer, user_author, user_viewer):
        # Recent post with moderate engagement vs very old post with many likes
        p_recent = CommunityPost.objects.create(user=user_author, title="Trending Recent", body="body")
        p_old = CommunityPost.objects.create(user=user_author, title="Old Post", body="body")
        # Manually backdate p_old to 5 days ago
        CommunityPost.objects.filter(id=p_old.id).update(created_at=timezone.now() - timedelta(days=5))

        PostLike.objects.create(post=p_recent, user=user_author)
        Comment.objects.create(post=p_recent, user=user_viewer, body="Great!")

        res = client_viewer.get('/api/community/posts/?sort=trending')
        assert res.status_code == 200
        results = res.data['results']
        assert results[0]['id'] == p_recent.id

    def test_feed_anime_specific_filtering(self, client_viewer, user_author, sample_anime):
        p_anime = CommunityPost.objects.create(user=user_author, anime=sample_anime, title="AoT Discussion", body="body")
        p_general = CommunityPost.objects.create(user=user_author, title="General Post", body="body")

        res = client_viewer.get(f'/api/community/posts/?anime_id={sample_anime.mal_id}')
        assert res.status_code == 200
        ids = [p['id'] for p in res.data['results']]
        assert p_anime.id in ids
        assert p_general.id not in ids

    def test_feed_tag_and_category_filtering(self, client_viewer, user_author):
        p_theory = CommunityPost.objects.create(
            user=user_author, title="AoT Ending Theory", body="body", category="theory", tags=["Theory", "Ending"]
        )
        p_art = CommunityPost.objects.create(
            user=user_author, title="Levi Fanart", body="body", category="fan_art", tags=["Art"]
        )

        res_cat = client_viewer.get('/api/community/posts/?category=theory')
        assert res_cat.status_code == 200
        assert len(res_cat.data['results']) == 1
        assert res_cat.data['results'][0]['id'] == p_theory.id

        res_tag = client_viewer.get('/api/community/posts/?tag=Theory')
        assert res_tag.status_code == 200
        assert len(res_tag.data['results']) == 1
        assert res_tag.data['results'][0]['id'] == p_theory.id

    def test_feed_keyword_search(self, client_viewer, user_author):
        p1 = CommunityPost.objects.create(user=user_author, title="UniqueSearchKeyword Discussion", body="Regular body")
        p2 = CommunityPost.objects.create(user=user_author, title="Another topic", body="Contains UniqueSearchKeyword inside body")
        p3 = CommunityPost.objects.create(user=user_author, title="Unrelated", body="No keyword here")

        res = client_viewer.get('/api/community/posts/?search=UniqueSearchKeyword')
        assert res.status_code == 200
        ids = [p['id'] for p in res.data['results']]
        assert p1.id in ids
        assert p2.id in ids
        assert p3.id not in ids


# ==========================================
# 2. SPOILER PROTECTION TESTS
# ==========================================
@pytest.mark.django_db
class TestSpoilerProtection:
    def test_post_spoiler_flag_persistence(self, client_author, client_viewer):
        res = client_author.post('/api/community/posts/', {
            'title': 'Chapter 139 Secret Reveal',
            'body': 'Eren planned everything from the start.',
            'category': 'theory',
            'is_spoiler': True,
        }, format='json')
        assert res.status_code == 201
        assert res.data['is_spoiler'] is True
        post_id = res.data['id']

        # Viewer retrieves post
        res_view = client_viewer.get(f'/api/community/posts/{post_id}/')
        assert res_view.status_code == 200
        assert res_view.data['post']['is_spoiler'] is True

    def test_comment_spoiler_flag_persistence(self, client_author, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Title", body="Body")
        res = client_viewer.post(f'/api/community/posts/{post.id}/comments/', {
            'body': 'This character dies in episode 12.',
            'is_spoiler': True,
        }, format='json')
        assert res.status_code == 201
        assert res.data['is_spoiler'] is True

    def test_review_spoiler_flag_persistence(self, client_author, sample_anime):
        res = client_author.post(f'/api/anime/{sample_anime.mal_id}/reviews/', {
            'title': 'Major plot twist review',
            'score': 9,
            'body': 'The twist at the end changes everything about the series.',
            'is_spoiler': True,
        }, format='json')
        assert res.status_code == 201
        assert res.data['is_spoiler'] is True

    def test_spoiler_notification_preview_protection(self, client_viewer, user_author):
        # Post has spoiler
        post = CommunityPost.objects.create(
            user=user_author,
            title="Eren dies in final chapter",
            body="Spoiler content",
            is_spoiler=True
        )

        # Viewer likes spoiler post
        res_like = client_viewer.post(f'/api/community/posts/{post.id}/like/')
        assert res_like.status_code == 200

        like_notif = Notification.objects.filter(user=user_author, notification_type='community_like').first()
        assert like_notif is not None
        # Does NOT leak the spoiler title
        assert "Eren dies" not in like_notif.message
        assert "[Contains Spoilers]" in like_notif.message

        # Viewer comments with spoiler flag
        res_comment = client_viewer.post(f'/api/community/posts/{post.id}/comments/', {
            'body': 'Mikasa kills him in the mouth.',
            'is_spoiler': True
        }, format='json')
        assert res_comment.status_code == 201

        comment_notif = Notification.objects.filter(user=user_author, notification_type='community_comment').first()
        assert comment_notif is not None
        # Preview MUST mask the spoiler body
        assert "Mikasa kills" not in comment_notif.message
        assert "[Contains Spoilers]" in comment_notif.message


# ==========================================
# 3. COMMUNITY POLLS TESTS
# ==========================================
@pytest.mark.django_db
class TestCommunityPolls:
    def test_poll_creation_with_post(self, client_author):
        payload = {
            'title': 'Best Anime Genre Poll',
            'body': 'Vote for your favorite genre below!',
            'category': 'discussion',
            'poll': {
                'question': 'Which genre do you prefer?',
                'options': ['Action', 'Psychological', 'Romance', 'Fantasy'],
                'expires_days': 5,
            }
        }
        res = client_author.post('/api/community/posts/', payload, format='json')
        assert res.status_code == 201
        assert res.data['poll'] is not None
        poll = res.data['poll']
        assert poll['question'] == 'Which genre do you prefer?'
        assert len(poll['options']) == 4
        assert poll['total_votes'] == 0

    def test_poll_option_validation_requires_two_options(self, client_author):
        payload = {
            'title': 'Invalid Poll',
            'body': 'body',
            'poll': {
                'question': 'Only one option?',
                'options': ['Option 1'],
            }
        }
        res = client_author.post('/api/community/posts/', payload, format='json')
        assert res.status_code == 400
        assert 'poll' in res.data['details']

    def test_poll_voting_and_single_vote_enforcement(self, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Poll Post", body="body")
        poll = Poll.objects.create(user=user_author, post=post, question="Favorite Titan?")
        opt1 = PollOption.objects.create(poll=poll, text="Attack Titan", order=0)
        opt2 = PollOption.objects.create(poll=poll, text="Colossal Titan", order=1)

        # 1. Cast first vote
        res_vote = client_viewer.post(f'/api/community/polls/{poll.id}/vote/', {'option_id': opt1.id}, format='json')
        assert res_vote.status_code == 200
        assert res_vote.data['total_votes'] == 1
        assert res_vote.data['my_vote_option_id'] == opt1.id
        opt1_res = [o for o in res_vote.data['options'] if o['id'] == opt1.id][0]
        assert opt1_res['vote_count'] == 1
        assert opt1_res['percentage'] == 100.0

        # 2. Duplicate vote attempt by same user fails (409 Conflict)
        res_dup = client_viewer.post(f'/api/community/polls/{poll.id}/vote/', {'option_id': opt2.id}, format='json')
        assert res_dup.status_code == 409

    def test_poll_closed_restrictions(self, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Expired Poll Post", body="body")
        poll = Poll.objects.create(
            user=user_author,
            post=post,
            question="Old Question?",
            expires_at=timezone.now() - timedelta(days=1)
        )
        opt = PollOption.objects.create(poll=poll, text="Expired Option", order=0)

        res = client_viewer.post(f'/api/community/polls/{poll.id}/vote/', {'option_id': opt.id}, format='json')
        assert res.status_code == 400
        assert "closed" in res.data['message'].lower()


# ==========================================
# 4. INTERACTIONS & NOTIFICATION TESTS
# ==========================================
@pytest.mark.django_db
class TestCommunityInteractions:
    def test_post_like_and_unlike_toggle(self, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Nice Post", body="body")
        res_like = client_viewer.post(f'/api/community/posts/{post.id}/like/')
        assert res_like.status_code == 200
        assert res_like.data['liked'] is True
        assert res_like.data['like_count'] == 1

        res_unlike = client_viewer.delete(f'/api/community/posts/{post.id}/like/')
        assert res_unlike.status_code == 200
        assert res_unlike.data['liked'] is False
        assert res_unlike.data['like_count'] == 0

    def test_comment_and_reply_threading(self, client_author, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Thread Post", body="body")

        # Root comment
        res_root = client_viewer.post(f'/api/community/posts/{post.id}/comments/', {'body': 'Root comment'}, format='json')
        assert res_root.status_code == 201
        root_id = res_root.data['id']

        # Reply comment
        res_reply = client_author.post(f'/api/community/posts/{post.id}/comments/', {
            'body': 'Reply to root',
            'parent_id': root_id
        }, format='json')
        assert res_reply.status_code == 201
        assert res_reply.data['parent_id'] == root_id

        # Check post detail hierarchy
        res_detail = client_viewer.get(f'/api/community/posts/{post.id}/')
        assert res_detail.status_code == 200
        assert len(res_detail.data['comments']) == 1
        assert len(res_detail.data['comments'][0]['replies']) == 1

    def test_self_notification_prevention(self, client_author, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Self post", body="body")
        # Author likes own post
        client_author.post(f'/api/community/posts/{post.id}/like/')
        assert Notification.objects.filter(user=user_author).count() == 0

        # Author comments on own post
        client_author.post(f'/api/community/posts/{post.id}/comments/', {'body': 'my own comment'}, format='json')
        assert Notification.objects.filter(user=user_author).count() == 0

    def test_review_helpful_vote_toggle(self, client_viewer, user_author, sample_anime):
        review = Review.objects.create(user=user_author, anime=sample_anime, score=10, body="Incredible masterpiece of modern anime.")

        res_helpful = client_viewer.post(f'/api/reviews/{review.id}/helpful/')
        assert res_helpful.status_code == 200
        assert res_helpful.data['is_helpful'] is True
        assert res_helpful.data['helpful_count'] == 1

        res_unhelpful = client_viewer.post(f'/api/reviews/{review.id}/helpful/')
        assert res_unhelpful.status_code == 200
        assert res_unhelpful.data['is_helpful'] is False
        assert res_unhelpful.data['helpful_count'] == 0


# ==========================================
# 5. REPORTING & MODERATION TESTS
# ==========================================
@pytest.mark.django_db
class TestReportingAndModeration:
    def test_report_creation(self, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Reportable Title", body="Spam message")

        res = client_viewer.post('/api/community/reports/', {
            'target_type': 'post',
            'target_id': post.id,
            'reason': 'spam',
            'explanation': 'Promoting commercial crypto scam.'
        }, format='json')
        assert res.status_code == 201
        assert res.data['status'] == 'pending'
        assert CommunityReport.objects.filter(post=post).count() == 1

    def test_duplicate_report_prevention(self, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Title", body="body")
        client_viewer.post('/api/community/reports/', {
            'target_type': 'post',
            'target_id': post.id,
            'reason': 'spam'
        }, format='json')

        res_dup = client_viewer.post('/api/community/reports/', {
            'target_type': 'post',
            'target_id': post.id,
            'reason': 'inappropriate'
        }, format='json')
        assert res_dup.status_code == 409

    def test_unauthorized_moderation_access_forbidden(self, client_viewer):
        # Normal user cannot view moderation dashboard
        res = client_viewer.get('/api/community/moderation/reports/')
        assert res.status_code == 403

    def test_moderator_access_and_action_hide_content(self, client_moderator, user_author, user_viewer):
        post = CommunityPost.objects.create(user=user_author, title="Toxic Post", body="Hate speech body")
        report = CommunityReport.objects.create(
            reporter=user_viewer,
            target_type='post',
            post=post,
            reason='harassment',
            status='pending'
        )

        # Moderator lists reports
        res_list = client_moderator.get('/api/community/moderation/reports/?status=pending')
        assert res_list.status_code == 200
        assert len(res_list.data['results']) >= 1

        # Moderator hides toxic post
        res_action = client_moderator.patch(f'/api/community/moderation/reports/{report.id}/', {
            'status': 'resolved',
            'action_taken': 'content_hidden',
            'moderator_notes': 'Violation of harassment policy.'
        }, format='json')
        assert res_action.status_code == 200
        assert res_action.data['status'] == 'resolved'
        assert res_action.data['action_taken'] == 'content_hidden'

        # Post is now hidden
        post.refresh_from_db()
        assert post.is_hidden is True


# ==========================================
# 6. SECURITY & CONTENT SAFETY TESTS
# ==========================================
@pytest.mark.django_db
class TestSecurityAndContentSafety:
    def test_ownership_checks_post_edit_and_delete(self, client_author, client_viewer, user_author):
        post = CommunityPost.objects.create(user=user_author, title="Author Post", body="Original body")

        # Viewer tries to edit author's post -> 403 Forbidden
        res_edit_forbidden = client_viewer.patch(f'/api/community/posts/{post.id}/', {'title': 'Hacked Title'}, format='json')
        assert res_edit_forbidden.status_code == 403

        # Viewer tries to delete author's post -> 403 Forbidden
        res_del_forbidden = client_viewer.delete(f'/api/community/posts/{post.id}/')
        assert res_del_forbidden.status_code == 403

        # Author edits own post -> 200 OK
        res_edit_ok = client_author.patch(f'/api/community/posts/{post.id}/', {'title': 'Updated Title'}, format='json')
        assert res_edit_ok.status_code == 200
        assert res_edit_ok.data['title'] == 'Updated Title'

    def test_adult_anime_exclusion_in_discussions(self, client_author):
        from apps.anime.models import JikanCache
        adult_mal_id = 99999
        JikanCache.objects.create(
            cache_key=f"details_{adult_mal_id}",
            payload={'data': {'mal_id': adult_mal_id, 'genres': [{'mal_id': 12, 'name': 'Hentai'}], 'rating': 'Rx - Hentai'}},
            expires_at=timezone.now() + timedelta(days=1)
        )

        res_adult = client_author.post('/api/community/posts/', {
            'title': 'Adult Anime Discussion',
            'body': 'Discussing explicit 18+ content here.',
            'anime_id': adult_mal_id,
        }, format='json')
        assert res_adult.status_code == 400
        assert "not available" in res_adult.data['message'].lower() or "blocked" in res_adult.data['message'].lower()

    def test_invalid_parameters_and_ids(self, client_author):
        # 404 on missing post
        res_404 = client_author.get('/api/community/posts/9999999/')
        assert res_404.status_code == 404

        # Validation error on empty post body
        res_invalid = client_author.post('/api/community/posts/', {'title': 'Title'}, format='json')
        assert res_invalid.status_code == 400

    def test_mass_assignment_privileged_role_rejection(self, client_author, user_author):
        """Ordinary users cannot modify privileged role or staff status via profile update."""
        # Attempt to escalate role to moderator
        res_role = client_author.patch('/api/profile/', {'role': 'moderator'}, format='json')
        assert res_role.status_code == 400
        assert "prohibited" in str(res_role.data).lower()

        # Attempt to escalate is_staff
        res_staff = client_author.patch('/api/profile/', {'is_staff': True}, format='json')
        assert res_staff.status_code == 400
        assert "prohibited" in str(res_staff.data).lower()

        # Verify database fields were NOT modified
        user_author.refresh_from_db()
        assert user_author.role == 'user'
        assert user_author.is_staff is False
        assert user_author.is_moderator is False
