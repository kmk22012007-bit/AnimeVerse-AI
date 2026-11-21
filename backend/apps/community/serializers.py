from rest_framework import serializers

class ReviewCreateUpdateSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=10, required=True, error_messages={
        'min_value': 'Score must be between 1 and 10.',
        'max_value': 'Score must be between 1 and 10.',
        'required': 'Score is required.'
    })
    body = serializers.CharField(min_length=20, max_length=2000, required=True, error_messages={
        'min_length': 'Review body must be at least 20 characters.',
        'max_length': 'Review body cannot exceed 2000 characters.',
        'required': 'Review body is required.'
    })

class CommunityPostCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=120, required=True, error_messages={
        'max_length': 'Title cannot exceed 120 characters.',
        'required': 'Title is required.'
    })
    body = serializers.CharField(min_length=1, max_length=2000, required=True, error_messages={
        'max_length': 'Body cannot exceed 2000 characters.',
        'required': 'Body is required.'
    })

class CommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=500, required=True, error_messages={
        'max_length': 'Comment cannot exceed 500 characters.',
        'required': 'Comment body is required.'
    })
