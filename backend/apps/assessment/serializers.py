from rest_framework import serializers
from .models import PersonalityAssessment


class AssessmentSubmitSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=5),
        min_length=20,
        max_length=45,
    )


class PersonalityAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalityAssessment
        fields = [
            'openness', 'conscientiousness', 'extraversion',
            'agreeableness', 'neuroticism', 'self_awareness',
            'empathy', 'emotional_regulation', 'social_skills',
            'analytical_thinking', 'creative_thinking', 'practical_thinking',
            'risk_tolerance', 'learning_style', 'completed_at',
        ]
