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
