from django.urls import path
from apps.community.views import (
    ReviewDetailView,
    CommunityPostListView,
    CommunityPostDetailView,
    CommunityPostLikeView,
    CommunityPostCommentView,
)

urlpatterns = [
    # Review detail update / delete
    path('reviews/<int:id>/', ReviewDetailView.as_view(), name='review-detail'),
    # Community posts
    path('community/posts/', CommunityPostListView.as_view(), name='community-post-list'),
    path('community/posts/<int:id>/', CommunityPostDetailView.as_view(), name='community-post-detail'),
    path('community/posts/<int:id>/like/', CommunityPostLikeView.as_view(), name='community-post-like'),
    path('community/posts/<int:id>/comments/', CommunityPostCommentView.as_view(), name='community-post-comment'),
]
