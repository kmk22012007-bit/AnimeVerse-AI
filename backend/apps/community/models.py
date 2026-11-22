from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.profiles.models import User
from apps.anime.models import Anime


class Review(models.Model):
    """
    SRS REVIEW entity.
    Score: 1 to 10. Body: 20 to 2000 chars. Title: optional up to 150 chars.
    Unique per (user, anime).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='reviews')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, db_column='anime_id', related_name='reviews')
    title = models.CharField(max_length=150, blank=True, default='')
    score = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    body = models.TextField()  # 20 to 2000 characters
    is_spoiler = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review'
        constraints = [
            models.UniqueConstraint(fields=['user', 'anime'], name='unique_user_anime_review'),
            models.CheckConstraint(condition=models.Q(score__gte=1, score__lte=10), name='check_review_score_1_to_10'),
        ]
        indexes = [
            models.Index(fields=['anime', 'is_hidden', '-created_at'], name='rev_anime_hidden_created_idx'),
            models.Index(fields=['user', '-created_at'], name='rev_user_created_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.user.display_name} for MAL {self.anime_id} ({self.score}/10)"


class ReviewHelpful(models.Model):
    """
    Tracks helpful votes on reviews. One helpful vote per user per review.
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_helpful'
        constraints = [
            models.UniqueConstraint(fields=['review', 'user'], name='unique_review_user_helpful'),
        ]

    def __str__(self):
        return f"Helpful vote by {self.user.display_name} on review {self.review_id}"


class CommunityPost(models.Model):
    """
    SRS COMMUNITY_POST entity.
    Title: up to 120 chars. Body: up to 2000 chars.
    Category, tags, spoiler flag, and optional anime link.
    """
    CATEGORY_CHOICES = [
        ('discussion', 'Discussion'),
        ('theory', 'Theory'),
        ('review', 'Review'),
        ('question', 'Question'),
        ('news', 'News'),
        ('fan_art', 'Fan Art'),
        ('recommendation', 'Recommendation'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='posts')
    anime = models.ForeignKey(
        Anime,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column='anime_id',
        related_name='community_posts'
    )
    title = models.CharField(max_length=120)
    body = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='discussion')
    tags = models.JSONField(default=list, blank=True)
    is_spoiler = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'community_post'
        indexes = [
            models.Index(fields=['is_hidden', '-created_at'], name='comm_post_hidden_created_idx'),
            models.Index(fields=['category', '-created_at'], name='comm_post_cat_created_idx'),
            models.Index(fields=['anime', '-created_at'], name='comm_post_anime_created_idx'),
            models.Index(fields=['user', '-created_at'], name='comm_post_user_created_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Comment(models.Model):
    """
    SRS COMMENT entity.
    Body: up to 500 chars. Supports nested replies via parent.
    """
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, db_column='post_id', related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    body = models.CharField(max_length=500)
    is_spoiler = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comment'
        indexes = [
            models.Index(fields=['post', 'is_hidden', 'created_at'], name='comm_comment_post_idx'),
            models.Index(fields=['parent', 'created_at'], name='comm_comment_parent_idx'),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.display_name} on post {self.post_id}"


class PostLike(models.Model):
    """
    SRS LIKE entity.
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


class Poll(models.Model):
    """
    Community Poll entity.
    Can be linked 1:1 to a CommunityPost or stand alone.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='polls')
    post = models.OneToOneField(
        CommunityPost,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='poll'
    )
    question = models.CharField(max_length=255)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'poll'
        ordering = ['-created_at']

    @property
    def is_closed(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def __str__(self):
        return self.question


class PollOption(models.Model):
    """
    Answer option for a community poll.
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=150)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'poll_option'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.poll_id} - {self.text}"


class PollVote(models.Model):
    """
    Single vote record for a community poll.
    Enforces strictly 1 vote per user per poll via unique constraint.
    """
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poll_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'poll_vote'
        constraints = [
            models.UniqueConstraint(fields=['poll', 'user'], name='unique_poll_user_vote'),
        ]

    def __str__(self):
        return f"Vote by {self.user.display_name} on poll {self.poll_id}"


class CommunityReport(models.Model):
    """
    Reporting and moderation system.
    Users report posts, comments, reviews, or polls.
    Only authorized moderators can access and act on reports.
    """
    TARGET_TYPE_CHOICES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('review', 'Review'),
        ('poll', 'Poll'),
    ]

    REASON_CHOICES = [
        ('inappropriate', 'Inappropriate or sexually graphic content'),
        ('spam', 'Spam, advertising, or bot activity'),
        ('harassment', 'Harassment, hate speech, or abuse'),
        ('unmarked_spoilers', 'Spoilers without warning'),
        ('other', 'Other policy violation'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    ACTION_CHOICES = [
        ('none', 'No Action'),
        ('content_hidden', 'Content Hidden'),
        ('content_deleted', 'Content Deleted'),
        ('warning_issued', 'Warning Issued'),
        ('dismissed', 'Report Dismissed'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    post = models.ForeignKey(CommunityPost, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    comment = models.ForeignKey(Comment, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    review = models.ForeignKey(Review, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    poll = models.ForeignKey(Poll, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    explanation = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    moderator_notes = models.TextField(blank=True, default='')
    moderated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='moderated_reports'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.CharField(max_length=30, choices=ACTION_CHOICES, default='none')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'community_report'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} [{self.target_type}] ({self.status}) by {self.reporter.display_name}"
