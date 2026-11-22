import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from apps.profiles.models import User, UserFollow
from apps.community.models import CommunityPost, Comment, Review, ReviewHelpful
from apps.notifications.models import Notification, NotificationType
from apps.anime.models import Anime, JikanCache
from apps.tracking.models import UserAnimeList, WatchStatus


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create(
        session_key="a" * 64,
        display_name="UserAlice",
        bio="Alice the anime enthusiast",
        is_public=True
    )


@pytest.fixture
def user_b(db):
    return User.objects.create(
        session_key="b" * 64,
        display_name="UserBob",
        bio="Bob the Shounen fan",
        is_public=True
    )


@pytest.fixture
def user_c(db):
    return User.objects.create(
        session_key="c" * 64,
        display_name="UserCharlie",
        bio="Charlie the critic",
        is_public=True
    )


@pytest.fixture
def sample_anime(db):
    anime = Anime.objects.create(
        mal_id=777,
        title="Epic Fantasy Anime",
        anime_type="TV",
        total_episodes=24,
        poster_url="https://example.com/poster777.jpg"
    )
    payload = {
        'mal_id': 777,
        'title': "Epic Fantasy Anime",
        'genres': [{'name': 'Action'}, {'name': 'Fantasy'}],
        'score': 8.5,
        'episodes': 24,
        'poster_url': "https://example.com/poster777.jpg"
    }
    JikanCache.objects.create(
        cache_key="anime:777:full",
        payload={'data': payload},
        expires_at=timezone.now() + timedelta(days=7)
    )
    return anime


@pytest.mark.django_db
class TestUserFollowSystem:

    def test_follow_user_success(self, api_client, user_a, user_b):
        """User A follows User B: creates relationship, updates counts, dispatches notification."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.post(f"/api/users/{user_b.id}/follow/")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['is_following'] is True
        assert data['follower_count'] == 1
        assert UserFollow.objects.filter(follower=user_a, followed=user_b).exists()

        # Check in-app notification sent to User B
        notif = Notification.objects.filter(user=user_b, notification_type=NotificationType.SYSTEM).first()
        assert notif is not None
        assert "UserAlice started following you" in notif.message

    def test_self_follow_rejected(self, api_client, user_a):
        """User cannot follow themselves."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.post(f"/api/users/{user_a.id}/follow/")

        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot follow yourself" in res.json().get('message', '').lower()

    def test_duplicate_follow_is_idempotent(self, api_client, user_a, user_b):
        """Following an already-followed user succeeds idempotently without duplicate rows."""
        api_client.cookies['animeverse_session'] = user_a.session_key
        res1 = api_client.post(f"/api/users/{user_b.id}/follow/")
        assert res1.status_code == status.HTTP_200_OK

        res2 = api_client.post(f"/api/users/{user_b.id}/follow/")
        assert res2.status_code == status.HTTP_200_OK
        assert UserFollow.objects.filter(follower=user_a, followed=user_b).count() == 1

    def test_unfollow_user(self, api_client, user_a, user_b):
        """Unfollow removes the relationship and updates follower count."""
        UserFollow.objects.create(follower=user_a, followed=user_b)
        assert UserFollow.objects.filter(follower=user_a, followed=user_b).exists()

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.delete(f"/api/users/{user_b.id}/follow/")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['is_following'] is False
        assert data['follower_count'] == 0
        assert not UserFollow.objects.filter(follower=user_a, followed=user_b).exists()

    def test_follower_and_following_lists(self, api_client, user_a, user_b, user_c):
        """Followers and following lists return paginated users with is_following context."""
        UserFollow.objects.create(follower=user_a, followed=user_b)
        UserFollow.objects.create(follower=user_c, followed=user_b)

        api_client.cookies['animeverse_session'] = user_a.session_key

        # Check User B's followers
        res_followers = api_client.get(f"/api/users/{user_b.id}/followers/")
        assert res_followers.status_code == status.HTTP_200_OK
        data_followers = res_followers.json()
        assert len(data_followers['results']) == 2
        follower_names = [f['display_name'] for f in data_followers['results']]
        assert "UserAlice" in follower_names
        assert "UserCharlie" in follower_names

        # Check User A's following
        res_following = api_client.get(f"/api/users/{user_a.id}/following/")
        assert res_following.status_code == status.HTTP_200_OK
        data_following = res_following.json()
        assert len(data_following['results']) == 1
        assert data_following['results'][0]['display_name'] == "UserBob"
        assert data_following['results'][0]['is_following'] is True


@pytest.mark.django_db
class TestPersonalizedCommunityFeed:

    def test_following_feed_filter(self, api_client, user_a, user_b, user_c):
        """Feed with sort=following or feed=following only returns posts from followed authors."""
        # User A follows User B, but does not follow User C
        UserFollow.objects.create(follower=user_a, followed=user_b)

        post_b = CommunityPost.objects.create(
            user=user_b,
            title="Bob's Anime Theory",
            body="Theory details about the world",
            category="theory"
        )
        post_c = CommunityPost.objects.create(
            user=user_c,
            title="Charlie's Review",
            body="Review details about an anime",
            category="review"
        )

        api_client.cookies['animeverse_session'] = user_a.session_key

        # All feed includes both
        res_all = api_client.get("/api/community/posts/")
        assert res_all.status_code == status.HTTP_200_OK
        all_ids = [p['id'] for p in res_all.json()['results']]
        assert post_b.id in all_ids
        assert post_c.id in all_ids

        # Following feed includes only post_b
        res_following = api_client.get("/api/community/posts/?sort=following")
        assert res_following.status_code == status.HTTP_200_OK
        following_ids = [p['id'] for p in res_following.json()['results']]
        assert post_b.id in following_ids
        assert post_c.id not in following_ids

    def test_genre_community_feed_filter(self, api_client, user_a):
        """Community posts can be filtered by genre matching tags or body."""
        post_shounen = CommunityPost.objects.create(
            user=user_a,
            title="Best Shounen Arcs",
            body="Discussing shounen pacing and battle fights",
            category="discussion",
            tags=["Shounen", "Action"]
        )
        post_romance = CommunityPost.objects.create(
            user=user_a,
            title="Heartwarming Romance Moments",
            body="Discussing romance drama anime",
            category="discussion",
            tags=["Romance", "Drama"]
        )

        res_shounen = api_client.get("/api/community/posts/?genre=Shounen")
        assert res_shounen.status_code == status.HTTP_200_OK
        results = res_shounen.json()['results']
        ids = [p['id'] for p in results]
        assert post_shounen.id in ids
        assert post_romance.id not in ids


@pytest.mark.django_db
class TestUserMentionsAndNotifications:

    def test_post_mention_dispatches_notification(self, api_client, user_a, user_b):
        """Mentioning @UserBob in a post creates a notification for UserBob."""
        api_client.cookies['animeverse_session'] = user_a.session_key

        res = api_client.post("/api/community/posts/", {
            'title': "Exciting Discussion",
            'body': "What do you think about this arc, @UserBob?",
            'category': "discussion"
        }, format='json')

        assert res.status_code == status.HTTP_201_CREATED

        # Check notification dispatched to user_b
        notif = Notification.objects.filter(
            user=user_b,
            notification_type=NotificationType.COMMUNITY_COMMENT
        ).first()
        assert notif is not None
        assert "Mentioned by UserAlice" in notif.title

    def test_comment_mention_dispatches_notification(self, api_client, user_a, user_b):
        """Mentioning @UserBob in a comment creates a notification for UserBob."""
        post = CommunityPost.objects.create(
            user=user_a,
            title="General Discussion",
            body="Let us chat about the anime season.",
            category="discussion"
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.post(f"/api/community/posts/{post.id}/comments/", {
            'body': "Paging @UserBob for your perspective on episode 5!"
        }, format='json')

        assert res.status_code == status.HTTP_201_CREATED

        notif = Notification.objects.filter(
            user=user_b,
            notification_type=NotificationType.COMMUNITY_COMMENT
        ).first()
        assert notif is not None
        assert "Mentioned by UserAlice" in notif.title

    def test_self_mention_suppressed(self, api_client, user_a):
        """Self-mentions (@UserAlice by UserAlice) must not dispatch notifications."""
        api_client.cookies['animeverse_session'] = user_a.session_key

        res = api_client.post("/api/community/posts/", {
            'title': "Note to Self",
            'body': "Reminder for @UserAlice to check the soundtrack later.",
            'category': "discussion"
        }, format='json')

        assert res.status_code == status.HTTP_201_CREATED
        notifs = Notification.objects.filter(user=user_a)
        assert notifs.count() == 0


@pytest.mark.django_db
class TestPublicUserProfileSocialData:

    def test_public_user_profile_response(self, api_client, user_a, user_b, sample_anime):
        """Public user profile returns stats, favorite genres, follow status, and community activity."""
        # User B watches sample_anime
        UserAnimeList.objects.create(
            user=user_b,
            anime=sample_anime,
            status=WatchStatus.COMPLETED,
            watched_episodes=24,
            rating=9
        )

        # User B has a post and review
        post = CommunityPost.objects.create(
            user=user_b,
            title="Bob's Analysis",
            body="Deep analysis of themes",
            category="theory"
        )
        Review.objects.create(
            user=user_b,
            anime=sample_anime,
            title="Masterpiece",
            body="One of the best series ever made.",
            score=9
        )

        # User A follows User B
        UserFollow.objects.create(follower=user_a, followed=user_b)

        # User A requests User B's profile
        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get(f"/api/users/{user_b.id}/")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data['id'] == user_b.id
        assert data['display_name'] == "UserBob"
        assert data['is_following'] is True
        assert data['is_self'] is False
        assert data['follower_count'] == 1
        assert data['following_count'] == 0

        # Stats
        assert data['stats']['completed_count'] == 1
        assert data['stats']['total_episodes_watched'] == 24
        assert data['stats']['average_rating'] == 9.0

        # Favorite genres
        assert "Action" in data['favorite_genres'] or "Fantasy" in data['favorite_genres']

        # Community Activity
        assert data['community_activity']['posts_count'] == 1
        assert data['community_activity']['reviews_count'] == 1
        assert len(data['recent_posts']) == 1
        assert data['recent_posts'][0]['title'] == "Bob's Analysis"


@pytest.mark.django_db
class TestReviewHelpfulVoting:

    def test_review_helpful_toggle(self, api_client, user_a, user_b, sample_anime):
        """Users can toggle helpful feedback on reviews."""
        review = Review.objects.create(
            user=user_b,
            anime=sample_anime,
            title="Helpful Review",
            body="Detailed breakdown of plot and animation.",
            score=8
        )
        assert review.helpful_count == 0

        api_client.cookies['animeverse_session'] = user_a.session_key

        # Vote helpful
        res1 = api_client.post(f"/api/reviews/{review.id}/helpful/")
        assert res1.status_code == status.HTTP_200_OK
        assert res1.json()['is_helpful'] is True
        assert res1.json()['helpful_count'] == 1
        review.refresh_from_db()
        assert review.helpful_count == 1

        # Toggle off
        res2 = api_client.post(f"/api/reviews/{review.id}/helpful/")
        assert res2.status_code == status.HTTP_200_OK
        assert res2.json()['is_helpful'] is False
        assert res2.json()['helpful_count'] == 0
        review.refresh_from_db()
        assert review.helpful_count == 0
