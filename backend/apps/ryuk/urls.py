from django.urls import path
from apps.ryuk.views import (
    RyukMessageView,
    RyukConversationListView,
    RyukConversationDetailView,
    RyukConversationClearView,
    RyukConversationMessagesView,
    RyukRecommendationView,
)

urlpatterns = [
    path('messages/', RyukMessageView.as_view(), name='ryuk-message'),
    path('recommendations/', RyukRecommendationView.as_view(), name='ryuk-recommendations'),
    path('conversations/', RyukConversationListView.as_view(), name='ryuk-conversations'),
    path('conversations/clear/', RyukConversationClearView.as_view(), name='ryuk-conversation-clear'),
    path('conversations/<int:id>/', RyukConversationDetailView.as_view(), name='ryuk-conversation-detail'),
    path('conversations/<int:id>/messages/', RyukConversationMessagesView.as_view(), name='ryuk-conversation-messages'),
]
