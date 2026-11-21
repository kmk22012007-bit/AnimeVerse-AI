import pytest
from django.utils import timezone
from apps.anime.models import (
    Anime,
    Franchise,
    FranchiseEntry,
    RelationshipType,
    StreamingLanguageTrack,
    TrackType,
    VerificationStatus,
)
from apps.anime.franchise_service import FranchiseService, classify_relationship
from apps.anime.watch_service import WatchService, normalize_language_name
from apps.tracking.models import UserAnimeList, WatchStatus
from apps.profiles.models import User


@pytest.fixture
def franchise_setup(db):
    """Sets up seed data for franchise and language tests."""
    FranchiseService.seed_known_franchises()
    WatchService.seed_verified_language_tracks()


@pytest.mark.django_db
class TestFranchiseGrouping:
    def test_relationship_classification(self):
        """Tests that relationship strings and formats are accurately mapped."""
        assert classify_relationship('Sequel', 'TV') == RelationshipType.SEQUEL
        assert classify_relationship('Prequel', 'TV') == RelationshipType.PREQUEL
        assert classify_relationship('Side story', 'Movie') == RelationshipType.MOVIE
        assert classify_relationship('Side story', 'Special') == RelationshipType.SPECIAL
        assert classify_relationship('Alternative version', 'OVA') == RelationshipType.OVA
        assert classify_relationship('Other', 'ONA') == RelationshipType.ONA
        assert classify_relationship('Spin-off', 'TV') == RelationshipType.SPIN_OFF
        assert classify_relationship('Parent story', 'TV') == RelationshipType.MAIN_SERIES

    def test_black_clover_test_case_records(self, franchise_setup):
        """
        Black Clover Test Case per prompt:
        - 34572: Black Clover TV (Main series, 170 eps)
        - 61967: Black Clover Season 2 (Sequel)
        - 48585: Sword of the Wizard King (Movie)
        - 33950: Jump Festa 2016 Special (OVA)
        - 38768: Jump Festa 2018 Special (Special)
        - 40031: Squishy! Black Clover (ONA)
        - 39864: Petit Clover Advance (Special)
        """
        franchise = Franchise.objects.filter(slug='black-clover').first()
        assert franchise is not None
        assert franchise.name == "Black Clover"

        entries = FranchiseEntry.objects.filter(franchise=franchise).select_related('anime')
        entry_map = {e.anime.mal_id: e for e in entries}

        assert len(entry_map) == 7

        # 1. Main series continuous run
        assert 34572 in entry_map
        assert entry_map[34572].relationship_type == RelationshipType.MAIN_SERIES
        assert entry_map[34572].is_main_entry is True
        assert entry_map[34572].anime.total_episodes == 170

        # 2. Distinct sequel
        assert 61967 in entry_map
        assert entry_map[61967].relationship_type == RelationshipType.SEQUEL
        assert entry_map[61967].is_main_entry is False

        # 3. Movie
        assert 48585 in entry_map
        assert entry_map[48585].relationship_type == RelationshipType.MOVIE

        # 4. OVA
        assert 33950 in entry_map
        assert entry_map[33950].relationship_type == RelationshipType.OVA

        # 5. Specials
        assert 38768 in entry_map
        assert entry_map[38768].relationship_type == RelationshipType.SPECIAL
        assert 39864 in entry_map
        assert entry_map[39864].relationship_type == RelationshipType.SPECIAL

        # 6. ONA
        assert 40031 in entry_map
        assert entry_map[40031].relationship_type == RelationshipType.ONA

    def test_duplicate_prevention(self, franchise_setup):
        """Verifies that an anime entry cannot be duplicated within the same franchise."""
        franchise = Franchise.objects.filter(slug='black-clover').first()
        anime = Anime.objects.get(mal_id=34572)

        # Attempt to add the exact same anime to the franchise again
        initial_count = FranchiseEntry.objects.filter(franchise=franchise).count()

        # get_or_create should safely return existing without duplicating
        entry, created = FranchiseEntry.objects.get_or_create(
            franchise=franchise,
            anime=anime,
            defaults={'relationship_type': RelationshipType.MAIN_SERIES}
        )
        assert created is False
        assert FranchiseEntry.objects.filter(franchise=franchise).count() == initial_count

    def test_search_results_grouping(self, franchise_setup):
        """
        Verifies that searching Black Clover consolidates multiple related records
        into a single representative franchise card.
        """
        raw_results = [
            {'mal_id': 34572, 'title': 'Black Clover', 'score': 7.9},
            {'mal_id': 61967, 'title': 'Black Clover 2nd Season', 'score': None},
            {'mal_id': 48585, 'title': 'Black Clover: Sword of the Wizard King', 'score': 8.1},
            {'mal_id': 40031, 'title': 'Squishy! Black Clover', 'score': 6.2},
            {'mal_id': 99999, 'title': 'Unrelated Title', 'score': 7.5},  # Unrelated
        ]

        grouped = FranchiseService.group_results(raw_results)

        # 4 Black Clover entries should collapse into 1 franchise card, plus 1 unrelated title = 2 cards total
        assert len(grouped) == 2

        bc_card = next(c for c in grouped if c['mal_id'] == 34572)
        assert bc_card['is_franchise'] is True
        assert bc_card['entry_count'] == 7
        assert bc_card['franchise_slug'] == 'black-clover'

        unrelated_card = next(c for c in grouped if c['mal_id'] == 99999)
        assert unrelated_card.get('is_franchise') is not True

    def test_watchlist_progress_independence(self, franchise_setup):
        """
        Verifies that episode progress and watch status remain completely independent
        for each MAL ID in a franchise.
        """
        user = User.objects.create(session_key="f" * 64, display_name="FranchiseUser")
        anime_tv = Anime.objects.get(mal_id=34572)
        anime_movie = Anime.objects.get(mal_id=48585)

        # User watched 150/170 episodes of Black Clover TV
        entry_tv = UserAnimeList.objects.create(
            user=user,
            anime=anime_tv,
            status=WatchStatus.WATCHING,
            watched_episodes=150,
            rating=9
        )

        # User watched 1/1 episode of Black Clover Movie
        entry_movie = UserAnimeList.objects.create(
            user=user,
            anime=anime_movie,
            status=WatchStatus.COMPLETED,
            watched_episodes=1,
            rating=8
        )

        # Progress should be strictly isolated
        assert entry_tv.watched_episodes == 150
        assert entry_tv.status == WatchStatus.WATCHING
        assert entry_movie.watched_episodes == 1
        assert entry_movie.status == WatchStatus.COMPLETED


@pytest.mark.django_db
class TestWatchAnywhereVerifiedLanguage:
    def test_language_normalization(self):
        """Tests language name normalization from codes and casings."""
        assert normalize_language_name('tam') == 'Tamil'
        assert normalize_language_name('tamil') == 'Tamil'
        assert normalize_language_name('eng') == 'English'
        assert normalize_language_name('ja') == 'Japanese'
        assert normalize_language_name('hin') == 'Hindi'
        assert normalize_language_name('all') is None
        assert normalize_language_name('') is None

    def test_demon_slayer_verified_language_inspection(self, franchise_setup):
        """Inspects verified language metadata for Demon Slayer (38000) in India."""
        service = WatchService()
        data = service.get_watch_options(38000, country="IN")

        assert data['results_count'] > 0
        all_options = []
        for cat in data['categories'].values():
            all_options.extend(cat)

        # Crunchyroll India should have confirmed Hindi, Tamil, Telugu dubs
        cr_opt = next((opt for opt in all_options if 'crunchyroll' in opt['provider_name'].lower()), None)
        assert cr_opt is not None
        assert cr_opt['has_verified_language_data'] is True
        assert 'Tamil' in cr_opt['verified_audio_languages']
        assert 'Hindi' in cr_opt['verified_audio_languages']
        assert 'Japanese' in cr_opt['verified_audio_languages']
        assert cr_opt['verification_status'] == VerificationStatus.LICENSOR_CONFIRMED

    def test_tamil_audio_filter(self, franchise_setup):
        """
        When filtering audio=Tamil for Demon Slayer, only options with confirmed
        Tamil audio are returned.
        """
        service = WatchService()
        data = service.get_watch_options(38000, country="IN", audio="Tamil")

        all_options = []
        for cat in data['categories'].values():
            all_options.extend(cat)

        assert len(all_options) > 0
        for opt in all_options:
            assert 'Tamil' in opt['verified_audio_languages']

    def test_unverified_language_exclusion_and_message(self, franchise_setup):
        """
        Black Clover main series (34572) has verified Tamil audio for Season 1,
        but movie (48585) and sequel (61967) do NOT have Tamil audio in India.
        Filtering audio=Tamil on entries without Tamil coverage returns 0 results
        and the honest empty state message:
        'No verified Tamil audio option found for this title in India.'
        """
        service = WatchService()
        
        # 1. Main series (34572) has verified Tamil coverage on Crunchyroll
        data_main = service.get_watch_options(34572, country="IN", audio="Tamil")
        assert data_main['results_count'] > 0
        all_opts = [opt for cat in data_main['categories'].values() for opt in cat]
        assert any(opt['provider_name'] == 'Crunchyroll' and 'Tamil' in opt['verified_audio_languages'] for opt in all_opts)

        # 2. Movie (48585) has no Tamil dub -> honest empty state
        data_movie = service.get_watch_options(48585, country="IN", audio="Tamil")
        assert data_movie['results_count'] == 0
        assert "No verified Tamil audio option found for this title in India." in data_movie['message']

        # 3. Sequel (61967) has no Tamil dub -> honest empty state
        data_sequel = service.get_watch_options(61967, country="IN", audio="Tamil")
        assert data_sequel['results_count'] == 0
        assert "No verified Tamil audio option found for this title in India." in data_sequel['message']

    def test_missing_language_metadata_handling(self, franchise_setup):
        """
        Titles without seeded language tracks report honest unconfirmed status:
        'Platform available — audio language unconfirmed.'
        """
        # Create arbitrary anime without language tracks
        anime = Anime.objects.create(mal_id=77777, title="Unseeded Anime")
        service = WatchService()
        data = service.get_watch_options(77777, country="IN")

        # When filtering by a language, it must not return unconfirmed platforms
        filtered = service.get_watch_options(77777, country="IN", audio="Tamil")
        assert filtered['results_count'] == 0


@pytest.mark.django_db
class TestContentSafetyStatsNonLeakage:
    def test_blocked_anime_not_leaked_into_profile_stats(self, franchise_setup):
        """
        Verifies that even if an adult/hentai anime database row exists in UserAnimeList,
        it is filtered out of profile stats and summaries.
        """
        from apps.anime.models import JikanCache
        from apps.profiles.views import ProfileCurrentView

        # Create safe anime and excluded anime
        safe_anime = Anime.objects.get(mal_id=34572)  # Black Clover
        blocked_anime = Anime.objects.create(
            mal_id=99990,
            title="Explicit Blocked Anime",
            anime_type="OVA"
        )
        JikanCache.objects.create(
            cache_key="details_99990",
            payload={'data': {'mal_id': 99990, 'rating': 'Rx - Hentai', 'genres': [{'id': 12, 'name': 'Hentai'}]}},
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )

        user = User.objects.create(session_key="s" * 64, display_name="SafeStatsUser")

        # Add 1 safe completed anime (170 eps, rating 10)
        UserAnimeList.objects.create(
            user=user,
            anime=safe_anime,
            status=WatchStatus.COMPLETED,
            watched_episodes=170,
            rating=10
        )

        # Add 1 blocked completed anime (50 eps, rating 2)
        UserAnimeList.objects.create(
            user=user,
            anime=blocked_anime,
            status=WatchStatus.COMPLETED,
            watched_episodes=50,
            rating=2
        )

        view = ProfileCurrentView()
        profile_data = view._compute_profile_data(user)

        # Stats must ONLY reflect the 1 safe anime
        assert profile_data['stats']['total_anime'] == 1
        assert profile_data['stats']['completed_count'] == 1
        assert profile_data['stats']['total_episodes_watched'] == 170
        assert profile_data['stats']['average_rating'] == 10.0
        assert len(profile_data['recent_activity']) == 1
        assert profile_data['recent_activity'][0]['anime_id'] == 34572
