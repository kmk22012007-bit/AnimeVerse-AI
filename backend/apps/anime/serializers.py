from rest_framework import serializers

class AnimeSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(min_length=2, max_length=100, required=True, error_messages={
        'min_length': 'Search query must be at least 2 characters.',
        'max_length': 'Search query cannot exceed 100 characters.',
        'required': 'Search query "q" is required.'
    })
    page = serializers.IntegerField(min_value=1, default=1, required=False)

class AnimeBrowseQuerySerializer(serializers.Serializer):
    genre = serializers.CharField(required=False, allow_blank=True)
    min_score = serializers.FloatField(min_value=0.0, max_value=10.0, required=False, error_messages={
        'min_value': 'Minimum score must be at least 0.',
        'max_value': 'Minimum score cannot exceed 10.',
    })
    type = serializers.ChoiceField(
        choices=['TV', 'Movie', 'OVA', 'Special', 'ONA', 'Music', 'tv', 'movie', 'ova', 'special', 'ona', 'music'],
        required=False,
        error_messages={'invalid_choice': 'Type must be one of TV, Movie, OVA, Special, ONA, or Music.'}
    )
    status = serializers.ChoiceField(
        choices=['airing', 'complete', 'upcoming'],
        required=False,
        error_messages={'invalid_choice': 'Status must be one of airing, complete, or upcoming.'}
    )
    page = serializers.IntegerField(min_value=1, default=1, required=False)
