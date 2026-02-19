from rest_framework import serializers
from .models import Realm, Quest, Challenge


class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = [
            'id', 'slug', 'challenge_type', 'title_en', 'title_ar',
            'description_en', 'content', 'difficulty', 'primary_trait',
            'time_limit_secs', 'base_xp', 'bonus_xp', 'sort_order', 'scene_id',
        ]


class ChallengeSubmitSerializer(serializers.Serializer):
    answer_data = serializers.DictField()
    time_taken_secs = serializers.FloatField(min_value=0)


class QuestListSerializer(serializers.ModelSerializer):
    challenge_count = serializers.IntegerField(source='challenges.count', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'slug', 'title_en', 'title_ar', 'quest_type',
            'sort_order', 'xp_reward', 'required_realm_level', 'challenge_count',
        ]


class QuestDetailSerializer(serializers.ModelSerializer):
    challenges = ChallengeSerializer(many=True, read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'slug', 'title_en', 'title_ar', 'description_en',
            'quest_type', 'sort_order', 'xp_reward', 'required_realm_level',
            'stat_reward', 'intro_dialogue', 'outro_dialogue', 'world_position',
            'challenges',
        ]


class RealmListSerializer(serializers.ModelSerializer):
    quest_count = serializers.IntegerField(source='quests.count', read_only=True)

    class Meta:
        model = Realm
        fields = [
            'id', 'slug', 'name_en', 'name_ar', 'description_en', 'icon',
            'color_primary', 'color_secondary', 'unlock_level', 'sort_order',
            'primary_trait', 'quest_count',
        ]


class RealmDetailSerializer(serializers.ModelSerializer):
    quests = QuestListSerializer(many=True, read_only=True)

    class Meta:
        model = Realm
        fields = [
            'id', 'slug', 'name_en', 'name_ar', 'description_en', 'description_ar',
            'icon', 'color_primary', 'color_secondary', 'unlock_level', 'sort_order',
            'primary_trait', 'secondary_trait', 'quests',
        ]
