"""Arena models — Phase 2 implementation."""
from django.db import models


class ArenaMatch(models.Model):
    """Placeholder for competitive arena matches."""
    MATCH_TYPES = [
        ('speed', 'Speed Duel'),
        ('strategic', 'Strategic Battle'),
        ('team', 'Team Arena'),
    ]
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    realm = models.ForeignKey('realms.Realm', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']


class PlayerArenaStats(models.Model):
    """Placeholder for player arena statistics."""
    player = models.OneToOneField('accounts.Player', on_delete=models.CASCADE, related_name='arena_stats')
    elo_rating = models.IntegerField(default=1000)
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    win_streak = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Player arena stats'
