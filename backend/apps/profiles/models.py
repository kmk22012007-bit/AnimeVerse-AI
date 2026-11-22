from django.db import models

class User(models.Model):
    """
    SRS USER entity.
    Represents anonymous demo visitor or future authenticated user.
    """
    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    display_name = models.CharField(max_length=40, default="Guest")
    bio = models.CharField(max_length=300, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    role = models.CharField(max_length=20, default="user")  # 'user', 'moderator', 'admin'
    is_staff = models.BooleanField(default=False)
    auth_user_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'
        ordering = ['-created_at']

    @property
    def is_moderator(self):
        return self.is_staff or self.role in ('moderator', 'admin')

    def get_or_create_preferences(self):
        prefs, _ = UserPreferences.objects.get_or_create(user=self)
        return prefs

    def __str__(self):
        return f"{self.display_name} ({self.session_key[:8]}...)"


class UserPreferences(models.Model):
    """
    User personalization and recommendation preference controls.
    Maintains explicit preferences and personalization feature toggles.
    """
    DIVERSITY_CHOICES = [
        ('focused', 'Focused'),
        ('balanced', 'Balanced'),
        ('exploratory', 'Exploratory'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_genres = models.JSONField(default=list, blank=True)
    preferred_formats = models.JSONField(default=list, blank=True)
    excluded_genres = models.JSONField(default=list, blank=True)
    recommendation_diversity = models.CharField(
        max_length=20,
        default='balanced',
        choices=DIVERSITY_CHOICES
    )
    enable_personalized_recommendations = models.BooleanField(default=True)
    enable_dashboard_personalization = models.BooleanField(default=True)
    enable_discovery_personalization = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'

    def __str__(self):
        return f"Preferences for {self.user.display_name}"


class UserFollow(models.Model):
    """
    Represents a directional user follow relationship: follower -> followed.
    Enforces uniqueness, prevents self-following, and indexes for fast feed lookups.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_relations',
        db_column='follower_id'
    )
    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_relations',
        db_column='followed_id'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_follow'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'followed'],
                name='unique_user_follow_pair'
            ),
        ]

    def __str__(self):
        return f"{self.follower.display_name} follows {self.followed.display_name}"
