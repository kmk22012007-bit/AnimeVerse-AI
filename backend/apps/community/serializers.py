from rest_framework import serializers
from apps.community.models import CommunityPost, Review, Comment, Poll, PollOption, CommunityReport

class ReviewCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
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
    is_spoiler = serializers.BooleanField(required=False, default=False)

    def validate_body(self, value):
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError("Review body must contain at least 20 non-whitespace characters.")
        return value.strip()


class PollOptionCreateSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=150, required=True)


class PollCreateSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=255, required=True)
    options = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=150),
        min_length=2,
        max_length=10,
        required=True,
        error_messages={
            'min_length': 'A poll must have at least 2 options.',
            'max_length': 'A poll cannot have more than 10 options.',
        }
    )
    expires_days = serializers.IntegerField(min_value=1, max_value=30, required=False, default=7)


class CommunityPostCreateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=120, required=True, error_messages={
        'max_length': 'Title cannot exceed 120 characters.',
        'required': 'Title is required.'
    })
    body = serializers.CharField(min_length=1, max_length=2000, required=True, error_messages={
        'max_length': 'Body cannot exceed 2000 characters.',
        'required': 'Body is required.'
    })
    anime_id = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.ChoiceField(
        choices=CommunityPost.CATEGORY_CHOICES,
        required=False,
        default='discussion'
    )
    tags = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=30),
        max_length=5,
        required=False,
        default=list
    )
    is_spoiler = serializers.BooleanField(required=False, default=False)

    def validate_body(self, value):
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError("Review body must contain at least 20 non-whitespace characters.")
        return value.strip()
    poll = PollCreateSerializer(required=False, allow_null=True)

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty or solely whitespace.")
        return value.strip()

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Body cannot be empty or solely whitespace.")
        return value.strip()

    def validate_tags(self, value):
        if not value:
            return []
        cleaned = []
        for tag in value:
            t = str(tag).strip()
            if t and len(t) <= 30 and t not in cleaned:
                cleaned.append(t)
        return cleaned[:5]


class CommunityPostUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=1, max_length=120, required=False)
    body = serializers.CharField(min_length=1, max_length=2000, required=False)
    category = serializers.ChoiceField(choices=CommunityPost.CATEGORY_CHOICES, required=False)
    tags = serializers.ListField(child=serializers.CharField(min_length=1, max_length=30), max_length=5, required=False)
    is_spoiler = serializers.BooleanField(required=False)

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty or solely whitespace.")
        return value.strip()

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Body cannot be empty or solely whitespace.")
        return value.strip()

    def validate_tags(self, value):
        if not value:
            return []
        cleaned = []
        for tag in value:
            t = str(tag).strip()
            if t and len(t) <= 30 and t not in cleaned:
                cleaned.append(t)
        return cleaned[:5]


class CommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=500, required=True, error_messages={
        'max_length': 'Comment cannot exceed 500 characters.',
        'required': 'Comment body is required.'
    })
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    is_spoiler = serializers.BooleanField(required=False, default=False)

    def validate_body(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Comment body cannot be empty or solely whitespace.")
        return value.strip()


class CommentUpdateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=500, required=False)
    is_spoiler = serializers.BooleanField(required=False)


class PollVoteSerializer(serializers.Serializer):
    option_id = serializers.IntegerField(required=True)


class CommunityReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=CommunityReport.TARGET_TYPE_CHOICES, required=True)
    target_id = serializers.IntegerField(required=True)
    reason = serializers.ChoiceField(choices=CommunityReport.REASON_CHOICES, required=True)
    explanation = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')


class ModerationReportActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CommunityReport.STATUS_CHOICES, required=False)
    action_taken = serializers.ChoiceField(choices=CommunityReport.ACTION_CHOICES, required=False)
    moderator_notes = serializers.CharField(max_length=1000, required=False, allow_blank=True, default='')
