import pytest
from django.db import IntegrityError, transaction
from apps.profiles.models import User
from apps.anime.models import Anime, JikanCache
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus
from apps.community.models import Review, CommunityPost, Comment, PostLike
from apps.ryuk.models import AIConversation, AIMessage
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
class TestDatabaseModelsAndConstraints:
    """
    Validates database models and constraints matching SRS Section:
    Database Design & Sample Test Cases (DB-01, DB-02, DB-03, etc.)
    """

    def test_user_creation_and_fields(self):
        user = User.objects.create(session_key="a" * 64, display_name="OtakuHero", is_public=True)
        assert user.id is not None
        assert user.display_name == "OtakuHero"
        assert user.is_public is True
        assert user.auth_user_id is None

    def test_anime_and_jikan_cache(self):
        anime = Anime.objects.create(
            mal_id=1535,
            title="Death Note",
            poster_url="https://example.com/deathnote.jpg",
            anime_type="TV",
            total_episodes=37
        )
        assert anime.mal_id == 1535
        assert anime.title == "Death Note"

        cache = JikanCache.objects.create(
            cache_key="anime:1535:full",
            payload={"mal_id": 1535, "title": "Death Note"},
            expires_at=timezone.now() + timedelta(hours=6)
        )
        assert cache.cache_key == "anime:1535:full"
        assert cache.payload["title"] == "Death Note"

    def test_db_01_unique_user_anime_list_constraint(self):
        """DB-01: Two list entries for the same user and anime -> IntegrityError"""
        user = User.objects.create(session_key="b" * 64)
        anime = Anime.objects.create(mal_id=1, title="Cowboy Bebop")

        UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.WATCHING)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.COMPLETED)

    def test_db_02_episode_progress_creation_and_uniqueness(self):
        """DB-02: Episode progress unique per (list_entry, episode_number)"""
        user = User.objects.create(session_key="c" * 64)
        anime = Anime.objects.create(mal_id=20, title="Naruto", total_episodes=220)
        entry = UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=1)

        EpisodeProgress.objects.create(list_entry=entry, episode_number=1)

        # Duplicate episode for same list entry should fail
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                EpisodeProgress.objects.create(list_entry=entry, episode_number=1)

    def test_db_03_cascade_delete_user_anime_list(self):
        """DB-03: Delete a USER_ANIME_LIST row -> Its EPISODE_PROGRESS rows are deleted"""
        user = User.objects.create(session_key="d" * 64)
        anime = Anime.objects.create(mal_id=16498, title="Attack on Titan", total_episodes=25)
        entry = UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=3)

        EpisodeProgress.objects.create(list_entry=entry, episode_number=1)
        EpisodeProgress.objects.create(list_entry=entry, episode_number=2)
        EpisodeProgress.objects.create(list_entry=entry, episode_number=3)

        assert EpisodeProgress.objects.filter(list_entry=entry).count() == 3

        entry_id = entry.id
        entry.delete()

        assert EpisodeProgress.objects.filter(list_entry_id=entry_id).count() == 0

    def test_unique_review_per_user_and_anime(self):
        """SRS REVIEW: UNIQUE (user_id, anime_id)"""
        user = User.objects.create(session_key="e" * 64)
        anime = Anime.objects.create(mal_id=5114, title="Fullmetal Alchemist: Brotherhood")

        Review.objects.create(user=user, anime=anime, score=10, body="Masterpiece anime with great pacing.")

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(user=user, anime=anime, score=9, body="Another review should fail.")

    def test_unique_post_like_per_user(self):
        """SRS LIKE: UNIQUE (post_id, user_id). Repeated likes do nothing / fail on constraint"""
        user = User.objects.create(session_key="f" * 64)
        post = CommunityPost.objects.create(user=user, title="Favorite opening theme?", body="Mine is Again from FMA:B")

        PostLike.objects.create(post=post, user=user)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                PostLike.objects.create(post=post, user=user)

    def test_cascade_delete_community_post_removes_comments_and_likes(self):
        user = User.objects.create(session_key="g" * 64)
        post = CommunityPost.objects.create(user=user, title="Discussion", body="Let's talk about anime.")
        Comment.objects.create(post=post, user=user, body="First comment!")
        PostLike.objects.create(post=post, user=user)

        assert Comment.objects.filter(post=post).count() == 1
        assert PostLike.objects.filter(post=post).count() == 1

        post.delete()

        assert Comment.objects.filter(post_id=post.id).count() == 0
        assert PostLike.objects.filter(post_id=post.id).count() == 0

    def test_ai_conversation_and_messages(self):
        user = User.objects.create(session_key="h" * 64)
        convo = AIConversation.objects.create(user=user, title="Looking for dark thrillers")
        msg1 = AIMessage.objects.create(conversation=convo, role="user", content="Recommend something like Monster.")
        msg2 = AIMessage.objects.create(conversation=convo, role="assistant", content="Try Death Note and Psycho-Pass.")

        assert convo.messages.count() == 2
        convo.delete()
        assert AIMessage.objects.filter(id__in=[msg1.id, msg2.id]).count() == 0
