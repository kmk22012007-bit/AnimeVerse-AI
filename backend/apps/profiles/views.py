from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Avg
from apps.profiles.models import User
from apps.profiles.serializers import ProfileUpdateSerializer
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.community.models import Review
from apps.core.exceptions import ValidationError as CustomValidationError, NotFoundError

class ProfileCurrentView(APIView):
    """
    SRS GET /api/profile/
    SRS PATCH /api/profile/
    """
    def _compute_profile_data(self, user):
        from apps.anime.content_filter import is_excluded_adult_anime

        # Get all entries for user and filter out any excluded adult titles
        all_user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
            .order_by('-updated_at')
        )
        valid_entries = [e for e in all_user_entries if not is_excluded_adult_anime(e.anime)]

        # Stats computed strictly from valid non-excluded anime
        completed_count = sum(1 for e in valid_entries if e.status == WatchStatus.COMPLETED)
        total_episodes_watched = sum(e.watched_episodes or 0 for e in valid_entries)
        rated_entries = [e.rating for e in valid_entries if e.rating is not None]
        if rated_entries:
            average_rating = round(sum(rated_entries) / len(rated_entries), 1)
        else:
            average_rating = "No ratings yet"

        total_anime = len(valid_entries)

        stats = {
            'total_anime': total_anime,
            'completed_count': completed_count,
            'total_episodes_watched': total_episodes_watched,
            'average_rating': average_rating
        }

        # Status counts strictly from valid non-excluded anime
        status_counts = {
            'watching': sum(1 for e in valid_entries if e.status == WatchStatus.WATCHING),
            'completed': completed_count,
            'plan_to_watch': sum(1 for e in valid_entries if e.status == WatchStatus.PLAN_TO_WATCH),
            'on_hold': sum(1 for e in valid_entries if e.status == WatchStatus.ON_HOLD),
            'dropped': sum(1 for e in valid_entries if e.status == WatchStatus.DROPPED),
        }

        # Recently updated anime
        recent_activity = [
            {
                'id': e.id,
                'anime_id': e.anime.mal_id,
                'title': e.anime.title,
                'poster_url': e.anime.poster_url,
                'status': e.status,
                'watched_episodes': e.watched_episodes,
                'total_episodes': e.anime.total_episodes,
                'rating': e.rating,
                'updated_at': e.updated_at.isoformat(),
            }
            for e in valid_entries[:6]
        ]

        # Top rated favorites (ratings >= 8)
        fav_entries = [e for e in valid_entries if (e.rating or 0) >= 8]
        fav_entries.sort(key=lambda x: (x.rating or 0, x.updated_at), reverse=True)
        favorites = [
            {
                'id': f.id,
                'anime_id': f.anime.mal_id,
                'title': f.anime.title,
                'poster_url': f.anime.poster_url,
                'status': f.status,
                'watched_episodes': f.watched_episodes,
                'total_episodes': f.anime.total_episodes,
                'rating': f.rating,
            }
            for f in fav_entries[:6]
        ]

        return {
            'id': user.id,
            'display_name': user.display_name,
            'bio': user.bio,
            'is_public': user.is_public,
            'joined_at': user.created_at.isoformat(),
            'stats': stats,
            'status_counts': status_counts,
            'recent_activity': recent_activity,
            'favorites': favorites,
        }

    def get(self, request):
        data = self._compute_profile_data(request.animeverse_user)
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Profile update validation failed.", details=serializer.errors)

        user = request.animeverse_user
        validated = serializer.validated_data

        if 'display_name' in validated:
            user.display_name = validated['display_name']
        if 'bio' in validated:
            user.bio = validated['bio']
        if 'is_public' in validated:
            user.is_public = validated['is_public']

        user.save()
        data = self._compute_profile_data(user)
        return Response(data, status=status.HTTP_200_OK)

class PublicUserProfileView(APIView):
    """
    SRS GET /api/users/{id}/
    Returns public user profile or 404 if profile is private.
    """
    def get(self, request, id):
        user = User.objects.filter(id=id).first()
        # SRS API-06: 404 when profile is private or not found
        if not user or not user.is_public:
            raise NotFoundError("User not found or profile is private.")

        # Compute public stats
        completed_count = UserAnimeList.objects.filter(user=user, status=WatchStatus.COMPLETED).count()
        total_episodes_watched = (
            UserAnimeList.objects.filter(user=user)
            .aggregate(s=Sum('watched_episodes'))['s'] or 0
        )
        rated_qs = UserAnimeList.objects.filter(user=user, rating__isnull=False)
        avg_val = rated_qs.aggregate(avg=Avg('rating'))['avg'] if rated_qs.exists() else None
        average_rating = round(float(avg_val), 1) if avg_val is not None else "No ratings yet"

        stats = {
            'completed_count': completed_count,
            'total_episodes_watched': total_episodes_watched,
            'average_rating': average_rating
        }

        reviews_qs = Review.objects.filter(user=user).select_related('anime').order_by('-created_at')[:20]
        reviews_data = [
            {
                'id': r.id,
                'anime_mal_id': r.anime_id,
                'author': {
                    'id': user.id,
                    'display_name': user.display_name
                },
                'score': r.score,
                'body': r.body,
                'created_at': r.created_at.isoformat()
            }
            for r in reviews_qs
        ]

        return Response({
            'id': user.id,
            'display_name': user.display_name,
            'bio': user.bio,
            'joined_at': user.created_at.isoformat(),
            'stats': stats,
            'reviews': reviews_data
        }, status=status.HTTP_200_OK)
