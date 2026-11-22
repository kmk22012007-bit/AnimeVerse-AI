from rest_framework import serializers
from apps.notifications.models import Notification, NotificationPreference
from apps.anime.models import Anime

class RelatedAnimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anime
        fields = ['mal_id', 'title', 'poster_url', 'anime_type']

class NotificationSerializer(serializers.ModelSerializer):
    related_anime = RelatedAnimeSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'related_anime',
            'related_community_id',
            'is_read',
            'action_url',
            'created_at',
        ]
        read_only_fields = fields

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'anime_releases',
            'episode_releases',
            'community_likes',
            'community_comments',
            'watchlist_reminders',
            'system_notices',
            'updated_at',
        ]
        read_only_fields = ['updated_at']
