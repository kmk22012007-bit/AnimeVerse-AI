import math
import re
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.community.models import (
    Review,
    CommunityPost,
    Comment,
    PostLike,
    Poll,
    PollOption,
    PollVote,
    CommunityReport,
    ReviewHelpful,
)
from apps.community.serializers import (
    ReviewCreateUpdateSerializer,
    CommunityPostCreateSerializer,
    CommunityPostUpdateSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
    PollVoteSerializer,
    CommunityReportCreateSerializer,
    ModerationReportActionSerializer,
)
from apps.profiles.models import User
from apps.anime.models import Anime
from apps.anime.jikan_client import JikanClient
from apps.anime.content_filter import is_excluded_adult_anime, check_anime_id_is_excluded, BLOCKED_ANIME_MESSAGE
from apps.core.exceptions import (
    ValidationError as CustomValidationError,
    NotFoundError,
    ForbiddenError,
    DuplicateError
)
from apps.core.pagination import AnimeversePagination
from apps.core.throttling import CommunityActionThrottle
from apps.notifications.services import NotificationService


def _dispatch_mention_notifications(text, author, post, comment=None):
    if not text or not author:
        return
    mentions = set(re.findall(r'@([a-zA-Z0-9_\-\.]{2,40})', text))
    if not mentions:
        return

    for mention_name in mentions:
        target_user = User.objects.filter(display_name__iexact=mention_name).first()
        if not target_user:
            continue
        if target_user.id == author.id:
            continue
        try:
            NotificationService.notify_mention(actor=author, target_user=target_user, post=post, comment=comment)
        except Exception:
            pass


def _serialize_poll(poll, user=None):
    if not poll:
        return None

    # Check if options and votes are already in prefetch cache to avoid N+1 query storms
    all_options = getattr(poll, '_prefetched_objects_cache', {}).get('options')
    if all_options is None:
        all_options = list(poll.options.all().order_by('order'))
    else:
        all_options = sorted(all_options, key=lambda o: o.order)

    all_votes = getattr(poll, '_prefetched_objects_cache', {}).get('votes')
    if all_votes is None:
        all_votes = list(poll.votes.all())

    total_votes = len(all_votes)
    votes_by_option = {}
    my_vote_option_id = None
    user_id = getattr(user, 'id', None)

    for v in all_votes:
        votes_by_option[v.option_id] = votes_by_option.get(v.option_id, 0) + 1
        if user_id and v.user_id == user_id:
            my_vote_option_id = v.option_id

    options_data = []
    for opt in all_options:
        cnt = votes_by_option.get(opt.id, 0)
        pct = round((cnt / total_votes * 100), 1) if total_votes > 0 else 0.0
        options_data.append({
            'id': opt.id,
            'text': opt.text,
            'order': opt.order,
            'vote_count': cnt,
            'percentage': pct,
        })

    return {
        'id': poll.id,
        'question': poll.question,
        'expires_at': poll.expires_at.isoformat() if poll.expires_at else None,
        'is_closed': poll.is_closed,
        'total_votes': total_votes,
        'my_vote_option_id': my_vote_option_id,
        'options': options_data,
        'created_at': poll.created_at.isoformat(),
    }


def _serialize_post_card(post, user=None, user_liked_ids=None):
    liked_by_me = (post.id in user_liked_ids) if user_liked_ids is not None else (
        post.likes.filter(user=user).exists() if user else False
    )
    like_count = getattr(post, 'like_count_calc', None)
    if like_count is None:
        like_count = post.likes.count()

    comment_count = getattr(post, 'comment_count_calc', None)
    if comment_count is None:
        comment_count = post.comments.filter(is_hidden=False).count()

    poll_data = None
    if hasattr(post, 'poll') and post.poll:
        poll_data = _serialize_poll(post.poll, user)

    anime_data = None
    if post.anime_id and post.anime:
        anime_data = {
            'id': post.anime.mal_id,
            'title': post.anime.title,
            'poster_url': post.anime.poster_url,
            'anime_type': post.anime.anime_type,
        }

    return {
        'id': post.id,
        'title': post.title,
        'body': post.body,
        'category': post.category,
        'tags': post.tags or [],
        'is_spoiler': post.is_spoiler,
        'author': {
            'id': post.user.id,
            'display_name': post.user.display_name,
            'role': getattr(post.user, 'role', 'user'),
            'is_staff': getattr(post.user, 'is_staff', False),
        },
        'anime': anime_data,
        'poll': poll_data,
        'like_count': like_count,
        'comment_count': comment_count,
        'liked_by_me': liked_by_me,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat() if post.updated_at else None,
    }


class CommunityPostListView(APIView):
    """
    GET /api/community/posts/
    Query parameters:
    - sort: latest, popular, discussed, trending
    - anime_id: filter discussions for specific anime
    - category: filter by category
    - tag: filter by tag
    - filter: 'has_poll', 'is_spoiler'
    - search: keyword search in title/body
    """
    def get(self, request):
        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)

        posts_qs = CommunityPost.objects.all().select_related('user', 'anime', 'poll').prefetch_related(
            'poll__options', 'poll__votes'
        )

        if not is_mod:
            posts_qs = posts_qs.filter(is_hidden=False)

        # Feed / Following filter
        feed = request.query_params.get('feed', '').lower()
        sort_mode = request.query_params.get('sort', 'latest').lower()
        if feed == 'following' or sort_mode == 'following':
            if user and getattr(user, 'id', None):
                following_ids = list(user.following_relations.values_list('followed_id', flat=True))
                posts_qs = posts_qs.filter(user_id__in=following_ids)
            else:
                posts_qs = posts_qs.none()

        # Filters
        anime_id_param = request.query_params.get('anime_id')
        if anime_id_param:
            try:
                anime_mal_id = int(anime_id_param)
                if check_anime_id_is_excluded(anime_mal_id):
                    return Response({'results': [], 'pagination': {'page': 1, 'total_pages': 0, 'total': 0}}, status=status.HTTP_200_OK)
                posts_qs = posts_qs.filter(anime_id=anime_mal_id)
            except ValueError:
                raise CustomValidationError("Invalid anime_id parameter.")

        category = request.query_params.get('category')
        if category and category.lower() != 'all':
            posts_qs = posts_qs.filter(category__iexact=category.strip())

        genre_param = request.query_params.get('genre')
        if genre_param and genre_param.lower() != 'all':
            g = genre_param.strip()
            posts_qs = posts_qs.filter(
                Q(tags__icontains=g) |
                Q(category__iexact=g) |
                Q(title__icontains=g) |
                Q(body__icontains=g)
            )

        tag = request.query_params.get('tag')
        if tag and tag.lower() != 'all':
            # Case-insensitive tag matching in JSON array or icontains
            posts_qs = posts_qs.filter(tags__icontains=tag.strip())

        filter_type = request.query_params.get('filter')
        if filter_type == 'has_poll':
            posts_qs = posts_qs.filter(poll__isnull=False)
        elif filter_type == 'is_spoiler':
            posts_qs = posts_qs.filter(is_spoiler=True)

        search_query = request.query_params.get('search') or request.query_params.get('q')
        if search_query:
            sq = search_query.strip()
            posts_qs = posts_qs.filter(Q(title__icontains=sq) | Q(body__icontains=sq))

        # Annotate counts
        posts_qs = posts_qs.annotate(
            like_count_calc=Count('likes', distinct=True),
            comment_count_calc=Count('comments', filter=Q(comments__is_hidden=False), distinct=True)
        )

        # Sorting
        sort_mode = request.query_params.get('sort', 'latest').lower()
        if sort_mode == 'popular':
            posts_qs = posts_qs.order_by('-like_count_calc', '-comment_count_calc', '-created_at')
        elif sort_mode == 'discussed':
            posts_qs = posts_qs.order_by('-comment_count_calc', '-like_count_calc', '-created_at')
        elif sort_mode == 'trending':
            # Trending formula: (likes * 2 + comments * 3) / ((hours_since_created + 2) ^ 1.5)
            # Fetch all candidate posts, rank by trending score, then paginate
            candidates = list(posts_qs)
            now = timezone.now()

            def trending_score(p):
                hours = max(0.0, (now - p.created_at).total_seconds() / 3600.0)
                engagement = (p.like_count_calc * 2) + (p.comment_count_calc * 3)
                decay = math.pow(hours + 2.0, 1.5)
                return engagement / decay

            candidates.sort(key=trending_score, reverse=True)
            paginator = AnimeversePagination()
            page_slice = paginator.paginate_queryset(candidates, request)

            page_post_ids = [p.id for p in page_slice]
            user_liked_ids = set(
                PostLike.objects.filter(post_id__in=page_post_ids, user=user).values_list('post_id', flat=True)
            )
            results = [_serialize_post_card(p, user, user_liked_ids) for p in page_slice]
            return paginator.get_paginated_response(results)
        else:  # 'latest'
            posts_qs = posts_qs.order_by('-created_at')

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(posts_qs, request)

        page_post_ids = [p.id for p in page_slice]
        user_liked_ids = set(
            PostLike.objects.filter(post_id__in=page_post_ids, user=user).values_list('post_id', flat=True)
        )

        results = [_serialize_post_card(p, user, user_liked_ids) for p in page_slice]
        return paginator.get_paginated_response(results)

    def post(self, request):
        serializer = CommunityPostCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Post validation failed.", details=serializer.errors)

        user = request.animeverse_user
        validated = serializer.validated_data

        anime_instance = None
        anime_id = validated.get('anime_id')
        if anime_id:
            if check_anime_id_is_excluded(anime_id):
                raise CustomValidationError(
                    message=BLOCKED_ANIME_MESSAGE,
                    details={'anime_id': BLOCKED_ANIME_MESSAGE}
                )
            anime_instance = Anime.objects.filter(mal_id=anime_id).first()
            if not anime_instance:
                client = JikanClient()
                details = client.get_anime_details(anime_id)
                if details and details.get('data'):
                    card = client.normalize_poster_card(details['data'])
                    anime_instance = Anime.objects.create(
                        mal_id=anime_id,
                        title=card['title'],
                        poster_url=card['poster_url'],
                        anime_type=card['anime_type'],
                        total_episodes=card['total_episodes']
                    )

        post = CommunityPost.objects.create(
            user=user,
            anime=anime_instance,
            title=validated['title'],
            body=validated['body'],
            category=validated.get('category', 'discussion'),
            tags=validated.get('tags', []),
            is_spoiler=validated.get('is_spoiler', False),
        )

        # Handle optional Poll
        poll_data = validated.get('poll')
        if poll_data:
            expires_days = poll_data.get('expires_days', 7)
            expires_at = timezone.now() + timedelta(days=expires_days)
            poll = Poll.objects.create(
                user=user,
                post=post,
                question=poll_data['question'],
                expires_at=expires_at
            )
            for idx, opt_text in enumerate(poll_data['options']):
                PollOption.objects.create(
                    poll=poll,
                    text=opt_text.strip(),
                    order=idx
                )

        # Dispatch user mentions
        full_text = f"{validated.get('title', '')} {validated.get('body', '')}"
        _dispatch_mention_notifications(full_text, user, post)

        return Response(_serialize_post_card(post, user), status=status.HTTP_201_CREATED)


class CommunityPostDetailView(APIView):
    """
    GET /api/community/posts/{id}/
    PATCH /api/community/posts/{id}/
    DELETE /api/community/posts/{id}/
    """
    def get(self, request, id):
        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)

        post = CommunityPost.objects.filter(id=id).select_related('user', 'anime', 'poll').first()
        if not post or (post.is_hidden and not is_mod):
            raise NotFoundError(f"Post {id} not found.")

        # Serialize threaded comments
        comments_qs = Comment.objects.filter(post=post, is_hidden=False).select_related('user').order_by('created_at')

        # Build threaded hierarchy: root comments and nested replies
        roots = []
        replies_by_parent = {}

        for c in comments_qs:
            c_data = {
                'id': c.id,
                'author': {
                    'id': c.user.id,
                    'display_name': c.user.display_name,
                    'role': getattr(c.user, 'role', 'user'),
                    'is_staff': getattr(c.user, 'is_staff', False),
                },
                'parent_id': c.parent_id,
                'body': c.body,
                'is_spoiler': c.is_spoiler,
                'created_at': c.created_at.isoformat(),
                'updated_at': c.updated_at.isoformat() if c.updated_at else None,
                'replies': [],
            }
            if c.parent_id:
                replies_by_parent.setdefault(c.parent_id, []).append(c_data)
            else:
                roots.append(c_data)

        for root in roots:
            root['replies'] = replies_by_parent.get(root['id'], [])

        post_data = _serialize_post_card(post, user)
        return Response({
            'post': post_data,
            'comments': roots,
        }, status=status.HTTP_200_OK)

    def patch(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)
        if post.user_id != user.id and not is_mod:
            raise ForbiddenError("You do not have permission to edit this post.")

        serializer = CommunityPostUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Post update failed.", details=serializer.errors)

        validated = serializer.validated_data
        if 'title' in validated:
            post.title = validated['title']
        if 'body' in validated:
            post.body = validated['body']
        if 'category' in validated:
            post.category = validated['category']
        if 'tags' in validated:
            post.tags = validated['tags']
        if 'is_spoiler' in validated:
            post.is_spoiler = validated['is_spoiler']

        post.save()
        return Response(_serialize_post_card(post, user), status=status.HTTP_200_OK)

    def delete(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)
        if post.user_id != user.id and not is_mod:
            raise ForbiddenError("You do not have permission to delete this post.")

        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommunityPostLikeView(APIView):
    """
    POST /api/community/posts/{id}/like/
    DELETE /api/community/posts/{id}/like/
    """
    def post(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        user = request.animeverse_user
        _, created = PostLike.objects.get_or_create(post=post, user=user)
        if created:
            try:
                NotificationService.notify_community_like(post=post, actor=user)
            except Exception:
                pass
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
    POST /api/community/posts/{id}/comments/
    Create comment or nested reply.
    """
    def post(self, request, id):
        post = CommunityPost.objects.filter(id=id).first()
        if not post:
            raise NotFoundError("Post not found.")

        serializer = CommentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Comment validation failed.", details=serializer.errors)

        user = request.animeverse_user
        validated = serializer.validated_data

        parent_comment = None
        parent_id = validated.get('parent_id')
        if parent_id:
            parent_comment = Comment.objects.filter(id=parent_id, post=post).first()
            if not parent_comment:
                raise NotFoundError("Parent comment not found on this post.")

        comment = Comment.objects.create(
            post=post,
            user=user,
            parent=parent_comment,
            body=validated['body'],
            is_spoiler=validated.get('is_spoiler', False),
        )

        try:
            # Notify post author
            NotificationService.notify_community_comment(comment=comment, actor=user)
            # If reply, also notify parent comment author
            if parent_comment and parent_comment.user_id != user.id:
                NotificationService.notify_comment_reply(reply=comment, actor=user)
        except Exception:
            pass

        # Dispatch user mentions in comment
        _dispatch_mention_notifications(comment.body, user, post, comment=comment)

        return Response({
            'id': comment.id,
            'author': {
                'id': user.id,
                'display_name': user.display_name,
                'role': getattr(user, 'role', 'user'),
                'is_staff': getattr(user, 'is_staff', False),
            },
            'parent_id': comment.parent_id,
            'body': comment.body,
            'is_spoiler': comment.is_spoiler,
            'created_at': comment.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    """
    PATCH /api/community/comments/{id}/
    DELETE /api/community/comments/{id}/
    """
    def patch(self, request, id):
        comment = Comment.objects.filter(id=id).first()
        if not comment:
            raise NotFoundError("Comment not found.")

        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)
        if comment.user_id != user.id and not is_mod:
            raise ForbiddenError("You do not have permission to edit this comment.")

        serializer = CommentUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Comment update failed.", details=serializer.errors)

        validated = serializer.validated_data
        if 'body' in validated:
            comment.body = validated['body']
        if 'is_spoiler' in validated:
            comment.is_spoiler = validated['is_spoiler']
        comment.save()

        return Response({
            'id': comment.id,
            'author': {
                'id': comment.user.id,
                'display_name': comment.user.display_name,
            },
            'body': comment.body,
            'is_spoiler': comment.is_spoiler,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat(),
        }, status=status.HTTP_200_OK)

    def delete(self, request, id):
        comment = Comment.objects.filter(id=id).first()
        if not comment:
            raise NotFoundError("Comment not found.")

        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)
        if comment.user_id != user.id and not is_mod:
            raise ForbiddenError("You do not have permission to delete this comment.")

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PollVoteView(APIView):
    """
    POST /api/community/polls/{id}/vote/
    Cast a vote on a poll option.
    Enforces strictly 1 vote per user per poll.
    Rejects voting if poll has expired.
    """
    def post(self, request, id):
        poll = Poll.objects.filter(id=id).first()
        if not poll:
            raise NotFoundError("Poll not found.")

        if poll.is_closed:
            raise CustomValidationError("This poll has closed and is no longer accepting votes.")

        serializer = PollVoteSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Vote validation failed.", details=serializer.errors)

        option_id = serializer.validated_data['option_id']
        option = PollOption.objects.filter(id=option_id, poll=poll).first()
        if not option:
            raise NotFoundError("Poll option not found for this poll.")

        user = request.animeverse_user
        if PollVote.objects.filter(poll=poll, user=user).exists():
            raise DuplicateError("You have already voted on this poll.")

        PollVote.objects.create(
            poll=poll,
            option=option,
            user=user
        )

        return Response(_serialize_poll(poll, user), status=status.HTTP_200_OK)


class ReviewDetailView(APIView):
    """
    PATCH /api/reviews/{id}/
    DELETE /api/reviews/{id}/
    """
    def patch(self, request, id):
        review = Review.objects.filter(id=id).first()
        if not review:
            raise NotFoundError("Review not found.")

        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)
        if review.user_id != user.id and not is_mod:
            raise ForbiddenError("You do not have permission to edit another user's review.")

        serializer = ReviewCreateUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Review validation failed.", details=serializer.errors)

        if 'title' in serializer.validated_data:
            review.title = serializer.validated_data['title']
        if 'score' in serializer.validated_data:
            review.score = serializer.validated_data['score']
        if 'body' in serializer.validated_data:
            review.body = serializer.validated_data['body']
        if 'is_spoiler' in serializer.validated_data:
            review.is_spoiler = serializer.validated_data['is_spoiler']
        review.save()

        return Response({
            'id': review.id,
            'anime_mal_id': review.anime_id,
            'author': {
                'id': review.user.id,
                'display_name': review.user.display_name,
            },
            'title': review.title,
            'score': review.score,
            'body': review.body,
            'is_spoiler': review.is_spoiler,
            'helpful_count': review.helpful_count,
            'created_at': review.created_at.isoformat(),
        }, status=status.HTTP_200_OK)

    def delete(self, request, id):
        review = Review.objects.filter(id=id).first()
        if not review:
            raise NotFoundError("Review not found.")

        user = request.animeverse_user
        is_mod = getattr(user, 'is_moderator', False)
        if review.user_id != user.id and not is_mod:
            raise ForbiddenError("You do not have permission to delete another user's review.")

        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReviewHelpfulView(APIView):
    """
    POST /api/reviews/{id}/helpful/
    Toggle helpful feedback on a review.
    """
    def post(self, request, id):
        review = Review.objects.filter(id=id).first()
        if not review:
            raise NotFoundError("Review not found.")

        user = request.animeverse_user
        if review.user_id == user.id:
            raise CustomValidationError("You cannot vote helpful on your own review.")

        existing = ReviewHelpful.objects.filter(review=review, user=user).first()
        if existing:
            existing.delete()
            is_helpful = False
            review.helpful_count = max(0, review.helpful_count - 1)
        else:
            ReviewHelpful.objects.create(review=review, user=user)
            is_helpful = True
            review.helpful_count = review.helpful_count + 1

        review.save(update_fields=['helpful_count'])
        return Response({
            'review_id': review.id,
            'is_helpful': is_helpful,
            'helpful_count': review.helpful_count,
        }, status=status.HTTP_200_OK)


class CommunityReportCreateView(APIView):
    """
    POST /api/community/reports/
    Submit a report for a post, comment, review, or poll.
    Prevents duplicate submissions from the same user for active reports.
    Protects reporter identity.
    """
    throttle_classes = [CommunityActionThrottle]
    def post(self, request):
        serializer = CommunityReportCreateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError("Report validation failed.", details=serializer.errors)

        user = request.animeverse_user
        target_type = serializer.validated_data['target_type']
        target_id = serializer.validated_data['target_id']
        reason = serializer.validated_data['reason']
        explanation = serializer.validated_data.get('explanation', '')

        post = None
        comment = None
        review = None
        poll = None

        if target_type == 'post':
            post = CommunityPost.objects.filter(id=target_id).first()
            if not post:
                raise NotFoundError(f"Post {target_id} not found.")
            existing = CommunityReport.objects.filter(
                reporter=user, target_type='post', post=post, status__in=['pending', 'under_review']
            ).exists()
        elif target_type == 'comment':
            comment = Comment.objects.filter(id=target_id).first()
            if not comment:
                raise NotFoundError(f"Comment {target_id} not found.")
            existing = CommunityReport.objects.filter(
                reporter=user, target_type='comment', comment=comment, status__in=['pending', 'under_review']
            ).exists()
        elif target_type == 'review':
            review = Review.objects.filter(id=target_id).first()
            if not review:
                raise NotFoundError(f"Review {target_id} not found.")
            existing = CommunityReport.objects.filter(
                reporter=user, target_type='review', review=review, status__in=['pending', 'under_review']
            ).exists()
        elif target_type == 'poll':
            poll = Poll.objects.filter(id=target_id).first()
            if not poll:
                raise NotFoundError(f"Poll {target_id} not found.")
            existing = CommunityReport.objects.filter(
                reporter=user, target_type='poll', poll=poll, status__in=['pending', 'under_review']
            ).exists()
        else:
            raise CustomValidationError("Invalid target_type.")

        if existing:
            raise DuplicateError("You have already submitted a pending report for this item.")

        report = CommunityReport.objects.create(
            reporter=user,
            target_type=target_type,
            post=post,
            comment=comment,
            review=review,
            poll=poll,
            reason=reason,
            explanation=explanation,
            status='pending'
        )

        return Response({
            'id': report.id,
            'target_type': report.target_type,
            'status': report.status,
            'message': 'Report submitted successfully for moderation review.',
            'created_at': report.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class ModerationReportListView(APIView):
    """
    GET /api/community/moderation/reports/
    Accessible strictly by authorized staff and moderators.
    Lists reports with filtering by status and target type.
    """
    def get(self, request):
        user = request.animeverse_user
        if not getattr(user, 'is_moderator', False):
            raise ForbiddenError("Only authorized moderators can access moderation reports.")

        reports_qs = CommunityReport.objects.all().select_related(
            'reporter', 'post', 'comment', 'review', 'poll', 'moderated_by'
        )

        status_param = request.query_params.get('status')
        if status_param and status_param.lower() != 'all':
            reports_qs = reports_qs.filter(status=status_param.lower().strip())

        target_param = request.query_params.get('target_type')
        if target_param and target_param.lower() != 'all':
            reports_qs = reports_qs.filter(target_type=target_param.lower().strip())

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(reports_qs, request)

        results = []
        for r in page_slice:
            content_preview = ""
            if r.post:
                content_preview = f"Post: '{r.post.title}' - {r.post.body[:80]}"
            elif r.comment:
                content_preview = f"Comment: {r.comment.body[:100]}"
            elif r.review:
                content_preview = f"Review ({r.review.score}/10): {r.review.body[:100]}"
            elif r.poll:
                content_preview = f"Poll: '{r.poll.question}'"

            results.append({
                'id': r.id,
                'target_type': r.target_type,
                'target_id': r.post_id or r.comment_id or r.review_id or r.poll_id,
                'content_preview': content_preview,
                'reason': r.reason,
                'explanation': r.explanation,
                'status': r.status,
                'action_taken': r.action_taken,
                'moderator_notes': r.moderator_notes,
                'reporter': {
                    'id': r.reporter.id,
                    'display_name': r.reporter.display_name,
                },
                'moderated_by': {
                    'id': r.moderated_by.id,
                    'display_name': r.moderated_by.display_name,
                } if r.moderated_by else None,
                'moderated_at': r.moderated_at.isoformat() if r.moderated_at else None,
                'created_at': r.created_at.isoformat(),
            })

        return paginator.get_paginated_response(results)


class ModerationReportActionView(APIView):
    """
    PATCH /api/community/moderation/reports/{id}/
    Enact a moderation decision on a reported item.
    """
    def patch(self, request, id):
        user = request.animeverse_user
        if not getattr(user, 'is_moderator', False):
            raise ForbiddenError("Only authorized moderators can action moderation reports.")

        report = CommunityReport.objects.filter(id=id).select_related('post', 'comment', 'review', 'poll').first()
        if not report:
            raise NotFoundError("Report not found.")

        serializer = ModerationReportActionSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            raise CustomValidationError("Moderator action validation failed.", details=serializer.errors)

        validated = serializer.validated_data
        status_val = validated.get('status', report.status)
        action_val = validated.get('action_taken', report.action_taken)
        notes = validated.get('moderator_notes', report.moderator_notes)

        # Enforce action on content
        if action_val == 'content_hidden':
            if report.post:
                report.post.is_hidden = True
                report.post.save(update_fields=['is_hidden'])
            if report.comment:
                report.comment.is_hidden = True
                report.comment.save(update_fields=['is_hidden'])
            if report.review:
                report.review.is_hidden = True
                report.review.save(update_fields=['is_hidden'])
        elif action_val == 'content_deleted':
            if report.post:
                report.post.delete()
            elif report.comment:
                report.comment.delete()
            elif report.review:
                report.review.delete()
            elif report.poll:
                report.poll.delete()

        report.status = status_val
        report.action_taken = action_val
        report.moderator_notes = notes
        report.moderated_by = user
        report.moderated_at = timezone.now()
        report.save()

        return Response({
            'id': report.id,
            'status': report.status,
            'action_taken': report.action_taken,
            'moderator_notes': report.moderator_notes,
            'moderated_by': {
                'id': user.id,
                'display_name': user.display_name,
            },
            'moderated_at': report.moderated_at.isoformat(),
        }, status=status.HTTP_200_OK)
