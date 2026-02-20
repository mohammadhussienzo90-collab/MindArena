from django.contrib import admin
from .models import FeedItem, FeedInteraction


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'content_type', 'realm', 'xp_value', 'is_premium', 'is_active']
    list_filter = ['content_type', 'realm', 'is_premium', 'is_active']
    search_fields = ['title_en', 'title_ar', 'slug']


@admin.register(FeedInteraction)
class FeedInteractionAdmin(admin.ModelAdmin):
    list_display = ['player', 'feed_item', 'liked', 'completed', 'seen_at']
    list_filter = ['liked', 'completed']
