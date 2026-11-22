import logging
from django.db import transaction
from apps.notifications.models import Notification, NotificationType, NotificationPreference
from apps.anime.content_filter import is_excluded_adult_anime, check_anime_id_is_excluded

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Centralized, secure service for generating, filtering, and dispatching user notifications.
    """

    @classmethod
    def sanitize_action_url(cls, url: str) -> str:
        """
        Validates and sanitizes action URLs. Ensures they are safe internal paths.
        """
        if not url:
            return None
        url = url.strip()
        # Strictly permit internal relative application routes
        if url.startswith('/') and not url.startswith('//'):
            return url
        return None

    @classmethod
    def create_notification(
        cls,
        user,
        notification_type: str,
        title: str,
        message: str,
        related_anime=None,
        related_community_id: int = None,
        action_url: str = None,
        deduplication_key: str = None
    ):
        """
        Creates a notification after evaluating user preferences, adult content filters,
        and deduplication constraints.
        """
        if not user or not user.id:
            return None

        # 1. Evaluate User Preferences
        pref = NotificationPreference.get_for_user(user)
        if notification_type == NotificationType.ANIME_RELEASE and not pref.anime_releases:
            return None
        if notification_type == NotificationType.EPISODE_RELEASE and not pref.episode_releases:
            return None
        if notification_type == NotificationType.COMMUNITY_LIKE and not pref.community_likes:
            return None
        if notification_type == NotificationType.COMMUNITY_COMMENT and not pref.community_comments:
            return None
        if notification_type == NotificationType.WATCHLIST_REMINDER and not pref.watchlist_reminders:
            return None
        if notification_type == NotificationType.SYSTEM and not pref.system_notices:
            return None

        # 2. Strict Adult / Hentai Content Exclusion
        if related_anime:
            if is_excluded_adult_anime(related_anime):
                logger.info(f"Notification blocked by adult content filter for anime: {related_anime}")
                return None
            if check_anime_id_is_excluded(related_anime.mal_id):
                return None

        # 3. Deduplication Check
        if deduplication_key:
            if Notification.objects.filter(user=user, deduplication_key=deduplication_key).exists():
                return None

        safe_url = cls.sanitize_action_url(action_url)

        try:
            with transaction.atomic():
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=title.strip()[:150],
                    message=message.strip(),
                    related_anime=related_anime,
                    related_community_id=related_community_id,
                    action_url=safe_url,
                    deduplication_key=deduplication_key
                )
                return notification
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None

    @classmethod
    def notify_community_like(cls, post, actor):
        """
        Generates notification when an actor likes a post author's content.
        Guarantees:
        - Never notifies author of their own like.
        - Deduplicated per (post, actor).
        - Protects spoiler titles from unauthorized exposure.
        """
        if not post or not actor or post.user_id == actor.id:
            return None

        target_user = post.user
        dedup_key = f"like_post_{post.id}_user_{actor.id}"
        if getattr(post, 'is_spoiler', False):
            truncated_title = "your post [Contains Spoilers]"
        else:
            truncated_title = f"'{post.title[:35]}...'" if len(post.title) > 35 else f"'{post.title}'"

        return cls.create_notification(
            user=target_user,
            notification_type=NotificationType.COMMUNITY_LIKE,
            title="New Like on Your Post",
            message=f"{actor.display_name} liked {truncated_title}.",
            related_community_id=post.id,
            action_url=f"/community?post={post.id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_community_comment(cls, comment, actor):
        """
        Generates notification when an actor comments on a post author's content.
        Guarantees:
        - Never notifies author of their own comment.
        - Deduplicated per comment ID.
        - Conceals spoiler comments in previews.
        """
        if not comment or not actor or not comment.post:
            return None
        if comment.post.user_id == actor.id:
            return None

        target_user = comment.post.user
        dedup_key = f"comment_{comment.id}_actor_{actor.id}"
        if getattr(comment.post, 'is_spoiler', False):
            truncated_title = "your post [Contains Spoilers]"
        else:
            truncated_title = f"'{comment.post.title[:35]}...'" if len(comment.post.title) > 35 else f"'{comment.post.title}'"

        if getattr(comment, 'is_spoiler', False):
            snippet = "[Contains Spoilers]"
        else:
            snippet = f'"{comment.body[:45]}..."' if len(comment.body) > 45 else f'"{comment.body}"'

        return cls.create_notification(
            user=target_user,
            notification_type=NotificationType.COMMUNITY_COMMENT,
            title="New Comment on Your Post",
            message=f"{actor.display_name} commented on {truncated_title}: {snippet}",
            related_community_id=comment.post.id,
            action_url=f"/community?post={comment.post.id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_comment_reply(cls, reply, actor):
        """
        Generates notification when an actor replies to another user's comment.
        Guarantees:
        - Never notifies author of their own reply.
        - Conceals spoiler replies in previews.
        """
        if not reply or not actor or not reply.parent:
            return None
        if reply.parent.user_id == actor.id:
            return None

        target_user = reply.parent.user
        dedup_key = f"reply_{reply.id}_actor_{actor.id}"
        if getattr(reply, 'is_spoiler', False):
            snippet = "[Contains Spoilers]"
        else:
            snippet = f'"{reply.body[:45]}..."' if len(reply.body) > 45 else f'"{reply.body}"'

        return cls.create_notification(
            user=target_user,
            notification_type=NotificationType.COMMUNITY_COMMENT,
            title="New Reply to Your Comment",
            message=f"{actor.display_name} replied to your comment: {snippet}",
            related_community_id=reply.post_id,
            action_url=f"/community?post={reply.post_id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_mention(cls, actor, target_user, post, comment=None):
        """
        Notifies target_user that actor mentioned them (@username) in a community post or comment.
        Guarantees:
        - Never notifies target if actor is the same as target (self-mention suppression).
        - Deduplicated per (context, entity_id, actor_id, target_id).
        - Conceals spoiler post titles / comment bodies in preview.
        """
        if not actor or not target_user or actor.id == target_user.id or not post:
            return None

        context_type = "comment" if comment else "post"
        context_id = comment.id if comment else post.id
        dedup_key = f"mention_{context_type}_{context_id}_actor_{actor.id}_target_{target_user.id}"

        if getattr(post, 'is_spoiler', False):
            post_display = "a post [Contains Spoilers]"
        else:
            post_display = f"'{post.title[:35]}...'" if len(post.title) > 35 else f"'{post.title}'"

        return cls.create_notification(
            user=target_user,
            notification_type=NotificationType.COMMUNITY_COMMENT,
            title=f"Mentioned by {actor.display_name}",
            message=f"{actor.display_name} mentioned you in a {context_type} on {post_display}.",
            related_community_id=post.id,
            action_url=f"/community?post={post.id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_anime_release(cls, user, anime, premiere_info: str = None):
        """
        Notifies user of a verified new anime release.
        """
        if not user or not anime:
            return None

        dedup_key = f"release_anime_{anime.mal_id}_user_{user.id}"
        info_str = f" ({premiere_info})" if premiere_info else ""

        return cls.create_notification(
            user=user,
            notification_type=NotificationType.ANIME_RELEASE,
            title=f"Anime Premiere: {anime.title}",
            message=f"{anime.title}{info_str} is now scheduled or streaming. Check details and franchise order.",
            related_anime=anime,
            action_url=f"/anime/{anime.mal_id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_episode_release(cls, user, anime, episode_number: int):
        """
        Notifies user of a newly verified episode release.
        """
        if not user or not anime or not episode_number:
            return None

        dedup_key = f"ep_release_{episode_number}_anime_{anime.mal_id}_user_{user.id}"

        return cls.create_notification(
            user=user,
            notification_type=NotificationType.EPISODE_RELEASE,
            title=f"Episode {episode_number} Out: {anime.title}",
            message=f"Episode {episode_number} of {anime.title} has aired. Track your viewing progress now.",
            related_anime=anime,
            action_url=f"/anime/{anime.mal_id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_watchlist_reminder(cls, user, anime, custom_message: str = None):
        """
        Sends a watchlist reminder to a user for an anime in their queue.
        """
        if not user or not anime:
            return None

        dedup_key = f"reminder_anime_{anime.mal_id}_user_{user.id}"
        msg = custom_message or f"Continue watching {anime.title}. You have remaining episodes in your backlog."

        return cls.create_notification(
            user=user,
            notification_type=NotificationType.WATCHLIST_REMINDER,
            title=f"Watchlist Reminder: {anime.title}",
            message=msg,
            related_anime=anime,
            action_url=f"/anime/{anime.mal_id}",
            deduplication_key=dedup_key
        )

    @classmethod
    def notify_system(cls, user, title: str, message: str, action_url: str = None, deduplication_key: str = None):
        """
        Sends a platform or system announcement notice.
        """
        return cls.create_notification(
            user=user,
            notification_type=NotificationType.SYSTEM,
            title=title,
            message=message,
            action_url=action_url,
            deduplication_key=deduplication_key
        )
