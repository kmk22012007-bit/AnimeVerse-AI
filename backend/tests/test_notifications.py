import pytest
from datetime import datetime, timezone as dt_timezone
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.anime.models import Anime, JikanCache
from apps.community.models import CommunityPost, Comment, PostLike
from apps.notifications.models import Notification, NotificationType, NotificationPreference
from apps.notifications.services import NotificationService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_a(db):
    return User.objects.create(
        session_key="a" * 64,
        display_name="ErenYeager",
        is_public=True
    )

@pytest.fixture
def user_b(db):
    return User.objects.create(
        session_key="b" * 64,
        display_name="MikasaAckerman",
        is_public=True
    )

@pytest.fixture
def standard_anime(db):
    return Anime.objects.create(
        mal_id=16498,
        title="Attack on Titan",
        poster_url="https://cdn.myanimelist.net/images/anime/10/47347.jpg",
        anime_type="TV",
        total_episodes=25
    )

@pytest.fixture
def adult_anime(db):
    anime = Anime.objects.create(
        mal_id=999999,
        title="Explicit Adult Hentai OVA",
        poster_url="https://example.com/adult.jpg",
        anime_type="OVA",
        total_episodes=1
    )
    JikanCache.objects.create(
        cache_key="details_999999",
        payload={
            "data": {
                "mal_id": 999999,
                "title": "Explicit Adult Hentai OVA",
                "genres": [{"mal_id": 12, "name": "Hentai"}],
                "rating": "Rx - Hentai"
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )
    return anime

@pytest.mark.django_db
class TestNotificationSystem:

    def test_notification_list_empty(self, api_client, user_a):
        """Verifies clean empty list and 0 unread count for fresh user."""
        api_client.cookies['animeverse_session'] = user_a.session_key

        res = api_client.get('/api/notifications/')
        assert res.status_code == 200
        data = res.json()
        assert data['results'] == []
        assert data['pagination']['total'] == 0

        res_count = api_client.get('/api/notifications/unread-count/')
        assert res_count.status_code == 200
        assert res_count.json()['unread_count'] == 0

    def test_notification_creation_and_pagination(self, api_client, user_a):
        """Verifies notification creation and pagination envelopes."""
        for i in range(25):
            Notification.objects.create(
                user=user_a,
                notification_type=NotificationType.SYSTEM,
                title=f"Announcement {i}",
                message=f"System message {i}",
                is_read=False
            )

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.get('/api/notifications/?page=1')
        assert res.status_code == 200
        data = res.json()
        assert len(data['results']) == 20
        assert data['pagination']['total'] == 25
        assert data['pagination']['total_pages'] == 2

        res_page2 = api_client.get('/api/notifications/?page=2')
        assert res_page2.status_code == 200
        assert len(res_page2.json()['results']) == 5

    def test_user_isolation_and_idor_prevention(self, api_client, user_a, user_b):
        """Ensures notifications belonging to User A cannot be accessed, read, or deleted by User B."""
        notif_a = Notification.objects.create(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Private Notice for A",
            message="Only User A can see this.",
            is_read=False
        )

        api_client.cookies['animeverse_session'] = user_b.session_key

        # User B listing notifications should see 0
        res = api_client.get('/api/notifications/')
        assert res.status_code == 200
        assert res.json()['pagination']['total'] == 0

        # User B trying to mark User A's notification as read should get 404
        res_read = api_client.patch(f'/api/notifications/{notif_a.id}/read/')
        assert res_read.status_code == 404

        # User B trying to delete User A's notification should get 404
        res_delete = api_client.delete(f'/api/notifications/{notif_a.id}/')
        assert res_delete.status_code == 404

        # Verify notif_a is unchanged
        notif_a.refresh_from_db()
        assert notif_a.is_read is False

    def test_unread_count_and_mark_read(self, api_client, user_a):
        """Verifies unread counter accuracy and marking single notification read."""
        n1 = Notification.objects.create(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Test 1",
            message="Msg 1",
            is_read=False
        )
        n2 = Notification.objects.create(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Test 2",
            message="Msg 2",
            is_read=False
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        assert api_client.get('/api/notifications/unread-count/').json()['unread_count'] == 2

        # Mark n1 read
        res = api_client.patch(f'/api/notifications/{n1.id}/read/')
        assert res.status_code == 200
        assert res.json()['is_read'] is True

        # Unread count should now be 1
        assert api_client.get('/api/notifications/unread-count/').json()['unread_count'] == 1

    def test_mark_all_read(self, api_client, user_a):
        """Verifies bulk mark-all-read endpoint."""
        for i in range(5):
            Notification.objects.create(
                user=user_a,
                notification_type=NotificationType.SYSTEM,
                title=f"Test {i}",
                message=f"Msg {i}",
                is_read=False
            )

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.post('/api/notifications/mark-all-read/')
        assert res.status_code == 200
        assert res.json()['marked_count'] == 5
        assert res.json()['unread_count'] == 0

        assert Notification.objects.filter(user=user_a, is_read=False).count() == 0

    def test_delete_and_clear_read(self, api_client, user_a):
        """Verifies single deletion and clearing all read notifications."""
        n_unread = Notification.objects.create(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Keep Unread",
            message="Msg",
            is_read=False
        )
        n_read1 = Notification.objects.create(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Read 1",
            message="Msg",
            is_read=True
        )
        n_read2 = Notification.objects.create(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Read 2",
            message="Msg",
            is_read=True
        )

        api_client.cookies['animeverse_session'] = user_a.session_key

        # Delete single read notification
        res_del = api_client.delete(f'/api/notifications/{n_read1.id}/')
        assert res_del.status_code == 204
        assert not Notification.objects.filter(id=n_read1.id).exists()

        # Clear remaining read notifications
        res_clear = api_client.delete('/api/notifications/clear-read/')
        assert res_clear.status_code == 200
        assert res_clear.json()['deleted_count'] == 1
        assert res_clear.json()['unread_count'] == 1

        # Only unread notification remains
        remaining = list(Notification.objects.filter(user=user_a))
        assert len(remaining) == 1
        assert remaining[0].id == n_unread.id

    def test_deduplication_prevents_duplicate_notifications(self, user_a):
        """Verifies that duplicate notifications sharing a deduplication key are suppressed."""
        n1 = NotificationService.create_notification(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="First insert",
            message="Initial notification",
            deduplication_key="unique_system_key_1"
        )
        assert n1 is not None

        # Attempt to insert identical deduplication key
        n2 = NotificationService.create_notification(
            user=user_a,
            notification_type=NotificationType.SYSTEM,
            title="Second insert",
            message="Duplicate notification",
            deduplication_key="unique_system_key_1"
        )
        assert n2 is None
        assert Notification.objects.filter(user=user_a).count() == 1

    def test_community_like_generates_notification(self, api_client, user_a, user_b):
        """Verifies that User B liking User A's post dispatches a notification to User A."""
        post = CommunityPost.objects.create(
            user=user_a,
            title="Shingeki no Kyojin is a masterpiece",
            body="The narrative depth and pacing are unmatched."
        )

        api_client.cookies['animeverse_session'] = user_b.session_key
        res = api_client.post(f'/api/community/posts/{post.id}/like/')
        assert res.status_code == 200

        # User A should have received a notification
        notifs = Notification.objects.filter(user=user_a)
        assert notifs.count() == 1
        notif = notifs.first()
        assert notif.notification_type == NotificationType.COMMUNITY_LIKE
        assert user_b.display_name in notif.message
        assert notif.action_url == f"/community?post={post.id}"

    def test_self_like_does_not_generate_notification(self, api_client, user_a):
        """Verifies that User A liking their own post does NOT generate a notification."""
        post = CommunityPost.objects.create(
            user=user_a,
            title="My own thoughts",
            body="Self-reflection post."
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.post(f'/api/community/posts/{post.id}/like/')
        assert res.status_code == 200

        assert Notification.objects.filter(user=user_a).count() == 0

    def test_community_comment_generates_notification(self, api_client, user_a, user_b):
        """Verifies that User B commenting on User A's post dispatches a notification to User A."""
        post = CommunityPost.objects.create(
            user=user_a,
            title="Favorite soundtrack?",
            body="Sawano Hiroyuki or Kohta Yamamoto?"
        )

        api_client.cookies['animeverse_session'] = user_b.session_key
        res = api_client.post(f'/api/community/posts/{post.id}/comments/', data={
            'body': "Definitely Sawano's Vogel im Kafig!"
        })
        assert res.status_code == 201

        notifs = Notification.objects.filter(user=user_a)
        assert notifs.count() == 1
        notif = notifs.first()
        assert notif.notification_type == NotificationType.COMMUNITY_COMMENT
        assert user_b.display_name in notif.message
        assert "Vogel im Kafig" in notif.message

    def test_self_comment_does_not_generate_notification(self, api_client, user_a):
        """Verifies that User A commenting on their own post does NOT generate a notification."""
        post = CommunityPost.objects.create(
            user=user_a,
            title="Follow-up note",
            body="Original post body."
        )

        api_client.cookies['animeverse_session'] = user_a.session_key
        res = api_client.post(f'/api/community/posts/{post.id}/comments/', data={
            'body': "Adding extra detail myself."
        })
        assert res.status_code == 201

        assert Notification.objects.filter(user=user_a).count() == 0

    def test_notification_preferences_controls_generation(self, api_client, user_a, user_b):
        """Verifies that disabling specific categories in preferences suppresses notifications."""
        pref = NotificationPreference.get_for_user(user_a)
        pref.community_likes = False
        pref.save()

        post = CommunityPost.objects.create(
            user=user_a,
            title="Testing preference suppression",
            body="Should not receive like notifications."
        )

        # User B likes post
        api_client.cookies['animeverse_session'] = user_b.session_key
        api_client.post(f'/api/community/posts/{post.id}/like/')

        # User A should NOT receive notification
        assert Notification.objects.filter(user=user_a).count() == 0

        # Now update preferences via API
        api_client.cookies['animeverse_session'] = user_a.session_key
        patch_res = api_client.patch('/api/notifications/preferences/', data={
            'community_likes': True,
            'anime_releases': False
        })
        assert patch_res.status_code == 200
        assert patch_res.json()['community_likes'] is True
        assert patch_res.json()['anime_releases'] is False

        pref.refresh_from_db()
        assert pref.community_likes is True
        assert pref.anime_releases is False

    def test_adult_content_exclusion(self, user_a, adult_anime, standard_anime):
        """Verifies that adult/hentai anime are strictly rejected by the notification service."""
        # 1. Standard anime generates clean notification
        safe_notif = NotificationService.notify_anime_release(user=user_a, anime=standard_anime)
        assert safe_notif is not None
        assert safe_notif.related_anime == standard_anime

        # 2. Adult anime is blocked
        blocked_notif = NotificationService.notify_anime_release(user=user_a, anime=adult_anime)
        assert blocked_notif is None
        assert Notification.objects.filter(user=user_a, related_anime=adult_anime).count() == 0

    def test_invalid_notification_id_returns_404(self, api_client, user_a):
        """Verifies that requests for nonexistent notification IDs return 404."""
        api_client.cookies['animeverse_session'] = user_a.session_key

        assert api_client.patch('/api/notifications/999999/read/').status_code == 404
        assert api_client.delete('/api/notifications/999999/').status_code == 404
