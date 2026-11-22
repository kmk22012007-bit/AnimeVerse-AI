from django.urls import path
from apps.anime.views import (
    AnimeSearchView,
    AnimeTrendingView,
    AnimeBrowseView,
    DiscoveryFiltersView,
    AnimeDetailView,
    AnimeEpisodesView,
    AnimeRelatedView,
    AnimeReviewsView,
    AnimeWatchOptionsView,
    AnimeTrailersView,
    WatchmodeStatusView,
    FranchiseDetailView,
    AnimeFranchiseView,
)

urlpatterns = [
    path('search/', AnimeSearchView.as_view(), name='anime-search'),
    path('trending/', AnimeTrendingView.as_view(), name='anime-trending'),
    path('discovery/filters/', DiscoveryFiltersView.as_view(), name='discovery-filters'),
    path('browse/', AnimeBrowseView.as_view(), name='anime-browse'),
    path('watchmode-status/', WatchmodeStatusView.as_view(), name='watchmode-status'),
    path('franchises/<str:id_or_slug>/', FranchiseDetailView.as_view(), name='franchise-detail'),
    path('<int:mal_id>/', AnimeDetailView.as_view(), name='anime-detail'),
    path('<int:mal_id>/franchise/', AnimeFranchiseView.as_view(), name='anime-franchise'),
    path('<int:mal_id>/episodes/', AnimeEpisodesView.as_view(), name='anime-episodes'),
    path('<int:mal_id>/related/', AnimeRelatedView.as_view(), name='anime-related'),
    path('<int:mal_id>/reviews/', AnimeReviewsView.as_view(), name='anime-reviews'),
    path('<int:mal_id>/watch-options/', AnimeWatchOptionsView.as_view(), name='anime-watch-options'),
    path('<int:mal_id>/trailers/', AnimeTrailersView.as_view(), name='anime-trailers'),
]
