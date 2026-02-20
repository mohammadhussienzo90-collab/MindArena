from django.contrib import admin
from .models import FeedItem, FeedInteraction


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = [
        'title_en', 'content_type', 'realm', 'difficulty',
        'xp_value', 'is_premium', 'is_active', 'created_at',
    ]
    list_filter = ['content_type', 'realm', 'is_premium', 'is_active', 'difficulty']
    search_fields = ['title_en', 'title_ar', 'slug']
    list_editable = ['is_active', 'is_premium']
    list_per_page = 30
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('title_en',)}
    fieldsets = (
        ('Content', {
            'fields': (
                'slug', 'content_type', 'realm', 'difficulty',
                'image_url', 'xp_value',
            ),
        }),
        ('Localization', {
            'fields': (
                'title_en', 'title_ar',
                'body_en', 'body_ar',
            ),
        }),
        ('Configuration', {
            'fields': ('is_premium', 'is_active'),
        }),
    )


@admin.register(FeedInteraction)
class FeedInteractionAdmin(admin.ModelAdmin):
    list_display = ['player', 'feed_item', 'seen', 'liked', 'completed', 'seen_at']
    list_filter = ['liked', 'completed', 'seen']
    search_fields = ['player__display_name', 'feed_item__title_en']
    list_select_related = ['player', 'feed_item']
    date_hierarchy = 'seen_at'
    ordering = ['-seen_at']
    list_per_page = 50
