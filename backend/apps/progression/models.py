from django.db import models


class PlayerRealmStat(models.Model):
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='realm_stats')
    realm = models.ForeignKey('realms.Realm', on_delete=models.CASCADE)
    realm_level = models.IntegerField(default=1)
    realm_xp = models.BigIntegerField(default=0)
    challenges_completed = models.IntegerField(default=0)
    challenges_perfect = models.IntegerField(default=0)
    quests_completed = models.IntegerField(default=0)
    visual_stage = models.SmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['player', 'realm']
        ordering = ['realm__sort_order']
        indexes = [
            models.Index(fields=['player', 'realm']),
        ]

    def __str__(self):
        return f"{self.player} - {self.realm} (Lv{self.realm_level})"


class PlayerChallengeResult(models.Model):
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='challenge_results')
    challenge = models.ForeignKey('realms.Challenge', on_delete=models.CASCADE)
    score = models.IntegerField()
    is_correct = models.BooleanField()
    time_taken_secs = models.FloatField()
    answer_data = models.JSONField(default=dict)
    xp_earned = models.IntegerField(default=0)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']
        indexes = [
            models.Index(fields=['player', 'challenge']),
            models.Index(fields=['played_at']),
        ]


class PlayerQuestProgress(models.Model):
    STATUS_CHOICES = [
        ('locked', 'Locked'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='quest_progress')
    quest = models.ForeignKey('realms.Quest', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
    challenges_completed = models.IntegerField(default=0)
    challenges_total = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['player', 'quest']


class XPTransaction(models.Model):
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='xp_transactions')
    amount = models.IntegerField()
    source = models.CharField(max_length=30)
    source_id = models.IntegerField(null=True, blank=True)
    realm = models.ForeignKey('realms.Realm', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Achievement(models.Model):
    slug = models.CharField(max_length=100, unique=True)
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200, blank=True)
    description_en = models.TextField()
    description_ar = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=30)
    requirement_type = models.CharField(max_length=30)
    requirement_value = models.IntegerField(default=1)
    xp_reward = models.IntegerField(default=50)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ['category', 'slug']

    def __str__(self):
        return self.title_en


class PlayerAchievement(models.Model):
    player = models.ForeignKey('accounts.Player', on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player', 'achievement']


class DailyStreak(models.Model):
    player = models.OneToOneField('accounts.Player', on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.player} - {self.current_streak} days"
