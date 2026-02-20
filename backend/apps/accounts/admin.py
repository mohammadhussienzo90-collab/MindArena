from django.contrib import admin
from .models import Player, CompanionProfile


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'user', 'overall_level', 'total_xp', 'premium_tier', 'onboarding_done']
    list_filter = ['premium_tier', 'preferred_lang', 'onboarding_done']
    search_fields = ['display_name', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CompanionProfile)
class CompanionProfileAdmin(admin.ModelAdmin):
    list_display = ['player', 'warmth', 'directness', 'humor', 'interaction_count']
    readonly_fields = ['updated_at']
