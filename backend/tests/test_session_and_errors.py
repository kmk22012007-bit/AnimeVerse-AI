import pytest
from rest_framework.test import APIRequestFactory
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.profiles.models import User
from apps.core.middleware import AnimeverseSessionMiddleware, SESSION_COOKIE_NAME
from apps.core.exceptions import (
    custom_exception_handler,
    AnimeverseAPIException,
    DuplicateError,
    ServiceUnavailableError,
    RateLimitError
)
from apps.core.pagination import AnimeversePagination

pytestmark = pytest.mark.django_db

class TestSessionMiddleware:
    """
    Tests session identity management:
    - Automatically provisions anonymous User for first-time visitors
    - Sets 64-char animeverse_session cookie
    - Persists existing session across subsequent requests
    """

    def test_creates_session_for_new_visitor(self):
        factory = APIRequestFactory()
        middleware = AnimeverseSessionMiddleware(get_response=lambda r: HttpResponse("OK"))

        request = factory.get('/')
        assert SESSION_COOKIE_NAME not in request.COOKIES

        middleware.process_request(request)
        assert hasattr(request, 'animeverse_user')
        assert len(request.animeverse_user.session_key) == 64
        assert request.animeverse_user.display_name == "Guest"

        response = HttpResponse("OK")
        response = middleware.process_response(request, response)
        assert SESSION_COOKIE_NAME in response.cookies
        assert response.cookies[SESSION_COOKIE_NAME].value == request.animeverse_user.session_key

    def test_reuses_existing_valid_session(self):
        user = User.objects.create(session_key="1" * 64, display_name="ExistingOtaku")
        factory = APIRequestFactory()
        middleware = AnimeverseSessionMiddleware(get_response=lambda r: HttpResponse("OK"))

        request = factory.get('/')
        request.COOKIES[SESSION_COOKIE_NAME] = user.session_key

        middleware.process_request(request)
        assert request.animeverse_user.id == user.id
        assert request.animeverse_user.display_name == "ExistingOtaku"
        assert not getattr(request, '_new_animeverse_session', False)


class TestStandardizedExceptionsAndPagination:
    """
    Validates SRS-mandated error envelope:
    {
        "error": "validation_error",
        "message": "...",
        "details": {...}
    }
    """

    def test_validation_error_envelope(self):
        exc = DRFValidationError({"watched_episodes": ["Above total episodes."]})
        response = custom_exception_handler(exc, {})
        assert response is not None
        assert response.status_code == 400
        assert response.data["error"] == "validation_error"
        assert "watched_episodes" in response.data["details"]
        assert "Above total episodes." in response.data["message"]

    def test_custom_duplicate_error(self):
        exc = DuplicateError("Anime already in watchlist.", details={"mal_id": "Already added."})
        response = custom_exception_handler(exc, {})
        assert response is not None
        assert response.status_code == 409
        assert response.data["error"] == "duplicate_resource"
        assert response.data["message"] == "Anime already in watchlist."

    def test_service_unavailable_error(self):
        exc = ServiceUnavailableError("Jikan API is unreachable.")
        response = custom_exception_handler(exc, {})
        assert response is not None
        assert response.status_code == 503
        assert response.data["error"] == "service_unavailable"
        assert response.data["message"] == "Jikan API is unreachable."

    def test_rate_limit_error(self):
        exc = RateLimitError("Rate limit reached.")
        response = custom_exception_handler(exc, {})
        assert response is not None
        assert response.status_code == 429
        assert response.data["error"] == "rate_limit_exceeded"

    def test_srs_pagination_envelope(self):
        from rest_framework.request import Request
        factory = APIRequestFactory()
        wsgi_request = factory.get('/?page=1&page_size=20')
        drf_request = Request(wsgi_request)
        paginator = AnimeversePagination()

        sample_items = list(range(45))  # 45 items, page_size 20 => 3 pages
        page_slice = paginator.paginate_queryset(sample_items, drf_request)
        response = paginator.get_paginated_response(page_slice)

        assert "results" in response.data
        assert len(response.data["results"]) == 20
        assert "pagination" in response.data
        assert response.data["pagination"]["page"] == 1
        assert response.data["pagination"]["total_pages"] == 3
        assert response.data["pagination"]["total"] == 45
