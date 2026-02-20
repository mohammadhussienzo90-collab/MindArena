from django.contrib import admin
from django.utils.html import format_html

from .models import Player, CompanionProfile
from .friends_models import FriendRequest, Friendship


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'user', 'overall_level', 'total_xp',
        'premium_tier', 'preferred_lang', 'onboarding_done', 'last_active_at',
    ]
    list_filter = ['premium_tier', 'preferred_lang', 'onboarding_done', 'overall_level']
    search_fields = ['display_name', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    list_select_related = ['user']
    list_per_page = 30
    ordering = ['-total_xp']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Personal Info', {
            'fields': (
                'user', 'display_name', 'avatar_preset', 'avatar_colors',
            ),
        }),
        ('Game Progress', {
            'fields': (
                'overall_level', 'total_xp',
            ),
        }),
        ('Settings', {
            'fields': (
                'premium_tier', 'preferred_lang', 'onboarding_done',
            ),
        }),
        ('Timestamps', {
            'fields': (
                'last_active_at', 'created_at', 'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = ['reset_onboarding']

    @admin.action(description='Reset onboarding for selected players')
    def reset_onboarding(self, request, queryset):
        updated = queryset.update(onboarding_done=False)
        self.message_user(request, f'{updated} player(s) had their onboarding reset.')


@admin.register(CompanionProfile)
class CompanionProfileAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'warmth', 'directness', 'humor', 'formality',
        'challenge_level', 'interaction_count',
    ]
    list_filter = ['warmth', 'directness']
    search_fields = ['player__display_name', 'player__user__username']
    readonly_fields = ['updated_at']
    list_select_related = ['player']
    list_per_page = 30
    ordering = ['-interaction_count']

    fieldsets = (
        ('Player', {
            'fields': ('player',),
        }),
        ('Personality Sliders', {
            'fields': (
                'warmth', 'directness', 'humor', 'formality', 'challenge_level',
            ),
        }),
        ('Knowledge', {
            'fields': (
                'known_strengths', 'known_weaknesses', 'player_preferences',
            ),
            'classes': ('collapse',),
        }),
        ('Stats', {
            'fields': ('interaction_count', 'updated_at'),
        }),
    )


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['from_player', 'to_player', 'status', 'created_at', 'responded_at']
    list_filter = ['status', 'created_at']
    search_fields = [
        'from_player__display_name', 'to_player__display_name',
        'from_player__user__username', 'to_player__user__username',
    ]
    readonly_fields = ['created_at', 'responded_at']
    list_select_related = ['from_player', 'to_player']
    list_per_page = 30
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['player1', 'player2', 'created_at']
    search_fields = [
        'player1__display_name', 'player2__display_name',
        'player1__user__username', 'player2__user__username',
    ]
    readonly_fields = ['created_at']
    list_select_related = ['player1', 'player2']
    list_per_page = 30
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
