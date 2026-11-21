from django.db import models
from apps.profiles.models import User

class AIConversation(models.Model):
    """
    SRS AI_CONVERSATION entity.
    Maintains a chat session with RYUK.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', related_name='ai_conversations')
    title = models.CharField(max_length=120, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_conversation'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f"Conversation {self.id}"

class AIMessage(models.Model):
    """
    SRS AI_MESSAGE entity.
    Role: 'user' or 'assistant'.
    Content: up to 4000 characters.
    is_fallback: True if AI was unavailable and fallback notice was rendered.
    """
    ROLE_CHOICES = (
        ('user', 'user'),
        ('assistant', 'assistant'),
    )
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, db_column='conversation_id', related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()  # up to 4000 characters
    is_fallback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_message'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:30]}..."
