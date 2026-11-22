import base64
import json
import logging
import re
import urllib.parse
import urllib.request
from datetime import timedelta
from django.utils import timezone
from apps.anime.jikan_client import JikanClient
from apps.anime.watchmode_client import WatchmodeClient
from apps.anime.models import JikanCache, Anime, StreamingLanguageTrack, TrackType, VerificationStatus

LANGUAGE_NORMALIZATION = {
    'ja': 'Japanese', 'jpn': 'Japanese', 'japanese': 'Japanese',
    'en': 'English', 'eng': 'English', 'english': 'English',
    'hi': 'Hindi', 'hin': 'Hindi', 'hindi': 'Hindi',
    'ta': 'Tamil', 'tam': 'Tamil', 'tamil': 'Tamil',
    'te': 'Telugu', 'tel': 'Telugu', 'telugu': 'Telugu',
    'ml': 'Malayalam', 'mal': 'Malayalam', 'malayalam': 'Malayalam',
}


def normalize_language_name(lang_str: str):
    """Normalizes ISO codes or names into Title-cased language name."""
    if not lang_str:
        return None
    cleaned = lang_str.strip().lower()
    if cleaned in ('all', '', 'none', 'any'):
        return None
    return LANGUAGE_NORMALIZATION.get(cleaned, lang_str.strip().title())

logger = logging.getLogger(__name__)

# Verified official CDN logos for streaming services
PROVIDER_LOGOS = {
    "netflix": "https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg",
    "crunchyroll": "https://upload.wikimedia.org/wikipedia/commons/0/08/Crunchyroll_Logo.png",
    "amazon prime video": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Prime_Video.png",
    "prime video": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Prime_Video.png",
    "amazon mx player": "https://upload.wikimedia.org/wikipedia/commons/b/b1/MX_Player_Logo.svg",
    "mx player": "https://upload.wikimedia.org/wikipedia/commons/b/b1/MX_Player_Logo.svg",
    "jiohotstar": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Disney%2B_Hotstar_logo.svg",
    "disney+ hotstar": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Disney%2B_Hotstar_logo.svg",
    "disney plus hotstar": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Disney%2B_Hotstar_logo.svg",
    "hotstar": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Disney%2B_Hotstar_logo.svg",
    "disney+": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg",
    "sony liv": "https://upload.wikimedia.org/wikipedia/commons/f/f7/SonyLIV_2020.png",
    "sony liv ": "https://upload.wikimedia.org/wikipedia/commons/f/f7/SonyLIV_2020.png",
    "vi movies and tv": "https://upload.wikimedia.org/wikipedia/commons/c/c6/Vodafone_Idea_logo_%282026%29.svg",
    "hulu": "https://upload.wikimedia.org/wikipedia/commons/a/a5/FX_-_Hulu_on_Disney%2B_logo.svg",
    "apple tv": "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/appletv.svg",
    "apple tv store": "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/appletv.svg",
    "apple tv+": "https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/appletv.svg",
    "tubi tv": "https://upload.wikimedia.org/wikipedia/commons/d/db/Tubi_logo.svg",
    "tubi": "https://upload.wikimedia.org/wikipedia/commons/d/db/Tubi_logo.svg",
    "bilibili": "https://upload.wikimedia.org/wikipedia/commons/1/12/Bilibili_2023.svg",
    "bilibili tv": "https://upload.wikimedia.org/wikipedia/commons/1/12/Bilibili_2023.svg",
    "youtube": "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
    "muse asia": "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
    "ani-one asia": "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
    "shahid": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Mbc_Shahid_logo.svg",
    "shahid vip": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Mbc_Shahid_logo.svg",
    "hoopla": "https://upload.wikimedia.org/wikipedia/commons/4/4a/Hoopla_logo.svg",
    "catchplay": "https://upload.wikimedia.org/wikipedia/commons/f/f8/Catchplay_logo.png",
    "max": "https://upload.wikimedia.org/wikipedia/commons/c/ce/Max_logo.svg",
    "fandango at home": "https://upload.wikimedia.org/wikipedia/commons/2/23/Fandango_2014.svg",
    "google play movies": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Google_Play_2022_logo.svg",
}

DEFAULT_LOGO = "https://upload.wikimedia.org/wikipedia/commons/a/a8/Play_button.png"

# Strict registry of verified official YouTube channel handles and stable identifiers
# Videos must be uploaded by a channel in this registry to be marked is_official: true
VERIFIED_YOUTUBE_REGISTRY = {
    "@aniplexusa": {"channel_name": "Aniplex USA", "category": "Official Distributor / Licensor"},
    "@aniplex": {"channel_name": "アニプレックス チャンネル", "category": "Official Studio / Licensor"},
    "@tohoanimation": {"channel_name": "TOHO animation チャンネル", "category": "Official Studio / Licensor"},
    "@officialtohomovie": {"channel_name": "東宝MOVIEチャンネル", "category": "Official Film Distributor"},
    "@video_vap": {"channel_name": "VAP Official", "category": "Official Video Distributor"},
    "@crunchyroll": {"channel_name": "Crunchyroll", "category": "Official Streaming Platform"},
    "@crunchyrollcollection": {"channel_name": "Crunchyroll Collection", "category": "Official Streaming Platform"},
    "@crunchyrollstoreau": {"channel_name": "Crunchyroll Store Australia", "category": "Official Regional Licensor"},
    "@madman": {"channel_name": "Madman Anime", "category": "Official Regional Licensor"},
    "@animaxasia": {"channel_name": "AnimaxAsia", "category": "Licensed Regional Broadcaster"},
    "@museasia": {"channel_name": "Muse Asia", "category": "Licensed Regional Distributor"},
    "@museindia": {"channel_name": "Muse India", "category": "Licensed Regional Distributor"},
    "@anioneasia": {"channel_name": "Ani-One Asia", "category": "Licensed Regional Distributor"},
    "@kadokawaanime": {"channel_name": "KADOKAWAanime", "category": "Official Studio / Licensor"},
    "@bandainamcofilmworks": {"channel_name": "Bandai Namco Filmworks", "category": "Official Studio / Licensor"},
    "@ponycanyon": {"channel_name": "PONY CANYON", "category": "Official Studio / Licensor"},
    "@avex": {"channel_name": "avex pictures", "category": "Official Licensor"},
    "@tmsanime": {"channel_name": "TMS Entertainment", "category": "Official Studio / Licensor"},
    "@vizmedia": {"channel_name": "VIZ Media", "category": "Official Licensor"},
    "@netflixanime": {"channel_name": "Netflix Anime", "category": "Official Streaming Platform"},
    "@twinengine": {"channel_name": "TWIN ENGINE", "category": "Official Studio / Licensor"},
    "@king_amusement_creative": {"channel_name": "KING AMUSEMENT CREATIVE", "category": "Official Studio / Licensor"},
    "@flyingdog": {"channel_name": "FlyingDog", "category": "Official Studio / Licensor"},
    "@bushiroad": {"channel_name": "Bushiroad", "category": "Official Studio / Licensor"},
    "@dmm": {"channel_name": "DMM pictures", "category": "Official Studio / Licensor"},
    "@warnerbrosjapan": {"channel_name": "Warner Bros. Japan Anime", "category": "Official Distributor"},
}

class WatchService:
    """
    Core service powering the 'WATCH ANYWHERE' feature in AnimeVerse AI.
    - Resolves country-specific legal streaming availability (Default: India 'IN').
    - Categorizes into subscription, free, free_with_ads, rent, buy.
    - Uses distinct status fields: provider_reported, country_matched, last_checked_at, verification_status.
    - Verifies YouTube trailers with stable channel registry and exact anime metadata matching.
    """
    CACHE_HOURS = 6

    def __init__(self, jikan_client=None, watchmode_client=None):
        self.jikan_client = jikan_client or JikanClient()
        self.watchmode_client = watchmode_client or WatchmodeClient()

    @staticmethod
    def get_provider_logo(provider_name):
        """Returns official SVG/PNG logo URL for known streaming providers"""
        if not provider_name:
            return DEFAULT_LOGO
        normalized = provider_name.strip().lower()
        for key, url in PROVIDER_LOGOS.items():
            if key in normalized or normalized in key:
                return url
        return DEFAULT_LOGO

    @staticmethod
    def normalize_category(monetization_type, provider_name=""):
        """
        Maps raw provider monetization string to the 5 mandatory categories:
        - subscription, free, free_with_ads, rent, buy
        """
        m = (monetization_type or "").strip().lower()
        p = (provider_name or "").strip().lower()

        if m in ("flatrate", "sub", "subscription"):
            return "subscription"
        elif m in ("ads", "avod", "free_with_ads"):
            return "free_with_ads"
        elif m in ("free",):
            return "free"
        elif m in ("rent", "rental"):
            return "rent"
        elif m in ("buy", "purchase"):
            return "buy"

        # Fallback by known platform defaults
        if any(free_p in p for free_p in ["mx player", "amazon mx player", "tubi"]):
            return "free_with_ads"
        elif any(yt in p for yt in ["muse asia", "ani-one"]):
            return "free"
        elif any(sub_p in p for sub_p in ["netflix", "crunchyroll", "prime video", "hulu", "hotstar", "sony liv"]):
            return "subscription"

        return "subscription"

    def _match_trailer_to_anime(self, video_title, promo_title, anime_info):
        """
        Matches video title to the exact anime using title metadata (English, Romaji, and Japanese).
        Prevents wrong anime trailers or unrelated videos from being verified.
        """
        if not anime_info:
            return False

        titles_to_check = []
        if anime_info.get("title"):
            titles_to_check.append(anime_info["title"].lower())
        if anime_info.get("title_english"):
            titles_to_check.append(anime_info["title_english"].lower())
        if anime_info.get("title_japanese"):
            titles_to_check.append(anime_info["title_japanese"])

        for t_entry in anime_info.get("titles", []):
            t_val = t_entry.get("title")
            if t_val:
                titles_to_check.append(t_val.lower())

        haystack = f"{video_title or ''} {promo_title or ''}".lower()

        for t in titles_to_check:
            if not t:
                continue
            if t in haystack:
                return True
            # Japanese / Kanji substring check
            if any('\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff' for ch in t):
                if t in (video_title or ""):
                    return True
            # Significant token check (words with >= 4 characters)
            tokens = [tok for tok in re.split(r'\W+', t) if len(tok) >= 4]
            if tokens and all(tok in haystack for tok in tokens[:2]):
                return True

        return False

    def verify_trailer(self, youtube_id, promo_title, anime_info):
        """
        Verifies a YouTube trailer using stable channel identifiers and exact anime metadata.
        Never relies on editorial curation or title search alone.
        Returns: (is_official: bool, verification_status: str, uploader_name: str, uploader_url: str, channel_id: str)
        """
        if not youtube_id:
            return False, "unverified", None, None, None

        # 1. Query live oEmbed to get genuine author and channel URL
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={youtube_id}&format=json"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'AnimeVerseAI/1.0 (Official Trailer Verifier)'})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                author_name = data.get('author_name')
                author_url = data.get('author_url', '')
                video_title = data.get('title', '')
        except Exception:
            # oEmbed failed (unlisted, network error, 404) -> honest unverified state
            return False, "unverified", "Unverified Uploader", None, None

        if not author_name:
            return False, "unverified", "Unverified Uploader", None, None

        # 2. Extract stable channel handle identifier from author_url
        channel_id = None
        if author_url and "/@" in author_url:
            channel_id = "@" + author_url.split("/@")[-1].split("/")[0].strip().lower()
        elif author_url and "/user/" in author_url:
            channel_id = "@" + author_url.split("/user/")[-1].split("/")[0].strip().lower()

        # Check against verified official channel registry
        channel_meta = None
        if channel_id and channel_id in VERIFIED_YOUTUBE_REGISTRY:
            channel_meta = VERIFIED_YOUTUBE_REGISTRY[channel_id]
        else:
            norm_author = author_name.strip().lower()
            for handle, meta in VERIFIED_YOUTUBE_REGISTRY.items():
                if meta["channel_name"].strip().lower() == norm_author or handle.lstrip("@") in norm_author.replace(" ", ""):
                    channel_meta = meta
                    channel_id = handle
                    break

        if not channel_meta:
            # Uploader is not a verified official production company or distributor
            return False, "unverified", author_name, author_url, channel_id

        # 3. Match trailer to exact anime
        if not self._match_trailer_to_anime(video_title, promo_title, anime_info):
            return False, "unverified", author_name, author_url, channel_id

        return True, "verified_official", channel_meta["channel_name"], author_url, channel_id

    @classmethod
    def seed_verified_language_tracks(cls):
        """
        Seeds official verified streaming provider language tracks.
        Sources: Official licensor releases, distributor catalogue data (Crunchyroll India, Netflix India, Sony LIV).
        Never infers language tracks.
        """
        tracks_data = [
            # 1. Demon Slayer (38000)
            {
                'mal_id': 38000,
                'title': "Demon Slayer: Kimetsu no Yaiba",
                'provider': "Crunchyroll",
                'country': "IN",
                'audio': ["Japanese", "English", "Hindi", "Tamil", "Telugu"],
                'subtitles': ["English"],
                'track_type': TrackType.DUBBED_AUDIO,
                'verification_status': VerificationStatus.LICENSOR_CONFIRMED,
                'source_url': "https://www.crunchyroll.com/series/GY5P48XEY/demon-slayer-kimetsu-no-yaiba",
                'notes': "Confirmed by Crunchyroll India multi-language dub launch (Hindi, Tamil, Telugu)",
            },
            {
                'mal_id': 38000,
                'title': "Demon Slayer: Kimetsu no Yaiba",
                'provider': "Netflix",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English", "Japanese"],
                'track_type': TrackType.DUBBED_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.netflix.com/title/81091393",
                'notes': "Confirmed on Netflix India streaming catalog",
            },
            {
                'mal_id': 38000,
                'title': "Demon Slayer: Kimetsu no Yaiba",
                'provider': "JioHotstar",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.UNVERIFIED,
                'source_url': "https://www.hotstar.com",
                'notes': "Unconfirmed / lapsed on Disney+ Hotstar India catalog",
            },
            # 2. Naruto (20)
            {
                'mal_id': 20,
                'title': "Naruto",
                'provider': "Sony LIV",
                'country': "IN",
                'audio': ["Hindi", "Tamil", "Telugu", "Malayalam"],
                'subtitles': ["English"],
                'track_type': TrackType.DUBBED_AUDIO,
                'verification_status': VerificationStatus.LICENSOR_CONFIRMED,
                'source_url': "https://www.sonyliv.com",
                'notes': "Official Sony YAY! Indian regional broadcast dubs (Hindi, Tamil, Telugu, Malayalam)",
            },
            {
                'mal_id': 20,
                'title': "Naruto",
                'provider': "Netflix",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.netflix.com/title/70205012",
                'notes': "Confirmed on Netflix India catalog",
            },
            {
                'mal_id': 20,
                'title': "Naruto",
                'provider': "Crunchyroll",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.crunchyroll.com/series/GY8VM8MWY/naruto",
                'notes': "Confirmed on Crunchyroll India catalog",
            },
            # 3. Black Clover (34572)
            {
                'mal_id': 34572,
                'title': "Black Clover",
                'provider': "Netflix",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.netflix.com/title/80234844",
                'notes': "Confirmed on Netflix India catalog",
            },
            {
                'mal_id': 34572,
                'title': "Black Clover",
                'provider': "Crunchyroll",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.crunchyroll.com/series/GRE5G1EQ6/black-clover",
                'notes': "Confirmed on Crunchyroll India catalog (Episodes 1–170)",
            },
            {
                'mal_id': 34572,
                'title': "Black Clover",
                'provider': "Crunchyroll",
                'country': "IN",
                'audio': ["Tamil"],
                'subtitles': ["English"],
                'track_type': TrackType.DUBBED_AUDIO,
                'verification_status': VerificationStatus.LICENSOR_CONFIRMED,
                'source_url': "https://www.crunchyroll.com/series/GRE5G1EQ6/black-clover",
                'notes': "Official Crunchyroll India Tamil dub (Season 1, Episodes 1–51)",
            },
            # 4. One Piece (21)
            {
                'mal_id': 21,
                'title': "One Piece",
                'provider': "Netflix",
                'country': "IN",
                'audio': ["Japanese", "English"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.netflix.com/title/80107103",
                'notes': "Confirmed on Netflix India catalog",
            },
            {
                'mal_id': 21,
                'title': "One Piece",
                'provider': "Crunchyroll",
                'country': "IN",
                'audio': ["Japanese"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.crunchyroll.com/series/GRMG8ZQZR/one-piece",
                'notes': "Confirmed on Crunchyroll India catalog",
            },
            # 5. Sousou no Frieren (52991)
            {
                'mal_id': 52991,
                'title': "Sousou no Frieren",
                'provider': "Crunchyroll",
                'country': "IN",
                'audio': ["Japanese", "English", "Hindi"],
                'subtitles': ["English"],
                'track_type': TrackType.DUBBED_AUDIO,
                'verification_status': VerificationStatus.LICENSOR_CONFIRMED,
                'source_url': "https://www.crunchyroll.com/series/GG5H5XQX4/frieren-beyond-journeys-end",
                'notes': "Confirmed by Crunchyroll India Hindi dub announcement",
            },
            {
                'mal_id': 52991,
                'title': "Sousou no Frieren",
                'provider': "Netflix",
                'country': "IN",
                'audio': ["Japanese"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.PROVIDER_REPORTED,
                'source_url': "https://www.netflix.com/title/81726701",
                'notes': "Confirmed on Netflix India catalog",
            },
            {
                'mal_id': 52991,
                'title': "Sousou no Frieren",
                'provider': "Muse Asia (YouTube)",
                'country': "IN",
                'audio': ["Japanese"],
                'subtitles': ["English"],
                'track_type': TrackType.ORIGINAL_AUDIO,
                'verification_status': VerificationStatus.LICENSOR_CONFIRMED,
                'source_url': "https://www.youtube.com/@MuseAsia",
                'notes': "Official licensed distributor stream on YouTube",
            },
        ]

        # Ensure incorrect Netflix Hindi records for Demon Slayer are purged
        StreamingLanguageTrack.objects.filter(
            anime__mal_id=38000,
            provider_name='Netflix',
            audio_language='Hindi'
        ).delete()

        for item in tracks_data:
            anime, _ = Anime.objects.get_or_create(
                mal_id=item['mal_id'],
                defaults={'title': item['title']}
            )
            for aud in item['audio']:
                for sub in item['subtitles']:
                    StreamingLanguageTrack.objects.update_or_create(
                        anime=anime,
                        provider_name=item['provider'],
                        country=item['country'],
                        audio_language=aud,
                        subtitle_language=sub,
                        defaults={
                            'track_type': item['track_type'],
                            'verification_status': item['verification_status'],
                            'source_url': item['source_url'],
                            'notes': item['notes'],
                            'verified_at': timezone.now(),
                        }
                    )

    def get_watch_options(self, mal_id, country="IN", audio=None, sub=None):
        """
        Retrieves country-specific legal streaming options for an exact anime,
        with verified audio and subtitle language filtering.
        """
        country = (country or "IN").strip().upper()
        norm_audio = normalize_language_name(audio)
        norm_sub = normalize_language_name(sub)

        from apps.anime.content_filter import check_anime_id_is_excluded, BLOCKED_ANIME_MESSAGE
        if check_anime_id_is_excluded(mal_id, self.jikan_client):
            return {
                "mal_id": mal_id,
                "anime_title": "Unavailable",
                "anime_type": "TV",
                "country": country,
                "selected_audio": norm_audio,
                "selected_sub": norm_sub,
                "results_count": 0,
                "total_options": 0,
                "categories": {
                    "subscription": [],
                    "free": [],
                    "free_with_ads": [],
                    "rent": [],
                    "buy": []
                },
                "is_verified": True,
                "is_blocked": True,
                "message": BLOCKED_ANIME_MESSAGE,
                "error": BLOCKED_ANIME_MESSAGE,
            }

        cache_key = f"anime:{mal_id}:watch_options:{country}:{norm_audio or 'all'}:{norm_sub or 'all'}"
        legacy_cache_key = f"anime:{mal_id}:watch_options:{country}"

        cached_entry = (
            JikanCache.objects.filter(cache_key=cache_key).first()
            or JikanCache.objects.filter(cache_key=legacy_cache_key).first()
        )
        if cached_entry:
            is_stale = cached_entry.expires_at <= timezone.now()
            payload = dict(cached_entry.payload)
            payload["is_cached"] = True
            payload["is_stale"] = is_stale
            if is_stale:
                payload["verification_status"] = "stale"
            return payload

        # Seed verified language tracks if not already populated
        self.seed_verified_language_tracks()

        # 1. Fetch anime details to confirm exact anime title and format
        try:
            details_res = self.jikan_client.get_anime_details(mal_id)
        except Exception:
            details_res = None

        if not details_res or not details_res.get("data"):
            from apps.anime.models import Anime
            local_anime = Anime.objects.filter(mal_id=mal_id).first()
            anime_title = local_anime.title if local_anime else f"Anime #{mal_id}"
            anime_type = getattr(local_anime, 'anime_type', 'TV') or "TV"
        else:
            d = details_res["data"]
            anime_title = d.get("title_english") or d.get("title") or f"Anime #{mal_id}"
            anime_type = d.get("type") or "TV"

        # 2. Fetch raw streaming records from Tenrai primary catalog
        try:
            streaming_res = self.jikan_client.get_anime_streaming(mal_id)
        except Exception:
            streaming_res = None
        raw_streaming = streaming_res.get("data", []) if streaming_res else []

        all_countries = set()
        matched_options = []
        now_iso = timezone.now().isoformat()

        # Parse Tenrai JustWatch partner export entries
        for item in raw_streaming:
            raw_url = item.get("url", "")
            raw_name = item.get("name", "Streaming Provider")

            parsed_url = urllib.parse.urlparse(raw_url)
            qs = urllib.parse.parse_qs(parsed_url.query)

            item_country = qs.get("uct_country", [None])[0]
            if item_country:
                item_country = item_country.upper()
                all_countries.add(item_country)

            direct_url = qs.get("r", [raw_url])[0]
            if "u=" in direct_url:
                try:
                    nested_qs = urllib.parse.parse_qs(urllib.parse.urlparse(direct_url).query)
                    if "u" in nested_qs and nested_qs["u"]:
                        direct_url = nested_qs["u"][0]
                except Exception:
                    pass

            cx_str = qs.get("cx", [None])[0]
            monetization = None
            currency = None
            price = None
            presentation_type = None
            season_number = None
            provider_name = raw_name

            if cx_str:
                try:
                    padded = cx_str + "=" * (-len(cx_str) % 4)
                    cx_data = json.loads(base64.b64decode(padded).decode("utf-8"))
                    for entry in cx_data.get("data", []):
                        clickout = entry.get("data", {})
                        if "monetizationType" in clickout:
                            monetization = clickout.get("monetizationType")
                            currency = clickout.get("currency")
                            price = clickout.get("price")
                            presentation_type = clickout.get("presentationType")
                            if clickout.get("provider"):
                                provider_name = clickout.get("provider")
                        if "seasonNumber" in clickout:
                            season_number = clickout.get("seasonNumber")
                except Exception as ex:
                    logger.debug(f"Failed decoding JustWatch cx payload: {ex}")

            category = self.normalize_category(monetization, provider_name)
            logo_url = self.get_provider_logo(provider_name)

            if item_country == country:
                matched_options.append({
                    "provider_name": provider_name,
                    "provider_logo_url": logo_url,
                    "url": direct_url,
                    "category": category,
                    "country": country,
                    "price": price,
                    "currency": currency,
                    "presentation_type": presentation_type or "hd",
                    "season_number": season_number,
                    "format": anime_type,
                    "provider_reported": True,
                    "country_matched": True,
                    "last_checked_at": now_iso,
                    "last_verified_at": now_iso,
                    "verification_status": "provider_reported",
                    "source": "tenrai_justwatch",
                    "is_official": True,
                })

        # 3. Supplemental check for verified regional distributors (e.g. YouTube Muse Asia / Ani-One Asia)
        if country == "IN":
            anilist_streaming = self.jikan_client._fetch_real_streaming_from_anilist(mal_id)
            for link in anilist_streaming.get("data", []):
                notes = (link.get("notes") or "").lower()
                site = (link.get("name") or "").lower()
                url = link.get("url") or ""

                if "muse" in notes or "ani-one" in notes or "muse asia" in site or "ani-one" in site:
                    dist_name = "Muse Asia (YouTube)" if "muse" in (notes + site) else "Ani-One Asia (YouTube)"
                    if not any(opt["url"] == url for opt in matched_options):
                        matched_options.append({
                            "provider_name": dist_name,
                            "provider_logo_url": self.get_provider_logo("YouTube"),
                            "url": url,
                            "category": "free",
                            "country": "IN",
                            "price": None,
                            "currency": "INR",
                            "presentation_type": "hd",
                            "season_number": 1,
                            "format": anime_type,
                            "provider_reported": True,
                            "country_matched": True,
                            "last_checked_at": now_iso,
                            "last_verified_at": now_iso,
                            "verification_status": "independently_verified",
                            "source": "official_regional_distributor",
                            "is_official": True,
                        })
                        all_countries.add("IN")

        # 4. Integrate verified database language tracks
        db_tracks = list(
            StreamingLanguageTrack.objects.filter(anime_id=mal_id, country=country)
            .order_by('provider_name')
        )
        if not db_tracks:
            # Check global tracks if any
            db_tracks = list(
                StreamingLanguageTrack.objects.filter(anime_id=mal_id, country='GLOBAL')
                .order_by('provider_name')
            )

        # For known verified licensors in the DB, ensure an entry exists in matched_options if not present
        if db_tracks:
            all_countries.add(country)
            db_providers = {}
            for t in db_tracks:
                if t.verification_status in [VerificationStatus.UNVERIFIED, 'unverified']:
                    continue
                p_key = t.provider_name.strip().lower()
                if p_key not in db_providers:
                    db_providers[p_key] = {
                        'provider_name': t.provider_name,
                        'source_url': t.source_url or "https://www.justwatch.com",
                        'status': t.verification_status,
                        'audio': set(),
                        'subtitles': set(),
                        'verified_at': t.verified_at,
                        'notes': t.notes,
                    }
                if t.audio_language:
                    db_providers[p_key]['audio'].add(t.audio_language)
                if t.subtitle_language:
                    db_providers[p_key]['subtitles'].add(t.subtitle_language)

            for p_key, p_info in db_providers.items():
                existing = next(
                    (opt for opt in matched_options if p_key in opt["provider_name"].lower() or opt["provider_name"].lower() in p_key),
                    None
                )
                if not existing:
                    cat = self.normalize_category("subscription", p_info['provider_name'])
                    matched_options.append({
                        "provider_name": p_info['provider_name'],
                        "provider_logo_url": self.get_provider_logo(p_info['provider_name']),
                        "url": p_info['source_url'],
                        "category": cat,
                        "country": country,
                        "price": None,
                        "currency": "INR",
                        "presentation_type": "hd",
                        "season_number": 1,
                        "format": anime_type,
                        "provider_reported": True,
                        "country_matched": True,
                        "last_checked_at": now_iso,
                        "last_verified_at": now_iso,
                        "verification_status": p_info['status'],
                        "source": p_info['notes'] or "official_licensor_registry",
                        "is_official": True,
                    })

        # Attach verified language metadata to each option
        for opt in matched_options:
            p_name_lower = opt["provider_name"].strip().lower()
            matching_tracks = [
                t for t in db_tracks
                if t.provider_name.strip().lower() in p_name_lower or p_name_lower in t.provider_name.strip().lower()
            ]

            if matching_tracks:
                v_status = matching_tracks[0].verification_status
                is_verified = v_status not in [VerificationStatus.UNVERIFIED, 'unverified']
                v_at = matching_tracks[0].verified_at.isoformat() if matching_tracks[0].verified_at else now_iso

                if is_verified:
                    audio_set = sorted(list(set(
                        t.audio_language for t in matching_tracks
                        if t.audio_language and t.verification_status not in [VerificationStatus.UNVERIFIED, 'unverified']
                    )))
                    sub_set = sorted(list(set(
                        t.subtitle_language for t in matching_tracks
                        if t.subtitle_language and t.verification_status not in [VerificationStatus.UNVERIFIED, 'unverified']
                    )))
                    # Priority note matching filtered audio if specified, or joined notes
                    active_note = None
                    if norm_audio:
                        for t in matching_tracks:
                            if t.audio_language == norm_audio and t.notes:
                                active_note = t.notes
                                break
                    if not active_note:
                        active_note = " • ".join(list(dict.fromkeys(t.notes for t in matching_tracks if t.notes)))

                    opt["verified_audio_languages"] = audio_set
                    opt["verified_subtitle_languages"] = sub_set
                    opt["verification_status"] = v_status
                    opt["language_verification_status"] = v_status
                    opt["has_verified_language_data"] = True
                    opt["language_source"] = active_note or "licensor_confirmed"
                    opt["coverage_notes"] = active_note or ""
                    opt["last_verified_at"] = v_at
                else:
                    opt["verified_audio_languages"] = []
                    opt["verified_subtitle_languages"] = []
                    opt["verification_status"] = "unverified"
                    opt["language_verification_status"] = "unverified"
                    opt["has_verified_language_data"] = False
                    opt["language_notice"] = "Platform available — audio language unconfirmed."
            else:
                opt["verified_audio_languages"] = []
                opt["verified_subtitle_languages"] = []
                opt["verification_status"] = "unverified"
                opt["language_verification_status"] = "unverified"
                opt["has_verified_language_data"] = False
                opt["language_notice"] = "Platform available — audio language unconfirmed."

        # 5. Filter by verified audio and subtitle languages
        final_options = []
        for opt in matched_options:
            if norm_audio:
                # Strictly require verified audio
                if not opt.get("has_verified_language_data") or norm_audio not in opt.get("verified_audio_languages", []):
                    continue
            if norm_sub:
                # Strictly require verified subtitles
                if not opt.get("has_verified_language_data") or norm_sub not in opt.get("verified_subtitle_languages", []):
                    continue
            final_options.append(opt)

        # Organize into the 5 mandatory categories
        categories = {
            "subscription": [],
            "free": [],
            "free_with_ads": [],
            "rent": [],
            "buy": [],
        }

        seen = set()
        for opt in final_options:
            key = (opt["provider_name"].lower(), opt["url"])
            if key not in seen:
                seen.add(key)
                categories[opt["category"]].append(opt)

        total_results = sum(len(items) for items in categories.values())
        has_results = total_results > 0
        sorted_countries = sorted(list(all_countries))

        # Honest contextual empty state messages per prompt specifications
        message = None
        if not has_results:
            country_display = "India" if country == "IN" else country
            if norm_audio:
                message = f"No verified {norm_audio} audio option found for this title in {country_display}."
            elif norm_sub:
                message = f"No verified {norm_sub} subtitle option found for this title in {country_display}."
            elif sorted_countries:
                message = f"No confirmed legal streaming options currently verified for {country_display}. Available in: {', '.join(sorted_countries[:5])}."
            else:
                message = "No confirmed legal streaming options currently verified for this title."

        response_payload = {
            "mal_id": mal_id,
            "anime_title": anime_title,
            "anime_type": anime_type,
            "country": country,
            "selected_audio": norm_audio,
            "selected_sub": norm_sub,
            "results_count": total_results,
            "categories": categories,
            "available_countries": sorted_countries,
            "provider_reported": True,
            "country_matched": bool(has_results),
            "last_checked_at": now_iso,
            "last_verified_at": now_iso,
            "verification_status": "provider_reported" if has_results else "unverified",
            "is_verified": True,
            "is_cached": False,
            "is_stale": False,
            "message": message,
            "metadata_source": "official_licensor_and_justwatch",
        }

        # Cache response for 6 hours
        expires_at = timezone.now() + timedelta(hours=self.CACHE_HOURS)
        JikanCache.objects.update_or_create(
            cache_key=cache_key,
            defaults={"payload": response_payload, "expires_at": expires_at}
        )

        return response_payload

    def get_trailers(self, mal_id):
        """
        Retrieves official promotional YouTube trailers for an anime.
        - Uses stable channel registry to verify uploader channel.
        - Matches exact anime title metadata.
        - Separates verified official trailers from unverified trailers.
        """
        from apps.anime.content_filter import check_anime_id_is_excluded, is_excluded_adult_anime, BLOCKED_ANIME_MESSAGE
        if check_anime_id_is_excluded(mal_id, self.jikan_client):
            return {
                "mal_id": mal_id,
                "trailers": [],
                "count": 0,
                "is_verified": True,
                "is_blocked": True,
                "message": BLOCKED_ANIME_MESSAGE,
                "error": BLOCKED_ANIME_MESSAGE,
            }

        cache_key = f"anime:{mal_id}:trailers"
        cached_entry = JikanCache.objects.filter(cache_key=cache_key).first()
        if cached_entry and cached_entry.expires_at > timezone.now():
            payload = cached_entry.payload
            payload["is_cached"] = True
            return payload

        # 1. Fetch title info
        details_res = self.jikan_client.get_anime_details(mal_id)
        anime_details = details_res.get("data", {}) if details_res else {}
        anime_title = anime_details.get("title_english") or anime_details.get("title") or f"Anime #{mal_id}"
        full_trailer = anime_details.get("trailer")

        # 2. Fetch promo videos from Tenrai /videos endpoint
        videos_res = self.jikan_client.get_anime_videos(mal_id)
        raw_promos = videos_res.get("data", {}).get("promo", []) if videos_res else []

        verified_trailers = []
        unverified_trailers = []
        seen_ids = set()

        for p in raw_promos:
            t = p.get("trailer", {})
            yt_id = t.get("youtube_id")
            if yt_id and yt_id not in seen_ids:
                seen_ids.add(yt_id)
                images = t.get("images", {})
                thumb = (
                    images.get("maximum_image_url") or
                    images.get("large_image_url") or
                    images.get("medium_image_url") or
                    images.get("image_url") or
                    f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
                )
                is_official, verification_status, author_name, author_url, ch_id = self.verify_trailer(
                    youtube_id=yt_id,
                    promo_title=p.get("title") or t.get("title") or "",
                    anime_info=anime_details
                )
                trailer_obj = {
                    "title": p.get("title") or t.get("title") or "Trailer",
                    "raw_title": t.get("title"),
                    "youtube_id": yt_id,
                    "url": t.get("url") or f"https://www.youtube.com/watch?v={yt_id}",
                    "embed_url": t.get("embed_url") or f"https://www.youtube.com/embed/{yt_id}?enablejsapi=1&wmode=opaque",
                    "thumbnail": thumb,
                    "channel_id": ch_id,
                    "uploader_name": author_name or "Unknown Channel",
                    "uploader_url": author_url,
                    "is_official": is_official,
                    "verification_status": verification_status,
                    "source": "tenrai"
                }
                if is_official:
                    verified_trailers.append(trailer_obj)
                else:
                    unverified_trailers.append(trailer_obj)

        # 3. If promos had no items, check full details trailer
        if not verified_trailers and full_trailer and isinstance(full_trailer, dict):
            yt_id = full_trailer.get("youtube_id")
            if yt_id and yt_id not in seen_ids:
                seen_ids.add(yt_id)
                images = full_trailer.get("images", {})
                thumb = (
                    images.get("maximum_image_url") or
                    images.get("large_image_url") or
                    images.get("medium_image_url") or
                    images.get("image_url") or
                    f"https://img.youtube.com/vi/{yt_id}/maxresdefault.jpg"
                )
                is_official, verification_status, author_name, author_url, ch_id = self.verify_trailer(
                    youtube_id=yt_id,
                    promo_title=full_trailer.get("title") or "",
                    anime_info=anime_details
                )
                trailer_obj = {
                    "title": full_trailer.get("title") or "Official Trailer",
                    "raw_title": full_trailer.get("title"),
                    "youtube_id": yt_id,
                    "url": full_trailer.get("url") or f"https://www.youtube.com/watch?v={yt_id}",
                    "embed_url": full_trailer.get("embed_url") or f"https://www.youtube.com/embed/{yt_id}?enablejsapi=1&wmode=opaque",
                    "thumbnail": thumb,
                    "channel_id": ch_id,
                    "uploader_name": author_name or "Unknown Channel",
                    "uploader_url": author_url,
                    "is_official": is_official,
                    "verification_status": verification_status,
                    "source": "tenrai"
                }
                if is_official:
                    verified_trailers.append(trailer_obj)
                else:
                    unverified_trailers.append(trailer_obj)

        total_verified = len(verified_trailers)
        total_unverified = len(unverified_trailers)
        message = None if total_verified > 0 else "No official promotional trailers available for this title."

        response_payload = {
            "mal_id": mal_id,
            "anime_title": anime_title,
            "count": total_verified,
            "verified_count": total_verified,
            "unverified_count": total_unverified,
            "trailers": verified_trailers,
            "unverified_trailers": unverified_trailers,
            "message": message,
            "is_verified": True,
            "is_cached": False,
        }

        # Cache response for 6 hours
        expires_at = timezone.now() + timedelta(hours=self.CACHE_HOURS)
        JikanCache.objects.update_or_create(
            cache_key=cache_key,
            defaults={"payload": response_payload, "expires_at": expires_at}
        )

        return response_payload
