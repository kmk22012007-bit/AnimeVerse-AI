import pytest
from apps.profiles.models import User
from apps.anime.models import Anime
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus
from apps.tracking.services import TrackingService
from apps.dashboard.services import DashboardService
from apps.core.exceptions import ValidationError, DuplicateError, NotFoundError

pytestmark = pytest.mark.django_db

class TestStage5WatchlistAndTracking:
    """
    Comprehensive tests for Stage 5: My List & Episode Tracking.
    Verifies:
    1. Add anime
    2. Duplicate anime prevention
    3. Change status
    4. Increase and decrease episode progress
    5. Complete an anime
    6. Rating and notes
    7. Remove anime
    8. Data persistence
    9. Demo-user isolation
    10. Dashboard statistics updates
    """

    @pytest.fixture
    def test_user_a(self):
        return User.objects.create(session_key="a" * 64, display_name="User Alpha")

    @pytest.fixture
    def test_user_b(self):
        return User.objects.create(session_key="b" * 64, display_name="User Beta")

    @pytest.fixture
    def anime_frieren(self):
        return Anime.objects.create(
            mal_id=52991,
            title="Sousou no Frieren",
            anime_type="TV",
            total_episodes=28
        )

    @pytest.fixture
    def anime_demon_slayer(self):
        return Anime.objects.create(
            mal_id=38000,
            title="Kimetsu no Yaiba",
            anime_type="TV",
            total_episodes=26
        )

    # 1. Add anime
    def test_add_anime_to_watchlist(self, test_user_a, anime_frieren):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id, status=WatchStatus.PLAN_TO_WATCH)
        assert entry.id is not None
        assert entry.user == test_user_a
        assert entry.anime.mal_id == 52991
        assert entry.status == WatchStatus.PLAN_TO_WATCH
        assert entry.watched_episodes == 0

    # 2. Duplicate anime prevention (409 Conflict / DuplicateError)
    def test_duplicate_anime_prevention(self, test_user_a, anime_frieren):
        service = TrackingService()
        service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id, status=WatchStatus.PLAN_TO_WATCH)
        with pytest.raises(DuplicateError) as exc_info:
            service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id, status=WatchStatus.WATCHING)
        assert "already in your watchlist" in str(exc_info.value).lower()

    # 3. Change status
    def test_change_status_across_all_five_states(self, test_user_a, anime_frieren):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id, status=WatchStatus.PLAN_TO_WATCH)
        for target_status in [WatchStatus.WATCHING, WatchStatus.ON_HOLD, WatchStatus.DROPPED, WatchStatus.COMPLETED, WatchStatus.PLAN_TO_WATCH]:
            updated = service.update_entry(test_user_a, entry.id, status=target_status)
            assert updated.status == target_status

    # 4. Increase and decrease episode progress
    def test_episode_progress_bounds(self, test_user_a, anime_demon_slayer):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_demon_slayer.mal_id, status=WatchStatus.WATCHING)

        # Increment to 5
        updated = service.update_progress(test_user_a, entry.id, watched_episodes=5)
        assert updated.watched_episodes == 5
        assert EpisodeProgress.objects.filter(list_entry=entry).count() == 5

        # Decrement to 3
        updated = service.update_progress(test_user_a, entry.id, watched_episodes=3)
        assert updated.watched_episodes == 3
        assert EpisodeProgress.objects.filter(list_entry=entry).count() == 3

        # Negative progress prevented
        with pytest.raises(ValidationError):
            service.update_progress(test_user_a, entry.id, watched_episodes=-1)

        # Progress beyond total episodes (26) prevented
        with pytest.raises(ValidationError):
            service.update_progress(test_user_a, entry.id, watched_episodes=27)

    # 5. Automatically mark Completed when final episode reached
    def test_auto_complete_when_final_episode_reached(self, test_user_a, anime_demon_slayer):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_demon_slayer.mal_id, status=WatchStatus.WATCHING)

        # Setting watched to 26 (total_episodes)
        updated = service.update_progress(test_user_a, entry.id, watched_episodes=26)
        assert updated.watched_episodes == 26
        assert updated.status == WatchStatus.COMPLETED

        # Reducing below total resets status back to WATCHING
        updated = service.update_progress(test_user_a, entry.id, watched_episodes=25)
        assert updated.watched_episodes == 25
        assert updated.status == WatchStatus.WATCHING

    # 6. Explicit mark completed helper
    def test_explicit_mark_completed(self, test_user_a, anime_frieren):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id, status=WatchStatus.WATCHING)
        completed = service.mark_completed(test_user_a, entry.id)
        assert completed.status == WatchStatus.COMPLETED
        assert completed.watched_episodes == 28

    # 7. Rating and personal notes
    def test_rating_and_notes_validation(self, test_user_a, anime_frieren):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id)

        # Valid rating (9) and note
        updated = service.update_entry(test_user_a, entry.id, rating=9, note="Masterpiece pacing and emotional depth.")
        assert updated.rating == 9
        assert "Masterpiece" in updated.note

        # Rating out of bounds (11)
        with pytest.raises(ValidationError):
            service.update_entry(test_user_a, entry.id, rating=11)

        # Rating out of bounds (0)
        with pytest.raises(ValidationError):
            service.update_entry(test_user_a, entry.id, rating=0)

        # Note exceeding 2000 chars
        with pytest.raises(ValidationError):
            service.update_entry(test_user_a, entry.id, note="X" * 2001)

    # 8. Remove anime from watchlist (cascade deletion)
    def test_remove_anime_cascades_progress(self, test_user_a, anime_frieren):
        service = TrackingService()
        entry = service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id, status=WatchStatus.WATCHING)
        service.update_progress(test_user_a, entry.id, watched_episodes=10)
        entry_id = entry.id

        assert EpisodeProgress.objects.filter(list_entry_id=entry_id).count() == 10

        # Remove entry
        service.remove_from_watchlist(test_user_a, entry_id)
        assert not UserAnimeList.objects.filter(id=entry_id).exists()
        assert not EpisodeProgress.objects.filter(list_entry_id=entry_id).exists()

    # 9. Demo user session isolation
    def test_demo_user_isolation(self, test_user_a, test_user_b, anime_frieren):
        service = TrackingService()
        entry_a = service.add_to_watchlist(test_user_a, mal_id=anime_frieren.mal_id)

        # User B cannot access User A's entry
        with pytest.raises(NotFoundError):
            service.get_user_entry(test_user_b, entry_a.id)

        # User B cannot update User A's entry
        with pytest.raises(NotFoundError):
            service.update_entry(test_user_b, entry_a.id, rating=10)

        # User B cannot delete User A's entry
        with pytest.raises(NotFoundError):
            service.remove_from_watchlist(test_user_b, entry_a.id)

    # 10. Dashboard statistics updates dynamically from real database records
    def test_dashboard_statistics_updates_dynamically(self, test_user_a, anime_frieren, anime_demon_slayer):
        dash_service = DashboardService()
        track_service = TrackingService()

        # Initial state: 0 completed, 0 episodes, "No ratings yet"
        dash_0 = dash_service.get_dashboard_data(test_user_a)
        assert dash_0['stats']['completed_count'] == 0
        assert dash_0['stats']['total_episodes_watched'] == 0
        assert dash_0['stats']['average_rating'] == "No ratings yet"

        # Add Frieren: watching, 12 eps, rated 10
        entry_1 = track_service.add_to_watchlist(test_user_a, anime_frieren.mal_id, status=WatchStatus.WATCHING)
        track_service.update_progress(test_user_a, entry_1.id, watched_episodes=12)
        track_service.update_entry(test_user_a, entry_1.id, rating=10)

        dash_1 = dash_service.get_dashboard_data(test_user_a)
        assert dash_1['stats']['completed_count'] == 0
        assert dash_1['stats']['total_episodes_watched'] == 12
        assert dash_1['stats']['average_rating'] == 10.0
        assert len(dash_1['watching']) == 1
        assert dash_1['watching'][0]['title'] == "Sousou no Frieren"

        # Add Demon Slayer: completed, 26 eps, rated 8
        entry_2 = track_service.add_to_watchlist(test_user_a, anime_demon_slayer.mal_id, status=WatchStatus.COMPLETED)
        track_service.update_progress(test_user_a, entry_2.id, watched_episodes=26)
        track_service.update_entry(test_user_a, entry_2.id, rating=8)

        dash_2 = dash_service.get_dashboard_data(test_user_a)
        assert dash_2['stats']['completed_count'] == 1
        assert dash_2['stats']['total_episodes_watched'] == 38  # 12 + 26
        assert dash_2['stats']['average_rating'] == 9.0        # (10 + 8) / 2
