from rest_framework import serializers
from apps.tracking.models import WatchStatus

class AddWatchlistSerializer(serializers.Serializer):
    mal_id = serializers.IntegerField(required=True, error_messages={'required': 'mal_id is required.'})
    status = serializers.ChoiceField(
        choices=WatchStatus.choices,
        default=WatchStatus.PLAN_TO_WATCH,
        error_messages={'invalid_choice': f'Status must be one of {WatchStatus.values}'}
    )

class UpdateWatchlistSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=WatchStatus.choices, required=False)
    rating = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True, error_messages={
        'min_value': 'Rating must be between 1 and 10.',
        'max_value': 'Rating must be between 1 and 10.',
    })
    note = serializers.CharField(max_length=2000, required=False, allow_blank=True, allow_null=True, error_messages={
        'max_length': 'Note cannot exceed 2000 characters.'
    })

class UpdateProgressSerializer(serializers.Serializer):
    watched_episodes = serializers.IntegerField(min_value=0, required=True, error_messages={
        'min_value': 'watched_episodes must be an integer 0 or greater.',
        'required': 'watched_episodes is required.'
    })
