import pytest
from rest_framework.test import APIClient
from apps.anime.content_filter import (
    is_excluded_adult_anime,
    filter_anime_list,
    check_anime_id_is_excluded,
    BLOCKED_ANIME_MESSAGE,
)
from apps.anime.models import Anime, JikanCache
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.profiles.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_user():
    return User.objects.create(session_key="s" * 64, display_name="SafetyTester")


@pytest.fixture
def api_client(test_user):
    client = APIClient()
    client.cookies['animeverse_session'] = test_user.session_key
    return client


# ---------------------------------------------------------------------------
# 1. Unit Tests for Content Safety Rule Engine
# ---------------------------------------------------------------------------

def test_hentai_genre_excluded():
    """Hentai genre ID 12 or name 'Hentai' must be excluded."""
    assert is_excluded_adult_anime({'genres': [{'mal_id': 12, 'name': 'Hentai'}]}) is True
    assert is_excluded_adult_anime({'genres': [{'id': 12, 'name': 'hentai'}]}) is True
    assert is_excluded_adult_anime({'genres': ['Hentai']}) is True
    assert is_excluded_adult_anime({'genres': 'hentai'}) is True


def test_erotica_genre_excluded():
    """Erotica genre ID 49 must be excluded."""
    assert is_excluded_adult_anime({'genres': [{'mal_id': 49, 'name': 'Erotica'}]}) is True
    assert is_excluded_adult_anime({'genres': ['Erotica']}) is True


def test_explicit_genres_field_excluded():
    """Jikan v4 explicit_genres field must trigger exclusion."""
    assert is_excluded_adult_anime({'explicit_genres': [{'mal_id': 12, 'name': 'Hentai'}]}) is True
    assert is_excluded_adult_anime({'explicit_genres': [{'mal_id': 49, 'name': 'Erotica'}]}) is True


def test_rx_rating_excluded():
    """MyAnimeList Rx ratings (Rx - Hentai, Rx - Adult) must be excluded."""
    assert is_excluded_adult_anime({'rating': 'Rx - Hentai'}) is True
    assert is_excluded_adult_anime({'rating': 'Rx'}) is True
    assert is_excluded_adult_anime({'rating': 'rx - adult'}) is True


def test_anilist_is_adult_excluded():
    """AniList isAdult boolean flag must trigger exclusion."""
    assert is_excluded_adult_anime({'isAdult': True}) is True


def test_normal_anime_remain_visible():
    """Mainstream titles across G, PG, PG-13 must NEVER be excluded."""
    assert is_excluded_adult_anime({
        'title': 'Demon Slayer',
        'rating': 'R - 17+ (violence & profanity)',
        'genres': [{'name': 'Action'}, {'name': 'Fantasy'}]
    }) is False
    assert is_excluded_adult_anime({
        'title': 'One Piece',
        'rating': 'PG-13 - Teens 13 or older',
        'genres': [{'name': 'Action'}, {'name': 'Adventure'}]
    }) is False
    assert is_excluded_adult_anime({
        'title': 'Kaguya-sama: Love is War',
        'rating': 'PG-13',
        'genres': [{'name': 'Comedy'}, {'name': 'Romance'}]
    }) is False
    assert is_excluded_adult_anime({
        'title': 'Spirited Away',
        'rating': 'PG - Children',
        'genres': [{'name': 'Adventure'}, {'name': 'Award Winning'}]
    }) is False


def test_mature_non_hentai_not_removed():
    """
    CRITICAL REQUIREMENT:
    Do not automatically exclude every anime with an 18+ rating.
    Mature anime (Berserk, AoT, Psycho-Pass, Tokyo Ghoul) and Ecchi (High School DxD)
    must NOT be classified as hentai.
    """
    # Berserk
    assert is_excluded_adult_anime({
        'title': 'Berserk',
        'rating': 'R - 17+ (violence & profanity)',
        'genres': [{'mal_id': 1, 'name': 'Action'}, {'mal_id': 14, 'name': 'Horror'}]
    }) is False

    # Attack on Titan
    assert is_excluded_adult_anime({
        'title': 'Shingeki no Kyojin',
        'rating': 'R - 17+ (violence & profanity)',
        'genres': [{'mal_id': 1, 'name': 'Action'}, {'mal_id': 41, 'name': 'Suspense'}]
    }) is False

    # High School DxD (Ecchi with R+ Mild Nudity)
    assert is_excluded_adult_anime({
        'title': 'High School DxD',
        'rating': 'R+ - Mild Nudity',
        'genres': [{'mal_id': 9, 'name': 'Ecchi'}, {'mal_id': 4, 'name': 'Comedy'}, {'mal_id': 22, 'name': 'Romance'}]
    }) is False

    # Kill la Kill (Action / Ecchi)
    assert is_excluded_adult_anime({
        'title': 'Kill la Kill',
        'rating': 'R - 17+ (violence & profanity)',
        'genres': [{'mal_id': 1, 'name': 'Action'}, {'mal_id': 9, 'name': 'Ecchi'}]
    }) is False


def test_missing_metadata_safety():
    """
    If metadata is missing, do not automatically classify the title as hentai.
    Never rely only on title keywords.
    """
    assert is_excluded_adult_anime({'title': 'Unknown Anime', 'genres': [], 'rating': None}) is False
    assert is_excluded_adult_anime({}) is False
    assert is_excluded_adult_anime(None) is False


def test_filter_anime_list():
    """filter_anime_list must remove only adult items while retaining all safe items."""
    raw_list = [
        {'mal_id': 1, 'title': 'Clean Action', 'genres': [{'name': 'Action'}], 'rating': 'PG-13'},
        {'mal_id': 2, 'title': 'Hentai OVA', 'genres': [{'mal_id': 12, 'name': 'Hentai'}], 'rating': 'Rx - Hentai'},
        {'mal_id': 3, 'title': 'Dark Mature', 'genres': [{'name': 'Horror'}], 'rating': 'R - 17+ (violence & profanity)'},
        {'mal_id': 4, 'title': 'Explicit Erotica', 'genres': [{'mal_id': 49, 'name': 'Erotica'}], 'rating': 'Rx'},
    ]
    filtered = filter_anime_list(raw_list)
    assert len(filtered) == 2
    assert [x['mal_id'] for x in filtered] == [1, 3]


# ---------------------------------------------------------------------------
# 2. Integration Tests Across Endpoints
# ---------------------------------------------------------------------------

def test_search_excludes_adult_anime(api_client):
    """Anime Search API must never return excluded adult/hentai titles."""
    mock_jikan_res = {
        'data': [
            {'mal_id': 100, 'title': 'Ninja Scroll TV', 'type': 'TV', 'rating': 'R - 17+', 'genres': [{'name': 'Action'}]},
            {'mal_id': 200, 'title': 'Explicit Hentai 1', 'type': 'OVA', 'rating': 'Rx - Hentai', 'genres': [{'mal_id': 12, 'name': 'Hentai'}]},
            {'mal_id': 300, 'title': 'Ninja Senshi', 'type': 'TV', 'rating': 'PG-13', 'genres': [{'name': 'Sci-Fi'}]},
        ],
        'pagination': {'last_visible_page': 1, 'items': {'total': 3}}
    }
    with patch('apps.anime.jikan_client.JikanClient.search_anime', return_value=mock_jikan_res):
        response = api_client.get('/api/anime/search/?q=ninja')
        assert response.status_code == 200
        results = response.json()['results']
        ids = [r['mal_id'] for r in results]
        assert 200 not in ids
        assert 100 in ids
        assert 300 in ids


def test_browse_adult_genre_blocked(api_client):
    """Requesting genre=12 or genre=hentai in browse must return empty results."""
    response = api_client.get('/api/anime/browse/?genre=12')
    assert response.status_code == 200
    assert response.json()['results'] == []

    response_named = api_client.get('/api/anime/browse/?genre=hentai')
    assert response_named.status_code == 200
    assert response_named.json()['results'] == []


def test_direct_anime_detail_access_blocked(api_client):
    """
    Direct access to a known adult/hentai ID via /api/anime/{id}/
    must be blocked with 404 and BLOCKED_ANIME_MESSAGE.
    """
    mock_adult_details = {
        'data': {
            'mal_id': 99999,
            'title': 'Secret Adult OVA',
            'rating': 'Rx - Hentai',
            'genres': [{'mal_id': 12, 'name': 'Hentai'}],
        }
    }
    with patch('apps.anime.jikan_client.JikanClient.get_anime_details', return_value=mock_adult_details):
        response = api_client.get('/api/anime/99999/')
        assert response.status_code == 404
        data = response.json()
        assert data.get('is_blocked') is True
        assert data.get('error') == BLOCKED_ANIME_MESSAGE


def test_episodes_direct_access_blocked(api_client):
    """Direct episodes query for an adult anime must return 404 blocked."""
    mock_adult_details = {
        'data': {
            'mal_id': 99999,
            'title': 'Secret Adult OVA',
            'rating': 'Rx - Hentai',
            'genres': [{'mal_id': 12, 'name': 'Hentai'}],
        }
    }
    with patch('apps.anime.jikan_client.JikanClient.get_anime_details', return_value=mock_adult_details):
        response = api_client.get('/api/anime/99999/episodes/')
        assert response.status_code == 404
        assert response.json().get('is_blocked') is True


def test_related_anime_filters_adult_entries(api_client):
    """
    Related anime endpoint must filter out any hentai spinoffs/sequels
    from the relations list.
    """
    mock_details = {
        'data': {
            'mal_id': 500,
            'title': 'Mainstream Series',
            'rating': 'PG-13',
            'genres': [{'name': 'Action'}],
            'relations': [
                {
                    'relation': 'Sequel',
                    'entry': [{'mal_id': 501, 'type': 'anime', 'name': 'Mainstream Season 2'}]
                },
                {
                    'relation': 'Other',
                    'entry': [{'mal_id': 99999, 'type': 'anime', 'name': 'Explicit Adult Parody', 'genres': [{'mal_id': 12, 'name': 'Hentai'}], 'rating': 'Rx'}]
                }
            ]
        }
    }
    with patch('apps.anime.jikan_client.JikanClient.get_anime_details', return_value=mock_details):
        response = api_client.get('/api/anime/500/related/')
        assert response.status_code == 200
        results = response.json().get('results', [])
        ids = [r['mal_id'] for r in results]
        assert 501 in ids
        assert 99999 not in ids


def test_watch_options_direct_access_blocked(api_client):
    """Watch options for an adult anime must be blocked."""
    mock_adult_details = {
        'data': {
            'mal_id': 99999,
            'title': 'Secret Adult OVA',
            'rating': 'Rx - Hentai',
            'genres': [{'mal_id': 12, 'name': 'Hentai'}],
        }
    }
    with patch('apps.anime.jikan_client.JikanClient.get_anime_details', return_value=mock_adult_details):
        response = api_client.get('/api/anime/99999/watch-options/')
        assert response.status_code == 404
        assert response.json().get('is_blocked') is True


def test_trailers_direct_access_blocked(api_client):
    """Trailers for an adult anime must be blocked."""
    mock_adult_details = {
        'data': {
            'mal_id': 99999,
            'title': 'Secret Adult OVA',
            'rating': 'Rx - Hentai',
            'genres': [{'mal_id': 12, 'name': 'Hentai'}],
        }
    }
    with patch('apps.anime.jikan_client.JikanClient.get_anime_details', return_value=mock_adult_details):
        response = api_client.get('/api/anime/99999/trailers/')
        assert response.status_code == 404
        assert response.json().get('is_blocked') is True


def test_add_to_watchlist_blocked_for_adult_anime(api_client):
    """Attempting to add an excluded adult anime to watchlist must be rejected with 400."""
    mock_adult_details = {
        'data': {
            'mal_id': 99999,
            'title': 'Secret Adult OVA',
            'rating': 'Rx - Hentai',
            'genres': [{'mal_id': 12, 'name': 'Hentai'}],
        }
    }
    with patch('apps.anime.jikan_client.JikanClient.get_anime_details', return_value=mock_adult_details):
        response = api_client.post('/api/list/', {'mal_id': 99999, 'status': 'Plan to Watch'}, format='json')
        assert response.status_code == 400
        assert BLOCKED_ANIME_MESSAGE in str(response.json())


def test_watchlist_data_preserves_database_integrity(api_client, test_user):
    """
    Preserves database integrity:
    Existing user records are never deleted or corrupted, but if an anime
    is excluded it is omitted from active serialized responses.
    """
    user = test_user

    # Create one clean anime and one adult anime record
    clean_anime = Anime.objects.create(mal_id=1001, title="Safe Adventure", anime_type="TV")
    adult_anime = Anime.objects.create(mal_id=1002, title="Adult Legacy Entry", anime_type="OVA")

    # Cache metadata for adult anime indicating it's Rx
    JikanCache.objects.create(
        cache_key="details_1002",
        payload={'data': {'mal_id': 1002, 'rating': 'Rx - Hentai', 'genres': [{'mal_id': 12, 'name': 'Hentai'}]}},
        expires_at=timezone.now() + timedelta(days=1)
    )

    # User has both in database
    UserAnimeList.objects.create(user=user, anime=clean_anime, status=WatchStatus.WATCHING, watched_episodes=5)
    UserAnimeList.objects.create(user=user, anime=adult_anime, status=WatchStatus.COMPLETED, watched_episodes=2)

    # Confirm database rows are preserved (NOT deleted)
    assert UserAnimeList.objects.filter(user=user).count() == 2

    # Query GET /api/list/
    response = api_client.get('/api/list/')
    assert response.status_code == 200
    results = response.json()['results']

    # The clean anime is returned
    returned_ids = [r['mal_id'] for r in results]
    assert 1001 in returned_ids
    # The adult anime is NOT rendered in the active application interface
    assert 1002 not in returned_ids

    # The database record STILL exists intact
    assert UserAnimeList.objects.filter(user=user, anime_id=1002).exists()
