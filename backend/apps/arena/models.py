"""Arena models — full competitive arena implementation."""
from django.db import models


class ArenaMatch(models.Model):
    """A competitive arena match between players."""
    MATCH_TYPES = [
        ('speed', 'Speed Duel'),
        ('strategic', 'Strategic Battle'),
        ('team', 'Team Arena'),
    ]
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # --- existing fields (from 0001_initial) ---
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    realm = models.ForeignKey(
        'realms.Realm', on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # --- new fields ---
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='waiting'
    )
    max_players = models.IntegerField(default=2)
    current_round = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=5)
    challenge_pool = models.JSONField(default=list)
    winner = models.ForeignKey(
        'accounts.Player',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches_won_arena',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    elo_change = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Match #{self.id} ({self.match_type}) - {self.status}"


class PlayerArenaStats(models.Model):
    """Aggregated arena statistics for a player."""

    # --- existing fields (from 0001_initial) ---
    player = models.OneToOneField(
        'accounts.Player', on_delete=models.CASCADE, related_name='arena_stats'
    )
    elo_rating = models.IntegerField(default=1000)
    matches_played = models.IntegerField(default=0)
    matches_won = models.IntegerField(default=0)
    win_streak = models.IntegerField(default=0)

    # --- new fields ---
    best_win_streak = models.IntegerField(default=0)
    matches_lost = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    last_match_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Player arena stats'

    def __str__(self):
        return f"{self.player.display_name} — ELO {self.elo_rating}"


class ArenaMatchParticipant(models.Model):
    """A player's participation record in a specific arena match."""
    match = models.ForeignKey(
        ArenaMatch, on_delete=models.CASCADE, related_name='participants'
    )
    player = models.ForeignKey(
        'accounts.Player', on_delete=models.CASCADE,
        related_name='arena_participations',
    )
    score = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    total_time_secs = models.FloatField(default=0.0)
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['match', 'player']
        ordering = ['-score']

    def __str__(self):
        return f"{self.player.display_name} in Match #{self.match_id}"


class ArenaRoundResult(models.Model):
    """Result of a single round for a participant in an arena match."""
    match = models.ForeignKey(
        ArenaMatch, on_delete=models.CASCADE, related_name='round_results'
    )
    participant = models.ForeignKey(
        ArenaMatchParticipant, on_delete=models.CASCADE,
        related_name='round_results',
    )
    round_number = models.IntegerField()
    challenge = models.ForeignKey(
        'realms.Challenge', on_delete=models.CASCADE
    )
    is_correct = models.BooleanField()
    time_taken_secs = models.FloatField()
    score_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['round_number']
        unique_together = ['match', 'participant', 'round_number']

    def __str__(self):
        status = "correct" if self.is_correct else "wrong"
        return (
            f"Round {self.round_number} — "
            f"{self.participant.player.display_name} — {status}"
        )
