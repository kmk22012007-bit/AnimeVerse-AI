import logging
import json
import re
from collections import Counter
from django.utils import timezone
from apps.ryuk.models import AIConversation, AIMessage
from apps.ryuk.ai_client import AIClientFactory
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.anime.models import Anime, JikanCache
from apps.anime.jikan_client import JikanClient
from apps.anime.content_filter import is_excluded_adult_anime, filter_anime_list

logger = logging.getLogger(__name__)

RYUK_RECOMMENDATION_SYSTEM_PROMPT = """
You are RYUK, the observant, anime-savvy companion of AnimeVerse AI.
Your personality is sharp, observant, perceptive, and witty. You notice subtle storytelling tropes, directorial styles, and thematic connections.

Task:
You are provided with a user's anime taste profile (favorite titles, ratings, favorite genres, favorite studios) and a list of verified candidate anime titles.
For each candidate anime, write a compelling, concise 1-2 sentence rationale explaining why THIS specific user will enjoy it based on their tracked tastes.

Rules:
1. Speak in RYUK's iconic voice: insightful, slightly playful, but genuinely knowledgeable about anime lore and narrative craft.
2. Directly reference the user's specific favorite titles, studios, or themes when explaining the link.
3. Strictly avoid major spoilers.
4. Never invent fake plotlines, characters, release dates, or ratings.
5. Output MUST be valid JSON mapping each anime's MAL ID (as string) to its rationale string.
Format:
{"rationales": {"1535": "Because you rated Code Geass 9/10, this tactical battle of wits between Light and L will satisfy your craving for psychological chess matches."}}
"""

# Major standard anime genres for discovery and diversity analysis
POPULAR_ANIME_GENRES = [
    'Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy',
    'Mystery', 'Psychological', 'Romance', 'Sci-Fi',
    'Slice of Life', 'Sports', 'Supernatural', 'Suspense'
]

# Gateway anime for users with empty or very small watchlists
STARTER_GATEWAY_ANIME = [
    {
        'mal_id': 1535,
        'title': 'Death Note',
        'title_english': 'Death Note',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/9/9453.jpg',
        'anime_type': 'TV',
        'total_episodes': 37,
        'score': 8.62,
        'genres': ['Supernatural', 'Suspense', 'Psychological'],
        'studios': ['Madhouse'],
        'synopsis': 'A high school prodigy discovers a notebook that grants the ability to kill anyone whose name is written in it, sparking a high-stakes duel against a mysterious detective.',
    },
    {
        'mal_id': 5114,
        'title': 'Fullmetal Alchemist: Brotherhood',
        'title_english': 'Fullmetal Alchemist: Brotherhood',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/1223/96541.jpg',
        'anime_type': 'TV',
        'total_episodes': 64,
        'score': 9.10,
        'genres': ['Action', 'Adventure', 'Drama', 'Fantasy'],
        'studios': ['Bones'],
        'synopsis': 'Two brothers search for the Philosopher\'s Stone to restore their bodies after a disastrous failed alchemy experiment.',
    },
    {
        'mal_id': 16498,
        'title': 'Shingeki no Kyojin',
        'title_english': 'Attack on Titan',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/10/47347.jpg',
        'anime_type': 'TV',
        'total_episodes': 25,
        'score': 8.55,
        'genres': ['Action', 'Drama', 'Suspense', 'Mystery'],
        'studios': ['Wit Studio'],
        'synopsis': 'Humanity struggles for survival inside three concentric walls shielding them from gigantic human-eating humanoid Titans.',
    },
    {
        'mal_id': 52991,
        'title': 'Sousou no Frieren',
        'title_english': "Frieren: Beyond Journey's End",
        'poster_url': 'https://cdn.myanimelist.net/images/anime/1015/138062.jpg',
        'anime_type': 'TV',
        'total_episodes': 28,
        'score': 9.30,
        'genres': ['Adventure', 'Drama', 'Fantasy'],
        'studios': ['Madhouse'],
        'synopsis': 'An elf mage reflects on mortality and her former companions during a pilgrimage years after defeating the Demon King.',
    },
    {
        'mal_id': 9253,
        'title': 'Steins;Gate',
        'title_english': 'Steins;Gate',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/1935/127974.jpg',
        'anime_type': 'TV',
        'total_episodes': 24,
        'score': 9.07,
        'genres': ['Drama', 'Sci-Fi', 'Suspense', 'Psychological'],
        'studios': ['White Fox'],
        'synopsis': 'A self-proclaimed mad scientist invents a microwave that can send text messages into the past, unraveling a dangerous global conspiracy.',
    },
    {
        'mal_id': 199,
        'title': 'Sen to Chihiro no Kamikakushi',
        'title_english': 'Spirited Away',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/6/79597.jpg',
        'anime_type': 'Movie',
        'total_episodes': 1,
        'score': 8.78,
        'genres': ['Adventure', 'Award Winning', 'Supernatural', 'Fantasy'],
        'studios': ['Studio Ghibli'],
        'synopsis': 'A young girl enters an enchanted spirit realm and must work in a bathhouse to free her parents who were turned into pigs.',
    },
    {
        'mal_id': 38000,
        'title': 'Kimetsu no Yaiba',
        'title_english': 'Demon Slayer: Kimetsu no Yaiba',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/1286/99889.jpg',
        'anime_type': 'TV',
        'total_episodes': 26,
        'score': 8.48,
        'genres': ['Action', 'Fantasy', 'Historical'],
        'studios': ['ufotable'],
        'synopsis': 'A kindhearted boy becomes a demon slayer after his family is slaughtered and his sister transformed into a demon.',
    },
    {
        'mal_id': 32281,
        'title': 'Kimi no Na wa.',
        'title_english': 'Your Name.',
        'poster_url': 'https://cdn.myanimelist.net/images/anime/1915/113883.jpg',
        'anime_type': 'Movie',
        'total_episodes': 1,
        'score': 8.84,
        'genres': ['Drama', 'Supernatural', 'Romance'],
        'studios': ['CoMix Wave Films'],
        'synopsis': 'Two high schoolers inexplicably begin intermittently swapping bodies across distance and time, bound by a looming cosmic secret.',
    },
]


class RyukRecommendationEngine:
    """
    Intelligent anime recommendation engine powered by user tracking data,
    metadata synergy, and RYUK AI context generation.
    """

    def __init__(self, ai_provider=..., jikan_client=None):
        if ai_provider is Ellipsis:
            self.ai_provider = AIClientFactory.get_provider()
        else:
            self.ai_provider = ai_provider
        self.jikan_client = jikan_client or JikanClient()

    def analyze_user_preferences(self, user):
        """
        Deeply inspects the user's completed, watching, rated, and favorite titles.
        Extracts genre frequency, studio affinities, and top-rated reference anime.
        """
        user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
            .order_by('-updated_at')
        )
        valid_entries = [e for e in user_entries if not is_excluded_adult_anime(e.anime)]

        completed_ids = set(e.anime.mal_id for e in valid_entries if e.status == WatchStatus.COMPLETED)
        watching_ids = set(e.anime.mal_id for e in valid_entries if e.status == WatchStatus.WATCHING)
        all_tracked_ids = set(e.anime.mal_id for e in valid_entries)

        # High scoring titles (rating >= 7 or completed with high engagement)
        rated_entries = [e for e in valid_entries if e.rating is not None and e.rating >= 7]
        rated_entries.sort(key=lambda x: x.rating, reverse=True)

        top_rated_titles = [f"{e.anime.title} ({e.rating}/10)" for e in rated_entries[:5]]
        top_rated_mal_ids = [e.anime.mal_id for e in rated_entries[:5]]

        # Extract genres and studios from cache or upstream details
        genre_counter = Counter()
        studio_counter = Counter()

        for entry in valid_entries[:15]:
            mal_id = entry.anime.mal_id
            cached = JikanCache.objects.filter(cache_key=f"anime:{mal_id}:full").first()
            if cached and isinstance(cached.payload, dict) and 'data' in cached.payload:
                d = cached.payload['data']
                genres = d.get('genres', [])
                for g in genres:
                    name = g.get('name') if isinstance(g, dict) else str(g)
                    if name and name.lower() not in ('hentai', 'erotica'):
                        genre_counter[name] += 2 if (entry.rating and entry.rating >= 8) else 1

                studios = d.get('studios', [])
                for s in studios:
                    s_name = s.get('name') if isinstance(s, dict) else str(s)
                    if s_name:
                        studio_counter[s_name] += 2 if (entry.rating and entry.rating >= 8) else 1

        favorite_genres = [g for g, _ in genre_counter.most_common(5)]
        favorite_studios = [s for s, _ in studio_counter.most_common(3)]

        # Determine underrepresented / unexplored genres for "discovery" mode
        top_genres_lower = set(g.lower() for g in favorite_genres)
        unexplored_genres = [
            g for g in POPULAR_ANIME_GENRES
            if g.lower() not in top_genres_lower
        ]

        return {
            'has_watch_history': len(valid_entries) > 0,
            'total_tracked': len(valid_entries),
            'completed_count': len(completed_ids),
            'watching_count': len(watching_ids),
            'completed_ids': completed_ids,
            'watching_ids': watching_ids,
            'all_tracked_ids': all_tracked_ids,
            'favorite_genres': favorite_genres,
            'favorite_studios': favorite_studios,
            'unexplored_genres': unexplored_genres,
            'top_rated_titles': top_rated_titles,
            'top_rated_mal_ids': top_rated_mal_ids,
        }

    def get_candidate_pool(self, user_profile, requested_genre=None, mode='personalized', limit=12):
        """
        Retrieves real, verified candidate anime while strictly excluding:
        1. Completed or currently watching anime
        2. Excluded adult anime (hentai/erotica)

        Supports two modes:
        - 'personalized': prioritizes user's highest rated genres and related anime.
        - 'different': pulls acclaimed gems from unexplored/unrepresented genres.
        """
        candidates = {}
        # Strictly exclude anime user is already watching or has completed
        excluded_ids = user_profile['completed_ids'] | user_profile['watching_ids']

        # 0. If user has NO watch history, directly return the curated STARTER_GATEWAY_ANIME
        if not user_profile['has_watch_history']:
            for starter in STARTER_GATEWAY_ANIME:
                mal_id = starter['mal_id']
                if mal_id not in excluded_ids:
                    candidates[mal_id] = starter.copy()
            return list(candidates.values())[:limit]

        # 1. Mode: 'different' (Serendipitous Exploration)
        if mode == 'different' and user_profile.get('unexplored_genres'):
            target_genre = requested_genre or user_profile['unexplored_genres'][0]
            try:
                browse_res = self.jikan_client.browse_anime(genre=target_genre, min_score=8.0, page=1)
                if browse_res and browse_res.get('data'):
                    for item in browse_res['data']:
                        mal_id = item.get('mal_id')
                        if mal_id and mal_id not in excluded_ids and not is_excluded_adult_anime(item):
                            candidates[mal_id] = self._normalize_candidate(item)
            except Exception as e:
                logger.warning(f"Error fetching exploratory genre candidates: {e}")

        # 2. Mode: 'personalized' (Default) - Target or favorite genre
        else:
            target_genre = requested_genre or (user_profile['favorite_genres'][0] if user_profile['favorite_genres'] else None)
            if target_genre:
                try:
                    browse_res = self.jikan_client.browse_anime(genre=target_genre, min_score=7.8, page=1)
                    if browse_res and browse_res.get('data'):
                        for item in browse_res['data']:
                            mal_id = item.get('mal_id')
                            if mal_id and mal_id not in excluded_ids and not is_excluded_adult_anime(item):
                                candidates[mal_id] = self._normalize_candidate(item)
                except Exception as e:
                    logger.warning(f"Error fetching candidate genre anime: {e}")

        # 3. If user has top-rated anime, check relations/sequels/spin-offs from cache
        for top_id in user_profile['top_rated_mal_ids'][:2]:
            try:
                cached_full = JikanCache.objects.filter(cache_key=f"anime:{top_id}:full").first()
                if cached_full and isinstance(cached_full.payload, dict) and 'data' in cached_full.payload:
                    data = cached_full.payload['data']
                    relations = data.get('relations', [])
                    for rel in relations:
                        for entry in rel.get('entry', []):
                            entry_mal_id = entry.get('mal_id')
                            if (
                                entry_mal_id
                                and entry_mal_id not in excluded_ids
                                and entry.get('type') == 'anime'
                                and not is_excluded_adult_anime(entry)
                            ):
                                rel_cache = JikanCache.objects.filter(cache_key=f"anime:{entry_mal_id}:full").first()
                                if rel_cache and isinstance(rel_cache.payload, dict) and 'data' in rel_cache.payload:
                                    candidates[entry_mal_id] = self._normalize_candidate(rel_cache.payload['data'])
            except Exception as e:
                logger.warning(f"Error checking cached relations for MAL {top_id}: {e}")

        # 4. Add trending / top anime candidates to ensure high variety
        try:
            trending = self.jikan_client.get_trending_anime(page=1)
            if trending and trending.get('data'):
                for item in trending['data']:
                    mal_id = item.get('mal_id')
                    if mal_id and mal_id not in excluded_ids and not is_excluded_adult_anime(item):
                        if mal_id not in candidates:
                            candidates[mal_id] = self._normalize_candidate(item)
        except Exception as e:
            logger.warning(f"Error fetching trending candidates: {e}")

        # 5. Fallback / Gateway candidates if pool is still small
        for starter in STARTER_GATEWAY_ANIME:
            mal_id = starter['mal_id']
            if mal_id not in excluded_ids and mal_id not in candidates:
                candidates[mal_id] = starter.copy()

        # Filter all candidates strictly against adult safety
        safe_candidates = [
            c for c in candidates.values()
            if not is_excluded_adult_anime(c)
        ]

        return safe_candidates[:limit]

    def _normalize_candidate(self, item):
        """Converts raw Jikan item into clean candidate object with genres, studios, and score."""
        card = self.jikan_client.normalize_poster_card(item)
        genres = []
        raw_genres = item.get('genres', [])
        for g in raw_genres:
            if isinstance(g, dict):
                genres.append(g.get('name', ''))
            elif isinstance(g, str):
                genres.append(g)

        studios = []
        raw_studios = item.get('studios', [])
        for s in raw_studios:
            if isinstance(s, dict):
                studios.append(s.get('name', ''))
            elif isinstance(s, str):
                studios.append(s)

        synopsis = item.get('synopsis') or "No synopsis available."
        if len(synopsis) > 280:
            synopsis = synopsis[:277] + "..."

        return {
            'mal_id': card['mal_id'],
            'title': card['title'],
            'title_english': card['title_english'],
            'poster_url': card['poster_url'],
            'anime_type': card['anime_type'] or 'TV',
            'total_episodes': card['total_episodes'],
            'score': card['score'] or 7.5,
            'genres': genres,
            'studios': studios,
            'synopsis': synopsis,
            'metadata_source': card.get('metadata_source', 'tenrai'),
        }

    def calculate_relevance(self, candidate, user_profile, mode='personalized'):
        """
        Computes match percentage, confidence tier, and specific reason chips based on:
        - Community score baseline
        - Genre affinity overlap
        - Studio affinity match
        - High-tier rating bonuses
        """
        score = candidate.get('score') or 7.5
        # Base between 68 and 84 based on score
        base_match = min(84, max(68, int(score * 9.2)))

        c_genres_lower = [g.lower() for g in candidate.get('genres', [])]
        user_genres = user_profile.get('favorite_genres', [])
        shared_genres = [g for g in user_genres if g.lower() in c_genres_lower]

        # Calculate genre bonus
        genre_bonus = min(15, len(shared_genres) * 5)

        # Studio affinity bonus (+3 if candidate studio matches user favorite)
        c_studios_lower = [s.lower() for s in candidate.get('studios', [])]
        user_studios = user_profile.get('favorite_studios', [])
        shared_studios = [s for s in user_studios if s.lower() in c_studios_lower]
        studio_bonus = 3 if shared_studios else 0

        # Rating tier bonus
        score_bonus = 4 if score >= 8.5 else (2 if score >= 8.0 else 0)

        match_percentage = min(99, max(72, base_match + genre_bonus + studio_bonus + score_bonus))

        # Confidence tier (avoiding presentation of scores as scientific probabilities)
        if match_percentage >= 90:
            confidence_tier = "Very High Affinity"
        elif match_percentage >= 83:
            confidence_tier = "High Affinity"
        elif match_percentage >= 76:
            confidence_tier = "Strong Match"
        else:
            confidence_tier = "Curated Match"

        matched_reasons = []
        if mode == 'different':
            matched_reasons.append(f"Broadens your journey with acclaimed {', '.join(candidate.get('genres', [])[:2])}")
        elif shared_genres:
            matched_reasons.append(f"Matches your affinity for {', '.join(shared_genres[:2])}")

        if shared_studios:
            matched_reasons.append(f"From acclaimed studio {shared_studios[0]}")
        elif score >= 8.5:
            matched_reasons.append(f"Acclaimed {score}/10 community rating")

        if candidate.get('anime_type') == 'Movie':
            matched_reasons.append("Stand-alone cinematic masterwork")
        elif not matched_reasons:
            matched_reasons.append(f"Highly popular {candidate.get('anime_type', 'TV')} series")

        return match_percentage, confidence_tier, matched_reasons

    def generate_rationales(self, candidates, user_profile, mode='personalized'):
        """
        Generates contextual explanations in RYUK's iconic voice.
        Attempts Gemini AI invocation first; falls back gracefully to
        intelligent heuristic generation if AI is unconfigured, times out, or fails.
        """
        rationales = {}
        ai_success = False

        if self.ai_provider:
            try:
                candidate_snippets = []
                for c in candidates:
                    studios_str = f", Studio: {', '.join(c.get('studios', []))}" if c.get('studios') else ""
                    snippet = f"ID {c['mal_id']}: '{c['title']}' ({c.get('anime_type', 'TV')}, Genres: {', '.join(c.get('genres', []))}{studios_str}, Score: {c.get('score')}). Premise: {c.get('synopsis')}"
                    candidate_snippets.append(snippet)

                prompt = (
                    f"User Watch Profile:\n"
                    f"- Favorite Titles: {', '.join(user_profile['top_rated_titles']) or 'New anime enthusiast with diverse curiosity'}\n"
                    f"- Preferred Genres: {', '.join(user_profile['favorite_genres']) or 'All popular genres'}\n"
                    f"- Preferred Studios: {', '.join(user_profile.get('favorite_studios', [])) or 'Various'}\n"
                    f"- Recommendation Mode: {'Genre Diversity / Something Different' if mode == 'different' else 'Personalized Alignment'}\n"
                    f"- Watchlist Size: {user_profile['total_tracked']} tracked series\n\n"
                    f"Candidate Anime Titles:\n"
                    + "\n".join(candidate_snippets)
                    + "\n\nProvide the JSON with a rationale for each candidate ID."
                )

                response_text = self.ai_provider.generate_response(
                    prompt=prompt,
                    system_instruction=RYUK_RECOMMENDATION_SYSTEM_PROMPT,
                    timeout=5.0
                )

                json_str = response_text.strip()
                match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    r_map = parsed.get('rationales', parsed)
                    for c in candidates:
                        mid_str = str(c['mal_id'])
                        if mid_str in r_map and isinstance(r_map[mid_str], str) and len(r_map[mid_str]) > 10:
                            rationales[c['mal_id']] = r_map[mid_str].strip()
                    if rationales:
                        ai_success = True
            except Exception as e:
                logger.warning(f"Gemini rationale generation failed or timed out: {e}. Using RYUK heuristic fallback.")

        # Heuristic fallback for any candidate missing an AI rationale
        for c in candidates:
            mal_id = c['mal_id']
            if mal_id not in rationales:
                rationales[mal_id] = self._build_heuristic_rationale(c, user_profile, mode=mode)

        return rationales, ai_success

    def _build_heuristic_rationale(self, candidate, user_profile, mode='personalized'):
        """Constructs an intelligent, natural RYUK rationale grounded in genuine user data."""
        title = candidate['title']
        genres = candidate.get('genres', [])
        score = candidate.get('score') or 7.5
        top_titles = user_profile.get('top_rated_titles', [])

        if mode == 'different':
            return (
                f"Curated as a compelling departure from your usual rotation: {title} "
                f"({score}/10) offers a masterful introduction to {', '.join(genres[:2]) or 'new narrative horizons'}."
            )

        if top_titles:
            ref_title = top_titles[0].split('(')[0].strip()
            if any(g.lower() in ['action', 'supernatural', 'fantasy'] for g in genres):
                return f"Since you loved {ref_title}, RYUK picked {title} for its extraordinary kinetic animation, supernatural stakes, and relentlessly gripping narrative arc."
            elif any(g.lower() in ['suspense', 'psychological', 'mystery'] for g in genres):
                return f"Echoing your appreciation for {ref_title}, {title} delivers a cerebral, nail-biting cat-and-mouse dynamic where every second counts."
            elif any(g.lower() in ['adventure', 'drama'] for g in genres):
                return f"Following your journey through {ref_title}, {title} ({score}/10) offers an emotionally profound odyssey with unforgettable world-building."

        if genres:
            return f"Tailored to your curiosity for {', '.join(genres[:2])}, this {score}/10 acclaimed series is one of the sharpest gems in the modern anime landscape."

        return f"A critically celebrated {candidate.get('anime_type', 'series')} holding a {score}/10 score—RYUK's top recommendation for an unforgettable binge."

    def get_recommendations(self, user, requested_genre=None, mode='personalized', limit=6, refresh=False):
        """
        Coordinates full recommendation workflow:
        1. Analyzes user profile (genres, studios, completed history).
        2. Retrieves safe candidates excluding completed/watching titles.
        3. Computes match percentage, confidence tier, and verified metadata chips.
        4. Generates contextual RYUK rationales (AI + heuristic fallback).
        Caches recommendations per user for 5 minutes when refresh=False.
        """
        from django.core.cache import cache
        user_id = getattr(user, 'id', 'anon')

        track_ver = "0_0"
        if getattr(user, 'is_authenticated', False) or (user and getattr(user, 'id', None)):
            latest_entry = (
                UserAnimeList.objects.filter(user=user)
                .order_by('-updated_at')
                .values('updated_at')
                .first()
            )
            count = UserAnimeList.objects.filter(user=user).count()
            if latest_entry and latest_entry.get('updated_at'):
                track_ver = f"{count}_{int(latest_entry['updated_at'].timestamp())}"
            else:
                track_ver = f"{count}_0"

        cache_key = f"ryuk_recs_u{user_id}_v{track_ver}_{requested_genre or 'all'}_{mode}_{limit}"

        if not refresh:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        user_profile = self.analyze_user_preferences(user)
        candidates = self.get_candidate_pool(
            user_profile,
            requested_genre=requested_genre,
            mode=mode,
            limit=limit + 4
        )

        def sort_key(c):
            score = c.get('score') or 0
            has_shared = any(
                g.lower() in [ug.lower() for ug in user_profile['favorite_genres']]
                for g in c.get('genres', [])
            )
            return (1 if has_shared else 0, score)

        candidates.sort(key=sort_key, reverse=True)
        selected = candidates[:limit]

        # Generate rationales
        rationales, ai_active = self.generate_rationales(selected, user_profile, mode=mode)

        recommendation_objects = []
        for c in selected:
            mal_id = c['mal_id']
            match_pct, conf_tier, matched_reasons = self.calculate_relevance(c, user_profile, mode=mode)
            already_in_list = mal_id in user_profile['all_tracked_ids']

            recommendation_objects.append({
                'mal_id': mal_id,
                'title': c['title'],
                'title_english': c.get('title_english'),
                'poster_url': c['poster_url'],
                'anime_type': c.get('anime_type', 'TV'),
                'total_episodes': c.get('total_episodes'),
                'score': c.get('score'),
                'genres': c.get('genres', []),
                'studios': c.get('studios', []),
                'synopsis': c.get('synopsis'),
                'match_percentage': match_pct,
                'confidence_tier': conf_tier,
                'why_recommended': rationales.get(mal_id, ""),
                'is_ai_rationale': ai_active,
                'rationale_source': 'gemini' if ai_active else 'ryuk_heuristics',
                'matched_reasons': matched_reasons,
                'already_in_list': already_in_list,
                'verified_metadata': {
                    'format': c.get('anime_type', 'TV'),
                    'score': c.get('score'),
                    'episodes': c.get('total_episodes'),
                    'studios': c.get('studios', []),
                    'source': c.get('metadata_source', 'tenrai'),
                }
            })

        result = {
            'recommendations': recommendation_objects,
            'user_profile_summary': {
                'total_tracked': user_profile['total_tracked'],
                'completed_count': user_profile['completed_count'],
                'watching_count': user_profile['watching_count'],
                'favorite_genres': user_profile['favorite_genres'],
                'favorite_studios': user_profile.get('favorite_studios', []),
                'unexplored_genres': user_profile.get('unexplored_genres', []),
                'top_rated_titles': user_profile['top_rated_titles'],
                'has_watch_history': user_profile['has_watch_history'],
            },
            'mode': mode,
            'available_modes': ['personalized', 'different'],
            'generated_by': 'ryuk_intelligence_engine',
            'ai_provider_active': bool(self.ai_provider),
            'disclaimer': 'Metadata is verified through official anime registries; rationales are generated by RYUK\'s contextual intelligence engine.'
        }
        cache.set(cache_key, result, timeout=300)
        return result
