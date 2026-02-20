from django.contrib import admin
from django.utils.html import format_html

from .models import Realm, Quest, Challenge


@admin.register(Realm)
class RealmAdmin(admin.ModelAdmin):
    list_display = [
        'name_en', 'slug', 'primary_trait', 'secondary_trait',
        'unlock_level', 'sort_order', 'is_active',
    ]
    list_filter = ['is_active', 'primary_trait']
    list_editable = ['sort_order', 'is_active']
    search_fields = ['name_en', 'name_ar', 'slug']
    prepopulated_fields = {'slug': ('name_en',)}
    readonly_fields = ['created_at']
    list_per_page = 30
    ordering = ['sort_order']

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'slug', 'primary_trait', 'secondary_trait',
                'icon', 'unlock_level', 'sort_order', 'is_active',
            ),
        }),
        ('Localization', {
            'fields': (
                'name_en', 'name_ar', 'description_en', 'description_ar',
            ),
        }),
        ('Configuration', {
            'fields': (
                'color_primary', 'color_secondary', 'created_at',
            ),
            'classes': ('collapse',),
        }),
    )


class ChallengeInline(admin.TabularInline):
    model = Challenge
    extra = 0
    fields = [
        'slug', 'title_en', 'challenge_type', 'difficulty',
        'base_xp', 'sort_order', 'is_active',
    ]
    show_change_link = True


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = [
        'title_en', 'realm', 'quest_type', 'required_realm_level',
        'xp_reward', 'sort_order', 'is_active',
    ]
    list_filter = ['realm', 'quest_type', 'is_active']
    search_fields = ['title_en', 'title_ar', 'slug']
    prepopulated_fields = {'slug': ('title_en',)}
    readonly_fields = ['created_at']
    list_select_related = ['realm']
    list_per_page = 30
    ordering = ['realm', 'sort_order']
    inlines = [ChallengeInline]

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'realm', 'slug', 'quest_type', 'sort_order',
                'prerequisite_quest', 'required_realm_level', 'is_active',
            ),
        }),
        ('Localization', {
            'fields': (
                'title_en', 'title_ar', 'description_en', 'description_ar',
            ),
        }),
        ('Rewards', {
            'fields': ('xp_reward', 'stat_reward'),
        }),
        ('Dialogue & Visuals', {
            'fields': ('intro_dialogue', 'outro_dialogue', 'world_position'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = [
        'title_en', 'quest', 'realm_name', 'challenge_type',
        'difficulty', 'base_xp', 'bonus_xp', 'primary_trait', 'is_active',
    ]
    list_filter = ['challenge_type', 'difficulty', 'primary_trait', 'quest__realm', 'is_active']
    search_fields = ['title_en', 'title_ar', 'slug']
    readonly_fields = ['created_at']
    list_select_related = ['quest', 'quest__realm']
    list_per_page = 30
    ordering = ['quest', 'sort_order']

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'quest', 'slug', 'challenge_type', 'difficulty',
                'sort_order', 'is_active',
            ),
        }),
        ('Localization', {
            'fields': (
                'title_en', 'title_ar', 'description_en', 'description_ar',
            ),
        }),
        ('Traits & Scoring', {
            'fields': (
                'primary_trait', 'secondary_trait', 'trait_points',
                'base_xp', 'bonus_xp',
            ),
        }),
        ('Content', {
            'fields': ('content', 'time_limit_secs', 'scene_id'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Realm', ordering='quest__realm__name_en')
    def realm_name(self, obj):
        return obj.quest.realm.name_en
