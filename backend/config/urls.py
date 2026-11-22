"""Main URL Configuration for AnimeVerse."""
from django.urls import path, include
from apps.core.views import HealthCheckView

urlpatterns = [
    # System Health Check
    path('api/health/', HealthCheckView.as_view(), name='api-health'),

    # Feature Subsystems
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/anime/', include('apps.anime.urls')),
    path('api/list/', include('apps.tracking.urls')),
    path('api/', include('apps.community.urls')),
    path('api/ryuk/', include('apps.ryuk.urls')),
    path('api/calendar/', include('apps.calendar.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/', include('apps.profiles.urls')),
]
