from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Avg, Count
from apps.profiles.models import User, UserFollow
from apps.profiles.serializers import ProfileUpdateSerializer, UserPreferencesSerializer
from apps.profiles.services import TasteProfileService
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.community.models import Review, CommunityPost, Comment
from apps.notifications.services import NotificationService
from apps.notifications.models import NotificationType
from apps.core.pagination import AnimeversePagination
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
            'role': getattr(user, 'role', 'user'),
            'is_staff': getattr(user, 'is_staff', False),
            'is_moderator': getattr(user, 'is_moderator', False),
            'joined_at': user.created_at.isoformat(),
            'stats': stats,
            'status_counts': status_counts,
            'recent_activity': recent_activity,
            'favorites': favorites,
            'follower_count': user.follower_relations.count(),
            'following_count': user.following_relations.count(),
        }

    def get(self, request):
        user = request.animeverse_user
        data = self._compute_profile_data(user)
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Validation failed.", details=serializer.errors)

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


class ProfilePreferencesView(APIView):
    """
    GET /api/profile/preferences/
    Returns explicit user personalization preferences.

    PUT /api/profile/preferences/
    PATCH /api/profile/preferences/
    Updates explicit user preferences with strict validation.
    """
    def get(self, request):
        user = request.animeverse_user
        prefs = user.get_or_create_preferences()
        serializer = UserPreferencesSerializer(prefs)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update_preferences(request, partial=False)

    def patch(self, request):
        return self._update_preferences(request, partial=True)

    def _update_preferences(self, request, partial=False):
        user = request.animeverse_user
        serializer = UserPreferencesSerializer(data=request.data, partial=partial)
        if not serializer.is_valid():
            raise CustomValidationError("Preferences validation failed.", details=serializer.errors)

        prefs = user.get_or_create_preferences()
        validated = serializer.validated_data

        for field in [
            'preferred_genres',
            'preferred_formats',
            'excluded_genres',
            'recommendation_diversity',
            'enable_personalized_recommendations',
            'enable_dashboard_personalization',
            'enable_discovery_personalization',
        ]:
            if field in validated:
                setattr(prefs, field, validated[field])

        prefs.save()
        return Response(UserPreferencesSerializer(prefs).data, status=status.HTTP_200_OK)


class ProfileTasteProfileView(APIView):
    """
    GET /api/profile/taste-profile/
    Returns comprehensive grounded taste profile (inferred signals + explicit preferences).
    """
    def get(self, request):
        user = request.animeverse_user
        profile_data = TasteProfileService.get_taste_profile(user)
        return Response(profile_data, status=status.HTTP_200_OK)


class PublicUserProfileView(APIView):
    """
    SRS GET /api/users/{id}/
    Returns public user profile with community stats, social graph (followers/following),
    favorite genres, recent posts, and verified reviews.
    """
    def get(self, request, id):
        user = User.objects.filter(id=id).first()
        if not user or not user.is_public:
            raise NotFoundError("User profile is private or does not exist.")

        request_user = getattr(request, 'animeverse_user', None)

        from apps.anime.content_filter import is_excluded_adult_anime
        from apps.anime.models import JikanCache
        from collections import Counter

        all_user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
        )
        valid_entries = [e for e in all_user_entries if not is_excluded_adult_anime(e.anime)]

        completed_count = sum(1 for e in valid_entries if e.status == WatchStatus.COMPLETED)
        total_episodes_watched = sum(e.watched_episodes or 0 for e in valid_entries)
        rated_entries = [e.rating for e in valid_entries if e.rating is not None]
        if rated_entries:
            average_rating = round(sum(rated_entries) / len(rated_entries), 1)
        else:
            average_rating = "No ratings yet"

        stats = {
            'completed_count': completed_count,
            'total_episodes_watched': total_episodes_watched,
            'average_rating': average_rating
        }

        # Calculate favorite genres from watch activity
        genre_counter = Counter()
        for entry in valid_entries:
            cached = (
                JikanCache.objects.filter(cache_key=f"anime:{entry.anime_id}:full").first()
                or JikanCache.objects.filter(cache_key=f"details_{entry.anime_id}").first()
            )
            if cached and isinstance(cached.payload, dict):
                d = cached.payload.get('data') or cached.payload
                for g in d.get('genres', []):
                    name = g.get('name') if isinstance(g, dict) else str(g)
                    if name and name.lower() not in ('hentai', 'erotica'):
                        genre_counter[name] += 1
        favorite_genres = [name for name, _ in genre_counter.most_common(5)]

        # Reviews
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

        # Recent Community Posts
        posts_qs = CommunityPost.objects.filter(user=user, is_hidden=False).order_by('-created_at')[:5]
        recent_posts = [
            {
                'id': p.id,
                'title': p.title,
                'category': p.category,
                'created_at': p.created_at.isoformat(),
                'like_count': p.likes.count(),
                'comment_count': p.comments.filter(is_hidden=False).count(),
            }
            for p in posts_qs
        ]

        follower_count = user.follower_relations.count()
        following_count = user.following_relations.count()
        is_following = False
        is_self = False

        if request_user and request_user.id:
            is_self = (request_user.id == user.id)
            if not is_self:
                is_following = UserFollow.objects.filter(
                    follower=request_user,
                    followed=user
                ).exists()

        return Response({
            'id': user.id,
            'display_name': user.display_name,
            'bio': user.bio,
            'joined_at': user.created_at.isoformat(),
            'stats': stats,
            'favorite_genres': favorite_genres,
            'follower_count': follower_count,
            'following_count': following_count,
            'is_following': is_following,
            'is_self': is_self,
            'community_activity': {
                'posts_count': user.posts.filter(is_hidden=False).count(),
                'comments_count': user.comments.filter(is_hidden=False).count(),
                'reviews_count': len(reviews_data),
            },
            'recent_posts': recent_posts,
            'reviews': reviews_data
        }, status=status.HTTP_200_OK)


class UserFollowActionView(APIView):
    """
    POST /api/users/<int:id>/follow/
    DELETE /api/users/<int:id>/follow/
    """
    def post(self, request, id):
        follower = request.animeverse_user
        target = User.objects.filter(id=id).first()
        if not target:
            raise NotFoundError("Target user not found.")
        if follower.id == target.id:
            raise CustomValidationError("You cannot follow yourself.")

        follow_obj, created = UserFollow.objects.get_or_create(
            follower=follower,
            followed=target
        )

        if created:
            try:
                NotificationService.create_notification(
                    user=target,
                    notification_type=NotificationType.SYSTEM,
                    title="New Follower",
                    message=f"{follower.display_name} started following you.",
                    action_url=f"/users/{follower.id}/",
                    deduplication_key=f"follow_{follower.id}_{target.id}"
                )
            except Exception:
                pass

        return Response({
            'is_following': True,
            'follower_count': target.follower_relations.count(),
            'following_count': target.following_relations.count(),
            'message': f"You are now following {target.display_name}."
        }, status=status.HTTP_200_OK)

    def delete(self, request, id):
        follower = request.animeverse_user
        target = User.objects.filter(id=id).first()
        if not target:
            raise NotFoundError("Target user not found.")

        UserFollow.objects.filter(follower=follower, followed=target).delete()

        return Response({
            'is_following': False,
            'follower_count': target.follower_relations.count(),
            'following_count': target.following_relations.count(),
            'message': f"You have unfollowed {target.display_name}."
        }, status=status.HTTP_200_OK)


class UserFollowersListView(APIView):
    """
    GET /api/users/<int:id>/followers/
    Paginated list of followers for user with ID <id>.
    """
    def get(self, request, id):
        target = User.objects.filter(id=id).first()
        if not target:
            raise NotFoundError("Target user not found.")

        current_user = request.animeverse_user
        follows_qs = UserFollow.objects.filter(followed=target).select_related('follower').order_by('-created_at')

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(follows_qs, request)

        follower_user_ids = [f.follower_id for f in page_slice]
        my_following_ids = set()
        if current_user and current_user.id:
            my_following_ids = set(
                UserFollow.objects.filter(
                    follower=current_user,
                    followed_id__in=follower_user_ids
                ).values_list('followed_id', flat=True)
            )

        results = [
            {
                'id': f.follower.id,
                'display_name': f.follower.display_name,
                'bio': f.follower.bio,
                'role': f.follower.role,
                'is_following': f.follower.id in my_following_ids,
                'is_self': bool(current_user and current_user.id == f.follower.id),
                'followed_at': f.created_at.isoformat(),
            }
            for f in page_slice
        ]
        return paginator.get_paginated_response(results)


class UserFollowingListView(APIView):
    """
    GET /api/users/<int:id>/following/
    Paginated list of users that user <id> is following.
    """
    def get(self, request, id):
        target = User.objects.filter(id=id).first()
        if not target:
            raise NotFoundError("Target user not found.")

        current_user = request.animeverse_user
        follows_qs = UserFollow.objects.filter(follower=target).select_related('followed').order_by('-created_at')

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(follows_qs, request)

        followed_user_ids = [f.followed_id for f in page_slice]
        my_following_ids = set()
        if current_user and current_user.id:
            my_following_ids = set(
                UserFollow.objects.filter(
                    follower=current_user,
                    followed_id__in=followed_user_ids
                ).values_list('followed_id', flat=True)
            )

        results = [
            {
                'id': f.followed.id,
                'display_name': f.followed.display_name,
                'bio': f.followed.bio,
                'role': f.followed.role,
                'is_following': f.followed.id in my_following_ids,
                'is_self': bool(current_user and current_user.id == f.followed.id),
                'followed_at': f.created_at.isoformat(),
            }
            for f in page_slice
        ]
        return paginator.get_paginated_response(results)
