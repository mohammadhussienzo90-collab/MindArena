from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Player, CompanionProfile


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True, min_length=8)
    display_name = serializers.CharField(max_length=50)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        player = Player.objects.create(
            user=user,
            display_name=validated_data['display_name'],
        )
        CompanionProfile.objects.create(player=player)
        return user


class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    companion_warmth = serializers.IntegerField(source='companion_profile.warmth', read_only=True)
    companion_humor = serializers.IntegerField(source='companion_profile.humor', read_only=True)

    class Meta:
        model = Player
        fields = [
            'id', 'username', 'display_name', 'avatar_preset', 'avatar_colors',
            'overall_level', 'total_xp', 'premium_tier', 'preferred_lang',
            'onboarding_done', 'companion_warmth', 'companion_humor',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'overall_level', 'total_xp', 'created_at', 'updated_at']


class PlayerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['display_name', 'avatar_preset', 'avatar_colors', 'preferred_lang']
