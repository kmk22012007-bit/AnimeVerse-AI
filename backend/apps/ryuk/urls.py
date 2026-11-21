from django.urls import path
from apps.ryuk.views import (
    RyukMessageView,
    RyukConversationListView,
    RyukConversationMessagesView,
)

urlpatterns = [
    path('messages/', RyukMessageView.as_view(), name='ryuk-message'),
    path('conversations/', RyukConversationListView.as_view(), name='ryuk-conversations'),
    path('conversations/<int:id>/messages/', RyukConversationMessagesView.as_view(), name='ryuk-conversation-messages'),
]
