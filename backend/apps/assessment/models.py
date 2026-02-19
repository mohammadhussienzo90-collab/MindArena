from django.db import models


class PersonalityAssessment(models.Model):
    player = models.OneToOneField('accounts.Player', on_delete=models.CASCADE, related_name='assessment')

    # Big Five traits (0-100)
    openness = models.FloatField(default=50)
    conscientiousness = models.FloatField(default=50)
    extraversion = models.FloatField(default=50)
    agreeableness = models.FloatField(default=50)
    neuroticism = models.FloatField(default=50)

    # Emotional Intelligence (0-100)
    self_awareness = models.FloatField(default=50)
    empathy = models.FloatField(default=50)
    emotional_regulation = models.FloatField(default=50)
    social_skills = models.FloatField(default=50)

    # Cognitive Style (0-100)
    analytical_thinking = models.FloatField(default=50)
    creative_thinking = models.FloatField(default=50)
    practical_thinking = models.FloatField(default=50)

    # Additional
    risk_tolerance = models.FloatField(default=50)
    learning_style = models.CharField(max_length=20, default='mixed')

    raw_answers = models.JSONField(default=dict, blank=True)
    version = models.IntegerField(default=1)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assessment: {self.player}"
