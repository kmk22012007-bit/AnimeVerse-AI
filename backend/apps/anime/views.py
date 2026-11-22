from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.anime.jikan_client import JikanClient
from apps.anime.serializers import AnimeSearchQuerySerializer, AnimeBrowseQuerySerializer
from apps.anime.content_filter import (
    is_excluded_adult_anime,
    filter_anime_list,
    check_anime_id_is_excluded,
    BLOCKED_ANIME_MESSAGE,
)
from apps.tracking.models import UserAnimeList
from apps.tracking.services import TrackingService
from apps.community.models import Review
from apps.core.exceptions import ValidationError as CustomValidationError, NotFoundError
from apps.core.pagination import AnimeversePagination

class AnimeSearchView(APIView):
    """
    SRS GET /api/anime/search/
    Search anime by title with 2 to 100 chars, paginated.
    """
    def get(self, request):
        serializer = AnimeSearchQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            raise CustomValidationError(
                message=str(serializer.errors.get('q', ['Validation failed.'])[0]),
                details=serializer.errors
            )

        q = serializer.validated_data['q']
        page = serializer.validated_data.get('page', 1)

        client = JikanClient()
        res = client.search_anime(q=q, page=page)
        if not res or 'data' not in res:
            return Response({'results': [], 'pagination': {'page': page, 'total_pages': 1, 'total': 0}})

        results = [client.normalize_poster_card(item) for item in res['data'] if not is_excluded_adult_anime(item)]
        results = filter_anime_list(results)

        # Rank exact matches before related matches
        q_lower = q.lower().strip()
        def score_relevance(item):
            title = (item.get('title') or '').lower()
            title_en = (item.get('title_english') or '').lower()

            base_score = 0
            # 1. Exact match on title or english title
            if title == q_lower or title_en == q_lower:
                base_score = 1000
            # 2. Title begins with exact query
            elif title.startswith(q_lower) or title_en.startswith(q_lower):
                base_score = 500
                # Shorter title (fewer subtitle words) is closer to the original query
                word_count = len((title_en or title).split())
                base_score += max(0, 50 - word_count)
            # 3. Whole word or prefix match
            else:
                words = (
                    title.replace(':', ' ').replace('-', ' ').split() +
                    title_en.replace(':', ' ').replace('-', ' ').split()
                )
                if any(w == q_lower for w in words):
                    base_score = 300
                elif any(w.startswith(q_lower) for w in words):
                    base_score = 200
                elif q_lower in title or q_lower in title_en:
                    base_score = 100

            return base_score + (item.get('score') or 0)

        results.sort(key=score_relevance, reverse=True)

        # Apply franchise grouping so related entries collapse into primary franchise cards
        from apps.anime.franchise_service import FranchiseService
        results = FranchiseService.group_results(results)

        pagination = res.get('pagination', {})
        last_page = pagination.get('last_visible_page', 1)
        total_items = pagination.get('items', {}).get('total', len(results))

        return Response({
            'results': results,
            'pagination': {
                'page': page,
                'total_pages': last_page,
                'total': total_items
            }
        })

class AnimeTrendingView(APIView):
    """
    SRS GET /api/anime/trending/
    """
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        client = JikanClient()
        res = client.get_trending_anime(page=page)
        if not res or 'data' not in res:
            return Response({'results': [], 'pagination': {'page': page, 'total_pages': 1, 'total': 0}})

        results = [client.normalize_poster_card(item) for item in res['data'] if not is_excluded_adult_anime(item)]
        results = filter_anime_list(results)
        from apps.anime.franchise_service import FranchiseService
        results = FranchiseService.group_results(results)
        pagination = res.get('pagination', {})
        return Response({
            'results': results,
            'pagination': {
                'page': page,
                'total_pages': pagination.get('last_visible_page', 1),
                'total': pagination.get('items', {}).get('total', len(results))
            }
        })

class DiscoveryFiltersView(APIView):
    """
    GET /api/anime/discovery/filters/
    Returns discovery filter choices including verified audio languages,
    supported genres, formats, airing statuses, and sort modes.
    """
    def get(self, request):
        from apps.anime.discovery_service import DiscoveryService
        filters_data = DiscoveryService.get_available_filters()
        return Response(filters_data, status=status.HTTP_200_OK)

class AnimeBrowseView(APIView):
    """
    SRS GET /api/anime/browse/
    Advanced anime discovery with multi-genre, format, score range,
    year range, verified audio language, and status filtering.
    """
    def get(self, request):
        serializer = AnimeBrowseQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            raise CustomValidationError(
                message="Filter parameters are invalid.",
                details=serializer.errors
            )

        from apps.anime.discovery_service import DiscoveryService
        data = DiscoveryService.browse(serializer.validated_data, user=request.animeverse_user)
        return Response(data, status=status.HTTP_200_OK)

class AnimeDetailView(APIView):
    """
    SRS GET /api/anime/{mal_id}/
    Full details including user watchlist entry if present.
    """
    def get(self, request, mal_id):
        client = JikanClient()
        details_res = client.get_anime_details(mal_id)
        if not details_res or not details_res.get('data'):
            raise NotFoundError(f"Anime with MAL ID {mal_id} not found.", details={'mal_id': 'Not found.'})

        data = details_res['data']
        # Global content safety check: exclude Hentai / explicit adult content
        if is_excluded_adult_anime(data):
            return Response({
                'error': BLOCKED_ANIME_MESSAGE,
                'is_blocked': True,
                'detail': BLOCKED_ANIME_MESSAGE
            }, status=status.HTTP_404_NOT_FOUND)

        characters_res = client.get_anime_characters(mal_id)
        characters_data = characters_res.get('data', []) if characters_res else []

        user_entry = None
        if hasattr(request, 'animeverse_user'):
            entry = UserAnimeList.objects.filter(user=request.animeverse_user, anime_id=mal_id).first()
            if entry:
                user_entry = TrackingService.serialize_entry(entry)

        normalized = client.normalize_anime_details(
            data,
            characters_data=characters_data,
            user_entry=user_entry
        )
        return Response(normalized, status=200)

class AnimeEpisodesView(APIView):
    """
    SRS GET /api/anime/{mal_id}/episodes/?page=1
    Returns verified episode list with actual episode descriptions.
    """
    def get(self, request, mal_id):
        page = int(request.query_params.get('page', 1))
        client = JikanClient()

        # Retrieve main anime synopsis to prevent duplication in episode description
        details_res = client.get_anime_details(mal_id)
        if details_res and details_res.get('data') and is_excluded_adult_anime(details_res['data']):
            return Response({
                'error': BLOCKED_ANIME_MESSAGE,
                'is_blocked': True,
                'detail': BLOCKED_ANIME_MESSAGE,
                'episodes': []
            }, status=status.HTTP_404_NOT_FOUND)

        main_synopsis = details_res.get('data', {}).get('synopsis') if details_res else None

        ep_res = client.get_anime_episodes(mal_id, page=page)
        if not ep_res or 'data' not in ep_res:
            return Response({
                'mal_id': mal_id,
                'episodes': [],
                'pagination': {'page': page, 'total_pages': 1, 'total': 0},
                'metadata_source': client._primary_provider_name()
            })

        raw_list = ep_res.get('data', [])
        source = ep_res.get('metadata_source') or client._primary_provider_name()

        episodes = [
            client.normalize_episode(ep, main_synopsis=main_synopsis, metadata_source=source)
            for ep in raw_list
        ]

        pagination = ep_res.get('pagination', {})
        return Response({
            'mal_id': mal_id,
            'episodes': episodes,
            'pagination': {
                'page': page,
                'total_pages': pagination.get('last_visible_page', 1),
                'total': pagination.get('items', {}).get('total', len(episodes))
            },
            'metadata_source': source
        })

class AnimeRelatedView(APIView):
    """
    SRS GET /api/anime/{mal_id}/related/
    """
    def get(self, request, mal_id):
        client = JikanClient()
        details_res = client.get_anime_details(mal_id)
        if not details_res or not details_res.get('data'):
            return Response({'results': []})

        if is_excluded_adult_anime(details_res['data']):
            return Response({'results': [], 'error': BLOCKED_ANIME_MESSAGE, 'is_blocked': True}, status=status.HTTP_404_NOT_FOUND)

        raw_relations = details_res['data'].get('relations', [])
        results = []
        for rel in raw_relations:
            for entry in rel.get('entry', []):
                if entry.get('type') == 'anime' and entry.get('mal_id'):
                    if is_excluded_adult_anime(entry) or check_anime_id_is_excluded(entry['mal_id'], client):
                        continue
                    images = entry.get('images', {})
                    poster_url = None
                    if isinstance(images, dict):
                        poster_url = images.get('jpg', {}).get('image_url')

                    results.append({
                        'mal_id': entry['mal_id'],
                        'title': entry.get('name') or "Untitled",
                        'poster_url': poster_url,
                        'score': None,
                        'anime_type': 'anime',
                        'total_episodes': None,
                        'metadata_source': details_res['data'].get('metadata_source', 'jikan'),
                        'is_stale': False
                    })

        return Response({'results': results})

class AnimeReviewsView(APIView):
    """
    SRS GET /api/anime/{mal_id}/reviews/
    SRS POST /api/anime/{mal_id}/reviews/
    Supports sorting by recent, helpful, highest_rating, lowest_rating.
    Includes spoiler flags and helpful feedback counts.
    """
    def get(self, request, mal_id):
        if check_anime_id_is_excluded(mal_id):
            return Response({'results': [], 'error': BLOCKED_ANIME_MESSAGE, 'is_blocked': True}, status=status.HTTP_404_NOT_FOUND)

        from apps.community.models import Review, ReviewHelpful

        user = getattr(request, 'animeverse_user', None)
        is_mod = getattr(user, 'is_moderator', False) if user else False

        reviews_qs = Review.objects.filter(anime_id=mal_id).select_related('user')
        if not is_mod:
            reviews_qs = reviews_qs.filter(is_hidden=False)

        sort_param = request.query_params.get('sort', 'recent').lower()
        if sort_param == 'helpful':
            reviews_qs = reviews_qs.order_by('-helpful_count', '-created_at')
        elif sort_param == 'highest_rating':
            reviews_qs = reviews_qs.order_by('-score', '-created_at')
        elif sort_param == 'lowest_rating':
            reviews_qs = reviews_qs.order_by('score', '-created_at')
        else:  # 'recent'
            reviews_qs = reviews_qs.order_by('-created_at')

        paginator = AnimeversePagination()
        page_slice = paginator.paginate_queryset(reviews_qs, request)

        page_review_ids = [r.id for r in page_slice]
        helpful_review_ids = set()
        if user and page_review_ids:
            helpful_review_ids = set(
                ReviewHelpful.objects.filter(review_id__in=page_review_ids, user=user).values_list('review_id', flat=True)
            )

        serialized = [
            {
                'id': r.id,
                'anime_mal_id': r.anime_id,
                'author': {
                    'id': r.user.id,
                    'display_name': r.user.display_name,
                },
                'title': r.title or '',
                'score': r.score,
                'body': r.body,
                'is_spoiler': r.is_spoiler,
                'helpful_count': r.helpful_count,
                'marked_helpful_by_me': r.id in helpful_review_ids,
                'created_at': r.created_at.isoformat(),
            }
            for r in page_slice
        ]
        return paginator.get_paginated_response(serialized)

    def post(self, request, mal_id):
        from apps.community.serializers import ReviewCreateUpdateSerializer
        from apps.community.models import Review
        from apps.anime.models import Anime
        from apps.core.exceptions import DuplicateError, NotFoundError, ValidationError as CustomValidationError

        if check_anime_id_is_excluded(mal_id):
            return Response({'error': BLOCKED_ANIME_MESSAGE, 'is_blocked': True}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            raise CustomValidationError(
                message="Review validation failed.",
                details=serializer.errors
            )

        user = request.animeverse_user
        if Review.objects.filter(user=user, anime_id=mal_id).exists():
            raise DuplicateError("You have already reviewed this anime.", details={'anime_id': 'Review already exists.'})

        anime = Anime.objects.filter(mal_id=mal_id).first()
        if not anime:
            client = JikanClient()
            details = client.get_anime_details(mal_id)
            if not details or not details.get('data'):
                raise NotFoundError(f"Anime with MAL ID {mal_id} not found.")
            if is_excluded_adult_anime(details['data']):
                return Response({'error': BLOCKED_ANIME_MESSAGE, 'is_blocked': True}, status=status.HTTP_400_BAD_REQUEST)
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
            title=serializer.validated_data.get('title', ''),
            score=serializer.validated_data['score'],
            body=serializer.validated_data['body'],
            is_spoiler=serializer.validated_data.get('is_spoiler', False),
        )

        return Response({
            'id': review.id,
            'anime_mal_id': review.anime_id,
            'author': {
                'id': user.id,
                'display_name': user.display_name,
            },
            'title': review.title,
            'score': review.score,
            'body': review.body,
            'is_spoiler': review.is_spoiler,
            'helpful_count': 0,
            'marked_helpful_by_me': False,
            'created_at': review.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)

class AnimeWatchOptionsView(APIView):
    """
    GET /api/anime/{mal_id}/watch-options/?country=IN
    Returns legal streaming availability categorized into:
    - subscription
    - free
    - free_with_ads
    - rent
    - buy
    Default country is India (IN).
    """
    def get(self, request, mal_id):
        if check_anime_id_is_excluded(mal_id):
            return Response({
                'error': BLOCKED_ANIME_MESSAGE,
                'is_blocked': True,
                'mal_id': mal_id,
                'total_options': 0,
                'results_count': 0,
                'categories': {'subscription': [], 'free': [], 'free_with_ads': [], 'rent': [], 'buy': []}
            }, status=status.HTTP_404_NOT_FOUND)

        from apps.anime.watch_service import WatchService
        country = request.query_params.get('country', 'IN')
        if not country or len(country.strip()) < 2:
            country = 'IN'
        country = country.strip()[:2].upper()

        service = WatchService()
        audio = request.query_params.get('audio')
        sub = request.query_params.get('sub')
        data = service.get_watch_options(mal_id=mal_id, country=country, audio=audio, sub=sub)
        return Response(data, status=200)

class AnimeTrailersView(APIView):
    """
    GET /api/anime/{mal_id}/trailers/
    Returns official promotional YouTube trailers and video records.
    """
    def get(self, request, mal_id):
        if check_anime_id_is_excluded(mal_id):
            return Response({
                'error': BLOCKED_ANIME_MESSAGE,
                'is_blocked': True,
                'mal_id': mal_id,
                'trailers': [],
                'count': 0
            }, status=status.HTTP_404_NOT_FOUND)

        from apps.anime.watch_service import WatchService
        service = WatchService()
        data = service.get_trailers(mal_id=mal_id)
        return Response(data, status=200)

class WatchmodeStatusView(APIView):
    """
    GET /api/anime/watchmode-status/
    Returns evaluation and configuration status of Watchmode API.
    """
    def get(self, request):
        from apps.anime.watchmode_client import WatchmodeClient
        client = WatchmodeClient()
        return Response(client.evaluate_service(), status=200)


class FranchiseDetailView(APIView):
    """
    GET /api/anime/franchises/{id_or_slug}/
    Retrieves full franchise information with categorized entries
    (Main Series, Sequels/Prequels, Movies, OVAs/Specials, Spin-offs).
    """
    def get(self, request, id_or_slug):
        from apps.anime.models import Franchise
        from apps.anime.franchise_service import FranchiseService
        FranchiseService.seed_known_franchises()

        franchise = None
        if str(id_or_slug).isdigit():
            franchise = Franchise.objects.filter(id=int(id_or_slug)).first()
        if not franchise:
            franchise = Franchise.objects.filter(slug=id_or_slug).first()

        if not franchise:
            raise NotFoundError(f"Franchise '{id_or_slug}' not found.")

        data = FranchiseService.serialize_franchise(franchise)
        return Response(data, status=status.HTTP_200_OK)


class AnimeFranchiseView(APIView):
    """
    GET /api/anime/{mal_id}/franchise/
    Returns franchise information and related entries for an exact anime.
    """
    def get(self, request, mal_id):
        if check_anime_id_is_excluded(mal_id):
            return Response({'error': BLOCKED_ANIME_MESSAGE, 'is_blocked': True}, status=status.HTTP_404_NOT_FOUND)

        from apps.anime.franchise_service import FranchiseService
        franchise = FranchiseService.get_franchise_for_anime(mal_id)
        if not franchise:
            return Response({'franchise': None})

        data = FranchiseService.serialize_franchise(franchise)
        return Response({'franchise': data}, status=status.HTTP_200_OK)

