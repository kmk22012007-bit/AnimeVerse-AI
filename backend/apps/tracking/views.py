from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.tracking.services import TrackingService
from apps.tracking.serializers import AddWatchlistSerializer, UpdateWatchlistSerializer, UpdateProgressSerializer
from apps.core.pagination import AnimeversePagination
from apps.core.exceptions import ValidationError as CustomValidationError

class WatchlistView(APIView):
    """
    SRS GET /api/list/
    SRS POST /api/list/
    """
    def get(self, request):
        user = request.animeverse_user
        qs = UserAnimeList.objects.filter(user=user).select_related('anime')

        status_param = request.query_params.get('status')
        if status_param and status_param in WatchStatus.values:
            qs = qs.filter(status=status_param)

        sort_param = request.query_params.get('sort', 'updated')
        if sort_param == 'title':
            qs = qs.order_by('anime__title')
        elif sort_param == 'rating':
            qs = qs.order_by('-rating', '-updated_at')
        else:
            qs = qs.order_by('-updated_at')

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(qs, request)
        from apps.anime.content_filter import is_excluded_adult_anime
        serialized = [
            TrackingService.serialize_entry(e)
            for e in page_slice
            if not is_excluded_adult_anime(e.anime)
        ]
        return paginator.get_paginated_response(serialized)

    def post(self, request):
        serializer = AddWatchlistSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError(
                message="Validation failed for watchlist addition.",
                details=serializer.errors
            )

        mal_id = serializer.validated_data['mal_id']
        from apps.anime.content_filter import check_anime_id_is_excluded, BLOCKED_ANIME_MESSAGE
        if check_anime_id_is_excluded(mal_id):
            raise CustomValidationError(
                message=BLOCKED_ANIME_MESSAGE,
                details={'mal_id': BLOCKED_ANIME_MESSAGE}
            )

        watch_status = serializer.validated_data.get('status', WatchStatus.PLAN_TO_WATCH)

        service = TrackingService()
        entry = service.add_to_watchlist(user=request.animeverse_user, mal_id=mal_id, status=watch_status)
        return Response(TrackingService.serialize_entry(entry), status=status.HTTP_201_CREATED)

class WatchlistDetailView(APIView):
    """
    SRS PATCH /api/list/{id}/
    SRS DELETE /api/list/{id}/
    """
    def patch(self, request, id):
        serializer = UpdateWatchlistSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError(
                message="Validation failed for watchlist update.",
                details=serializer.errors
            )

        service = TrackingService()
        entry = service.update_entry(
            user=request.animeverse_user,
            entry_id=id,
            status=serializer.validated_data.get('status'),
            rating=serializer.validated_data.get('rating'),
            note=serializer.validated_data.get('note')
        )
        return Response(TrackingService.serialize_entry(entry), status=status.HTTP_200_OK)

    def delete(self, request, id):
        service = TrackingService()
        service.remove_from_watchlist(user=request.animeverse_user, entry_id=id)
        return Response(status=status.HTTP_204_NO_CONTENT)

class WatchlistProgressView(APIView):
    """
    SRS PUT /api/list/{id}/progress/
    """
    def put(self, request, id):
        serializer = UpdateProgressSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError(
                message="Validation failed for episode progress update.",
                details=serializer.errors
            )

        service = TrackingService()
        entry = service.update_progress(
            user=request.animeverse_user,
            entry_id=id,
            watched_episodes=serializer.validated_data['watched_episodes']
        )
        return Response(TrackingService.serialize_entry(entry), status=status.HTTP_200_OK)

class WatchlistCompleteView(APIView):
    """
    SRS POST /api/list/{id}/complete/
    """
    def post(self, request, id):
        service = TrackingService()
        entry = service.mark_completed(user=request.animeverse_user, entry_id=id)
        return Response(TrackingService.serialize_entry(entry), status=status.HTTP_200_OK)
