from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.analytics.services import AnalyticsService

class AnalyticsOverviewView(APIView):
    """
    GET /api/analytics/overview/
    Returns unified personal analytics including core stats, genre distribution,
    rating metrics, timeline activity, and calculated insights.
    """
    def get(self, request):
        user = request.animeverse_user
        service = AnalyticsService()
        data = service.get_overview(user)
        return Response(data, status=status.HTTP_200_OK)

class AnalyticsGenresView(APIView):
    """
    GET /api/analytics/genres/
    Returns user genre distribution, frequency, and preference affinity.
    """
    def get(self, request):
        user = request.animeverse_user
        service = AnalyticsService()
        valid_entries = service.get_valid_user_entries(user)
        data = service.get_genre_analytics(valid_entries)
        return Response(data, status=status.HTTP_200_OK)

class AnalyticsRatingsView(APIView):
    """
    GET /api/analytics/ratings/
    Returns personal rating distribution (1-10) and community score comparisons.
    """
    def get(self, request):
        user = request.animeverse_user
        service = AnalyticsService()
        valid_entries = service.get_valid_user_entries(user)
        data = service.get_rating_analytics(valid_entries)
        return Response(data, status=status.HTTP_200_OK)

class AnalyticsActivityView(APIView):
    """
    GET /api/analytics/activity/
    Returns monthly and yearly watching activity timeline and recent history.
    """
    def get(self, request):
        user = request.animeverse_user
        service = AnalyticsService()
        valid_entries = service.get_valid_user_entries(user)
        data = service.get_activity_analytics(user, valid_entries)
        return Response(data, status=status.HTTP_200_OK)

class AnalyticsWatchlistView(APIView):
    """
    GET /api/analytics/watchlist/
    Returns status distribution and in-progress overview.
    """
    def get(self, request):
        user = request.animeverse_user
        service = AnalyticsService()
        valid_entries = service.get_valid_user_entries(user)
        data = service.get_watchlist_insights(valid_entries)
        return Response(data, status=status.HTTP_200_OK)
