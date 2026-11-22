from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.profiles.models import User
from apps.anime.models import Anime

class WatchStatus(models.TextChoices):
    WATCHING = 'Watching', 'Watching'
    COMPLETED = 'Completed', 'Completed'
    PLAN_TO_WATCH = 'Plan to Watch', 'Plan to Watch'
    ON_HOLD = 'On Hold', 'On Hold'
    DROPPED = 'Dropped', 'Dropped'

class UserAnimeList(models.Model):
    """
    SRS USER_ANIME_LIST entity.
    Tracks user status, watched episodes, rating, and notes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='watchlist_entries')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, db_column='anime_id', related_name='watchlist_entries')
    status = models.CharField(max_length=20, choices=WatchStatus.choices)
    watched_episodes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    rating = models.SmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)])
    note = models.CharField(max_length=2000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_anime_list'
        constraints = [
            models.UniqueConstraint(fields=['user', 'anime'], name='unique_user_anime_list'),
            models.CheckConstraint(condition=models.Q(watched_episodes__gte=0), name='check_watched_episodes_gte_0'),
            models.CheckConstraint(
                condition=models.Q(rating__isnull=True) | models.Q(rating__gte=1, rating__lte=10),
                name='check_rating_1_to_10'
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'status'], name='user_anime_status_idx'),
            models.Index(fields=['user', '-updated_at'], name='user_anime_updated_idx'),
            models.Index(fields=['anime', 'status'], name='anime_status_idx'),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.display_name} - {self.anime.title} [{self.status}]"

class EpisodeProgress(models.Model):
    """
    SRS EPISODE_PROGRESS entity.
    Maintains 1..N records for watched episodes.
    """
    list_entry = models.ForeignKey(UserAnimeList, on_delete=models.CASCADE, db_column='list_entry_id', related_name='episodes')
    episode_number = models.IntegerField(validators=[MinValueValidator(1)])
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'episode_progress'
        constraints = [
            models.UniqueConstraint(fields=['list_entry', 'episode_number'], name='unique_list_entry_episode_progress'),
            models.CheckConstraint(condition=models.Q(episode_number__gte=1), name='check_episode_number_gte_1'),
        ]
        ordering = ['episode_number']

    def __str__(self):
        return f"Entry {self.list_entry_id} - Ep {self.episode_number}"
