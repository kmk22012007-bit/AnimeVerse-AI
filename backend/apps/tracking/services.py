from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.tracking.models import UserAnimeList, EpisodeProgress, WatchStatus
from apps.anime.models import Anime
from apps.anime.jikan_client import JikanClient
from apps.core.exceptions import (
    AnimeverseAPIException,
    DuplicateError,
    ValidationError as CustomValidationError,
    NotFoundError,
)

class TrackingService:
    """
    Manages user watchlist and episode tracking with atomic transactions
    and denormalized consistency per SRS FR-4.1 - FR-4.9.
    """

    def __init__(self, jikan_client=None):
        self.jikan_client = jikan_client or JikanClient()

    def get_user_entry(self, user, entry_id):
        entry = UserAnimeList.objects.filter(id=entry_id, user=user).select_related('anime').first()
        if not entry:
            raise NotFoundError("Watchlist entry not found.", status_code=404)
        return entry

    def add_to_watchlist(self, user, mal_id, status=WatchStatus.PLAN_TO_WATCH):
        if status not in WatchStatus.values:
            raise CustomValidationError(f"Invalid status '{status}'. Must be one of {WatchStatus.values}")

        from apps.anime.content_filter import check_anime_id_is_excluded, is_excluded_adult_anime, BLOCKED_ANIME_MESSAGE
        if check_anime_id_is_excluded(mal_id, self.jikan_client):
            raise CustomValidationError(BLOCKED_ANIME_MESSAGE, details={"mal_id": BLOCKED_ANIME_MESSAGE})

        # Check if already exists in list (SRS: 409 conflict)
        if UserAnimeList.objects.filter(user=user, anime_id=mal_id).exists():
            raise DuplicateError("Anime is already in your watchlist.", details={"mal_id": "Duplicate entry."})

        # Ensure anime record exists in local ANIME table
        anime = Anime.objects.filter(mal_id=mal_id).first()
        if not anime:
            details_payload = self.jikan_client.get_anime_details(mal_id)
            if not details_payload or not details_payload.get('data'):
                raise NotFoundError(f"Anime with MAL ID {mal_id} not found.")

            anime_data = details_payload['data']
            if is_excluded_adult_anime(anime_data):
                raise CustomValidationError(BLOCKED_ANIME_MESSAGE, details={"mal_id": BLOCKED_ANIME_MESSAGE})

            normalized = self.jikan_client.normalize_poster_card(anime_data)

            anime = Anime.objects.create(
                mal_id=mal_id,
                title=normalized['title'],
                poster_url=normalized['poster_url'],
                anime_type=normalized['anime_type'],
                total_episodes=normalized['total_episodes'],
            )

        with transaction.atomic():
            watched = 0
            if status == WatchStatus.COMPLETED and anime.total_episodes:
                watched = anime.total_episodes

            entry = UserAnimeList.objects.create(
                user=user,
                anime=anime,
                status=status,
                watched_episodes=watched
            )

            if watched > 0:
                bulk_episodes = [
                    EpisodeProgress(list_entry=entry, episode_number=i)
                    for i in range(1, watched + 1)
                ]
                EpisodeProgress.objects.bulk_create(bulk_episodes)

        return entry

    def update_progress(self, user, entry_id, watched_episodes):
        """
        SRS PUT /api/list/{id}/progress/
        Atomic update of watched_episodes and 1..N EPISODE_PROGRESS rows.
        """
        entry = self.get_user_entry(user, entry_id)

        try:
            watched_episodes = int(watched_episodes)
        except (ValueError, TypeError):
            raise CustomValidationError("watched_episodes must be an integer.")

        if watched_episodes < 0:
            raise CustomValidationError("watched_episodes cannot be negative.", details={"watched_episodes": "Must be >= 0."})

        total = entry.anime.total_episodes
        if total is not None and watched_episodes > total:
            raise CustomValidationError(
                f"watched_episodes must be between 0 and {total}.",
                details={"watched_episodes": "Above total episodes."}
            )

        with transaction.atomic():
            # DB-02: Synchronize EpisodeProgress rows with new count
            entry.watched_episodes = watched_episodes

            # Automatically set status to Completed if all episodes watched
            if total is not None and watched_episodes == total and total > 0:
                entry.status = WatchStatus.COMPLETED
            elif entry.status == WatchStatus.COMPLETED and total is not None and watched_episodes < total:
                entry.status = WatchStatus.WATCHING
            elif entry.status == WatchStatus.PLAN_TO_WATCH and watched_episodes > 0:
                entry.status = WatchStatus.WATCHING

            entry.save()

            # Remove records > N
            EpisodeProgress.objects.filter(list_entry=entry, episode_number__gt=watched_episodes).delete()

            # Find existing numbers
            existing_eps = set(
                EpisodeProgress.objects.filter(list_entry=entry, episode_number__lte=watched_episodes)
                .values_list('episode_number', flat=True)
            )

            # Insert missing numbers
            missing_eps = [
                EpisodeProgress(list_entry=entry, episode_number=i)
                for i in range(1, watched_episodes + 1)
                if i not in existing_eps
            ]
            if missing_eps:
                EpisodeProgress.objects.bulk_create(missing_eps)

        return entry

    def mark_completed(self, user, entry_id):
        """
        SRS POST /api/list/{id}/complete/
        Sets status to Completed and watched_episodes to total when known.
        """
        entry = self.get_user_entry(user, entry_id)
        total = entry.anime.total_episodes

        with transaction.atomic():
            entry.status = WatchStatus.COMPLETED
            if total is not None and total > 0:
                entry.watched_episodes = total
                entry.save()

                # Sync progress
                existing_eps = set(
                    EpisodeProgress.objects.filter(list_entry=entry).values_list('episode_number', flat=True)
                )
                missing = [
                    EpisodeProgress(list_entry=entry, episode_number=i)
                    for i in range(1, total + 1)
                    if i not in existing_eps
                ]
                if missing:
                    EpisodeProgress.objects.bulk_create(missing)
            else:
                entry.save()

        return entry

    def update_entry(self, user, entry_id, status=None, rating=None, note=None):
        """
        SRS PATCH /api/list/{id}/
        Update status, rating, or personal note.
        """
        entry = self.get_user_entry(user, entry_id)

        with transaction.atomic():
            if status is not None:
                if status not in WatchStatus.values:
                    raise CustomValidationError(f"Invalid status '{status}'.", details={"status": "Invalid choice."})
                entry.status = status
                if status == WatchStatus.COMPLETED and entry.anime.total_episodes:
                    return self.mark_completed(user, entry_id)

            if rating is not None:
                if rating == "" or rating is False:
                    entry.rating = None
                else:
                    try:
                        r_int = int(rating)
                        if not (1 <= r_int <= 10):
                            raise ValueError()
                        entry.rating = r_int
                    except (ValueError, TypeError):
                        raise CustomValidationError("Rating must be an integer between 1 and 10.", details={"rating": "Invalid rating range."})

            if note is not None:
                if len(str(note)) > 2000:
                    raise CustomValidationError("Note cannot exceed 2000 characters.", details={"note": "Max 2000 characters."})
                entry.note = str(note)

            entry.save()

        return entry

    def remove_from_watchlist(self, user, entry_id):
        """
        SRS DELETE /api/list/{id}/
        Removes entry and cascades to episode progress.
        """
        entry = self.get_user_entry(user, entry_id)
        entry.delete()
        return True

    @staticmethod
    def serialize_entry(entry):
        """
        SRS Page 30:
        entry is {id, mal_id, title, poster_url, total_episodes, status,
        watched_episodes, rating, note, updated_at}.
        """
        return {
            'id': entry.id,
            'mal_id': entry.anime.mal_id,
            'title': entry.anime.title,
            'poster_url': entry.anime.poster_url,
            'total_episodes': entry.anime.total_episodes,
            'status': entry.status,
            'watched_episodes': entry.watched_episodes,
            'rating': entry.rating,
            'note': entry.note,
            'updated_at': entry.updated_at.isoformat(),
        }
