"""Main URL Configuration for AnimeVerse."""
from django.urls import path, include

urlpatterns = [
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/anime/', include('apps.anime.urls')),
    path('api/list/', include('apps.tracking.urls')),
    path('api/', include('apps.community.urls')),
    path('api/ryuk/', include('apps.ryuk.urls')),
    path('api/calendar/', include('apps.calendar.urls')),
    path('api/', include('apps.profiles.urls')),
]
