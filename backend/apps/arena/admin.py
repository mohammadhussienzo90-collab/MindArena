from django.contrib import admin
from django.utils.html import format_html

from .models import ArenaMatch, ArenaMatchParticipant, ArenaRoundResult, PlayerArenaStats


# ── Inlines ──────────────────────────────────────────────────────────────────

class ArenaMatchParticipantInline(admin.TabularInline):
    model = ArenaMatchParticipant
    extra = 0
    readonly_fields = ['player', 'score', 'correct_answers', 'total_time_secs', 'joined_at']


class ArenaRoundResultInline(admin.TabularInline):
    model = ArenaRoundResult
    extra = 0
    readonly_fields = [
        'participant', 'round_number', 'challenge',
        'is_correct', 'time_taken_secs', 'score_earned', 'created_at',
    ]


# ── ArenaMatch ───────────────────────────────────────────────────────────────

@admin.register(ArenaMatch)
class ArenaMatchAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'match_type', 'realm', 'status', 'current_round',
        'total_rounds', 'winner', 'elo_change', 'created_at',
    ]
    list_filter = ['match_type', 'status', 'is_active', 'realm']
    search_fields = ['id', 'winner__display_name']
    readonly_fields = ['challenge_pool', 'started_at', 'finished_at', 'created_at']
    inlines = [ArenaMatchParticipantInline, ArenaRoundResultInline]
    list_select_related = ['realm', 'winner']
    ordering = ['-created_at']
    list_per_page = 30
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Match Info', {
            'fields': (
                'match_type', 'realm', 'max_players',
                'current_round', 'total_rounds', 'elo_change',
            ),
        }),
        ('Status', {
            'fields': ('status', 'is_active'),
        }),
        ('Participants', {
            'fields': ('winner',),
            'description': 'Participant details are shown in the inline sections below.',
        }),
        ('Results', {
            'fields': ('challenge_pool',),
            'classes': ('collapse',),
            'description': 'Round-by-round results are shown in the inline sections below.',
        }),
        ('Timestamps', {
            'fields': ('started_at', 'finished_at', 'created_at'),
        }),
    )


# ── PlayerArenaStats ─────────────────────────────────────────────────────────

@admin.register(PlayerArenaStats)
class PlayerArenaStatsAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'elo_rating', 'matches_played', 'matches_won',
        'matches_lost', 'win_rate_display', 'win_streak', 'best_win_streak',
        'last_match_at',
    ]
    search_fields = ['player__display_name']
    list_filter = ['matches_played']
    ordering = ['-elo_rating']
    list_per_page = 30

    @admin.display(description='Win Rate', ordering='matches_won')
    def win_rate_display(self, obj):
        if obj.matches_played == 0:
            return format_html('<span style="color:#999;">N/A</span>')
        rate = (obj.matches_won / obj.matches_played) * 100
        if rate >= 60:
            color = '#28a745'
        elif rate >= 40:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color:{}; font-weight:bold;">{:.1f}%</span>',
            color,
            rate,
        )


# ── ArenaMatchParticipant ────────────────────────────────────────────────────

@admin.register(ArenaMatchParticipant)
class ArenaMatchParticipantAdmin(admin.ModelAdmin):
    list_display = ['match', 'player', 'score', 'correct_answers', 'is_ready', 'joined_at']
    list_filter = ['is_ready']
    search_fields = ['player__display_name']
    list_select_related = ['match', 'player']
    ordering = ['-joined_at']


# ── ArenaRoundResult ─────────────────────────────────────────────────────────

@admin.register(ArenaRoundResult)
class ArenaRoundResultAdmin(admin.ModelAdmin):
    list_display = [
        'match', 'participant', 'round_number', 'challenge',
        'is_correct', 'score_earned', 'time_taken_secs',
    ]
    list_filter = ['is_correct', 'round_number']
    list_select_related = ['match', 'participant', 'challenge']
    ordering = ['match', 'round_number']
