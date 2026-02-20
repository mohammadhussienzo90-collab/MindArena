from django.contrib import admin
from django.utils.html import format_html

from .models import PersonalityAssessment


@admin.register(PersonalityAssessment)
class PersonalityAssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'player', 'openness', 'conscientiousness', 'extraversion',
        'agreeableness', 'neuroticism', 'average_score_display',
        'version', 'completed_at',
    ]
    list_filter = ['version', 'learning_style', 'completed_at']
    search_fields = ['player__display_name', 'player__user__username']
    readonly_fields = ['completed_at', 'updated_at', 'average_score_display']
    list_select_related = ['player']
    list_per_page = 30
    date_hierarchy = 'completed_at'
    ordering = ['-completed_at']

    fieldsets = (
        ('Player', {
            'fields': ('player',),
        }),
        ('Big Five Scores', {
            'fields': (
                'openness', 'conscientiousness', 'extraversion',
                'agreeableness', 'neuroticism',
            ),
            'description': 'Big Five personality traits scored 0-100.',
        }),
        ('Emotional Intelligence', {
            'fields': (
                'self_awareness', 'empathy', 'emotional_regulation', 'social_skills',
            ),
        }),
        ('Cognitive Style', {
            'fields': (
                'analytical_thinking', 'creative_thinking', 'practical_thinking',
            ),
            'classes': ('collapse',),
        }),
        ('Additional', {
            'fields': (
                'risk_tolerance', 'learning_style',
            ),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': (
                'raw_answers', 'version', 'completed_at', 'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Avg Big Five')
    def average_score_display(self, obj):
        avg = (
            obj.openness + obj.conscientiousness + obj.extraversion
            + obj.agreeableness + obj.neuroticism
        ) / 5.0
        return f'{avg:.1f}'
