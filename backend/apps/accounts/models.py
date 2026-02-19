from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Player(models.Model):
    TIER_CHOICES = [('free', 'Free'), ('premium', 'Premium')]
    LANG_CHOICES = [('en', 'English'), ('ar', 'Arabic')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player')
    display_name = models.CharField(max_length=50)
    avatar_preset = models.CharField(max_length=30, default='default')
    avatar_colors = models.JSONField(default=dict, blank=True)
    overall_level = models.IntegerField(default=1)
    total_xp = models.BigIntegerField(default=0)
    premium_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    preferred_lang = models.CharField(max_length=5, choices=LANG_CHOICES, default='en')
    onboarding_done = models.BooleanField(default=False)
    last_active_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_xp']
        indexes = [
            models.Index(fields=['-overall_level']),
            models.Index(fields=['-total_xp']),
        ]

    def __str__(self):
        return self.display_name


class CompanionProfile(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='companion_profile')
    warmth = models.SmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    directness = models.SmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    humor = models.SmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    formality = models.SmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    challenge_level = models.SmallIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(100)])
    known_strengths = models.JSONField(default=list, blank=True)
    known_weaknesses = models.JSONField(default=list, blank=True)
    player_preferences = models.JSONField(default=dict, blank=True)
    interaction_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Companion for {self.player.display_name}"
