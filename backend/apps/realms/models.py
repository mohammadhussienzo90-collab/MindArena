from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Realm(models.Model):
    slug = models.CharField(max_length=50, unique=True)
    name_en = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100, blank=True)
    description_en = models.TextField()
    description_ar = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color_primary = models.CharField(max_length=7)
    color_secondary = models.CharField(max_length=7)
    unlock_level = models.IntegerField(default=1)
    sort_order = models.SmallIntegerField(default=0)
    primary_trait = models.CharField(max_length=30)
    secondary_trait = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name_en


CHALLENGE_TYPES = [
    ('multiple_choice', 'Multiple Choice'),
    ('pattern_match', 'Pattern Match'),
    ('sequence', 'Sequence'),
    ('spatial_puzzle', 'Spatial Puzzle'),
    ('timed_response', 'Timed Response'),
    ('scenario_choice', 'Scenario Choice'),
    ('math_logic', 'Math Logic'),
    ('emotional_scenario', 'Emotional Scenario'),
    ('creative_prompt', 'Creative Prompt'),
    ('memory_test', 'Memory Test'),
    ('debate_analysis', 'Debate Analysis'),
    ('financial_decision', 'Financial Decision'),
    ('word_puzzle', 'Word Puzzle'),
]

QUEST_TYPES = [
    ('main', 'Main Quest'),
    ('side', 'Side Quest'),
    ('daily', 'Daily Quest'),
    ('weekly', 'Weekly Quest'),
]


class Quest(models.Model):
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='quests')
    slug = models.CharField(max_length=100, unique=True)
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200, blank=True)
    description_en = models.TextField()
    description_ar = models.TextField(blank=True)
    quest_type = models.CharField(max_length=30, choices=QUEST_TYPES, default='main')
    sort_order = models.IntegerField(default=0)
    prerequisite_quest = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    required_realm_level = models.IntegerField(default=0)
    xp_reward = models.IntegerField(default=0)
    stat_reward = models.JSONField(default=dict, blank=True)
    intro_dialogue = models.JSONField(default=list, blank=True)
    outro_dialogue = models.JSONField(default=list, blank=True)
    world_position = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['realm', 'sort_order']
        indexes = [
            models.Index(fields=['realm', 'sort_order']),
        ]

    def __str__(self):
        return self.title_en


class Challenge(models.Model):
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='challenges')
    slug = models.CharField(max_length=100, unique=True)
    challenge_type = models.CharField(max_length=30, choices=CHALLENGE_TYPES)
    title_en = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200, blank=True)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    content = models.JSONField()
    difficulty = models.SmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    primary_trait = models.CharField(max_length=30)
    secondary_trait = models.CharField(max_length=30, blank=True)
    trait_points = models.JSONField(default=dict, blank=True)
    time_limit_secs = models.IntegerField(null=True, blank=True)
    base_xp = models.IntegerField(default=10)
    bonus_xp = models.IntegerField(default=5)
    sort_order = models.IntegerField(default=0)
    scene_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quest', 'sort_order']
        indexes = [
            models.Index(fields=['challenge_type']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['primary_trait']),
        ]

    def __str__(self):
        return self.title_en
