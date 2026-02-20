from django.contrib import admin
from .models import CompanionConversation, CompanionMessage


class MessageInline(admin.TabularInline):
    model = CompanionMessage
    extra = 0
    readonly_fields = ['role', 'content', 'created_at']


@admin.register(CompanionConversation)
class CompanionConversationAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'context_type', 'message_count',
        'started_at', 'is_active',
    ]
    list_filter = ['context_type', 'is_active']
    search_fields = ['player__display_name']
    list_select_related = ['player']
    ordering = ['-started_at']
    inlines = [MessageInline]

    def get_queryset(self, request):
        from django.db.models import Count
        qs = super().get_queryset(request)
        return qs.annotate(_message_count=Count('messages'))

    @admin.display(description='Messages', ordering='_message_count')
    def message_count(self, obj):
        return obj._message_count


@admin.register(CompanionMessage)
class CompanionMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'short_content', 'created_at']
    list_filter = ['role']
    search_fields = ['content', 'conversation__player__display_name']
    list_select_related = ['conversation', 'conversation__player']
    ordering = ['-created_at']
    list_per_page = 50

    def short_content(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    short_content.short_description = 'Content'
