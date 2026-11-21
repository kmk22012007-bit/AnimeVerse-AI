import logging
from django.db.models import Sum, Avg
from apps.ryuk.models import AIConversation, AIMessage
from apps.ryuk.ai_client import AIClientFactory
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.anime.jikan_client import JikanClient
from apps.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)

RYUK_SYSTEM_INSTRUCTION = """
You are RYUK, the intelligent, charismatic anime companion of AnimeVerse AI.
Personality traits:
- Sharp, slightly mischievous, observant, but genuinely helpful and insightful about anime lore.
- Adapt your tone: brief and practical when the user is organizing their list or asking quick facts; warmer and enthusiastic when recommending titles; careful and respectful when discussing story content to strictly avoid major spoilers unless the user explicitly asks for them.
- Reference the user's personal watching context when relevant.
- Do not invent non-existent anime titles or fake episode counts.
"""

class RyukService:
    """
    Orchestrates RYUK interactions per SRS Module 5 (FR-5.1 to FR-5.10).
    """
    def __init__(self, ai_provider=..., jikan_client=None):
        if ai_provider is Ellipsis:
            self.ai_provider = AIClientFactory.get_provider()
        else:
            self.ai_provider = ai_provider
        self.jikan_client = jikan_client or JikanClient()

    def get_or_create_conversation(self, user, conversation_id=None, initial_title=None):
        if conversation_id:
            convo = AIConversation.objects.filter(id=conversation_id, user=user).first()
            if convo:
                return convo
        title = (initial_title[:115] + "...") if initial_title and len(initial_title) > 115 else (initial_title or "New Conversation")
        return AIConversation.objects.create(user=user, title=title)

    def is_progress_summary_request(self, message: str) -> bool:
        lower = message.lower().strip()
        triggers = [
            "summarize my progress",
            "summary of my progress",
            "what is my progress",
            "show my progress",
            "my stats",
            "my watch statistics",
            "how much anime have i watched",
            "how many episodes",
        ]
        return any(trigger in lower for trigger in triggers)

    def generate_progress_summary(self, user) -> str:
        """
        SRS Page 33 & AI-04:
        Summary uses stored database counts, not external AI provider output.
        Filters out any excluded adult anime so they never leak into stats.
        """
        from apps.anime.content_filter import is_excluded_adult_anime
        all_user_entries = list(
            UserAnimeList.objects.filter(user=user)
            .select_related('anime')
        )
        valid_entries = [e for e in all_user_entries if not is_excluded_adult_anime(e.anime)]

        completed = sum(1 for e in valid_entries if e.status == WatchStatus.COMPLETED)
        watching = sum(1 for e in valid_entries if e.status == WatchStatus.WATCHING)
        plan_to_watch = sum(1 for e in valid_entries if e.status == WatchStatus.PLAN_TO_WATCH)

        total_episodes = sum(e.watched_episodes or 0 for e in valid_entries)

        rated = [e.rating for e in valid_entries if e.rating is not None]
        if rated:
            avg_str = f"{round(sum(rated) / len(rated), 1)}/10"
        else:
            avg_str = "No ratings yet"

        summary_text = (
            f"Here is your recorded anime journey so far:\n\n"
            f"• Completed: {completed} series\n"
            f"• Currently Watching: {watching} series\n"
            f"• Plan to Watch: {plan_to_watch} series\n"
            f"• Total Episodes Watched: {total_episodes} episodes\n"
            f"• Average Score: {avg_str}\n\n"
            f"Keep the momentum going! Need a recommendation for what to conquer next?"
        )
        return summary_text

    def build_user_context(self, user, anime_mal_id=None) -> str:
        lines = []
        lines.append(f"User Display Name: {user.display_name}")

        # Top rated titles
        top_rated = (
            UserAnimeList.objects.filter(user=user, rating__gte=7)
            .select_related('anime')
            .order_by('-rating')[:5]
        )
        if top_rated.exists():
            rated_str = ", ".join([f"{e.anime.title} ({e.rating}/10)" for e in top_rated])
            lines.append(f"Favorite/High-rated Anime: {rated_str}")

        # Currently watching
        watching = (
            UserAnimeList.objects.filter(user=user, status=WatchStatus.WATCHING)
            .select_related('anime')[:5]
        )
        if watching.exists():
            watching_str = ", ".join([f"{e.anime.title} (ep {e.watched_episodes}/{e.anime.total_episodes or '?'})" for e in watching])
            lines.append(f"Currently Watching: {watching_str}")

        # Specific anime subject if discussing one
        if anime_mal_id:
            try:
                from apps.anime.content_filter import is_excluded_adult_anime
                details = self.jikan_client.get_anime_details(anime_mal_id)
                if details and details.get('data') and not is_excluded_adult_anime(details['data']):
                    d = details['data']
                    lines.append(f"Currently viewing anime: {d.get('title')} (Genres: {', '.join([g['name'] for g in d.get('genres', [])])}; Score: {d.get('score')})")
            except Exception:
                pass

        return "\n".join(lines)

    def process_message(self, user, message: str, conversation_id=None, anime_mal_id=None):
        """
        Processes a user message to RYUK:
        - If progress summary request: answers from DB records.
        - If AI available: calls provider with context.
        - If AI unavailable / fails: stores fallback notice and returns suggestions.
        """
        convo = self.get_or_create_conversation(user, conversation_id, initial_title=message)

        # 1. Store user message
        AIMessage.objects.create(
            conversation=convo,
            role='user',
            content=message,
            is_fallback=False
        )

        # 2. Check for database-computed progress summary
        if self.is_progress_summary_request(message):
            reply_text = self.generate_progress_summary(user)
            assistant_msg = AIMessage.objects.create(
                conversation=convo,
                role='assistant',
                content=reply_text,
                is_fallback=False
            )
            return {
                'conversation_id': convo.id,
                'reply': reply_text,
                'is_fallback': False,
                'suggestions': []
            }

        # 3. Check if AI provider configured
        if not self.ai_provider:
            return self._handle_fallback(convo, message)

        # 4. Invoke AI provider with context and prompt
        try:
            context = self.build_user_context(user, anime_mal_id)
            prompt = f"User Context:\n{context}\n\nUser Question:\n{message}"
            reply_text = self.ai_provider.generate_response(
                prompt=prompt,
                system_instruction=RYUK_SYSTEM_INSTRUCTION,
                timeout=30.0  # FR-5.8: 30s timeout
            )
            AIMessage.objects.create(
                conversation=convo,
                role='assistant',
                content=reply_text,
                is_fallback=False
            )
            return {
                'conversation_id': convo.id,
                'reply': reply_text,
                'is_fallback': False,
                'suggestions': []
            }
        except Exception as e:
            logger.warning(f"AI Provider execution failed or timed out: {e}")
            return self._handle_fallback(convo, message)

    def _handle_fallback(self, convo, user_query):
        """
        SRS Page 33:
        When AI is unconfigured or fails, returns:
        {error: "ai_unavailable", message: "RYUK is unavailable right now.", is_fallback: True, suggestions: [anime]}
        Unavailable notice saved as AI_MESSAGE with is_fallback=True.
        """
        fallback_notice = "RYUK is unavailable right now."
        AIMessage.objects.create(
            conversation=convo,
            role='assistant',
            content=fallback_notice,
            is_fallback=True
        )

        # Fetch Discovery suggestions for same request
        suggestions = []
        try:
            search_query = user_query[:40].strip()
            res = self.jikan_client.search_anime(q=search_query, page=1)
            if not res or not res.get('data'):
                res = self.jikan_client.get_popular_anime(page=1)

            if res and res.get('data'):
                suggestions = [
                    self.jikan_client.normalize_poster_card(item)
                    for item in res['data'][:4]
                ]
        except Exception as e:
            logger.warning(f"Could not fetch discovery suggestions for fallback: {e}")

        return {
            'conversation_id': convo.id,
            'error': 'ai_unavailable',
            'message': fallback_notice,
            'is_fallback': True,
            'suggestions': suggestions
        }
