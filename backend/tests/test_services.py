import pytest
from apps.profiles.models import User
from apps.anime.models import Anime
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus
from apps.tracking.services import TrackingService
from apps.dashboard.services import DashboardService
from apps.ryuk.services import RyukService
from apps.core.exceptions import ValidationError as CustomValidationError, DuplicateError, NotFoundError

class MockJikanClient:
    def get_anime_details(self, mal_id):
        return {
            'data': {
                'mal_id': mal_id,
                'title': f'Mock Anime {mal_id}',
                'type': 'TV',
                'episodes': 24,
                'score': 8.5,
                'images': {'jpg': {'image_url': 'https://example.com/mock.jpg'}},
                'genres': [{'name': 'Action'}]
            }
        }

    def normalize_poster_card(self, item):
        return {
            'mal_id': item.get('mal_id'),
            'title': item.get('title'),
            'poster_url': 'https://example.com/mock.jpg',
            'score': item.get('score'),
            'anime_type': item.get('type'),
            'total_episodes': item.get('episodes'),
        }

    def get_trending_anime(self, page=1):
        return {
            'data': [
                {'mal_id': 1, 'title': 'Trending 1', 'type': 'TV', 'episodes': 12, 'score': 9.0},
                {'mal_id': 2, 'title': 'Trending 2', 'type': 'TV', 'episodes': 24, 'score': 8.8},
            ]
        }

    def search_anime(self, q, page=1):
        return {'data': [{'mal_id': 1, 'title': 'Search Result 1', 'score': 8.0, 'type': 'TV', 'episodes': 12}]}

    def get_popular_anime(self, page=1):
        return {'data': [{'mal_id': 10, 'title': 'Popular 1', 'score': 9.2, 'type': 'TV', 'episodes': 25}]}


@pytest.mark.django_db
class TestTrackingService:
    def test_ut_03_validation_error_when_exceeding_total_episodes(self):
        """UT-03: Entry with 26 total episodes, request for 27 watched -> Validation error"""
        user = User.objects.create(session_key="t1" * 32)
        anime = Anime.objects.create(mal_id=101, title="Series 101", total_episodes=26)
        entry = UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=10)

        service = TrackingService(jikan_client=MockJikanClient())
        with pytest.raises(CustomValidationError) as exc_info:
            service.update_progress(user, entry.id, watched_episodes=27)

        assert "watched_episodes must be between 0 and 26" in str(exc_info.value)
        entry.refresh_from_db()
        assert entry.watched_episodes == 10  # no change saved

    def test_db_02_set_watched_episodes_3_then_1(self):
        """DB-02: Set watched episodes to 3, then 1 -> One EPISODE_PROGRESS remains (ep 1)"""
        user = User.objects.create(session_key="t2" * 32)
        anime = Anime.objects.create(mal_id=102, title="Series 102", total_episodes=12)
        entry = UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=0)

        service = TrackingService(jikan_client=MockJikanClient())

        # Set to 3
        service.update_progress(user, entry.id, watched_episodes=3)
        entry.refresh_from_db()
        assert entry.watched_episodes == 3
        assert EpisodeProgress.objects.filter(list_entry=entry).count() == 3
        assert set(EpisodeProgress.objects.filter(list_entry=entry).values_list('episode_number', flat=True)) == {1, 2, 3}

        # Set to 1
        service.update_progress(user, entry.id, watched_episodes=1)
        entry.refresh_from_db()
        assert entry.watched_episodes == 1
        remaining = list(EpisodeProgress.objects.filter(list_entry=entry).values_list('episode_number', flat=True))
        assert remaining == [1]

    def test_mark_completed_sets_all_episodes(self):
        user = User.objects.create(session_key="t3" * 32)
        anime = Anime.objects.create(mal_id=103, title="Series 103", total_episodes=12)
        entry = UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.WATCHING, watched_episodes=4)

        service = TrackingService(jikan_client=MockJikanClient())
        service.mark_completed(user, entry.id)

        entry.refresh_from_db()
        assert entry.status == WatchStatus.COMPLETED
        assert entry.watched_episodes == 12
        assert EpisodeProgress.objects.filter(list_entry=entry).count() == 12

    def test_duplicate_add_raises_conflict(self):
        user = User.objects.create(session_key="t4" * 32)
        anime = Anime.objects.create(mal_id=104, title="Series 104")
        UserAnimeList.objects.create(user=user, anime=anime, status=WatchStatus.PLAN_TO_WATCH)

        service = TrackingService(jikan_client=MockJikanClient())
        with pytest.raises(DuplicateError):
            service.add_to_watchlist(user, mal_id=104, status=WatchStatus.WATCHING)


@pytest.mark.django_db
class TestDashboardService:
    def test_ut_01_average_rating_calculated(self):
        """UT-01: Three list entries with ratings 8, 7, and empty -> Average rating is 7.5"""
        user = User.objects.create(session_key="d1" * 32, display_name="TestFan")
        a1 = Anime.objects.create(mal_id=201, title="Anime 1", total_episodes=12)
        a2 = Anime.objects.create(mal_id=202, title="Anime 2", total_episodes=12)
        a3 = Anime.objects.create(mal_id=203, title="Anime 3", total_episodes=12)

        UserAnimeList.objects.create(user=user, anime=a1, status=WatchStatus.COMPLETED, rating=8, watched_episodes=12)
        UserAnimeList.objects.create(user=user, anime=a2, status=WatchStatus.COMPLETED, rating=7, watched_episodes=12)
        UserAnimeList.objects.create(user=user, anime=a3, status=WatchStatus.WATCHING, rating=None, watched_episodes=5)

        service = DashboardService(jikan_client=MockJikanClient())
        dash = service.get_dashboard_data(user)

        assert dash['welcome']['display_name'] == "TestFan"
        assert dash['stats']['completed_count'] == 2
        assert dash['stats']['total_episodes_watched'] == 29
        assert dash['stats']['average_rating'] == 7.5

    def test_ut_02_no_rated_entries(self):
        """UT-02: No rated entries -> Average rating text is 'No ratings yet'"""
        user = User.objects.create(session_key="d2" * 32)
        a1 = Anime.objects.create(mal_id=204, title="Anime 4")
        UserAnimeList.objects.create(user=user, anime=a1, status=WatchStatus.PLAN_TO_WATCH, rating=None)

        service = DashboardService(jikan_client=MockJikanClient())
        dash = service.get_dashboard_data(user)

        assert dash['stats']['average_rating'] == "No ratings yet"


@pytest.mark.django_db
class TestRyukService:
    def test_ai_01_fallback_when_unconfigured(self):
        """AI-01: RYUK message with no AI key set -> is_fallback: True, and Discovery suggestions included"""
        user = User.objects.create(session_key="r1" * 32)
        service = RyukService(ai_provider=None, jikan_client=MockJikanClient())

        res = service.process_message(user, "Recommend me some psychological anime.")
        assert res['is_fallback'] is True
        assert res['message'] == "RYUK is unavailable right now."
        assert len(res['suggestions']) > 0
        assert res['suggestions'][0]['mal_id'] == 1

    def test_ai_04_summarize_progress_uses_stored_counts(self):
        """AI-04: Message 'Summarize my progress' with seeded data -> Summary uses stored counts, not provider output"""
        user = User.objects.create(session_key="r2" * 32, display_name="OtakuMaster")
        a1 = Anime.objects.create(mal_id=301, title="Bleach", total_episodes=366)
        a2 = Anime.objects.create(mal_id=302, title="Hunter x Hunter", total_episodes=148)

        UserAnimeList.objects.create(user=user, anime=a1, status=WatchStatus.COMPLETED, watched_episodes=366, rating=9)
        UserAnimeList.objects.create(user=user, anime=a2, status=WatchStatus.WATCHING, watched_episodes=75, rating=10)

        service = RyukService(ai_provider=None, jikan_client=MockJikanClient())
        res = service.process_message(user, "Summarize my progress")

        assert res['is_fallback'] is False
        reply = res['reply']
        assert "Completed: 1 series" in reply
        assert "Currently Watching: 1 series" in reply
        assert "Total Episodes Watched: 441 episodes" in reply
        assert "9.5/10" in reply
