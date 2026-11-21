from rest_framework.views import APIView
from rest_framework.response import Response
from apps.dashboard.services import DashboardService

class DashboardView(APIView):
    """
    SRS GET /api/dashboard/
    Returns welcome info, currently watching items, calculated stats,
    5 recent items, and trending strip.
    """
    def get(self, request):
        service = DashboardService()
        data = service.get_dashboard_data(request.animeverse_user)
        return Response(data, status=200)
