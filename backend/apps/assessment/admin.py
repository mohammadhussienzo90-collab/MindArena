from django.contrib import admin
from .models import PersonalityAssessment


@admin.register(PersonalityAssessment)
class PersonalityAssessmentAdmin(admin.ModelAdmin):
    list_display = ['player', 'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism', 'created_at']
    search_fields = ['player__display_name']
    readonly_fields = ['created_at']
