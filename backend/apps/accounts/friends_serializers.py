from rest_framework import serializers
from .models import Player
from .friends_models import FriendRequest


class FriendSerializer(serializers.ModelSerializer):
    elo_rating = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ['id', 'display_name', 'avatar_preset', 'overall_level', 'elo_rating']

    def get_elo_rating(self, obj):
        try:
            return obj.arena_stats.elo_rating
        except Exception:
            return 1000


class FriendRequestSerializer(serializers.ModelSerializer):
    from_player = FriendSerializer(read_only=True)
    to_player = FriendSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ['id', 'from_player', 'to_player', 'message', 'status', 'created_at']


class SendFriendRequestSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    message = serializers.CharField(required=False, max_length=200, default='')


class RespondFriendRequestSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['accept', 'reject'])
