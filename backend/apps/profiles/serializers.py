from rest_framework import serializers

class ProfileUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(min_length=1, max_length=40, required=False, error_messages={
        'min_length': 'Display name cannot be empty.',
        'max_length': 'Display name cannot exceed 40 characters.',
    })
    bio = serializers.CharField(max_length=300, required=False, allow_blank=True, allow_null=True, error_messages={
        'max_length': 'Bio cannot exceed 300 characters.',
    })
    is_public = serializers.BooleanField(required=False)

    def validate_display_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Display name cannot be empty or solely whitespace.")
        return value.strip()

    def validate(self, attrs):
        # Explicit mass-assignment security protection:
        # Strictly reject any attempts to set privileged fields
        initial_data = getattr(self, 'initial_data', {})
        privileged_fields = {'role', 'is_staff', 'is_superuser', 'auth_user_id', 'session_key'}
        attempted_privileged = privileged_fields.intersection(initial_data.keys())
        if attempted_privileged:
            raise serializers.ValidationError(
                f"Modifying privileged fields ({', '.join(sorted(attempted_privileged))}) is strictly prohibited."
            )
        return attrs


class UserPreferencesSerializer(serializers.Serializer):
    preferred_genres = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=30,
        required=False,
        default=list
    )
    preferred_formats = serializers.ListField(
        child=serializers.CharField(max_length=20),
        max_length=30,
        required=False,
        default=list
    )
    excluded_genres = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=30,
        required=False,
        default=list
    )
    recommendation_diversity = serializers.ChoiceField(
        choices=['focused', 'balanced', 'exploratory'],
        default='balanced',
        required=False
    )
    enable_personalized_recommendations = serializers.BooleanField(default=True, required=False)
    enable_dashboard_personalization = serializers.BooleanField(default=True, required=False)
    enable_discovery_personalization = serializers.BooleanField(default=True, required=False)
