from django.db import models


class CompanionConversation(models.Model):
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='conversations')
    context_type = models.CharField(max_length=30, default='general')
    context_id = models.IntegerField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-started_at']


class CompanionMessage(models.Model):
    ROLE_CHOICES = [('player', 'Player'), ('companion', 'Companion')]
    conversation = models.ForeignKey(CompanionConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
