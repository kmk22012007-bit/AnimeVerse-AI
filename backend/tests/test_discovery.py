import pytest
from datetime import datetime, timezone as dt_timezone
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.anime.models import (
    Anime,
    JikanCache,
    StreamingLanguageTrack,
    VerificationStatus,
    TrackType,
    Franchise,
    FranchiseEntry,
    RelationshipType
)
from apps.anime.discovery_service import DiscoveryService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_a(db):
    return User.objects.create(
        session_key="a" * 64,
        display_name="DiscovererPrime",
        is_public=True
    )

@pytest.fixture
def discovery_catalog(db):
    """
    Sets up a rich mock catalog of cached anime entries and language tracks.
    """
    # 1. Demon Slayer (TV, 2019, 26 eps, score 8.49, Action/Fantasy/Supernatural, Verified Tamil & Hindi)
    ds = Anime.objects.create(
        mal_id=38000,
        title="Kimetsu no Yaiba",
        poster_url="https://cdn.myanimelist.net/images/anime/1286/99889.jpg",
        anime_type="TV",
        total_episodes=26
    )
    JikanCache.objects.create(
        cache_key="details_38000",
        payload={
            "data": {
                "mal_id": 38000,
                "title": "Kimetsu no Yaiba",
                "title_english": "Demon Slayer: Kimetsu no Yaiba",
                "title_japanese": "鬼滅の刃",
                "type": "TV",
                "episodes": 26,
                "status": "Finished Airing",
                "score": 8.49,
                "year": 2019,
                "aired": {"from": "2019-04-06T00:00:00+00:00", "to": "2019-09-28T00:00:00+00:00"},
                "genres": [{"name": "Action"}, {"name": "Fantasy"}, {"name": "Supernatural"}]
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )

    # Verified Tamil and Hindi tracks
    StreamingLanguageTrack.objects.create(
        anime=ds,
        provider_name="Crunchyroll",
        country="IN",
        audio_language="Tamil",
        track_type=TrackType.DUBBED_AUDIO,
        verification_status=VerificationStatus.LICENSOR_CONFIRMED
    )
    StreamingLanguageTrack.objects.create(
        anime=ds,
        provider_name="Crunchyroll",
        country="IN",
        audio_language="Hindi",
        track_type=TrackType.DUBBED_AUDIO,
        verification_status=VerificationStatus.LICENSOR_CONFIRMED
    )
    # Unverified track (must NOT be counted as verified)
    StreamingLanguageTrack.objects.create(
        anime=ds,
        provider_name="JioHotstar",
        country="IN",
        audio_language="Korean",
        track_type=TrackType.DUBBED_AUDIO,
        verification_status=VerificationStatus.UNVERIFIED
    )

    # 2. Naruto (TV, 2002, 220 eps, score 7.99, Action/Adventure, Verified Tamil)
    naruto = Anime.objects.create(
        mal_id=20,
        title="Naruto",
        poster_url="https://cdn.myanimelist.net/images/anime/13/17405.jpg",
        anime_type="TV",
        total_episodes=220
    )
    JikanCache.objects.create(
        cache_key="details_20",
        payload={
            "data": {
                "mal_id": 20,
                "title": "Naruto",
                "title_english": "Naruto",
                "title_japanese": "ナルト",
                "type": "TV",
                "episodes": 220,
                "status": "Finished Airing",
                "score": 7.99,
                "year": 2002,
                "aired": {"from": "2002-10-03T00:00:00+00:00", "to": "2007-02-08T00:00:00+00:00"},
                "genres": [{"name": "Action"}, {"name": "Adventure"}]
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )
    StreamingLanguageTrack.objects.create(
        anime=naruto,
        provider_name="Sony LIV",
        country="IN",
        audio_language="Tamil",
        track_type=TrackType.DUBBED_AUDIO,
        verification_status=VerificationStatus.LICENSOR_CONFIRMED
    )

    # 3. Frieren (TV, 2023, 28 eps, score 9.32, Adventure/Drama/Fantasy, Verified Hindi)
    frieren = Anime.objects.create(
        mal_id=52991,
        title="Sousou no Frieren",
        poster_url="https://cdn.myanimelist.net/images/anime/1015/138062.jpg",
        anime_type="TV",
        total_episodes=28
    )
    JikanCache.objects.create(
        cache_key="details_52991",
        payload={
            "data": {
                "mal_id": 52991,
                "title": "Sousou no Frieren",
                "title_english": "Frieren: Beyond Journey's End",
                "title_japanese": "葬送のフリーレン",
                "type": "TV",
                "episodes": 28,
                "status": "Finished Airing",
                "score": 9.32,
                "year": 2023,
                "aired": {"from": "2023-09-29T00:00:00+00:00", "to": "2024-03-22T00:00:00+00:00"},
                "genres": [{"name": "Adventure"}, {"name": "Drama"}, {"name": "Fantasy"}]
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )
    StreamingLanguageTrack.objects.create(
        anime=frieren,
        provider_name="Crunchyroll",
        country="IN",
        audio_language="Hindi",
        track_type=TrackType.DUBBED_AUDIO,
        verification_status=VerificationStatus.LICENSOR_CONFIRMED
    )

    # 4. Jujutsu Movie (Movie, 2021, 1 ep, score 8.48, Action/Fantasy)
    jjk_movie = Anime.objects.create(
        mal_id=48561,
        title="Jujutsu Kaisen 0",
        poster_url="https://cdn.myanimelist.net/images/anime/1121/119044.jpg",
        anime_type="Movie",
        total_episodes=1
    )
    JikanCache.objects.create(
        cache_key="details_48561",
        payload={
            "data": {
                "mal_id": 48561,
                "title": "Jujutsu Kaisen 0",
                "title_english": "Jujutsu Kaisen 0",
                "title_japanese": "劇場版 呪術廻戦 0",
                "type": "Movie",
                "episodes": 1,
                "status": "Finished Airing",
                "score": 8.48,
                "year": 2021,
                "aired": {"from": "2021-12-24T00:00:00+00:00", "to": "2021-12-24T00:00:00+00:00"},
                "genres": [{"name": "Action"}, {"name": "Fantasy"}]
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )

    # 5. Unrated Upcoming Sci-Fi (TV, 2026, None eps, score None)
    unrated = Anime.objects.create(
        mal_id=77777,
        title="Upcoming Cyber Odyssey",
        poster_url="https://example.com/cyber.jpg",
        anime_type="TV",
        total_episodes=None
    )
    JikanCache.objects.create(
        cache_key="details_77777",
        payload={
            "data": {
                "mal_id": 77777,
                "title": "Upcoming Cyber Odyssey",
                "title_english": "Cyber Odyssey",
                "type": "TV",
                "episodes": None,
                "status": "Not yet aired",
                "score": None,
                "year": 2026,
                "aired": {"from": "2026-10-01T00:00:00+00:00", "to": None},
                "genres": [{"name": "Sci-Fi"}]
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )

    # 6. Adult / Hentai entry (must be completely blocked)
    adult = Anime.objects.create(
        mal_id=999999,
        title="Explicit Adult OVA",
        poster_url="https://example.com/adult.jpg",
        anime_type="OVA",
        total_episodes=1
    )
    JikanCache.objects.create(
        cache_key="details_999999",
        payload={
            "data": {
                "mal_id": 999999,
                "title": "Explicit Adult OVA",
                "type": "OVA",
                "genres": [{"name": "Hentai"}],
                "rating": "Rx - Hentai"
            }
        },
        expires_at=datetime(2028, 1, 1, tzinfo=dt_timezone.utc)
    )

    return {
        'demon_slayer': ds,
        'naruto': naruto,
        'frieren': frieren,
        'jjk_movie': jjk_movie,
        'unrated': unrated,
        'adult': adult,
    }

@pytest.mark.django_db
class TestAdvancedDiscoveryEngine:

    def test_discovery_filters_endpoint(self, api_client, discovery_catalog):
        """Verifies GET /api/anime/discovery/filters/ returns available verified audio languages and options."""
        res = api_client.get('/api/anime/discovery/filters/')
        assert res.status_code == 200
        data = res.json()

        assert 'verified_languages' in data
        assert 'Tamil' in data['verified_languages']
        assert 'Hindi' in data['verified_languages']
        # Unverified 'Korean' must NOT appear
        assert 'Korean' not in data['verified_languages']

        assert 'genres' in data
        assert 'Action' in data['genres']
        assert 'formats' in data
        assert 'sort_options' in data

    def test_verified_audio_language_filter_tamil(self, api_client, discovery_catalog):
        """Verifies filtering by verified audio language Tamil returns only verified titles (Demon Slayer and Naruto)."""
        res = api_client.get('/api/anime/browse/?audio_language=Tamil')
        assert res.status_code == 200
        data = res.json()
        results = data['results']

        mal_ids = [r['mal_id'] for r in results]
        assert 38000 in mal_ids  # Demon Slayer
        assert 20 in mal_ids     # Naruto
        assert 52991 not in mal_ids  # Frieren (Hindi only)

    def test_unverified_audio_language_is_excluded(self, api_client, discovery_catalog):
        """Verifies that querying for an unverified audio language returns empty results."""
        res = api_client.get('/api/anime/browse/?audio_language=Korean')
        assert res.status_code == 200
        data = res.json()
        assert data['results'] == []
        assert data['pagination']['total'] == 0

    def test_country_specific_language_availability(self, api_client, discovery_catalog):
        """Verifies country filtering alongside audio language."""
        # Querying with country=IN returns Tamil titles
        res_in = api_client.get('/api/anime/browse/?audio_language=Tamil&country=IN')
        assert res_in.status_code == 200
        assert len(res_in.json()['results']) >= 2

        # Querying with non-matching country returns 0 results
        res_us = api_client.get('/api/anime/browse/?audio_language=Tamil&country=US')
        assert res_us.status_code == 200
        assert res_us.json()['results'] == []

    def test_multi_genre_and_exclusion_filtering(self, api_client, discovery_catalog):
        """Verifies multi-genre inclusion and exclusion."""
        # Include Action and Fantasy (Demon Slayer, JJK Movie match; Naruto is Action/Adventure so excluded)
        res = api_client.get('/api/anime/browse/?genres=Action,Fantasy')
        assert res.status_code == 200
        mal_ids = [r['mal_id'] for r in res.json()['results']]
        assert 38000 in mal_ids
        assert 48561 in mal_ids
        assert 20 not in mal_ids

        # Exclude Supernatural (Demon Slayer is Supernatural, so only JJK Movie remains)
        res_ex = api_client.get('/api/anime/browse/?genres=Action,Fantasy&exclude_genres=Supernatural')
        assert res_ex.status_code == 200
        ex_mal_ids = [r['mal_id'] for r in res_ex.json()['results']]
        assert 38000 not in ex_mal_ids
        assert 48561 in ex_mal_ids

    def test_format_filtering(self, api_client, discovery_catalog):
        """Verifies filtering by anime format (Movie vs TV)."""
        res_movie = api_client.get('/api/anime/browse/?format=movie')
        assert res_movie.status_code == 200
        movie_ids = [r['mal_id'] for r in res_movie.json()['results']]
        assert 48561 in movie_ids  # JJK 0 Movie
        assert 38000 not in movie_ids  # TV series

    def test_year_and_year_range_filtering(self, api_client, discovery_catalog):
        """Verifies filtering by exact year and year range."""
        # Exact year 2019 (Demon Slayer)
        res_2019 = api_client.get('/api/anime/browse/?year=2019')
        assert res_2019.status_code == 200
        ids_2019 = [r['mal_id'] for r in res_2019.json()['results']]
        assert 38000 in ids_2019
        assert 20 not in ids_2019

        # Year range 2020 to 2024 (JJK Movie 2021, Frieren 2023)
        res_range = api_client.get('/api/anime/browse/?year_from=2020&year_to=2024')
        assert res_range.status_code == 200
        range_ids = [r['mal_id'] for r in res_range.json()['results']]
        assert 48561 in range_ids
        assert 52991 in range_ids
        assert 38000 not in range_ids  # 2019
        assert 20 not in range_ids     # 2002

    def test_score_range_and_missing_score_handling(self, api_client, discovery_catalog):
        """Verifies score filtering and strict omission of missing/null scores."""
        # min_score = 8.5 (Frieren at 9.32 matches; Demon Slayer at 8.49 and unrated 77777 are excluded)
        res = api_client.get('/api/anime/browse/?min_score=8.5')
        assert res.status_code == 200
        ids = [r['mal_id'] for r in res.json()['results']]
        assert 52991 in ids
        assert 38000 not in ids
        assert 77777 not in ids  # Unrated must NOT appear

    def test_episode_range_filtering(self, api_client, discovery_catalog):
        """Verifies filtering by episode count range."""
        # 100+ episodes (Naruto at 220 matches)
        res = api_client.get('/api/anime/browse/?min_episodes=100')
        assert res.status_code == 200
        ids = [r['mal_id'] for r in res.json()['results']]
        assert 20 in ids
        assert 38000 not in ids
        assert 48561 not in ids

        # Single episode (Movie JJK 0 at 1 ep)
        res_1 = api_client.get('/api/anime/browse/?min_episodes=1&max_episodes=1')
        assert res_1.status_code == 200
        ids_1 = [r['mal_id'] for r in res_1.json()['results']]
        assert 48561 in ids_1
        assert 38000 not in ids_1

    def test_combined_complex_filters(self, api_client, discovery_catalog):
        """Verifies multi-filter intersection (Genre: Action, Format: TV, Min Score: 8.0, Audio: Tamil)."""
        res = api_client.get(
            '/api/anime/browse/?genres=Action&format=tv&min_score=8.0&audio_language=Tamil'
        )
        assert res.status_code == 200
        results = res.json()['results']

        assert len(results) == 1
        assert results[0]['mal_id'] == 38000  # Demon Slayer satisfies all conditions
        # Naruto fails min_score (7.99 < 8.0)
        # JJK Movie fails format (Movie != TV)
        # Frieren fails language (Hindi != Tamil)

    def test_sorting_highest_and_lowest_scores(self, api_client, discovery_catalog):
        """Verifies stable sorting by highest and lowest score."""
        res_high = api_client.get('/api/anime/browse/?sort=-score')
        assert res_high.status_code == 200
        results = res_high.json()['results']
        scores = [r['score'] for r in results if r.get('score') is not None]
        assert scores == sorted(scores, reverse=True)

        res_low = api_client.get('/api/anime/browse/?sort=score')
        assert res_low.status_code == 200
        results_low = res_low.json()['results']
        scores_low = [r['score'] for r in results_low if r.get('score') is not None]
        assert scores_low == sorted(scores_low)

    def test_adult_content_strictly_excluded(self, api_client, discovery_catalog):
        """Verifies adult/hentai content is never returned by browse, even when requested directly."""
        # 1. Normal browse never includes adult anime 999999
        res = api_client.get('/api/anime/browse/')
        assert res.status_code == 200
        mal_ids = [r['mal_id'] for r in res.json()['results']]
        assert 999999 not in mal_ids

        # 2. Explicit request for Hentai genre returns 0 results
        res_hentai = api_client.get('/api/anime/browse/?genres=Hentai')
        assert res_hentai.status_code == 200
        assert res_hentai.json()['results'] == []

    def test_invalid_parameters_raise_validation_error(self, api_client, discovery_catalog):
        """Verifies that invalid ranges (e.g. min_score > max_score or year_from > year_to) return 400."""
        # min_score > max_score
        res1 = api_client.get('/api/anime/browse/?min_score=9.0&max_score=5.0')
        assert res1.status_code == 400

        # year_from > year_to
        res2 = api_client.get('/api/anime/browse/?year_from=2025&year_to=2015')
        assert res2.status_code == 400

        # min_episodes > max_episodes
        res3 = api_client.get('/api/anime/browse/?min_episodes=50&max_episodes=10')
        assert res3.status_code == 400

    def test_title_and_english_japanese_partial_search(self, api_client, discovery_catalog):
        """Verifies title search with English, Japanese, and partial matching."""
        # 1. Search by English title "Demon Slayer"
        res_en = api_client.get('/api/anime/browse/?q=Demon%20Slayer')
        assert res_en.status_code == 200
        en_ids = [r['mal_id'] for r in res_en.json()['results']]
        assert 38000 in en_ids

        # 2. Search by Japanese title "鬼滅の刃"
        res_ja = api_client.get('/api/anime/browse/?q=鬼滅の刃')
        assert res_ja.status_code == 200
        ja_ids = [r['mal_id'] for r in res_ja.json()['results']]
        assert 38000 in ja_ids

        # 3. Partial matching "Frier"
        res_part = api_client.get('/api/anime/browse/?q=Frier')
        assert res_part.status_code == 200
        part_ids = [r['mal_id'] for r in res_part.json()['results']]
        assert 52991 in part_ids

    def test_franchise_grouping_in_browse_results(self, api_client, discovery_catalog):
        """Verifies that related anime are linked with franchise metadata in browse results."""
        franchise = Franchise.objects.create(name="Naruto Verse", slug="naruto-verse")
        FranchiseEntry.objects.create(
            franchise=franchise,
            anime=discovery_catalog['naruto'],
            relationship_type=RelationshipType.MAIN_SERIES,
            is_main_entry=True
        )
        shippuden = Anime.objects.create(
            mal_id=1735,
            title="Naruto: Shippuuden",
            poster_url="https://example.com/shippuuden.jpg",
            anime_type="TV",
            total_episodes=500
        )
        FranchiseEntry.objects.create(
            franchise=franchise,
            anime=shippuden,
            relationship_type=RelationshipType.SEQUEL,
            is_main_entry=False
        )

        res = api_client.get('/api/anime/browse/?q=Naruto')
        assert res.status_code == 200
        results = res.json()['results']
        naruto_card = next(r for r in results if r['mal_id'] == 20)
        assert naruto_card.get('franchise_name') == "Naruto Verse"
        assert naruto_card.get('franchise_slug') == "naruto-verse"
