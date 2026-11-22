from django.db import models
from apps.profiles.models import User
from apps.anime.models import Anime

class NotificationType(models.TextChoices):
    ANIME_RELEASE = 'anime_release', 'Anime Release'
    EPISODE_RELEASE = 'episode_release', 'Episode Release'
    COMMUNITY_LIKE = 'community_like', 'Community Like'
    COMMUNITY_COMMENT = 'community_comment', 'Community Comment'
    WATCHLIST_REMINDER = 'watchlist_reminder', 'Watchlist Reminder'
    SYSTEM = 'system', 'System Notice'

class Notification(models.Model):
    """
    SRS NOTIFICATION entity.
    Scoped to an individual authenticated/session user.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    related_anime = models.ForeignKey(
        Anime,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='anime_id',
        related_name='notifications'
    )
    related_community_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    action_url = models.CharField(max_length=500, null=True, blank=True)
    deduplication_key = models.CharField(max_length=160, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at'], name='notif_usr_read_idx'),
            models.Index(fields=['user', 'deduplication_key'], name='notif_usr_dedup_idx'),
        ]

    def __str__(self):
        return f"Notification({self.user.display_name}, {self.notification_type}, read={self.is_read})"

class NotificationPreference(models.Model):
    """
    User notification preferences controlling which events trigger alerts.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        related_name='notification_preference'
    )
    anime_releases = models.BooleanField(default=True)
    episode_releases = models.BooleanField(default=True)
    community_likes = models.BooleanField(default=True)
    community_comments = models.BooleanField(default=True)
    watchlist_reminders = models.BooleanField(default=True)
    system_notices = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preference'

    @classmethod
    def get_for_user(cls, user):
        pref, _ = cls.objects.get_or_create(user=user)
        return pref

    def __str__(self):
        return f"NotificationPreference for {self.user.display_name}"
