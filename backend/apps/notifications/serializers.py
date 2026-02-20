from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title_en',
            'title_ar',
            'message_en',
            'message_ar',
            'data',
            'is_read',
            'created_at',
        ]


class NotificationMarkReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
    )
