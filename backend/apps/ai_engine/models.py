from django.db import models
from django.utils import timezone


class PlayerAbility(models.Model):
    """IRT theta (ability estimate) per realm/skill for a player."""

    player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='abilities',
    )
    realm = models.ForeignKey(
        'realms.Realm',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    skill = models.CharField(max_length=50, blank=True)
    theta = models.FloatField(default=0.0, help_text='Ability estimate')
    theta_se = models.FloatField(default=1.0, help_text='Standard error')
    responses_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['player', 'realm', 'skill']
        indexes = [
            models.Index(fields=['player', 'realm']),
            models.Index(fields=['player', 'skill']),
        ]
        verbose_name_plural = 'Player abilities'

    def __str__(self):
        parts = [str(self.player)]
        if self.realm:
            parts.append(str(self.realm))
        if self.skill:
            parts.append(self.skill)
        return ' | '.join(parts) + f' (θ={self.theta:.2f})'


class ChallengeParameter(models.Model):
    """IRT item parameters for a challenge."""

    challenge = models.OneToOneField(
        'realms.Challenge',
        on_delete=models.CASCADE,
        related_name='irt_params',
    )
    discrimination = models.FloatField(default=1.0, help_text="IRT 'a' parameter")
    difficulty_b = models.FloatField(default=0.0, help_text="IRT 'b' parameter")
    guessing_c = models.FloatField(default=0.25)
    total_attempts = models.IntegerField(default=0)
    correct_rate = models.FloatField(default=0.5)
    avg_time_secs = models.FloatField(default=0.0)
    calibrated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['difficulty_b']),
        ]

    def __str__(self):
        return f'{self.challenge} (a={self.discrimination:.2f}, b={self.difficulty_b:.2f})'


class SpacedRepetitionCard(models.Model):
    """FSRS spaced-repetition card for a player-challenge pair."""

    STATE_NEW = 0
    STATE_LEARNING = 1
    STATE_REVIEW = 2
    STATE_RELEARNING = 3
    STATE_CHOICES = [
        (STATE_NEW, 'New'),
        (STATE_LEARNING, 'Learning'),
        (STATE_REVIEW, 'Review'),
        (STATE_RELEARNING, 'Relearning'),
    ]

    player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='srs_cards',
    )
    challenge = models.ForeignKey(
        'realms.Challenge',
        on_delete=models.CASCADE,
    )
    stability = models.FloatField(default=1.0)
    difficulty_fsrs = models.FloatField(default=0.3)
    elapsed_days = models.FloatField(default=0.0)
    scheduled_days = models.FloatField(default=1.0)
    reps = models.IntegerField(default=0)
    lapses = models.IntegerField(default=0)
    state = models.SmallIntegerField(
        default=STATE_NEW,
        choices=STATE_CHOICES,
        help_text='0=new, 1=learning, 2=review, 3=relearning',
    )
    due_date = models.DateTimeField(default=timezone.now)
    last_review = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['player', 'challenge']
        indexes = [
            models.Index(fields=['player', 'due_date']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        state_label = dict(self.STATE_CHOICES).get(self.state, 'Unknown')
        return f'{self.player} | {self.challenge} [{state_label}]'


class KnowledgeState(models.Model):
    """Bayesian Knowledge Tracing (BKT) state per player-skill."""

    player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='knowledge_states',
    )
    skill = models.CharField(max_length=50)
    p_known = models.FloatField(default=0.3)
    p_learn = models.FloatField(default=0.1)
    p_guess = models.FloatField(default=0.25)
    p_slip = models.FloatField(default=0.1)
    observations = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['player', 'skill']
        indexes = [
            models.Index(fields=['player', 'skill']),
        ]

    def __str__(self):
        return f'{self.player} | {self.skill} (P(K)={self.p_known:.2f})'


class PlayerSession(models.Model):
    """Tracks a single AI-monitored play session."""

    player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='ai_sessions',
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_secs = models.FloatField(default=0.0)
    challenges_attempted = models.IntegerField(default=0)
    challenges_correct = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    response_time_variance = models.FloatField(default=0.0)
    realms_visited = models.JSONField(default=list, blank=True)
    abandoned = models.BooleanField(default=False)
    inferred_emotion = models.CharField(max_length=30, blank=True)
    flow_score = models.FloatField(default=0.0)

    class Meta:
        indexes = [
            models.Index(fields=['player', '-started_at']),
        ]

    def __str__(self):
        return f'{self.player} session @ {self.started_at:%Y-%m-%d %H:%M}'


class PlayerEngagement(models.Model):
    """Aggregated engagement metrics and churn prediction for a player."""

    player = models.OneToOneField(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='engagement',
    )
    engagement_score = models.FloatField(default=0.5)
    churn_risk = models.FloatField(default=0.5)
    preferred_time_of_day = models.SmallIntegerField(default=12)
    avg_session_length_secs = models.FloatField(default=0.0)
    sessions_per_week = models.FloatField(default=0.0)
    optimal_session_length = models.FloatField(default=900.0)
    personality_cluster = models.CharField(max_length=30, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.player} (engagement={self.engagement_score:.2f}, churn={self.churn_risk:.2f})'


class RecommendationLog(models.Model):
    """Logs each recommendation served and its outcome."""

    player = models.ForeignKey(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='recommendation_logs',
    )
    challenge = models.ForeignKey(
        'realms.Challenge',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    feed_item = models.ForeignKey(
        'feed.FeedItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    recommendation_source = models.CharField(max_length=30)
    score = models.FloatField(default=0.0)
    was_attempted = models.BooleanField(default=False)
    was_correct = models.BooleanField(null=True, blank=True)
    engagement_time_secs = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['player', '-created_at']),
            models.Index(fields=['recommendation_source']),
        ]

    def __str__(self):
        target = self.challenge or self.feed_item or 'N/A'
        return f'{self.player} <- {self.recommendation_source}: {target}'


class LearningPath(models.Model):
    """AI-generated learning path for a player."""

    player = models.OneToOneField(
        'accounts.Player',
        on_delete=models.CASCADE,
        related_name='learning_path',
    )
    current_focus_realm = models.ForeignKey(
        'realms.Realm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    current_focus_skill = models.CharField(max_length=50, blank=True)
    weekly_plan = models.JSONField(default=dict, blank=True)
    skill_sequence = models.JSONField(default=list, blank=True)
    next_challenges = models.JSONField(default=list, blank=True)
    path_version = models.IntegerField(default=1)
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        focus = self.current_focus_skill or self.current_focus_realm or 'Unset'
        return f'{self.player} path v{self.path_version} -> {focus}'
