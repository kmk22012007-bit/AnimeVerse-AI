import logging
import math
from typing import List, Dict, Any, Set
from apps.anime.models import Anime, JikanCache, StreamingLanguageTrack, VerificationStatus
from apps.anime.jikan_client import JikanClient
from apps.anime.content_filter import is_excluded_adult_anime, filter_anime_list
from apps.anime.franchise_service import FranchiseService

logger = logging.getLogger(__name__)

GENRE_NAME_TO_ID = {
    'action': 1,
    'adventure': 2,
    'cars': 3,
    'comedy': 4,
    'dementia': 5,
    'demons': 6,
    'mystery': 7,
    'drama': 8,
    'ecchi': 9,
    'fantasy': 10,
    'game': 11,
    'historical': 13,
    'horror': 14,
    'kids': 15,
    'magic': 16,
    'martial arts': 17,
    'mecha': 18,
    'music': 19,
    'parody': 20,
    'samurai': 21,
    'romance': 22,
    'school': 23,
    'sci-fi': 24,
    'shoujo': 25,
    'shounen': 27,
    'space': 29,
    'sports': 30,
    'super power': 31,
    'vampire': 32,
    'slice of life': 36,
    'supernatural': 37,
    'military': 38,
    'police': 39,
    'psychological': 40,
    'suspense': 41,
    'award winning': 46,
    'gourmet': 47,
    'workplace': 48,
}

EXCLUDED_ADULT_GENRES = {'12', '49', 'hentai', 'erotica'}

class DiscoveryService:
    """
    Advanced discovery and search engine for anime titles.
    Orchestrates upstream metadata, verified local language records,
    content safety filters, franchise collapsing, and combined criteria.
    """

    @classmethod
    def get_available_filters(cls) -> Dict[str, Any]:
        """
        Returns metadata for discovery filters including verified audio languages,
        supported genres, formats, and available sort modes. Cached for 30 minutes.
        """
        from django.core.cache import cache
        cache_key = 'discovery_available_filters_v1'
        cached_filters = cache.get(cache_key)
        if cached_filters is not None:
            return cached_filters

        verified_tracks = StreamingLanguageTrack.objects.filter(
            verification_status__in=[
                VerificationStatus.LICENSOR_CONFIRMED,
                VerificationStatus.PROVIDER_REPORTED
            ]
        ).exclude(audio_language__isnull=True).exclude(audio_language__exact='')

        verified_languages = sorted(list(set(verified_tracks.values_list('audio_language', flat=True))))

        genres = [
            'Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror',
            'Mystery', 'Psychological', 'Romance', 'Sci-Fi', 'Shounen',
            'Slice of Life', 'Sports', 'Supernatural', 'Suspense', 'Award Winning'
        ]

        formats = [
            {'label': 'TV Series', 'value': 'tv'},
            {'label': 'Movie', 'value': 'movie'},
            {'label': 'OVA', 'value': 'ova'},
            {'label': 'ONA', 'value': 'ona'},
            {'label': 'Special', 'value': 'special'},
        ]

        statuses = [
            {'label': 'Currently Airing', 'value': 'airing'},
            {'label': 'Finished Airing', 'value': 'complete'},
            {'label': 'Upcoming', 'value': 'upcoming'},
        ]

        sort_options = [
            {'key': '-score', 'label': 'Highest Score'},
            {'key': 'score', 'label': 'Lowest Score'},
            {'key': '-start_date', 'label': 'Recently Released'},
            {'key': 'start_date', 'label': 'Oldest Releases'},
            {'key': '-episodes', 'label': 'Most Episodes'},
            {'key': 'title', 'label': 'Title (A-Z)'},
            {'key': 'relevance', 'label': 'Relevance'},
        ]

        result = {
            'verified_languages': verified_languages,
            'genres': genres,
            'formats': formats,
            'statuses': statuses,
            'sort_options': sort_options,
        }
        cache.set(cache_key, result, timeout=1800)
        return result

    @classmethod
    def parse_genre_list(cls, val) -> List[str]:
        if not val:
            return []
        if isinstance(val, list):
            return [str(v).strip().lower() for v in val if str(v).strip()]
        return [g.strip().lower() for g in str(val).split(',') if g.strip()]

    @classmethod
    def extract_year(cls, item: Dict[str, Any]) -> int:
        if item.get('year'):
            try:
                return int(item['year'])
            except (ValueError, TypeError):
                pass
        aired = item.get('aired') or {}
        from_str = aired.get('from')
        if from_str:
            try:
                return int(str(from_str)[:4])
            except (ValueError, TypeError):
                pass
        return None

    @classmethod
    def _normalize_candidate(cls, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preserves all metadata fields needed for discovery filtering, sorting,
        display, and adult content safety validation.
        """
        if not item or not isinstance(item, dict):
            return None

        images = item.get('images', {})
        poster_url = None
        if isinstance(images, dict):
            jpg = images.get('jpg', {})
            poster_url = jpg.get('image_url') or jpg.get('large_image_url')
        poster_url = poster_url or item.get('poster_url')

        raw_genres = item.get('genres') or []
        genres_list = [g.get('name') if isinstance(g, dict) else str(g) for g in raw_genres]

        anime_type = item.get('type') or item.get('anime_type')
        episodes = item.get('episodes') or item.get('total_episodes')
        year = item.get('year') or cls.extract_year(item)

        return {
            'mal_id': item.get('mal_id'),
            'title': item.get('title') or item.get('title_english') or "Untitled",
            'title_english': item.get('title_english'),
            'title_japanese': item.get('title_japanese'),
            'poster_url': poster_url,
            'score': item.get('score'),
            'anime_type': anime_type,
            'type': anime_type,
            'total_episodes': episodes,
            'episodes': episodes,
            'year': year,
            'aired': item.get('aired') or {},
            'status': item.get('status'),
            'genres': genres_list,
            'rating': item.get('rating'),
            'explicit_genres': item.get('explicit_genres') or [],
            'metadata_source': item.get('metadata_source', 'tenrai'),
            'fetched_at': item.get('fetched_at'),
            'is_cached': item.get('is_cached', False),
            'is_stale': item.get('is_stale', False),
        }

    @classmethod
    def calculate_relevance(cls, item: Dict[str, Any], query: str) -> float:
        if not query:
            return float(item.get('score') or 0)
        q = query.lower().strip()
        title = (item.get('title') or '').lower()
        title_en = (item.get('title_english') or '').lower()
        title_ja = (item.get('title_japanese') or '').lower()

        base = 0
        if title == q or title_en == q:
            base = 1000
        elif title.startswith(q) or title_en.startswith(q):
            base = 500
            word_count = len((title_en or title).split())
            base += max(0, 50 - word_count)
        elif q in title or q in title_en or q in title_ja:
            base = 200
        else:
            words = (
                title.replace(':', ' ').replace('-', ' ').split() +
                title_en.replace(':', ' ').replace('-', ' ').split()
            )
            if any(w == q for w in words):
                base = 300
            elif any(w.startswith(q) for w in words):
                base = 150

        return base + float(item.get('score') or 0)

    @classmethod
    def browse(cls, params: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Executes unified advanced discovery query with full filter combinations,
        with optional user taste profile personalization.
        """
        q = params.get('q', '').strip() if params.get('q') else ''
        page = int(params.get('page') or 1)
        page_size = int(params.get('page_size') or 20)
        personalized = bool(params.get('personalized', False))
        hide_tracked = bool(params.get('hide_tracked', False))

        # 1. Check for Adult Genres in query
        raw_genres = params.get('genres') or params.get('genre') or ''
        include_genres = cls.parse_genre_list(raw_genres)
        exclude_genres = cls.parse_genre_list(params.get('exclude_genres', ''))

        if any(g in EXCLUDED_ADULT_GENRES for g in include_genres):
            return {
                'results': [],
                'pagination': {'page': page, 'total_pages': 1, 'total': 0}
            }

        client = JikanClient()
        audio_language = params.get('audio_language', '').strip()
        country = params.get('country', '').strip()
        verified_mal_ids: Set[int] = set()

        # 2. Verified Language Filtering
        if audio_language:
            track_qs = StreamingLanguageTrack.objects.filter(
                audio_language__iexact=audio_language,
                verification_status__in=[
                    VerificationStatus.LICENSOR_CONFIRMED,
                    VerificationStatus.PROVIDER_REPORTED
                ]
            )
            if country:
                track_qs = track_qs.filter(country__iexact=country)

            verified_mal_ids = set(track_qs.values_list('anime_id', flat=True))
            if not verified_mal_ids:
                return {
                    'results': [],
                    'pagination': {'page': page, 'total_pages': 1, 'total': 0}
                }

        # 3. Retrieve Candidate Items
        seen_ids = set()
        candidates = []

        # A. Local Catalog (Database & Cache) Candidates
        local_anime_qs = Anime.objects.all()
        if audio_language:
            local_anime_qs = local_anime_qs.filter(mal_id__in=verified_mal_ids)

        for a in local_anime_qs:
            cached = (
                JikanCache.objects.filter(cache_key=f"details_{a.mal_id}").first()
                or JikanCache.objects.filter(cache_key=f"anime:{a.mal_id}:full").first()
            )
            if cached and isinstance(cached.payload, dict):
                data = cached.payload.get('data') or cached.payload
                card = cls._normalize_candidate(data)
                if card:
                    candidates.append(card)
                    seen_ids.add(card['mal_id'])
            else:
                card = {
                    'mal_id': a.mal_id,
                    'title': a.title,
                    'title_english': None,
                    'title_japanese': None,
                    'poster_url': a.poster_url,
                    'type': a.anime_type,
                    'anime_type': a.anime_type,
                    'total_episodes': a.total_episodes,
                    'episodes': a.total_episodes,
                    'score': None,
                    'year': None,
                    'genres': [],
                }
                candidates.append(card)
                seen_ids.add(a.mal_id)

        # B. Upstream Candidates (when not restricted to verified audio language)
        if not audio_language:
            try:
                upstream_res = None
                if q:
                    upstream_res = client.search_anime(q=q, page=page)
                else:
                    fmt = params.get('format') or params.get('type')
                    status_val = params.get('status')
                    min_score = params.get('min_score')

                    genre_id_str = None
                    if include_genres:
                        first_g = include_genres[0]
                        genre_id = GENRE_NAME_TO_ID.get(first_g) or (int(first_g) if first_g.isdigit() else None)
                        if genre_id:
                            genre_id_str = str(genre_id)

                    upstream_res = client.browse_anime(
                        genre=genre_id_str,
                        min_score=min_score,
                        anime_type=fmt,
                        status=status_val,
                        page=page
                    )

                if upstream_res and isinstance(upstream_res, dict) and 'data' in upstream_res:
                    for item in upstream_res['data']:
                        card = cls._normalize_candidate(item)
                        if card and card['mal_id'] not in seen_ids:
                            candidates.append(card)
                            seen_ids.add(card['mal_id'])
            except Exception as e:
                logger.warning(f"Upstream browse query failed ({e}); falling back cleanly to local catalog.")

        # 4. Strict Content Safety Filter
        candidates = [item for item in candidates if not is_excluded_adult_anime(item)]
        candidates = filter_anime_list(candidates)

        # 5. Apply All Combined Filters
        filtered = []
        fmt_filter = (params.get('format') or params.get('type') or '').lower().strip()
        status_filter = (params.get('status') or '').lower().strip()
        year_filter = params.get('year')
        year_from = params.get('year_from')
        year_to = params.get('year_to')
        min_score_val = params.get('min_score')
        max_score_val = params.get('max_score')
        min_episodes_val = params.get('min_episodes')
        max_episodes_val = params.get('max_episodes')

        for item in candidates:
            # Title partial match if q provided
            if q:
                t = (item.get('title') or '').lower()
                t_en = (item.get('title_english') or '').lower()
                t_ja = (item.get('title_japanese') or '').lower()
                q_low = q.lower()
                if q_low not in t and q_low not in t_en and q_low not in t_ja:
                    continue

            # Verified language constraint
            if audio_language and item.get('mal_id') not in verified_mal_ids:
                continue

            # Genre inclusion
            item_genres = [str(g).lower() for g in (item.get('genres') or [])]
            if include_genres:
                # Must match all included genres
                if not all(any(ig in g for g in item_genres) for ig in include_genres):
                    continue

            # Genre exclusion
            if exclude_genres:
                if any(any(eg in g for g in item_genres) for eg in exclude_genres):
                    continue

            # Format match
            if fmt_filter:
                item_fmt = (item.get('type') or item.get('anime_type') or '').lower()
                if fmt_filter != item_fmt:
                    continue

            # Airing Status match
            if status_filter:
                item_status = (item.get('status') or '').lower()
                if status_filter == 'airing' and 'airing' not in item_status:
                    continue
                elif status_filter == 'complete' and 'finished' not in item_status and 'complete' not in item_status:
                    continue
                elif status_filter == 'upcoming' and 'not yet' not in item_status and 'upcoming' not in item_status:
                    continue

            # Year filters
            item_year = cls.extract_year(item)
            if year_filter is not None:
                if item_year is None or item_year != int(year_filter):
                    continue
            if year_from is not None:
                if item_year is None or item_year < int(year_from):
                    continue
            if year_to is not None:
                if item_year is None or item_year > int(year_to):
                    continue

            # Score filters: Missing scores are strictly excluded if min_score/max_score is set
            score = item.get('score')
            if min_score_val is not None:
                if score is None or float(score) < float(min_score_val):
                    continue
            if max_score_val is not None:
                if score is None or float(score) > float(max_score_val):
                    continue

            # Episode count filters
            episodes = item.get('episodes') or item.get('total_episodes')
            if min_episodes_val is not None:
                if episodes is None or int(episodes) < int(min_episodes_val):
                    continue
            if max_episodes_val is not None:
                if episodes is None or int(episodes) > int(max_episodes_val):
                    continue

            filtered.append(item)

        # Check user personalization preferences
        effective_genres = []
        user_excluded = []
        tracked_ids = set()
        user_is_personalized = False

        if user:
            try:
                from apps.profiles.services import TasteProfileService
                from apps.tracking.models import UserAnimeList, WatchStatus
                prefs = user.get_or_create_preferences()
                user_excluded = [g.lower() for g in (prefs.excluded_genres or [])]
                if hide_tracked:
                    tracked_ids = set(
                        UserAnimeList.objects.filter(
                            user=user,
                            status__in=[WatchStatus.COMPLETED, WatchStatus.WATCHING]
                        ).values_list('anime__mal_id', flat=True)
                    )
                if personalized and prefs.enable_discovery_personalization:
                    user_is_personalized = True
                    taste = TasteProfileService.get_taste_profile(user)
                    effective_genres = [g.lower() for g in taste.get('effective_genres', [])]
            except Exception as e:
                logger.warning(f"Discovery personalization resolution failed: {e}")
                user_is_personalized = False

        # Apply user exclusions & tracked filter if personalized
        final_items = []
        for item in filtered:
            mal_id = item.get('mal_id')
            if tracked_ids and mal_id in tracked_ids:
                continue

            item_genres_lower = [str(g).lower() for g in (item.get('genres') or [])]
            if user_excluded and any(eg in item_genres_lower for eg in user_excluded):
                continue

            if user_is_personalized:
                shared = [g for g in effective_genres if g in item_genres_lower]
                bonus = len(shared) * 200 + (float(item.get('score') or 0) * 10)
                item['personalization_bonus'] = bonus
                item['is_personalized'] = True
                if shared:
                    item['personalization_reason'] = f"Matches your affinity for {', '.join([g.title() for g in shared[:2]])}"
                elif item.get('score') and float(item.get('score')) >= 8.0:
                    item['personalization_reason'] = f"Acclaimed {item.get('score')}/10 community rating"
                else:
                    item['personalization_reason'] = "Curated Discovery match"
            else:
                item['is_personalized'] = False
                item['personalization_reason'] = None

            final_items.append(item)

        # 6. Sorting
        sort_mode = (params.get('sort') or '').lower().strip()
        if user_is_personalized and (not sort_mode or sort_mode in ['relevance', 'personalized']):
            final_items.sort(key=lambda x: (x.get('personalization_bonus', 0), float(x.get('score') or 0), -(x.get('mal_id') or 0)), reverse=True)
        elif sort_mode in ['-score', 'score_desc', 'highest_score']:
            final_items.sort(key=lambda x: (x.get('score') is not None, float(x.get('score') or 0), -(x.get('mal_id') or 0)), reverse=True)
        elif sort_mode in ['score', 'score_asc', 'lowest_score']:
            final_items.sort(key=lambda x: (x.get('score') is not None, float(x.get('score') or 999), x.get('mal_id') or 0))
        elif sort_mode in ['-start_date', 'newest']:
            final_items.sort(key=lambda x: (cls.extract_year(x) or 0, -(x.get('mal_id') or 0)), reverse=True)
        elif sort_mode in ['start_date', 'oldest']:
            final_items.sort(key=lambda x: (cls.extract_year(x) or 9999, x.get('mal_id') or 0))
        elif sort_mode in ['-episodes', 'episodes_desc']:
            final_items.sort(key=lambda x: (int(x.get('episodes') or 0), -(x.get('mal_id') or 0)), reverse=True)
        elif sort_mode in ['title', 'title_asc']:
            final_items.sort(key=lambda x: (x.get('title') or '').lower())
        elif sort_mode == 'relevance' or q:
            final_items.sort(key=lambda x: cls.calculate_relevance(x, q), reverse=True)

        # 7. Franchise Grouping
        final_items = FranchiseService.group_results(final_items)

        # 8. Pagination Slicing
        total = len(final_items)
        total_pages = max(1, math.ceil(total / page_size))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        results_slice = final_items[start_idx:end_idx]

        return {
            'results': results_slice,
            'is_personalized': user_is_personalized,
            'pagination': {
                'page': page,
                'total_pages': total_pages,
                'total': total
            }
        }
