from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import NotificationSerializer, NotificationPreferenceSerializer
from apps.core.pagination import AnimeversePagination
from apps.core.exceptions import NotFoundError, ValidationError as CustomValidationError

class NotificationListView(APIView):
    """
    GET /api/notifications/
    Returns paginated notifications for the authenticated user with optional filtering by read status and type.
    """
    def get(self, request):
        user = request.animeverse_user
        qs = Notification.objects.filter(user=user).select_related('related_anime')

        is_read_param = request.query_params.get('is_read')
        if is_read_param is not None:
            if is_read_param.lower() in ['true', '1']:
                qs = qs.filter(is_read=True)
            elif is_read_param.lower() in ['false', '0']:
                qs = qs.filter(is_read=False)

        type_param = request.query_params.get('type')
        if type_param:
            qs = qs.filter(notification_type=type_param)

        paginator = AnimeversePagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class NotificationUnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    Returns total unread notification count for badge rendering.
    """
    def get(self, request):
        user = request.animeverse_user
        count = Notification.objects.filter(user=user, is_read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)

class NotificationMarkReadView(APIView):
    """
    PATCH /api/notifications/<int:id>/read/
    Marks a single notification as read. Enforces user isolation to prevent IDOR.
    """
    def patch(self, request, id):
        user = request.animeverse_user
        notification = Notification.objects.filter(id=id, user=user).select_related('related_anime').first()
        if not notification:
            raise NotFoundError("Notification not found.")

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationMarkAllReadView(APIView):
    """
    POST /api/notifications/mark-all-read/
    Marks all notifications for the authenticated user as read.
    """
    def post(self, request):
        user = request.animeverse_user
        updated = Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        return Response({
            'marked_count': updated,
            'unread_count': 0
        }, status=status.HTTP_200_OK)

class NotificationDetailView(APIView):
    """
    DELETE /api/notifications/<int:id>/
    Deletes a specific notification. Enforces user isolation to prevent IDOR.
    """
    def delete(self, request, id):
        user = request.animeverse_user
        notification = Notification.objects.filter(id=id, user=user).first()
        if not notification:
            raise NotFoundError("Notification not found.")

        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationClearReadView(APIView):
    """
    DELETE /api/notifications/clear-read/
    Purges all read notifications for the authenticated user.
    """
    def delete(self, request):
        user = request.animeverse_user
        deleted_count, _ = Notification.objects.filter(user=user, is_read=True).delete()
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        return Response({
            'deleted_count': deleted_count,
            'unread_count': unread_count
        }, status=status.HTTP_200_OK)

class NotificationPreferencesView(APIView):
    """
    GET /api/notifications/preferences/
    PATCH /api/notifications/preferences/
    Retrieves or updates user notification preference switches.
    """
    def get(self, request):
        user = request.animeverse_user
        pref = NotificationPreference.get_for_user(user)
        serializer = NotificationPreferenceSerializer(pref)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.animeverse_user
        pref = NotificationPreference.get_for_user(user)
        serializer = NotificationPreferenceSerializer(pref, data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Invalid notification preferences data.", details=serializer.errors)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
