from rest_framework import serializers
from .models import (
    PlayerRealmStat, PlayerChallengeResult, PlayerQuestProgress,
    XPTransaction, Achievement, PlayerAchievement, DailyStreak,
)


class PlayerRealmStatSerializer(serializers.ModelSerializer):
    realm_slug = serializers.CharField(source='realm.slug', read_only=True)
    realm_name = serializers.CharField(source='realm.name_en', read_only=True)

    class Meta:
        model = PlayerRealmStat
        fields = [
            'realm_slug', 'realm_name', 'realm_level', 'realm_xp',
            'challenges_completed', 'challenges_perfect', 'quests_completed',
            'visual_stage',
        ]


class PlayerChallengeResultSerializer(serializers.ModelSerializer):
    challenge_slug = serializers.CharField(source='challenge.slug', read_only=True)

    class Meta:
        model = PlayerChallengeResult
        fields = [
            'challenge_slug', 'score', 'is_correct', 'time_taken_secs',
            'xp_earned', 'played_at',
        ]


class PlayerQuestProgressSerializer(serializers.ModelSerializer):
    quest_slug = serializers.CharField(source='quest.slug', read_only=True)
    quest_title = serializers.CharField(source='quest.title_en', read_only=True)

    class Meta:
        model = PlayerQuestProgress
        fields = [
            'quest_slug', 'quest_title', 'status',
            'challenges_completed', 'challenges_total',
            'started_at', 'completed_at',
        ]


class XPTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XPTransaction
        fields = ['amount', 'source', 'source_id', 'created_at']


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = [
            'slug', 'title_en', 'title_ar', 'description_en',
            'icon', 'category', 'xp_reward',
        ]


class PlayerAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = PlayerAchievement
        fields = ['achievement', 'earned_at']


class DailyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStreak
        fields = ['current_streak', 'longest_streak', 'last_active_date']
