from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from apps.community.models import Review, CommunityPost, Comment, PostLike
from apps.community.serializers import ReviewCreateUpdateSerializer, CommunityPostCreateSerializer, CommentCreateSerializer
from apps.anime.models import Anime
from apps.anime.jikan_client import JikanClient
from apps.core.exceptions import (
    ValidationError as CustomValidationError,
    NotFoundError,
    ForbiddenError,
    DuplicateError
)
from apps.core.pagination import AnimeversePagination

class CreateReviewView(APIView):
    """
    SRS POST /api/anime/{mal_id}/reviews/
    Create a review for an anime. Score 1 to 10, Body 20 to 2000 chars.
    """
    def post(self, request, mal_id):
        from apps.anime.content_filter import check_anime_id_is_excluded, BLOCKED_ANIME_MESSAGE
        if check_anime_id_is_excluded(mal_id):
            raise CustomValidationError(message=BLOCKED_ANIME_MESSAGE, details={'anime_id': BLOCKED_ANIME_MESSAGE})

        serializer = ReviewCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError(
                message="Review validation failed.",
                details=serializer.errors
            )

        user = request.animeverse_user
        if Review.objects.filter(user=user, anime_id=mal_id).exists():
            raise DuplicateError("You have already reviewed this anime.", details={'anime_id': 'Review already exists.'})

        # Ensure anime exists in local DB
        anime = Anime.objects.filter(mal_id=mal_id).first()
        if not anime:
            client = JikanClient()
            details = client.get_anime_details(mal_id)
            if not details or not details.get('data'):
                raise NotFoundError(f"Anime with MAL ID {mal_id} not found.")
            card = client.normalize_poster_card(details['data'])
            anime = Anime.objects.create(
                mal_id=mal_id,
                title=card['title'],
                poster_url=card['poster_url'],
                anime_type=card['anime_type'],
                total_episodes=card['total_episodes']
            )

        review = Review.objects.create(
            user=user,
            anime=anime,
            score=serializer.validated_data['score'],
            body=serializer.validated_data['body']
        )

        return Response({
            'id': review.id,
            'anime_mal_id': review.anime_id,
            'author': {
                'id': user.id,
                'display_name': user.display_name,
            },
            'score': review.score,
            'body': review.body,
            'created_at': review.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

class ReviewDetailView(APIView):
    """
    SRS PATCH /api/reviews/{id}/
    SRS DELETE /api/reviews/{id}/
    """
    def patch(self, request, id):
        review = Review.objects.filter(id=id).first()
        if not review:
            raise NotFoundError("Review not found.")

        # SRS Page 27, 30: 403 when review edit targets another user's review
        if review.user_id != request.animeverse_user.id:
            raise ForbiddenError("You do not have permission to edit another user's review.")

        serializer = ReviewCreateUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Review validation failed.", details=serializer.errors)

        if 'score' in serializer.validated_data:
            review.score = serializer.validated_data['score']
        if 'body' in serializer.validated_data:
            review.body = serializer.validated_data['body']
        review.save()

        return Response({
            'id': review.id,
            'anime_mal_id': review.anime_id,
            'author': {
                'id': review.user.id,
                'display_name': review.user.display_name,
            },
            'score': review.score,
            'body': review.body,
            'created_at': review.created_at.isoformat()
        }, status=status.HTTP_200_OK)

    def delete(self, request, id):
        review = Review.objects.filter(id=id).first()
        if not review:
            raise NotFoundError("Review not found.")

        if review.user_id != request.animeverse_user.id:
            raise ForbiddenError("You do not have permission to delete another user's review.")

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CommunityPostListView(APIView):
    """
    SRS GET /api/community/posts/
    SRS POST /api/community/posts/
    """
    def get(self, request):
        user = request.animeverse_user
        posts_qs = (
            CommunityPost.objects.all()
            .select_related('user')
            .annotate(
                like_count_calc=Count('likes', distinct=True),
                comment_count_calc=Count('comments', distinct=True)
            )
            .order_by('-created_at')
        )

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(posts_qs, request)

        # Determine liked_by_me efficiently
        page_post_ids = [p.id for p in page_slice]
        user_liked_ids = set(
            PostLike.objects.filter(post_id__in=page_post_ids, user=user)
            .values_list('post_id', flat=True)
        )

        results = [
            {
                'id': p.id,
                'title': p.title,
                'body': p.body,
                'author': {
                    'id': p.user.id,
                    'display_name': p.user.display_name,
                },
                'like_count': p.like_count_calc,
                'comment_count': p.comment_count_calc,
                'liked_by_me': p.id in user_liked_ids,
                'created_at': p.created_at.isoformat(),
            }
            for p in page_slice
        ]
        return paginator.get_paginated_response(results)

    def post(self, request):
        serializer = CommunityPostCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Post validation failed.", details=serializer.errors)

        user = request.animeverse_user
        post = CommunityPost.objects.create(
            user=user,
            title=serializer.validated_data['title'],
            body=serializer.validated_data['body']
        )

        return Response({
            'id': post.id,
            'title': post.title,
            'body': post.body,
            'author': {
                'id': user.id,
                'display_name': user.display_name,
            },
            'like_count': 0,
            'comment_count': 0,
            'liked_by_me': False,
            'created_at': post.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)

class CommunityPostDetailView(APIView):
    """
    SRS GET /api/community/posts/{id}/
    """
    def get(self, request, id):
        post = CommunityPost.objects.filter(id=id).select_related('user').first()
        if not post:
            raise NotFoundError(f"Post {id} not found.")

        user = request.animeverse_user
        liked_by_me = PostLike.objects.filter(post=post, user=user).exists()
        like_count = PostLike.objects.filter(post=post).count()
        comments_qs = Comment.objects.filter(post=post).select_related('user').order_by('created_at')

        comments_data = [
            {
                'id': c.id,
                'author': {
                    'id': c.user.id,
                    'display_name': c.user.display_name,
                },
                'body': c.body,
                'created_at': c.created_at.isoformat(),
            }
            for c in comments_qs
        ]

        post_data = {
            'id': post.id,
            'title': post.title,
            'body': post.body,
            'author': {
                'id': post.user.id,
                'display_name': post.user.display_name,
            },
            'like_count': like_count,
            'comment_count': len(comments_data),
            'liked_by_me': liked_by_me,
            'created_at': post.created_at.isoformat(),
        }

        return Response({
            'post': post_data,
            'comments': comments_data,
        }, status=status.HTTP_200_OK)

class CommunityPostLikeView(APIView):
    """
    SRS POST /api/community/posts/{id}/like/
    SRS DELETE /api/community/posts/{id}/like/
    """
    def post(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        user = request.animeverse_user
        PostLike.objects.get_or_create(post=post, user=user)
        like_count = PostLike.objects.filter(post=post).count()

        return Response({'liked': True, 'like_count': like_count}, status=status.HTTP_200_OK)

    def delete(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        user = request.animeverse_user
        PostLike.objects.filter(post=post, user=user).delete()
        like_count = PostLike.objects.filter(post=post).count()

        return Response({'liked': False, 'like_count': like_count}, status=status.HTTP_200_OK)

class CommunityPostCommentView(APIView):
    """
    SRS POST /api/community/posts/{id}/comments/
    """
    def post(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Comment validation failed.", details=serializer.errors)

        user = request.animeverse_user
        comment = Comment.objects.create(
            post=post,
            user=user,
            body=serializer.validated_data['body']
        )

        return Response({
            'id': comment.id,
            'author': {
                'id': user.id,
                'display_name': user.display_name,
            },
            'body': comment.body,
            'created_at': comment.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)
