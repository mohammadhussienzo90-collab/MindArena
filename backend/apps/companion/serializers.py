from rest_framework import serializers
from .models import CompanionConversation, CompanionMessage


class CompanionMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanionMessage
        fields = ['role', 'content', 'created_at']


class CompanionChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    conversation_id = serializers.IntegerField(required=False)
