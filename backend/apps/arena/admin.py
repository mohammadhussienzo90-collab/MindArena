from django.contrib import admin
from .models import ArenaMatch, PlayerArenaStats


@admin.register(ArenaMatch)
class ArenaMatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'match_type', 'realm', 'created_at', 'is_active']
    list_filter = ['match_type', 'is_active']


@admin.register(PlayerArenaStats)
class PlayerArenaStatsAdmin(admin.ModelAdmin):
    list_display = ['player', 'elo_rating', 'matches_played', 'matches_won', 'win_streak']
