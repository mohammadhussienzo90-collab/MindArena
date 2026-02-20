from django.contrib import admin
from .models import ArenaMatch, ArenaMatchParticipant, ArenaRoundResult, PlayerArenaStats


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


@admin.register(PlayerArenaStats)
class PlayerArenaStatsAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'elo_rating', 'matches_played', 'matches_won',
        'matches_lost', 'win_streak', 'best_win_streak', 'last_match_at',
    ]
    search_fields = ['player__display_name']
    list_filter = ['matches_played']


@admin.register(ArenaMatchParticipant)
class ArenaMatchParticipantAdmin(admin.ModelAdmin):
    list_display = ['match', 'player', 'score', 'correct_answers', 'is_ready', 'joined_at']
    list_filter = ['is_ready']
    search_fields = ['player__display_name']


@admin.register(ArenaRoundResult)
class ArenaRoundResultAdmin(admin.ModelAdmin):
    list_display = [
        'match', 'participant', 'round_number', 'challenge',
        'is_correct', 'score_earned', 'time_taken_secs',
    ]
    list_filter = ['is_correct', 'round_number']
