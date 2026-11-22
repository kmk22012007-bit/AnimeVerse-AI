from django.urls import path
from apps.analytics.views import (
    AnalyticsOverviewView,
    AnalyticsGenresView,
    AnalyticsRatingsView,
    AnalyticsActivityView,
    AnalyticsWatchlistView,
)

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('genres/', AnalyticsGenresView.as_view(), name='analytics-genres'),
    path('ratings/', AnalyticsRatingsView.as_view(), name='analytics-ratings'),
    path('activity/', AnalyticsActivityView.as_view(), name='analytics-activity'),
    path('watchlist/', AnalyticsWatchlistView.as_view(), name='analytics-watchlist'),
]
