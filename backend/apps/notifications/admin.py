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
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title_en', 'title_ar', 'message_en', 'message_ar', 'recipient__display_name']
    raw_id_fields = ['recipient']
    readonly_fields = ['created_at']
