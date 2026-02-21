"""
AI Engine Serializers
======================
DRF serializers for all AI engine API endpoints.
"""
from rest_framework import serializers

from apps.ai_engine.models import (
    KnowledgeState,
    LearningPath,
    PlayerAbility,
    PlayerEngagement,
    PlayerSession,
    RecommendationLog,
    SpacedRepetitionCard,
)


# ======================================================================
# Model Serializers
# ======================================================================

class KnowledgeStateSerializer(serializers.ModelSerializer):
    """Serializer for BKT knowledge state per skill."""

    mastered = serializers.SerializerMethodField()
    expected_correct = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeState
        fields = [
            'id', 'skill', 'p_known', 'p_learn', 'p_guess', 'p_slip',
            'observations', 'mastered', 'expected_correct', 'last_updated',
        ]
        read_only_fields = fields

    def get_mastered(self, obj):
        return obj.p_known >= 0.95

    def get_expected_correct(self, obj):
        """P(correct) = P(known)*(1-P(slip)) + P(unknown)*P(guess)."""
        return round(
            obj.p_known * (1.0 - obj.p_slip) + (1.0 - obj.p_known) * obj.p_guess,
            3,
        )


class LearningPathSerializer(serializers.ModelSerializer):
    """Serializer for persisted learning paths."""

    current_focus_realm_slug = serializers.SerializerMethodField()
    current_focus_realm_name = serializers.SerializerMethodField()

    class Meta:
        model = LearningPath
        fields = [
            'id', 'current_focus_realm_slug', 'current_focus_realm_name',
            'current_focus_skill', 'weekly_plan', 'skill_sequence',
            'next_challenges', 'path_version', 'generated_at',
        ]
        read_only_fields = fields

    def get_current_focus_realm_slug(self, obj):
        return obj.current_focus_realm.slug if obj.current_focus_realm else None

    def get_current_focus_realm_name(self, obj):
        return obj.current_focus_realm.name_en if obj.current_focus_realm else None


class EngagementSerializer(serializers.ModelSerializer):
    """Serializer for player engagement metrics."""

    class Meta:
        model = PlayerEngagement
        fields = [
            'engagement_score', 'churn_risk', 'preferred_time_of_day',
            'avg_session_length_secs', 'sessions_per_week',
            'optimal_session_length', 'personality_cluster', 'updated_at',
        ]
        read_only_fields = fields


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for AI-monitored play sessions."""

    class Meta:
        model = PlayerSession
        fields = [
            'id', 'started_at', 'ended_at', 'duration_secs',
            'challenges_attempted', 'challenges_correct',
            'avg_response_time', 'response_time_variance',
            'realms_visited', 'abandoned', 'inferred_emotion', 'flow_score',
        ]
        read_only_fields = fields


class SRSCardSerializer(serializers.ModelSerializer):
    """Serializer for FSRS spaced repetition cards."""

    challenge_slug = serializers.SerializerMethodField()
    challenge_title = serializers.SerializerMethodField()
    challenge_type = serializers.SerializerMethodField()
    retrievability = serializers.SerializerMethodField()
    state_display = serializers.SerializerMethodField()

    class Meta:
        model = SpacedRepetitionCard
        fields = [
            'id', 'challenge_id', 'challenge_slug', 'challenge_title',
            'challenge_type', 'stability', 'difficulty_fsrs',
            'elapsed_days', 'scheduled_days', 'reps', 'lapses',
            'state', 'state_display', 'due_date', 'last_review',
            'retrievability',
        ]
        read_only_fields = fields

    def get_challenge_slug(self, obj):
        return obj.challenge.slug if obj.challenge else None

    def get_challenge_title(self, obj):
        return obj.challenge.title_en if obj.challenge else None

    def get_challenge_type(self, obj):
        return obj.challenge.challenge_type if obj.challenge else None

    def get_state_display(self, obj):
        return dict(SpacedRepetitionCard.STATE_CHOICES).get(obj.state, 'Unknown')

    def get_retrievability(self, obj):
        """Current probability of recall based on FSRS forgetting curve."""
        from apps.ai_engine.algorithms.fsrs import FSRSEngine
        from django.utils import timezone

        if obj.last_review is None:
            return 1.0

        elapsed = (timezone.now() - obj.last_review).total_seconds() / 86400.0
        return round(FSRSEngine.retrievability(elapsed, obj.stability), 3)


class PlayerAbilitySerializer(serializers.ModelSerializer):
    """Serializer for IRT ability (theta) estimates."""

    realm_slug = serializers.SerializerMethodField()
    realm_name = serializers.SerializerMethodField()

    class Meta:
        model = PlayerAbility
        fields = [
            'id', 'realm_slug', 'realm_name', 'skill',
            'theta', 'theta_se', 'responses_count', 'last_updated',
        ]
        read_only_fields = fields

    def get_realm_slug(self, obj):
        return obj.realm.slug if obj.realm else None

    def get_realm_name(self, obj):
        return obj.realm.name_en if obj.realm else None


class RecommendationLogSerializer(serializers.ModelSerializer):
    """Serializer for recommendation log entries."""

    challenge_slug = serializers.SerializerMethodField()
    challenge_title = serializers.SerializerMethodField()

    class Meta:
        model = RecommendationLog
        fields = [
            'id', 'challenge_id', 'challenge_slug', 'challenge_title',
            'feed_item_id', 'recommendation_source', 'score',
            'was_attempted', 'was_correct', 'engagement_time_secs',
            'created_at',
        ]
        read_only_fields = fields

    def get_challenge_slug(self, obj):
        return obj.challenge.slug if obj.challenge else None

    def get_challenge_title(self, obj):
        return obj.challenge.title_en if obj.challenge else None


# ======================================================================
# Request / Response Serializers (non-model)
# ======================================================================

class SmartChatRequestSerializer(serializers.Serializer):
    """Request serializer for the Smart Noor companion chat."""

    message = serializers.CharField(
        max_length=2000,
        help_text="The player's message to Smart Noor.",
    )
    context = serializers.DictField(
        required=False,
        default=dict,
        help_text=(
            "Optional context dict. Supported keys: context_type (str), "
            "challenge_score (int), challenge_trait (str), "
            "challenge_difficulty (int), realm_name (str), "
            "streak (int), level (int)."
        ),
    )


class SmartChatResponseSerializer(serializers.Serializer):
    """Response serializer for the Smart Noor companion chat."""

    response = serializers.CharField(help_text="Noor's response text.")
    emotion = serializers.CharField(help_text="Detected player emotion.")
    coaching_strategy = serializers.CharField(
        help_text="Selected coaching strategy."
    )
    suggestions = serializers.ListField(
        child=serializers.CharField(),
        help_text="Suggested next actions for the player.",
    )


class NextChallengeSerializer(serializers.Serializer):
    """Response serializer for the next recommended challenge."""

    challenge_id = serializers.IntegerField()
    challenge_slug = serializers.CharField()
    title_en = serializers.CharField()
    title_ar = serializers.CharField(allow_blank=True)
    challenge_type = serializers.CharField()
    difficulty = serializers.IntegerField()
    primary_trait = serializers.CharField()
    time_limit_secs = serializers.IntegerField(allow_null=True)
    base_xp = serializers.IntegerField()
    bonus_xp = serializers.IntegerField()
    realm = serializers.CharField(allow_null=True)
    quest = serializers.CharField(allow_null=True)
    ai_score = serializers.FloatField(
        help_text="Composite recommendation score (0-1)."
    )
    ai_signals = serializers.DictField(
        child=serializers.FloatField(),
        help_text="Per-signal score breakdown.",
    )
    ai_explanation = serializers.CharField(
        help_text="Human-readable explanation of why this was recommended."
    )


class RecommendationSerializer(serializers.Serializer):
    """Serializer for a single recommendation in the list view."""

    challenge_id = serializers.IntegerField()
    title = serializers.CharField()
    challenge_type = serializers.CharField()
    difficulty = serializers.IntegerField()
    primary_trait = serializers.CharField()
    realm_slug = serializers.CharField(allow_null=True)
    composite_score = serializers.FloatField()
    signals = serializers.DictField(child=serializers.FloatField())


class PlayerInsightsSerializer(serializers.Serializer):
    """Response serializer for the comprehensive player insights endpoint."""

    knowledge_radar = serializers.DictField(
        help_text="Per-skill mastery probabilities and metadata.",
    )
    flow_state = serializers.DictField(
        help_text="Latest session flow score and emotion.",
    )
    engagement = serializers.DictField(
        help_text="Engagement score, churn risk, session stats.",
    )
    recommendations = serializers.ListField(
        child=serializers.DictField(),
        help_text="Top recommended challenges.",
    )
    learning_path = serializers.ListField(
        child=serializers.DictField(),
        help_text="Ordered skill learning path.",
    )
    abilities = serializers.ListField(
        child=serializers.DictField(),
        help_text="IRT theta estimates per skill/realm.",
    )
    srs_summary = serializers.DictField(
        help_text="SRS card counts and review load.",
    )
    skill_gaps = serializers.ListField(
        child=serializers.DictField(),
        help_text="Top knowledge gaps.",
    )
    player_type = serializers.CharField(
        help_text="Bartle player type classification.",
    )


class SessionStartResponseSerializer(serializers.Serializer):
    """Response serializer for session start."""

    session_id = serializers.IntegerField()
    started_at = serializers.DateTimeField()


class SessionEndRequestSerializer(serializers.Serializer):
    """Request serializer for session end."""

    session_id = serializers.IntegerField(
        help_text="The session ID returned by session/start/.",
    )


class SessionEndResponseSerializer(serializers.Serializer):
    """Response serializer for session end."""

    session_id = serializers.IntegerField()
    duration_secs = serializers.FloatField()
    challenges_attempted = serializers.IntegerField()
    challenges_correct = serializers.IntegerField()
    flow_score = serializers.FloatField()
    inferred_emotion = serializers.CharField()
    abandoned = serializers.BooleanField()
    engagement_score = serializers.FloatField()
    churn_risk = serializers.FloatField()


class LearningPathDetailSerializer(serializers.Serializer):
    """Serializer for a single step in the generated learning path."""

    skill = serializers.CharField()
    current_mastery = serializers.FloatField()
    target_mastery = serializers.FloatField()
    priority = serializers.IntegerField()
    prerequisites = serializers.ListField(child=serializers.CharField())
    dependants = serializers.ListField(child=serializers.CharField())


class WeeklyPlanDaySerializer(serializers.Serializer):
    """Serializer for a single day in the weekly plan."""

    day = serializers.IntegerField()
    date = serializers.CharField()
    focus_skill = serializers.CharField()
    focus_mastery = serializers.FloatField()
    review_skill = serializers.CharField(allow_null=True)
    challenges = serializers.ListField(child=serializers.DictField())
    challenge_count = serializers.IntegerField()
