import secrets
from django.utils.deprecation import MiddlewareMixin
from apps.profiles.models import User

SESSION_COOKIE_NAME = 'animeverse_session'
COOKIE_MAX_AGE = 365 * 24 * 60 * 60  # 1 year

class AnimeverseSessionMiddleware(MiddlewareMixin):
    """
    Ensures every request is linked to a Demo User via the animeverse_session cookie.
    If the cookie is missing or invalid, generates a new 64-character token,
    creates a User instance, and sets the cookie in the response.
    """
    def process_request(self, request):
        session_key = request.COOKIES.get(SESSION_COOKIE_NAME)
        user = None
        new_session = False

        if session_key and len(session_key) == 64:
            user = User.objects.filter(session_key=session_key).first()

        if not user:
            session_key = secrets.token_hex(32)  # 64-character hex string
            user = User.objects.create(session_key=session_key, display_name="Guest")
            new_session = True

        request.animeverse_user = user
        request._new_animeverse_session = new_session

    def process_response(self, request, response):
        if getattr(request, '_new_animeverse_session', False) and hasattr(request, 'animeverse_user'):
            response.set_cookie(
                SESSION_COOKIE_NAME,
                request.animeverse_user.session_key,
                max_age=COOKIE_MAX_AGE,
                httponly=False,
                samesite='Lax',
            )
        return response
