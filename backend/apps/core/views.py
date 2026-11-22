from django.db import connection
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class HealthCheckView(APIView):
    """
    Production health-check endpoint for load balancers, container orchestrators,
    and uptime monitoring services (e.g., Render, Railway, UptimeRobot).
    GET /api/health/
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        db_status = "healthy"
        status_code = status.HTTP_200_OK

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        payload = {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_status,
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "environment": "production" if not settings.DEBUG else "development",
        }
        return Response(payload, status=status_code)
