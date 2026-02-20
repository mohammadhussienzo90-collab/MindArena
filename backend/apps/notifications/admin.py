from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'recipient',
        'notification_type',
        'title_en',
        'is_read',
        'created_at',
    ]
    list_display_links = ['id', 'title_en']
    list_editable = ['is_read']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title_en', 'title_ar', 'message_en', 'message_ar', 'recipient__display_name']
    raw_id_fields = ['recipient']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        ('Content', {
            'fields': ('recipient', 'notification_type'),
        }),
        ('Localization', {
            'fields': ('title_en', 'title_ar', 'message_en', 'message_ar'),
        }),
        ('Status', {
            'fields': ('is_read',),
        }),
        ('Metadata', {
            'fields': ('data', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')

    @admin.action(description='Mark selected notifications as unread')
    def mark_as_unread(self, request, queryset):
        updated = queryset.filter(is_read=True).update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
