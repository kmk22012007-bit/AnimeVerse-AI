from rest_framework import serializers

class RyukMessageSerializer(serializers.Serializer):
    message = serializers.CharField(
        min_length=1,
        max_length=2000,
        required=True,
        error_messages={
            'min_length': 'Message cannot be empty.',
            'max_length': 'Message cannot exceed 2000 characters.',
            'required': 'Message is required.'
        }
    )
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    anime_mal_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty or solely whitespace.")
        return value.strip()


class RyukRecommendationQuerySerializer(serializers.Serializer):
    genre = serializers.CharField(required=False, allow_blank=True, max_length=50)
    limit = serializers.IntegerField(min_value=1, max_value=20, default=6, required=False)
    refresh = serializers.BooleanField(default=False, required=False)
    mode = serializers.ChoiceField(
        choices=['personalized', 'different'],
        default='personalized',
        required=False
    )
