from django.contrib import admin

from .models import (
    ChallengeParameter,
    KnowledgeState,
    LearningPath,
    PlayerAbility,
    PlayerEngagement,
    PlayerSession,
    RecommendationLog,
    SpacedRepetitionCard,
)


@admin.register(PlayerAbility)
class PlayerAbilityAdmin(admin.ModelAdmin):
    list_display = ('player', 'realm', 'skill', 'theta', 'theta_se', 'responses_count')
    list_filter = ('realm', 'skill')
    search_fields = ('player__user__username',)


@admin.register(ChallengeParameter)
class ChallengeParameterAdmin(admin.ModelAdmin):
    list_display = (
        'challenge', 'discrimination', 'difficulty_b',
        'guessing_c', 'total_attempts', 'correct_rate',
    )
    list_filter = ('calibrated_at',)


@admin.register(SpacedRepetitionCard)
class SpacedRepetitionCardAdmin(admin.ModelAdmin):
    list_display = ('player', 'challenge', 'stability', 'state', 'due_date', 'reps', 'lapses')
    list_filter = ('state',)


@admin.register(KnowledgeState)
class KnowledgeStateAdmin(admin.ModelAdmin):
    list_display = ('player', 'skill', 'p_known', 'observations')
    list_filter = ('skill',)


@admin.register(PlayerSession)
class PlayerSessionAdmin(admin.ModelAdmin):
    list_display = (
        'player', 'started_at', 'duration_secs',
        'challenges_attempted', 'flow_score', 'inferred_emotion',
    )
    list_filter = ('inferred_emotion',)


@admin.register(PlayerEngagement)
class PlayerEngagementAdmin(admin.ModelAdmin):
    list_display = ('player', 'engagement_score', 'churn_risk', 'personality_cluster')
    list_filter = ('personality_cluster',)


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = (
        'player', 'challenge', 'recommendation_source',
        'score', 'was_attempted', 'was_correct',
    )
    list_filter = ('recommendation_source', 'was_attempted')


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('player', 'current_focus_realm', 'current_focus_skill', 'path_version')
