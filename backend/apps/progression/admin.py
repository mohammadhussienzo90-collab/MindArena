from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PlayerRealmStat, PlayerChallengeResult, PlayerQuestProgress,
    XPTransaction, Achievement, PlayerAchievement, DailyStreak,
)


@admin.register(PlayerRealmStat)
class PlayerRealmStatAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'realm', 'realm_level', 'realm_xp',
        'progress_pct', 'visual_stage', 'challenges_completed',
    ]
    list_filter = ['realm', 'realm_level']
    search_fields = ['player__display_name']
    list_select_related = ['player', 'realm']
    ordering = ['realm__sort_order', '-realm_level']

    @admin.display(description='Level Progress')
    def progress_pct(self, obj):
        xp_for_next = obj.realm_level * 100
        if xp_for_next == 0:
            return '100%'
        pct = min(int((obj.realm_xp / xp_for_next) * 100), 100)
        color = '#28a745' if pct >= 75 else '#ffc107' if pct >= 40 else '#dc3545'
        return format_html(
            '<div style="width:100px;background:#eee;border-radius:4px;">'
            '<div style="width:{}px;background:{};height:14px;border-radius:4px;'
            'text-align:center;color:#fff;font-size:11px;line-height:14px;">'
            '{}%</div></div>',
            pct, color, pct,
        )


@admin.register(PlayerChallengeResult)
class PlayerChallengeResultAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'challenge', 'is_correct', 'score',
        'xp_earned', 'time_taken_secs', 'played_at',
    ]
    list_filter = ['is_correct']
    search_fields = ['player__display_name', 'challenge__title_en']
    date_hierarchy = 'played_at'
    list_select_related = ['player', 'challenge']
    list_per_page = 50
    ordering = ['-played_at']


@admin.register(PlayerQuestProgress)
class PlayerQuestProgressAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'quest', 'status',
        'challenges_completed', 'challenges_total',
        'started_at', 'completed_at',
    ]
    list_filter = ['status']
    search_fields = ['player__display_name', 'quest__title_en']
    list_select_related = ['player', 'quest']
    ordering = ['status', '-started_at']


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ['player', 'amount', 'source', 'realm', 'created_at']
    list_filter = ['source', 'realm']
    search_fields = ['player__display_name']
    date_hierarchy = 'created_at'
    list_select_related = ['player', 'realm']
    list_per_page = 50
    ordering = ['-created_at']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = [
        'title_en', 'slug', 'category', 'requirement_type',
        'requirement_value', 'xp_reward', 'is_hidden', 'earned_count',
    ]
    list_filter = ['category', 'is_hidden', 'requirement_type']
    search_fields = ['title_en', 'title_ar', 'slug']
    list_editable = ['xp_reward']
    ordering = ['category', 'slug']
    fieldsets = (
        ('Basic Info', {
            'fields': ('slug', 'icon', 'category', 'is_hidden'),
        }),
        ('Requirements', {
            'fields': ('requirement_type', 'requirement_value'),
        }),
        ('Rewards', {
            'fields': ('xp_reward',),
        }),
        ('Localization', {
            'fields': ('title_en', 'title_ar', 'description_en', 'description_ar'),
        }),
    )

    @admin.display(description='Earned By')
    def earned_count(self, obj):
        count = obj.playerachievement_set.count()
        return format_html('<b>{}</b> player{}', count, 's' if count != 1 else '')


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ['player', 'achievement', 'earned_at']
    list_filter = ['achievement__category']
    search_fields = ['player__display_name', 'achievement__title_en']
    list_select_related = ['player', 'achievement']
    date_hierarchy = 'earned_at'
    ordering = ['-earned_at']


@admin.register(DailyStreak)
class DailyStreakAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'streak_status', 'current_streak',
        'longest_streak', 'last_active_date',
    ]
    search_fields = ['player__display_name']
    list_select_related = ['player']
    ordering = ['-current_streak']

    @admin.display(description='Status')
    def streak_status(self, obj):
        from datetime import date, timedelta
        today = date.today()
        if obj.last_active_date == today:
            return format_html(
                '<span style="color:#28a745;font-size:16px;" title="Active today">'
                '&#x1F525; Active</span>'
            )
        elif obj.last_active_date and obj.last_active_date >= today - timedelta(days=1):
            return format_html(
                '<span style="color:#ffc107;font-size:16px;" title="At risk">'
                '&#x26A0;&#xFE0F; At Risk</span>'
            )
        else:
            return format_html(
                '<span style="color:#dc3545;font-size:16px;" title="Lost streak">'
                '&#x274C; Lost</span>'
            )
