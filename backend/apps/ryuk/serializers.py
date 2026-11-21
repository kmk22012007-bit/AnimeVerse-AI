from rest_framework import serializers

class RyukMessageSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=1000, required=True, error_messages={
        'min_length': 'Message cannot be empty.',
        'max_length': 'Message cannot exceed 1000 characters.',
        'required': 'Message is required.'
    })
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    anime_mal_id = serializers.IntegerField(required=False, allow_null=True)
