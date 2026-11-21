import logging

logger = logging.getLogger(__name__)

BLOCKED_ANIME_MESSAGE = "This title is not available in AnimeVerse AI."

# Explicit adult / hentai genre identifiers
EXCLUDED_GENRE_IDS = {12, 49}  # MAL 12: Hentai, 49: Erotica
EXCLUDED_GENRE_NAMES = {'hentai', 'erotica'}

# Explicit adult rating prefixes and keywords
# MAL uses 'Rx - Hentai' or 'Rx' exclusively for explicit 18+ pornographic / hentai works.
# 'R - 17+ (violence & profanity)' and 'R+ - Mild Nudity' are explicitly ALLOWED.
EXCLUDED_RATING_KEYWORDS = {'rx', 'rx - hentai', 'rx - adult', 'hentai'}


def is_excluded_adult_anime(item) -> bool:
    """
    Centralized content-safety filtering function.
    Returns True ONLY if the anime is confirmed to be Hentai or explicitly sexually graphic adult content.

    Strict Rules per SRS & College Safety Requirements:
    - Excludes entries with Genre ID 12 (Hentai) or 49 (Erotica).
    - Excludes entries tagged with genre 'Hentai' or 'Erotica'.
    - Excludes entries with 'explicit_genres' containing Hentai or Erotica.
    - Excludes entries with rating 'Rx - Hentai' or 'Rx'.
    - Excludes AniList entries with 'isAdult' == True or genre 'Hentai'.
    - Excludes entries with explicit sexual content tags.

    Safeguards:
    - Does NOT exclude 'R - 17+ (violence & profanity)' (e.g. Berserk, Attack on Titan, Psycho-Pass).
    - Does NOT exclude 'R+ - Mild Nudity' or ordinary Ecchi, Romance, Action, or Mature themes.
    - If metadata is missing or empty, does NOT classify as hentai.
    - NEVER relies on title keywords.
    """
    if not item:
        return False

    # 1. Handle Django Anime model instance
    if hasattr(item, 'mal_id') and not isinstance(item, dict):
        # Anime model only caches basic display fields; check if there is an in-memory or cache payload
        # or check associated cached JikanCache
        mal_id = getattr(item, 'mal_id', None)
        if mal_id:
            from apps.anime.models import JikanCache
            cached = JikanCache.objects.filter(cache_key=f"details_{mal_id}").first()
            if cached and isinstance(cached.payload, dict):
                data = cached.payload.get('data') or cached.payload
                return is_excluded_adult_anime(data)
        return False

    if not isinstance(item, dict):
        return False

    # 2. Check explicit AniList flag
    if item.get('isAdult') is True:
        return True

    # 3. Check Rating field (MAL standard)
    rating_raw = str(item.get('rating') or '').strip().lower()
    if rating_raw:
        # Check if rating indicates Rx / Hentai
        # Be careful: 'r - 17+' starts with 'r' but not 'rx'
        if rating_raw.startswith('rx') or 'hentai' in rating_raw:
            return True

    # 4. Check standard genres
    genres = item.get('genres') or []
    if isinstance(genres, list):
        for g in genres:
            if isinstance(g, dict):
                gid = g.get('mal_id') or g.get('id')
                name = str(g.get('name') or '').strip().lower()
                if gid in EXCLUDED_GENRE_IDS or name in EXCLUDED_GENRE_NAMES:
                    return True
            elif isinstance(g, str):
                if g.strip().lower() in EXCLUDED_GENRE_NAMES:
                    return True
    elif isinstance(genres, str):
        if genres.strip().lower() in EXCLUDED_GENRE_NAMES:
            return True

    # 5. Check Jikan v4 'explicit_genres'
    explicit_genres = item.get('explicit_genres') or []
    if isinstance(explicit_genres, list):
        for eg in explicit_genres:
            if isinstance(eg, dict):
                egid = eg.get('mal_id') or eg.get('id')
                name = str(eg.get('name') or '').strip().lower()
                if egid in EXCLUDED_GENRE_IDS or name in EXCLUDED_GENRE_NAMES:
                    return True
            elif isinstance(eg, str):
                if eg.strip().lower() in EXCLUDED_GENRE_NAMES:
                    return True

    # 6. Check themes and demographics for explicit tags
    themes = item.get('themes') or []
    if isinstance(themes, list):
        for t in themes:
            if isinstance(t, dict):
                tid = t.get('mal_id') or t.get('id')
                name = str(t.get('name') or '').strip().lower()
                if tid in EXCLUDED_GENRE_IDS or name in EXCLUDED_GENRE_NAMES:
                    return True
            elif isinstance(t, str):
                if t.strip().lower() in EXCLUDED_GENRE_NAMES:
                    return True

    return False


def filter_anime_list(items):
    """
    Filters a list of anime items (dicts or model instances),
    removing any excluded adult/hentai records.
    """
    if not items or not isinstance(items, list):
        return []
    return [item for item in items if not is_excluded_adult_anime(item)]


def check_anime_id_is_excluded(mal_id, jikan_client=None) -> bool:
    """
    Checks if a given mal_id corresponds to an excluded adult/hentai anime.
    Inspects cache first, then upstream details.
    """
    if not mal_id:
        return False

    try:
        from apps.anime.models import JikanCache
        # Check cache
        for prefix in (f"details_{mal_id}", f"anime_{mal_id}"):
            cached = JikanCache.objects.filter(cache_key=prefix).first()
            if cached and isinstance(cached.payload, dict):
                data = cached.payload.get('data') or cached.payload
                return is_excluded_adult_anime(data)

        # Fallback to client check
        if jikan_client is None:
            from apps.anime.jikan_client import JikanClient
            jikan_client = JikanClient()

        details = jikan_client.get_anime_details(mal_id)
        if details and isinstance(details, dict):
            data = details.get('data') or details
            return is_excluded_adult_anime(data)
    except Exception as e:
        logger.debug(f"Error checking anime content safety for ID {mal_id}: {e}")

    return False
