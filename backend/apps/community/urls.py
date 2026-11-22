from django.urls import path
from apps.community.views import (
    ReviewDetailView,
    ReviewHelpfulView,
    CommunityPostListView,
    CommunityPostDetailView,
    CommunityPostLikeView,
    CommunityPostCommentView,
    CommentDetailView,
    PollVoteView,
    CommunityReportCreateView,
    ModerationReportListView,
    ModerationReportActionView,
)

urlpatterns = [
    # Review detail update / delete & helpful vote
    path('reviews/<int:id>/', ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:id>/helpful/', ReviewHelpfulView.as_view(), name='review-helpful'),

    # Community posts
    path('community/posts/', CommunityPostListView.as_view(), name='community-post-list'),
    path('community/posts/<int:id>/', CommunityPostDetailView.as_view(), name='community-post-detail'),
    path('community/posts/<int:id>/like/', CommunityPostLikeView.as_view(), name='community-post-like'),
    path('community/posts/<int:id>/comments/', CommunityPostCommentView.as_view(), name='community-post-comment'),
    path('community/comments/<int:id>/', CommentDetailView.as_view(), name='comment-detail'),

    # Poll voting
    path('community/polls/<int:id>/vote/', PollVoteView.as_view(), name='poll-vote'),

    # User reporting
    path('community/reports/', CommunityReportCreateView.as_view(), name='community-report-create'),

    # Moderation dashboard endpoints (Staff / Moderator only)
    path('community/moderation/reports/', ModerationReportListView.as_view(), name='moderation-report-list'),
    path('community/moderation/reports/<int:id>/', ModerationReportActionView.as_view(), name='moderation-report-action'),
]
