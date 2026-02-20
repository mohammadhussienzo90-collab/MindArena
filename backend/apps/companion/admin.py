from django.contrib import admin
from .models import CompanionConversation, CompanionMessage


class MessageInline(admin.TabularInline):
    model = CompanionMessage
    extra = 0
    readonly_fields = ['role', 'content', 'created_at']


@admin.register(CompanionConversation)
class CompanionConversationAdmin(admin.ModelAdmin):
    list_display = ['player', 'context_type', 'started_at', 'is_active']
    list_filter = ['context_type', 'is_active']
    inlines = [MessageInline]


@admin.register(CompanionMessage)
class CompanionMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'short_content', 'created_at']
    list_filter = ['role']

    def short_content(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    short_content.short_description = 'Content'
