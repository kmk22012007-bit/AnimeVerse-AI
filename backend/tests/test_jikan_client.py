import pytest
from apps.anime.jikan_client import JikanClient, RateLimiter
from apps.anime.models import JikanCache
from django.utils import timezone
from datetime import timedelta
import time

@pytest.mark.django_db
class TestJikanClient:
    """
    Validates JikanClient implementation:
    - Real anime discovery results
    - Rate limiter functionality (NFR-18)
    - Caching in JIKAN_CACHE (NFR-1, NFR-13)
    - Normalizers conforming to SRS specifications
    """

    def test_rate_limiter_acquires_tokens(self):
        limiter = RateLimiter(max_per_second=3, max_per_minute=60)
        start = time.time()
        for _ in range(3):
            limiter.acquire()
        elapsed = time.time() - start
        assert elapsed < 0.5  # 3 immediate tokens

    def test_cache_mechanism_stores_and_retrieves(self):
        client = JikanClient()
        cache_key = "test:anime:9999"
        mock_payload = {"data": {"mal_id": 9999, "title": "Test Cache Anime"}}

        # Set cache
        client._set_cache(cache_key, mock_payload, ttl_hours=1)
        assert JikanCache.objects.filter(cache_key=cache_key).exists()

        # Retrieve fresh
        cached = client._get_cache(cache_key)
        assert cached is not None
        assert cached["data"]["title"] == "Test Cache Anime"

        # Stale cache retrieval
        expired_entry = JikanCache.objects.get(cache_key=cache_key)
        expired_entry.expires_at = timezone.now() - timedelta(minutes=10)
        expired_entry.save()

        assert client._get_cache(cache_key, allow_expired=False) is None
        assert client._get_cache(cache_key, allow_expired=True) is not None

    def test_live_real_anime_search(self):
        """Fetches real anime records from live provider"""
        client = JikanClient()
        res = client.search_anime("Naruto", page=1)
        assert res is not None
        assert "data" in res
        assert len(res["data"]) > 0

        first_item = res["data"][0]
        assert first_item["mal_id"] is not None
        assert "Naruto" in first_item["title"]

        card = client.normalize_poster_card(first_item)
        assert card["mal_id"] is not None
        assert "Naruto" in card["title"]
        assert card["poster_url"] is not None

    def test_live_real_anime_details(self):
        """Fetches real anime details (Death Note MAL 1535)"""
        client = JikanClient()
        res = client.get_anime_details(1535)
        assert res is not None
        data = res.get("data")
        assert data is not None
        assert data["mal_id"] == 1535
        assert "Death Note" in data["title"]

        normalized = client.normalize_anime_details(data)
        assert normalized["mal_id"] == 1535
        assert normalized["title"] is not None
        assert normalized["poster_url"] is not None
        assert normalized["synopsis"] is not None

    def test_normalize_release_label_fallback(self):
        client = JikanClient()
        item = {"mal_id": 100, "title": "Undated Anime", "aired": None}
        normalized = client.normalize_release(item)
        assert normalized["release_label"] == "Date to be announced"
