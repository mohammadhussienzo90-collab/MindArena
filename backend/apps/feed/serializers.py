from rest_framework import serializers
from .models import FeedItem


class FeedItemSerializer(serializers.ModelSerializer):
    realm_slug = serializers.CharField(source='realm.slug', read_only=True, default=None)

    class Meta:
        model = FeedItem
        fields = [
            'id', 'slug', 'content_type', 'realm_slug',
            'title_en', 'title_ar', 'body_en', 'body_ar',
            'image_url', 'difficulty', 'xp_value',
        ]


class FeedInteractionSerializer(serializers.Serializer):
    liked = serializers.BooleanField(required=False, default=False)
    completed = serializers.BooleanField(required=False, default=False)
