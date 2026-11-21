from django.urls import path
from apps.tracking.views import (
    WatchlistView,
    WatchlistDetailView,
    WatchlistProgressView,
    WatchlistCompleteView,
)

urlpatterns = [
    path('', WatchlistView.as_view(), name='watchlist-list-create'),
    path('<int:id>/', WatchlistDetailView.as_view(), name='watchlist-detail'),
    path('<int:id>/progress/', WatchlistProgressView.as_view(), name='watchlist-progress'),
    path('<int:id>/complete/', WatchlistCompleteView.as_view(), name='watchlist-complete'),
]
