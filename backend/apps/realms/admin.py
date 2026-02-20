from django.contrib import admin
from .models import Realm, Quest, Challenge


@admin.register(Realm)
class RealmAdmin(admin.ModelAdmin):
    list_display = ['name_en', 'slug', 'primary_trait', 'sort_order', 'is_active']
    list_filter = ['is_active']
    prepopulated_fields = {'slug': ('name_en',)}


class ChallengeInline(admin.TabularInline):
    model = Challenge
    extra = 0
    fields = ['slug', 'title_en', 'challenge_type', 'difficulty', 'base_xp', 'sort_order', 'is_active']


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'realm', 'quest_type', 'sort_order', 'is_active']
    list_filter = ['realm', 'quest_type', 'is_active']
    inlines = [ChallengeInline]


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'quest', 'challenge_type', 'difficulty', 'base_xp', 'primary_trait', 'is_active']
    list_filter = ['challenge_type', 'difficulty', 'primary_trait', 'quest__realm', 'is_active']
    search_fields = ['title_en', 'title_ar', 'slug']
