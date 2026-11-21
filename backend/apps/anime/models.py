from django.db import models

class Anime(models.Model):
    """
    SRS ANIME entity.
    Cache of identifiers and display fields only.
    """
    mal_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    poster_url = models.CharField(max_length=500, null=True, blank=True)
    anime_type = models.CharField(max_length=20, null=True, blank=True)
    total_episodes = models.IntegerField(null=True, blank=True)
    last_fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'anime'
        ordering = ['title']

    def __str__(self):
        return f"{self.title} (MAL ID: {self.mal_id})"

class JikanCache(models.Model):
    """
    SRS JIKAN_CACHE entity.
    Supporting table storing cached Jikan response payloads.
    """
    cache_key = models.CharField(max_length=255, primary_key=True)
    payload = models.JSONField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'jikan_cache'

    def __str__(self):
        return f"Cache {self.cache_key}"


class RelationshipType(models.TextChoices):
    MAIN_SERIES = 'main_series', 'Main Series'
    SEQUEL = 'sequel', 'Sequel'
    PREQUEL = 'prequel', 'Prequel'
    MOVIE = 'movie', 'Movie'
    OVA = 'ova', 'OVA'
    ONA = 'ona', 'ONA'
    SPECIAL = 'special', 'Special'
    SIDE_STORY = 'side_story', 'Side Story'
    SPIN_OFF = 'spin_off', 'Spin-off'
    ALTERNATIVE_VERSION = 'alternative_version', 'Alternative Version'
    OTHER = 'other', 'Other Related Entry'


class Franchise(models.Model):
    """
    Franchise entity grouping multiple related anime entries
    (e.g., Black Clover TV, movie, sequels, specials, OVAs).
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    cover_image = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'franchise'
        ordering = ['name']

    def __str__(self):
        return self.name


class FranchiseEntry(models.Model):
    """
    Join table linking an anime entry to a franchise with verified relationship metadata.
    """
    franchise = models.ForeignKey(Franchise, on_delete=models.CASCADE, related_name='entries')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='franchise_entries')
    relationship_type = models.CharField(
        max_length=30,
        choices=RelationshipType.choices,
        default=RelationshipType.MAIN_SERIES
    )
    display_order = models.IntegerField(default=0)
    is_main_entry = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'franchise_entry'
        unique_together = ('franchise', 'anime')
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.franchise.name} - {self.anime.title} ({self.get_relationship_type_display()})"


class TrackType(models.TextChoices):
    ORIGINAL_AUDIO = 'original_audio', 'Original Audio'
    DUBBED_AUDIO = 'dubbed_audio', 'Dubbed Audio'
    SUBTITLES = 'subtitles', 'Subtitles'


class VerificationStatus(models.TextChoices):
    LICENSOR_CONFIRMED = 'licensor_confirmed', 'Licensor Confirmed'
    PROVIDER_REPORTED = 'provider_reported', 'Provider Reported'
    UNVERIFIED = 'unverified', 'Unverified'


class StreamingLanguageTrack(models.Model):
    """
    Verified audio and subtitle language tracks for legal streaming providers.
    Never infers language availability from platform name or catalogue.
    """
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='language_tracks')
    provider_name = models.CharField(max_length=100)
    country = models.CharField(max_length=10, default='IN')
    audio_language = models.CharField(max_length=50, null=True, blank=True)
    subtitle_language = models.CharField(max_length=50, null=True, blank=True)
    track_type = models.CharField(
        max_length=30,
        choices=TrackType.choices,
        default=TrackType.ORIGINAL_AUDIO
    )
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PROVIDER_REPORTED
    )
    source_url = models.CharField(max_length=500, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'streaming_language_track'
        indexes = [
            models.Index(fields=['anime', 'country']),
            models.Index(fields=['audio_language']),
            models.Index(fields=['subtitle_language']),
        ]

    def __str__(self):
        return f"{self.anime.title} - {self.provider_name} ({self.country}) [Audio: {self.audio_language}, Sub: {self.subtitle_language}]"
