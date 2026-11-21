import pytest
import requests
from django.utils import timezone
from apps.anime.jikan_client import JikanClient
from apps.anime.models import JikanCache
from rest_framework.test import APIClient
from apps.profiles.models import User
from apps.core.middleware import SESSION_COOKIE_NAME

@pytest.mark.django_db
class TestProviderVerification:
    """
    Validates:
    1. Tenrai API connectivity and endpoints (https://api.tenrai.org/documentation)
    2. AniList fallback connectivity
    3. Provider fallback switching when primary fails
    4. Metadata provenance and timestamp preservation in cache and responses
    5. Actual Django HTTP endpoints
    """

    def test_tenrai_api_connectivity_and_data(self):
        """1 & 2: Test Tenrai API real search, details, characters, and image URLs"""
        client = JikanClient(base_url="https://api.tenrai.org/v1")

        # Search test
        search_res = client.search_anime("Naruto", page=1)
        assert search_res is not None
        assert "data" in search_res
        assert len(search_res["data"]) > 0
        first_anime = search_res["data"][0]
        assert first_anime["mal_id"] == 20
        assert "Naruto" in first_anime["title"]
        assert "image_url" in first_anime["images"]["jpg"]
        assert "cdn.myanimelist.net" in first_anime["images"]["jpg"]["image_url"]

        # Details test
        details_res = client.get_anime_details(1535)
        assert details_res is not None
        d = details_res["data"]
        assert d["mal_id"] == 1535
        assert d["title"] == "Death Note"
        assert d["episodes"] == 37
        assert "cdn.myanimelist.net" in d["images"]["jpg"]["image_url"]

        # Characters test
        chars_res = client.get_anime_characters(1535)
        assert chars_res is not None
        chars = chars_res["data"]
        assert len(chars) > 0
        char_names = [c["character"]["name"] for c in chars]
        assert any("Ryuk" in name or "Yagami" in name for name in char_names)

    def test_anilist_fallback_connectivity_independently(self):
        """3: Verify AniList fallback connectivity independently"""
        client = JikanClient()
        fallback_res = client._fetch_real_anime_from_anilist(mal_id=1535)
        assert fallback_res is not None
        assert "data" in fallback_res
        data = fallback_res["data"]
        assert data["mal_id"] == 1535
        assert "Death Note" in data["title"]
        assert data["episodes"] == 37
        assert "anilist.co" in data["images"]["jpg"]["image_url"]

    def test_provider_switching_on_upstream_failure(self):
        """4: Confirm service switches to AniList fallback when primary provider is unavailable"""
        # Configure client with an unreachable primary base_url
        failing_client = JikanClient(base_url="https://invalid-upstream-999.test/v1")

        # Request should fail upstream, trip circuit breaker, and cleanly fall back to AniList
        res = failing_client.search_anime("Cowboy Bebop", page=1)
        assert res is not None
        assert "data" in res
        assert len(res["data"]) > 0
        assert res["metadata_source"] == "anilist"
        assert res["data"][0]["metadata_source"] == "anilist"
        assert "Cowboy Bebop" in res["data"][0]["title"]

    def test_cache_metadata_provenance_and_timestamp_retention(self):
        """5 & 6: Preserve actual metadata provenance and fetched timestamp across caching"""
        client = JikanClient(base_url="https://api.tenrai.org/v1")
        cache_key = "test:provenance:check:1535"

        # Clear existing test key if any
        JikanCache.objects.filter(cache_key=cache_key).delete()

        # Step 1: Live request
        payload = client._request("anime/1535", cache_key=cache_key)
        assert payload["metadata_source"] == "tenrai"
        assert payload["is_cached"] is False
        assert "fetched_at" in payload
        original_fetched_at = payload["fetched_at"]

        # Step 2: Cached request
        cached_payload = client._request("anime/1535", cache_key=cache_key)
        assert cached_payload["metadata_source"] == "tenrai"  # retains original provenance
        assert cached_payload["is_cached"] is True
        assert cached_payload["fetched_at"] == original_fetched_at  # retains original timestamp
        assert cached_payload["is_stale"] is False

    def test_actual_django_endpoints_real_data(self):
        """8: Test actual HTTP endpoints through Django REST Framework"""
        api_client = APIClient()
        user = User.objects.create(session_key="v" * 64, display_name="ProvenanceTester")
        api_client.cookies[SESSION_COOKIE_NAME] = user.session_key

        # Search endpoint
        res = api_client.get('/api/anime/search/?q=Demon%20Slayer')
        assert res.status_code == 200
        results = res.data["results"]
        assert len(results) > 0
        assert "Kimetsu" in results[0]["title"] or "Demon Slayer" in results[0]["title"] or "Demon Slayer" in str(results[0].get("title_english", ""))
        assert results[0]["metadata_source"] in ("tenrai", "anilist", "cache")

        # Details endpoint
        res_det = api_client.get('/api/anime/38000/')
        assert res_det.status_code == 200
        assert res_det.data["mal_id"] == 38000
        assert res_det.data["episodes"] == 26
        assert res_det.data["metadata_source"] in ("tenrai", "anilist", "cache")
        assert res_det.data["fetched_at"] is not None

        # Trending endpoint
        res_trend = api_client.get('/api/anime/trending/')
        assert res_trend.status_code == 200
        assert len(res_trend.data["results"]) > 0
