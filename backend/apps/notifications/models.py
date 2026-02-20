from django.db import models


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('achievement', 'Achievement'),
        ('arena_invite', 'Arena Invite'),
        ('arena_result', 'Arena Result'),
        ('friend_request', 'Friend Request'),
        ('friend_accepted', 'Friend Accepted'),
        ('level_up', 'Level Up'),
        ('streak', 'Streak'),
        ('system', 'System'),
    ]

    recipient = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
    )
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200, blank=True)
    message_en = models.TextField(blank=True)
    message_ar = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} -> {self.recipient.display_name}"
