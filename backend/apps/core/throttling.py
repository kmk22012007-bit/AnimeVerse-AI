import logging
from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)

class AnimeverseSessionThrottle(SimpleRateThrottle):
    """
    Identifies callers by their persistent session key or animeverse_user id,
    falling back to client IP address.
    """
    scope = 'animeverse_default'

    def __init__(self):
        super().__init__()
        self.history = []

    def wait(self):
        if not getattr(self, 'history', None):
            return 60
        return super().wait()

    def get_cache_key(self, request, view):
        # Anchor throttle strictly to client IP identity.
        # This prevents rate limit bypass via cookie deletion or session cycling.
        ip = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"ip_{ip}"
        }


class RyukMessageThrottle(AnimeverseSessionThrottle):
    """
    Rate limits conversational AI chat queries to protect LLM token budget and prevent API flooding.
    Default: 30 requests per minute.
    """
    scope = 'ryuk_message'


class RyukRecommendationThrottle(AnimeverseSessionThrottle):
    """
    Rate limits recommendation calls.
    Default: 40 requests per minute.
    """
    scope = 'ryuk_recommendation'


class CommunityActionThrottle(AnimeverseSessionThrottle):
    """
    Rate limits community mutations (post creation, report submissions, polls) to mitigate spam.
    Default: 40 requests per minute.
    """
    scope = 'community_action'
