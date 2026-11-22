from rest_framework import serializers

class AnimeSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=100, required=True, error_messages={
        'min_length': 'Search query must be at least 2 characters.',
        'max_length': 'Search query cannot exceed 100 characters.',
        'required': 'Search query "q" is required.'
    })
    page = serializers.IntegerField(min_value=1, default=1, required=False)

class AnimeBrowseQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=100, required=False, allow_blank=True, error_messages={
        'min_length': 'Search query must be at least 2 characters.',
        'max_length': 'Search query cannot exceed 100 characters.',
    })
    genre = serializers.CharField(required=False, allow_blank=True)
    genres = serializers.CharField(required=False, allow_blank=True)
    exclude_genres = serializers.CharField(required=False, allow_blank=True)
    format = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    year = serializers.IntegerField(min_value=1950, max_value=2030, required=False)
    year_from = serializers.IntegerField(min_value=1950, max_value=2030, required=False)
    year_to = serializers.IntegerField(min_value=1950, max_value=2030, required=False)
    min_score = serializers.FloatField(min_value=0.0, max_value=10.0, required=False, error_messages={
        'min_value': 'Minimum score must be at least 0.',
        'max_value': 'Minimum score cannot exceed 10.',
    })
    max_score = serializers.FloatField(min_value=0.0, max_value=10.0, required=False, error_messages={
        'min_value': 'Maximum score must be at least 0.',
        'max_value': 'Maximum score cannot exceed 10.',
    })
    status = serializers.CharField(required=False, allow_blank=True)
    min_episodes = serializers.IntegerField(min_value=0, required=False)
    max_episodes = serializers.IntegerField(min_value=0, required=False)
    audio_language = serializers.CharField(required=False, allow_blank=True, max_length=50)
    country = serializers.CharField(required=False, allow_blank=True, max_length=10)
    sort = serializers.CharField(required=False, allow_blank=True, max_length=30)
    personalized = serializers.BooleanField(required=False, default=False)
    hide_tracked = serializers.BooleanField(required=False, default=False)
    page = serializers.IntegerField(min_value=1, default=1, required=False)
    page_size = serializers.IntegerField(min_value=1, max_value=50, default=20, required=False)

    def validate(self, attrs):
        year_from = attrs.get('year_from')
        year_to = attrs.get('year_to')
        if year_from is not None and year_to is not None and year_from > year_to:
            raise serializers.ValidationError({'year_from': 'year_from cannot be greater than year_to.'})

        min_score = attrs.get('min_score')
        max_score = attrs.get('max_score')
        if min_score is not None and max_score is not None and min_score > max_score:
            raise serializers.ValidationError({'min_score': 'min_score cannot be greater than max_score.'})

        min_episodes = attrs.get('min_episodes')
        max_episodes = attrs.get('max_episodes')
        if min_episodes is not None and max_episodes is not None and min_episodes > max_episodes:
            raise serializers.ValidationError({'min_episodes': 'min_episodes cannot be greater than max_episodes.'})

        return attrs
