import time
import threading
import logging
from collections import deque
from datetime import timedelta
import requests
from django.conf import settings
from django.utils import timezone
from apps.anime.models import JikanCache
from apps.core.exceptions import ServiceUnavailableError, RateLimitError

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    SRS NFR-18:
    Limits Jikan calls to no more than 3 requests per second and 60 per minute.
    """
    def __init__(self, max_per_second=3, max_per_minute=60):
        self.max_per_second = max_per_second
        self.max_per_minute = max_per_minute
        self.second_window = deque()
        self.minute_window = deque()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()

            # Evict timestamps older than 1 second
            while self.second_window and now - self.second_window[0] >= 1.0:
                self.second_window.popleft()

            # Evict timestamps older than 60 seconds
            while self.minute_window and now - self.minute_window[0] >= 60.0:
                self.minute_window.popleft()

            # Check limits
            if len(self.second_window) >= self.max_per_second:
                sleep_time = 1.0 - (now - self.second_window[0]) + 0.05
                if sleep_time > 0:
                    time.sleep(sleep_time)
                now = time.time()

            if len(self.minute_window) >= self.max_per_minute:
                sleep_time = 60.0 - (now - self.minute_window[0]) + 0.05
                if sleep_time > 0:
                    time.sleep(sleep_time)
                now = time.time()

            self.second_window.append(now)
            self.minute_window.append(now)


class JikanClient:
    """
    Client for Jikan API v4 with caching, rate-limiting, and error resilience.
    Complies with SRS NFR-1, NFR-2, NFR-13, NFR-18.
    """
    DEFAULT_CACHE_HOURS = 6

    def __init__(self, base_url=None):
        self.base_url = (base_url or getattr(settings, 'JIKAN_BASE_URL', 'https://api.jikan.moe/v4')).rstrip('/')
        self.rate_limiter = RateLimiter(max_per_second=3, max_per_minute=60)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AnimeVerseAI/1.0 (BCA College Prototype; https://animeverse.local)',
            'Accept': 'application/json',
        })
        self._circuit_broken_until = 0  # timestamp until which offline upstream is skipped

    def _primary_provider_name(self):
        if 'tenrai' in self.base_url:
            return 'tenrai'
        elif 'jikan' in self.base_url:
            return 'jikan'
        return 'primary'

    def _get_cache(self, cache_key, allow_expired=False):
        try:
            cached = JikanCache.objects.filter(cache_key=cache_key).first()
            if not cached:
                return None
            is_stale = cached.expires_at <= timezone.now()
            if allow_expired or not is_stale:
                payload = cached.payload
                # Preserve original metadata provenance and fetched timestamp
                if isinstance(payload, dict):
                    payload['is_cached'] = True
                    payload['is_stale'] = is_stale
                    if 'data' in payload:
                        if isinstance(payload['data'], dict):
                            payload['data']['is_cached'] = True
                            payload['data']['is_stale'] = is_stale
                        elif isinstance(payload['data'], list):
                            for el in payload['data']:
                                if isinstance(el, dict):
                                    el['is_cached'] = True
                                    el['is_stale'] = is_stale
                return payload
            return None
        except Exception as e:
            logger.warning(f"Cache lookup failed for {cache_key}: {e}")
            return None

    def _set_cache(self, cache_key, payload, ttl_hours=None):
        try:
            hours = ttl_hours or self.DEFAULT_CACHE_HOURS
            expires_at = timezone.now() + timedelta(hours=hours)
            JikanCache.objects.update_or_create(
                cache_key=cache_key,
                defaults={'payload': payload, 'expires_at': expires_at}
            )
        except Exception as e:
            logger.warning(f"Cache save failed for {cache_key}: {e}")

    def _request(self, endpoint, params=None, cache_key=None, ttl_hours=None):
        """
        Executes a GET request against anime provider with rate limiting,
        timeout (5s per NFR-2), 429 retry (2s delay per NFR-18), and caching.
        Primary: Tenrai API v1 (or configured base_url).
        Secondary: AniList GraphQL.
        Tertiary: Stale cache.
        Preserves exact metadata provenance and fetched timestamps.
        """
        if cache_key:
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        now = time.time()
        should_try_upstream = now > self._circuit_broken_until
        primary_source = self._primary_provider_name()

        if should_try_upstream:
            self.rate_limiter.acquire()
            try:
                response = self.session.get(url, params=params, timeout=5.0)

                # NFR-18: retry 429 response once after 2 seconds
                if response.status_code == 429:
                    logger.warning(f"{primary_source} 429 received for {url}. Waiting 2s before retry...")
                    time.sleep(2.0)
                    self.rate_limiter.acquire()
                    response = self.session.get(url, params=params, timeout=5.0)

                if response.status_code == 200:
                    payload = response.json()
                    now_iso = timezone.now().isoformat()
                    payload['metadata_source'] = primary_source
                    payload['fetched_at'] = now_iso
                    payload['is_cached'] = False
                    payload['is_stale'] = False

                    if isinstance(payload, dict) and 'data' in payload:
                        if isinstance(payload['data'], dict):
                            payload['data']['metadata_source'] = primary_source
                            payload['data']['fetched_at'] = now_iso
                            payload['data']['is_cached'] = False
                            payload['data']['is_stale'] = False
                        elif isinstance(payload['data'], list):
                            for el in payload['data']:
                                if isinstance(el, dict):
                                    el['metadata_source'] = primary_source
                                    el['fetched_at'] = now_iso
                                    el['is_cached'] = False
                                    el['is_stale'] = False
                    if cache_key:
                        self._set_cache(cache_key, payload, ttl_hours=ttl_hours)
                    return payload
                elif response.status_code == 404:
                    return None

            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as exc:
                logger.warning(f"{primary_source} upstream request failed ({type(exc).__name__}): {exc}. Retrying once...")
                try:
                    time.sleep(1.0)
                    self.rate_limiter.acquire()
                    retry_resp = self.session.get(url, params=params, timeout=7.0)
                    if retry_resp.status_code == 200:
                        payload = retry_resp.json()
                        now_iso = timezone.now().isoformat()
                        payload['metadata_source'] = primary_source
                        payload['fetched_at'] = now_iso
                        payload['is_cached'] = False
                        payload['is_stale'] = False
                        if isinstance(payload, dict) and 'data' in payload:
                            if isinstance(payload['data'], dict):
                                payload['data']['metadata_source'] = primary_source
                                payload['data']['fetched_at'] = now_iso
                                payload['data']['is_cached'] = False
                                payload['data']['is_stale'] = False
                            elif isinstance(payload['data'], list):
                                for el in payload['data']:
                                    if isinstance(el, dict):
                                        el['metadata_source'] = primary_source
                                        el['fetched_at'] = now_iso
                                        el['is_cached'] = False
                                        el['is_stale'] = False
                        if cache_key:
                            self._set_cache(cache_key, payload, ttl_hours=ttl_hours)
                        return payload
                except Exception as retry_exc:
                    logger.warning(f"{primary_source} retry also failed: {retry_exc}. Tripping circuit breaker for 60s.")
                self._circuit_broken_until = time.time() + 60.0

        # Secondary fallback: AniList GraphQL adapter
        fallback_data = self._live_anime_fallback(endpoint, params)
        if fallback_data is not None:
            now_iso = timezone.now().isoformat()
            fallback_data['metadata_source'] = 'anilist'
            fallback_data['fetched_at'] = now_iso
            fallback_data['is_cached'] = False
            fallback_data['is_stale'] = False

            if isinstance(fallback_data, dict) and 'data' in fallback_data:
                if isinstance(fallback_data['data'], dict):
                    fallback_data['data']['metadata_source'] = 'anilist'
                    fallback_data['data']['fetched_at'] = now_iso
                    fallback_data['data']['is_cached'] = False
                    fallback_data['data']['is_stale'] = False
                elif isinstance(fallback_data['data'], list):
                    for el in fallback_data['data']:
                        if isinstance(el, dict):
                            el['metadata_source'] = 'anilist'
                            el['fetched_at'] = now_iso
                            el['is_cached'] = False
                            el['is_stale'] = False
            if cache_key:
                self._set_cache(cache_key, fallback_data, ttl_hours=ttl_hours)
            return fallback_data

        # NFR-13: Tertiary fallback: expired cached data if available
        if cache_key:
            stale_cached = self._get_cache(cache_key, allow_expired=True)
            if stale_cached is not None:
                logger.info(f"Serving stale cache for {cache_key} during all-provider outage.")
                return stale_cached

        raise ServiceUnavailableError("Anime discovery service is currently unavailable. Please try again.")

    def _live_anime_fallback(self, endpoint, params):
        """
        Resilient adapter that fetches real anime records directly from live GraphQL
        and structures them exactly into the Jikan v4 response schema.
        Ensures 100% genuine anime titles, posters, synopsis, and MAL IDs.
        """
        params = params or {}
        try:
            if 'anime/' in endpoint and '/episodes' in endpoint:
                mal_id = int(endpoint.split('/')[1])
                return self._fetch_real_episodes_from_fallback(mal_id)
            elif 'anime/' in endpoint and '/characters' in endpoint:
                mal_id = int(endpoint.split('/')[1])
                return self._fetch_real_characters_from_anilist(mal_id)
            elif 'anime/' in endpoint and '/videos' in endpoint:
                mal_id = int(endpoint.split('/')[1])
                return self._fetch_real_videos_from_anilist(mal_id)
            elif 'anime/' in endpoint and '/streaming' in endpoint:
                mal_id = int(endpoint.split('/')[1])
                return self._fetch_real_streaming_from_anilist(mal_id)
            elif 'anime/' in endpoint and '/full' in endpoint:
                mal_id = int(endpoint.split('/')[1])
                return self._fetch_real_anime_from_anilist(mal_id=mal_id)
            elif 'anime/' in endpoint:
                parts = endpoint.split('/')
                if len(parts) >= 2 and parts[1].isdigit():
                    mal_id = int(parts[1])
                    return self._fetch_real_anime_from_anilist(mal_id=mal_id)
            elif 'top/anime' in endpoint:
                filter_val = params.get('filter', 'bypopularity')
                page = int(params.get('page', 1))
                return self._fetch_real_top_from_anilist(filter_val=filter_val, page=page)
            elif 'anime' in endpoint:
                # Search or browse
                q = params.get('q')
                page = int(params.get('page', 1))
                min_score = params.get('min_score')
                genre = params.get('genres') or params.get('genre')
                status = params.get('status')
                anime_type = params.get('type')
                return self._search_real_anime_from_anilist(
                    q=q, page=page, min_score=min_score, genre=genre, status=status, anime_type=anime_type
                )
            elif 'seasons/now' in endpoint or 'seasons/' in endpoint:
                page = int(params.get('page', 1))
                return self._fetch_real_season_from_anilist(page=page)
            elif 'schedules' in endpoint or 'seasons/upcoming' in endpoint:
                page = int(params.get('page', 1))
                return self._fetch_real_upcoming_from_anilist(page=page)
        except Exception as e:
            logger.error(f"Live anime fallback error: {e}")
        return None

    def _fetch_real_episodes_from_fallback(self, mal_id):
        query = """
        query ($idMal: Int) {
          Media(idMal: $idMal, type: ANIME) {
            id
            title { romaji english }
            streamingEpisodes {
              title
              thumbnail
              url
              site
            }
          }
        }
        """
        try:
            resp = requests.post(
                'https://graphql.anilist.co',
                json={'query': query, 'variables': {'idMal': mal_id}},
                timeout=5.0
            )
            if resp.status_code == 200:
                media = resp.json().get('data', {}).get('Media', {})
                if media and media.get('streamingEpisodes'):
                    ep_list = []
                    for idx, ep in enumerate(media['streamingEpisodes'], 1):
                        ep_title = ep.get('title') or f"Episode {idx}"
                        cleaned_title = ep_title
                        if ' - ' in ep_title:
                            cleaned_title = ep_title.split(' - ', 1)[1]
                        ep_list.append({
                            'mal_id': idx,
                            'title': cleaned_title,
                            'title_japanese': None,
                            'title_romanji': None,
                            'aired': None,
                            'filler': False,
                            'recap': False,
                            'synopsis': None,
                            'images': {'jpg': {'image_url': ep.get('thumbnail')}},
                        })
                    return {
                        'data': ep_list,
                        'pagination': {
                            'last_visible_page': 1,
                            'has_next_page': False,
                            'items': {'count': len(ep_list), 'total': len(ep_list)}
                        }
                    }
        except Exception as e:
            logger.warning(f"AniList episode fallback failed: {e}")
        return None

    def _fetch_real_anime_from_anilist(self, mal_id):
        query = """
        query ($malId: Int) {
          Media(idMal: $malId, type: ANIME) {
            id
            idMal
            title { romaji english }
            coverImage { large extraLarge }
            bannerImage
            description(asHtml: false)
            format
            episodes
            averageScore
            genres
            status
            startDate { year month day }
            endDate { year month day }
            studios(isMain: true) { nodes { name } }
            relations {
              edges {
                relationType
                node {
                  idMal
                  title { romaji english }
                  format
                  episodes
                  averageScore
                  coverImage { large }
                }
              }
            }
          }
        }
        """
        try:
            resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'malId': mal_id}}, timeout=8.0)
            if resp.status_code == 200:
                media = resp.json().get('data', {}).get('Media')
                if media:
                    return {'data': self._convert_media_to_jikan_format(media)}
        except Exception as exc:
            logger.warning(f"AniList anime details lookup failed for MAL ID {mal_id}: {exc}")
        return None

    def _fetch_real_characters_from_anilist(self, mal_id):
        query = """
        query ($malId: Int) {
          Media(idMal: $malId, type: ANIME) {
            characters(perPage: 12, sort: [ROLE, RELEVANCE]) {
              edges {
                role
                node {
                  id
                  name { full }
                  image { large }
                }
              }
            }
          }
        }
        """
        try:
            resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'malId': mal_id}}, timeout=8.0)
            if resp.status_code == 200:
                chars_edges = resp.json().get('data', {}).get('Media', {}).get('characters', {}).get('edges', [])
                jikan_chars = []
                for edge in chars_edges:
                    node = edge.get('node', {})
                    jikan_chars.append({
                        'character': {
                            'mal_id': node.get('id'),
                            'name': node.get('name', {}).get('full', 'Unknown'),
                            'images': {'jpg': {'image_url': node.get('image', {}).get('large')}}
                        },
                        'role': edge.get('role', 'Main')
                    })
                return {'data': jikan_chars}
        except Exception as exc:
            logger.warning(f"AniList character lookup failed for MAL ID {mal_id}: {exc}")
        return {'data': []}

    def _fetch_real_streaming_from_anilist(self, mal_id):
        query = """
        query ($malId: Int) {
          Media(idMal: $malId, type: ANIME) {
            externalLinks {
              site
              url
              type
              language
              notes
            }
          }
        }
        """
        try:
            resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'malId': mal_id}}, timeout=8.0)
            if resp.status_code == 200:
                links = resp.json().get('data', {}).get('Media', {}).get('externalLinks', [])
                streaming = []
                for l in links:
                    if l.get('type') == 'STREAMING' or any(s in l.get('site', '').lower() for s in ['netflix', 'crunchyroll', 'youtube', 'prime', 'hulu', 'bilibili']):
                        streaming.append({
                            'name': l.get('site'),
                            'url': l.get('url'),
                            'language': l.get('language'),
                            'notes': l.get('notes')
                        })
                return {'data': streaming}
        except Exception as exc:
            logger.warning(f"AniList streaming lookup failed for MAL ID {mal_id}: {exc}")
        return {'data': []}

    def _fetch_real_videos_from_anilist(self, mal_id):
        query = """
        query ($malId: Int) {
          Media(idMal: $malId, type: ANIME) {
            trailer {
              id
              site
              thumbnail
            }
          }
        }
        """
        try:
            resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'malId': mal_id}}, timeout=8.0)
            if resp.status_code == 200:
                trailer = resp.json().get('data', {}).get('Media', {}).get('trailer')
                if trailer and trailer.get('site') == 'youtube' and trailer.get('id'):
                    yt_id = trailer['id']
                    return {
                        'data': {
                            'promo': [{
                                'title': 'Official Trailer',
                                'trailer': {
                                    'youtube_id': yt_id,
                                    'url': f"https://www.youtube.com/watch?v={yt_id}",
                                    'embed_url': f"https://www.youtube.com/embed/{yt_id}?enablejsapi=1&wmode=opaque",
                                    'images': {
                                        'image_url': trailer.get('thumbnail') or f"https://img.youtube.com/vi/{yt_id}/default.jpg",
                                        'large_image_url': f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg",
                                        'maximum_image_url': f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
                                    },
                                    'title': 'Official Trailer'
                                }
                            }],
                            'episodes': [],
                            'music_videos': []
                        }
                    }
        except Exception as exc:
            logger.warning(f"AniList video lookup failed for MAL ID {mal_id}: {exc}")
        return {'data': {'promo': [], 'episodes': [], 'music_videos': []}}

    def _fetch_real_top_from_anilist(self, filter_val='bypopularity', page=1):
        sort = ["POPULARITY_DESC"] if filter_val in ('bypopularity', 'popular') else ["SCORE_DESC"]
        query = """
        query ($page: Int, $sort: [MediaSort]) {
          Page(page: $page, perPage: 20) {
            pageInfo { total currentPage lastPage hasNextPage }
            media(sort: $sort, type: ANIME, isAdult: false) {
              id idMal title { romaji english }
              coverImage { large extraLarge }
              bannerImage description(asHtml: false)
              format episodes averageScore genres status isAdult
            }
          }
        }
        """
        resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'page': page, 'sort': sort}}, timeout=5.0)
        if resp.status_code == 200:
            page_data = resp.json().get('data', {}).get('Page', {})
            media_list = page_data.get('media', [])
            data = [self._convert_media_to_jikan_format(m) for m in media_list if m.get('idMal')]
            return {
                'data': data,
                'pagination': {
                    'last_visible_page': page_data.get('pageInfo', {}).get('lastPage', 1),
                    'has_next_page': page_data.get('pageInfo', {}).get('hasNextPage', False),
                    'current_page': page,
                    'items': {'count': len(data), 'total': page_data.get('pageInfo', {}).get('total', len(data))}
                }
            }
        return None

    def _search_real_anime_from_anilist(self, q=None, page=1, min_score=None, genre=None, status=None, anime_type=None):
        query = """
        query ($search: String, $page: Int, $genre: String, $status: MediaStatus, $format: MediaFormat) {
          Page(page: $page, perPage: 20) {
            pageInfo { total currentPage lastPage hasNextPage }
            media(search: $search, genre: $genre, status: $status, format: $format, type: ANIME, isAdult: false, sort: [POPULARITY_DESC]) {
              id idMal title { romaji english }
              coverImage { large extraLarge }
              bannerImage description(asHtml: false)
              format episodes averageScore genres status isAdult
            }
          }
        }
        """
        format_map = {'tv': 'TV', 'movie': 'MOVIE', 'ova': 'OVA', 'special': 'SPECIAL', 'ona': 'ONA', 'music': 'MUSIC'}
        status_map = {'airing': 'RELEASING', 'complete': 'FINISHED', 'upcoming': 'NOT_YET_RELEASED'}

        vars_dict = {'page': page}
        if q:
            vars_dict['search'] = q
        if genre:
            vars_dict['genre'] = genre
        if status and status.lower() in status_map:
            vars_dict['status'] = status_map[status.lower()]
        if anime_type and anime_type.lower() in format_map:
            vars_dict['format'] = format_map[anime_type.lower()]

        resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': vars_dict}, timeout=5.0)
        if resp.status_code == 200:
            page_data = resp.json().get('data', {}).get('Page', {})
            media_list = page_data.get('media', [])
            items = []
            for m in media_list:
                if not m.get('idMal'):
                    continue
                converted = self._convert_media_to_jikan_format(m)
                if min_score is not None:
                    score = converted.get('score')
                    if score is None or score < float(min_score):
                        continue
                items.append(converted)

            return {
                'data': items,
                'pagination': {
                    'last_visible_page': page_data.get('pageInfo', {}).get('lastPage', 1),
                    'has_next_page': page_data.get('pageInfo', {}).get('hasNextPage', False),
                    'current_page': page,
                    'items': {'count': len(items), 'total': page_data.get('pageInfo', {}).get('total', len(items))}
                }
            }
        return None

    def _fetch_real_season_from_anilist(self, page=1):
        query = """
        query ($page: Int) {
          Page(page: $page, perPage: 20) {
            pageInfo { total currentPage lastPage hasNextPage }
            media(status: RELEASING, type: ANIME, isAdult: false, sort: [POPULARITY_DESC]) {
              id idMal title { romaji english }
              coverImage { large extraLarge }
              bannerImage description(asHtml: false)
              format episodes averageScore genres status isAdult
              startDate { year month day }
            }
          }
        }
        """
        resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'page': page}}, timeout=5.0)
        if resp.status_code == 200:
            page_data = resp.json().get('data', {}).get('Page', {})
            media_list = page_data.get('media', [])
            data = [self._convert_media_to_jikan_format(m) for m in media_list if m.get('idMal')]
            return {
                'data': data,
                'pagination': {
                    'last_visible_page': page_data.get('pageInfo', {}).get('lastPage', 1),
                    'has_next_page': page_data.get('pageInfo', {}).get('hasNextPage', False),
                    'current_page': page,
                    'items': {'count': len(data), 'total': page_data.get('pageInfo', {}).get('total', len(data))}
                }
            }
        return None

    def _fetch_real_upcoming_from_anilist(self, page=1):
        query = """
        query ($page: Int) {
          Page(page: $page, perPage: 20) {
            pageInfo { total currentPage lastPage hasNextPage }
            media(status: NOT_YET_RELEASED, type: ANIME, isAdult: false, sort: [POPULARITY_DESC]) {
              id idMal title { romaji english }
              coverImage { large extraLarge }
              bannerImage description(asHtml: false)
              format episodes averageScore genres status isAdult
              startDate { year month day }
            }
          }
        }
        """
        resp = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'page': page}}, timeout=5.0)
        if resp.status_code == 200:
            page_data = resp.json().get('data', {}).get('Page', {})
            media_list = page_data.get('media', [])
            data = [self._convert_media_to_jikan_format(m) for m in media_list if m.get('idMal')]
            return {
                'data': data,
                'pagination': {
                    'last_visible_page': page_data.get('pageInfo', {}).get('lastPage', 1),
                    'has_next_page': page_data.get('pageInfo', {}).get('hasNextPage', False),
                    'current_page': page,
                    'items': {'count': len(data), 'total': page_data.get('pageInfo', {}).get('total', len(data))}
                }
            }
        return None

    def _convert_media_to_jikan_format(self, media):
        """Converts raw media node into standard Jikan v4 anime object"""
        title_eng = media.get('title', {}).get('english')
        title_rom = media.get('title', {}).get('romaji')
        title = title_eng or title_rom or "Untitled"

        avg_score = media.get('averageScore')
        score = round(avg_score / 10.0, 2) if avg_score is not None else None

        genres = [{'name': g} for g in media.get('genres', [])]
        start = media.get('startDate', {})
        end = media.get('endDate', {})

        aired_from = f"{start.get('year')}-{str(start.get('month', 1)).zfill(2)}-{str(start.get('day', 1)).zfill(2)}" if start and start.get('year') else None
        aired_to = f"{end.get('year')}-{str(end.get('month', 1)).zfill(2)}-{str(end.get('day', 1)).zfill(2)}" if end and end.get('year') else None

        studios = [{'name': s.get('name')} for s in media.get('studios', {}).get('nodes', [])] if 'studios' in media else []

        relations = []
        if 'relations' in media and media['relations']:
            for edge in media['relations'].get('edges', []):
                rel_node = edge.get('node', {})
                if rel_node.get('idMal'):
                    relations.append({
                        'relation': edge.get('relationType', 'Related'),
                        'entry': [{
                            'mal_id': rel_node.get('idMal'),
                            'type': 'anime',
                            'name': rel_node.get('title', {}).get('english') or rel_node.get('title', {}).get('romaji'),
                            'images': {'jpg': {'image_url': rel_node.get('coverImage', {}).get('large')}}
                        }]
                    })

        return {
            'mal_id': media.get('idMal') or media.get('id'),
            'title': title,
            'title_english': title_eng,
            'images': {
                'jpg': {
                    'image_url': media.get('coverImage', {}).get('large'),
                    'large_image_url': media.get('coverImage', {}).get('extraLarge') or media.get('coverImage', {}).get('large'),
                }
            },
            'banner_image': media.get('bannerImage'),
            'synopsis': media.get('description'),
            'type': media.get('format', 'TV'),
            'episodes': media.get('episodes'),
            'score': score,
            'genres': genres,
            'status': media.get('status', 'Finished Airing'),
            'isAdult': media.get('isAdult', False),
            'aired': {
                'from': aired_from,
                'to': aired_to,
                'string': aired_from or 'Not available'
            },
            'studios': studios,
            'relations': relations,
        }

    # Public API methods per SRS
    def search_anime(self, q, page=1):
        cache_key = f"anime:search:{q.lower().strip()}:{page}"
        res = self._request("anime", params={'q': q, 'page': page, 'sfw': 'true'}, cache_key=cache_key)
        if res and isinstance(res, dict) and 'data' in res:
            from apps.anime.content_filter import filter_anime_list
            res['data'] = filter_anime_list(res['data'])
            if 'pagination' in res and 'items' in res['pagination']:
                res['pagination']['items']['count'] = len(res['data'])
        return res

    def get_trending_anime(self, page=1):
        cache_key = f"anime:trending:{page}"
        res = self._request("top/anime", params={'filter': 'airing', 'page': page, 'sfw': 'true'}, cache_key=cache_key)
        if res and isinstance(res, dict) and 'data' in res:
            from apps.anime.content_filter import filter_anime_list
            res['data'] = filter_anime_list(res['data'])
        return res

    def get_popular_anime(self, page=1):
        cache_key = f"anime:popular:{page}"
        res = self._request("top/anime", params={'filter': 'bypopularity', 'page': page, 'sfw': 'true'}, cache_key=cache_key)
        if res and isinstance(res, dict) and 'data' in res:
            from apps.anime.content_filter import filter_anime_list
            res['data'] = filter_anime_list(res['data'])
        return res

    def browse_anime(self, genre=None, min_score=None, anime_type=None, status=None, page=1):
        # Explicit check for adult genres in browse request
        if genre and str(genre).lower().strip() in ('12', '49', 'hentai', 'erotica'):
            return {
                'data': [],
                'pagination': {'last_visible_page': 1, 'has_next_page': False, 'current_page': page, 'items': {'count': 0, 'total': 0}}
            }
        cache_key = f"anime:browse:{genre}:{min_score}:{anime_type}:{status}:{page}"
        params = {'page': page, 'sfw': 'true'}
        if genre:
            params['genres'] = genre
        if min_score is not None:
            params['min_score'] = min_score
        if anime_type:
            params['type'] = anime_type.lower()
        if status:
            params['status'] = status.lower()
        res = self._request("anime", params=params, cache_key=cache_key)
        if res and isinstance(res, dict) and 'data' in res:
            from apps.anime.content_filter import filter_anime_list
            res['data'] = filter_anime_list(res['data'])
            if 'pagination' in res and 'items' in res['pagination']:
                res['pagination']['items']['count'] = len(res['data'])
        return res

    def get_anime_episodes(self, mal_id, page=1):
        cache_key = f"anime:{mal_id}:episodes:{page}"
        return self._request(f"anime/{mal_id}/episodes", params={'page': page}, cache_key=cache_key)

    def get_anime_details(self, mal_id):
        cache_key = f"anime:{mal_id}:full"
        return self._request(f"anime/{mal_id}/full", cache_key=cache_key)

    def get_anime_characters(self, mal_id):
        cache_key = f"anime:{mal_id}:characters"
        return self._request(f"anime/{mal_id}/characters", cache_key=cache_key)

    def get_anime_streaming(self, mal_id):
        cache_key = f"anime:{mal_id}:streaming"
        return self._request(f"anime/{mal_id}/streaming", cache_key=cache_key)

    def get_anime_videos(self, mal_id):
        cache_key = f"anime:{mal_id}:videos"
        return self._request(f"anime/{mal_id}/videos", cache_key=cache_key)

    def get_season_anime(self, year=None, season=None, page=1):
        if year and season:
            endpoint = f"seasons/{year}/{season.lower()}"
            cache_key = f"calendar:season:{year}:{season.lower()}:{page}"
        else:
            endpoint = "seasons/now"
            cache_key = f"calendar:season:now:{page}"
        res = self._request(endpoint, params={'page': page, 'sfw': 'true'}, cache_key=cache_key, ttl_hours=6)
        if res and isinstance(res, dict) and 'data' in res:
            from apps.anime.content_filter import filter_anime_list
            res['data'] = filter_anime_list(res['data'])
        return res

    def get_upcoming_anime(self, page=1):
        cache_key = f"calendar:upcoming:{page}"
        res = self._request("seasons/upcoming", params={'page': page, 'sfw': 'true'}, cache_key=cache_key, ttl_hours=6)
        if res and isinstance(res, dict) and 'data' in res:
            from apps.anime.content_filter import filter_anime_list
            res['data'] = filter_anime_list(res['data'])
        return res

    # Normalizers conforming to SRS
    @staticmethod
    def normalize_poster_card(item, metadata_source="tenrai", is_stale=False, is_cached=False, fetched_at=None):
        """
        SRS Page 28:
        anime in these responses is {mal_id, title, poster_url, score, anime_type, total_episodes}.
        Missing values are null. Tracks real metadata source (tenrai/anilist/cache).
        """
        if not item:
            return None
        images = item.get('images', {})
        poster_url = None
        if isinstance(images, dict):
            jpg = images.get('jpg', {})
            poster_url = jpg.get('image_url') or jpg.get('large_image_url')

        actual_source = item.get('metadata_source') or metadata_source
        actual_fetched_at = item.get('fetched_at') or fetched_at
        actual_cached = item.get('is_cached', is_cached)
        actual_stale = item.get('is_stale', is_stale)

        return {
            'mal_id': item.get('mal_id'),
            'title': item.get('title') or item.get('title_english') or "Untitled",
            'title_english': item.get('title_english'),
            'poster_url': poster_url or item.get('poster_url'),
            'score': item.get('score'),
            'anime_type': item.get('type') or item.get('anime_type'),
            'total_episodes': item.get('episodes') or item.get('total_episodes'),
            'metadata_source': actual_source,
            'fetched_at': actual_fetched_at,
            'is_cached': actual_cached,
            'is_stale': actual_stale,
        }

    @staticmethod
    def normalize_anime_details(item, characters_data=None, user_entry=None, metadata_source="tenrai", is_stale=False, is_cached=False, fetched_at=None):
        """
        SRS Page 29:
        {mal_id, title, title_english, poster_url, banner_url, synopsis,
        genres, type, episodes, score, aired: {from, to}, characters: [character], user_entry}
        synopsis, banner_url, characters and aired.to may be null.
        """
        images = item.get('images', {})
        poster_url = None
        if isinstance(images, dict):
            jpg = images.get('jpg', {})
            poster_url = jpg.get('large_image_url') or jpg.get('image_url')

        banner_url = item.get('banner_image') or item.get('banner_url')
        synopsis = item.get('synopsis')
        genres = [g.get('name') if isinstance(g, dict) else str(g) for g in item.get('genres', [])]

        aired_data = item.get('aired') or {}
        aired = {
            'from': aired_data.get('from'),
            'to': aired_data.get('to'),
        }

        # Characters
        characters = []
        if characters_data and isinstance(characters_data, list):
            for ch in characters_data:
                char_info = ch.get('character', {})
                ch_images = char_info.get('images', {})
                ch_url = ch_images.get('jpg', {}).get('image_url') if isinstance(ch_images, dict) else None
                characters.append({
                    'id': char_info.get('mal_id'),
                    'name': char_info.get('name'),
                    'image_url': ch_url,
                    'role': ch.get('role', 'Supporting'),
                })

        actual_source = item.get('metadata_source') or metadata_source
        actual_fetched_at = item.get('fetched_at') or fetched_at
        actual_cached = item.get('is_cached', is_cached)
        actual_stale = item.get('is_stale', is_stale)

        return {
            'mal_id': item.get('mal_id'),
            'title': item.get('title') or "Untitled",
            'title_english': item.get('title_english'),
            'title_japanese': item.get('title_japanese'),
            'poster_url': poster_url or item.get('poster_url'),
            'banner_url': banner_url,
            'synopsis': synopsis,
            'genres': genres,
            'type': item.get('type'),
            'episodes': item.get('episodes'),
            'score': item.get('score'),
            'popularity': item.get('popularity'),
            'season': item.get('season'),
            'year': item.get('year'),
            'aired': aired,
            'characters': characters,
            'user_entry': user_entry,
            'metadata_source': actual_source,
            'fetched_at': actual_fetched_at,
            'is_cached': actual_cached,
            'is_stale': actual_stale,
        }

    @staticmethod
    def normalize_release(item, metadata_source="tenrai", is_stale=False, is_cached=False, fetched_at=None):
        """
        SRS Page 33:
        release is {mal_id, title, poster_url, release_label}.
        release_label reads "Date to be announced" when Jikan gives no date.
        """
        images = item.get('images', {})
        poster_url = None
        if isinstance(images, dict):
            jpg = images.get('jpg', {})
            poster_url = jpg.get('image_url') or jpg.get('large_image_url')

        aired = item.get('aired') or {}
        release_label = aired.get('from') or aired.get('string')
        if not release_label or release_label == 'Not available':
            release_label = "Date to be announced"

        actual_source = item.get('metadata_source') or metadata_source
        actual_fetched_at = item.get('fetched_at') or fetched_at
        actual_cached = item.get('is_cached', is_cached)
        actual_stale = item.get('is_stale', is_stale)

        return {
            'mal_id': item.get('mal_id'),
            'title': item.get('title') or "Untitled",
            'poster_url': poster_url or item.get('poster_url'),
            'release_label': release_label,
            'aired_from': aired.get('from'),
            'anime_type': item.get('type') or item.get('format') or 'TV',
            'score': item.get('score'),
            'broadcast': item.get('broadcast', {}).get('string') if isinstance(item.get('broadcast'), dict) else item.get('broadcast'),
            'metadata_source': actual_source,
            'fetched_at': actual_fetched_at,
            'is_cached': actual_cached,
            'is_stale': actual_stale,
        }

    @staticmethod
    def normalize_episode(item, main_synopsis=None, metadata_source="tenrai", is_stale=False, is_cached=False, fetched_at=None):
        """
        Normalizes a single anime episode.
        Guarantees:
        - Each episode has its own actual description or None (displayed as Description unavailable).
        - Does not repeat the main anime synopsis as an episode description.
        - Never fabricates summaries.
        """
        if not item:
            return None

        ep_num = item.get('mal_id') or item.get('number') or item.get('episode') or 0
        raw_synopsis = item.get('synopsis') or item.get('description')

        episode_synopsis = None
        if raw_synopsis and isinstance(raw_synopsis, str):
            cleaned_ep = raw_synopsis.strip()
            cleaned_main = (main_synopsis or '').strip()
            # Must not be empty and must not duplicate main anime synopsis
            if cleaned_ep and (not cleaned_main or cleaned_ep != cleaned_main):
                episode_synopsis = cleaned_ep

        images = item.get('images', {})
        thumbnail_url = item.get('thumbnail') or item.get('thumbnail_url')
        if not thumbnail_url and isinstance(images, dict):
            jpg = images.get('jpg', {})
            thumbnail_url = jpg.get('image_url') or jpg.get('large_image_url')

        actual_source = item.get('metadata_source') or metadata_source
        actual_fetched_at = item.get('fetched_at') or fetched_at
        actual_cached = item.get('is_cached', is_cached)
        actual_stale = item.get('is_stale', is_stale)

        return {
            'episode_number': ep_num,
            'title': item.get('title') or f"Episode {ep_num}",
            'title_japanese': item.get('title_japanese'),
            'title_romanji': item.get('title_romanji'),
            'aired': item.get('aired') or item.get('airdate'),
            'filler': bool(item.get('filler', False)),
            'recap': bool(item.get('recap', False)),
            'score': item.get('score'),
            'synopsis': episode_synopsis,
            'has_description': bool(episode_synopsis),
            'thumbnail_url': thumbnail_url,
            'duration': item.get('duration'),
            'metadata_source': actual_source,
            'fetched_at': actual_fetched_at,
            'is_cached': actual_cached,
            'is_stale': actual_stale,
        }
