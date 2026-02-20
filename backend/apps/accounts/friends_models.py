from django.db import models


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    from_player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='sent_friend_requests',
    )
    to_player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='received_friend_requests',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['from_player', 'to_player']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_player.display_name} -> {self.to_player.display_name} ({self.status})"


class Friendship(models.Model):
    player1 = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='friendships_as_player1',
    )
    player2 = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='friendships_as_player2',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player1', 'player2']

    def __str__(self):
        return f"{self.player1.display_name} <-> {self.player2.display_name}"
