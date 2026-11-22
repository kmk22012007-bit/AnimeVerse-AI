import pytest
from django.core.cache import cache

@pytest.fixture(autouse=True)
def clear_django_cache():
    """Ensure in-memory cache isolation across individual test runs."""
    cache.clear()
    yield
    cache.clear()
