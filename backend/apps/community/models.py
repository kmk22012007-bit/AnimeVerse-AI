from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.profiles.models import User
from apps.anime.models import Anime

class Review(models.Model):
    """
    SRS REVIEW entity.
    Score: 1 to 10. Body: 20 to 2000 chars.
    Unique per (user, anime).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='reviews')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, db_column='anime_id', related_name='reviews')
    score = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    body = models.TextField()  # 20 to 2000 characters
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review'
        constraints = [
            models.UniqueConstraint(fields=['user', 'anime'], name='unique_user_anime_review'),
            models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=10), name='check_review_score_1_to_10'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.display_name} for MAL {self.anime_id} ({self.score}/10)"

class CommunityPost(models.Model):
    """
    SRS COMMUNITY_POST entity.
    Title: up to 120 chars. Body: up to 2000 chars.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='posts')
    title = models.CharField(max_length=120)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_post'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Comment(models.Model):
    """
    SRS COMMENT entity.
    Body: up to 500 chars.
    """
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, db_column='post_id', related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='comments')
    body = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.display_name} on {self.post_id}"

class PostLike(models.Model):
    """
    SRS LIKE entity.
    Django model: PostLike, Table name: like.
    Unique per (post, user).
    """
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, db_column='post_id', related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'like'
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_user_like'),
        ]

    def __str__(self):
        return f"Like by {self.user.display_name} on post {self.post_id}"
