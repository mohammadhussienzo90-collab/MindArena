from django.contrib import admin
from .models import (
    PlayerRealmStat, PlayerChallengeResult, PlayerQuestProgress,
    XPTransaction, Achievement, PlayerAchievement, DailyStreak,
)


@admin.register(PlayerRealmStat)
class PlayerRealmStatAdmin(admin.ModelAdmin):
    list_display = ['player', 'realm', 'realm_level', 'realm_xp', 'visual_stage', 'challenges_completed']
    list_filter = ['realm']
    search_fields = ['player__display_name']


@admin.register(PlayerChallengeResult)
class PlayerChallengeResultAdmin(admin.ModelAdmin):
    list_display = ['player', 'challenge', 'is_correct', 'score', 'xp_earned', 'played_at']
    list_filter = ['is_correct']
    date_hierarchy = 'played_at'


@admin.register(PlayerQuestProgress)
class PlayerQuestProgressAdmin(admin.ModelAdmin):
    list_display = ['player', 'quest', 'status', 'challenges_completed', 'challenges_total']
    list_filter = ['status']


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ['player', 'amount', 'source', 'realm', 'created_at']
    list_filter = ['source']
    date_hierarchy = 'created_at'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'slug', 'category', 'requirement_type', 'requirement_value', 'xp_reward']
    list_filter = ['category', 'is_hidden']
    search_fields = ['title_en', 'slug']


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ['player', 'achievement', 'earned_at']


@admin.register(DailyStreak)
class DailyStreakAdmin(admin.ModelAdmin):
    list_display = ['player', 'current_streak', 'longest_streak', 'last_active_date']
