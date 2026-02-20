from django.contrib import admin
from .models import PersonalityAssessment


@admin.register(PersonalityAssessment)
class PersonalityAssessmentAdmin(admin.ModelAdmin):
    list_display = ['player', 'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism', 'completed_at']
    search_fields = ['player__display_name']
    readonly_fields = ['completed_at', 'updated_at']
