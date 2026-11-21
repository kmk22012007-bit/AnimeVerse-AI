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
    auth_user_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.display_name} ({self.session_key[:8]}...)"
