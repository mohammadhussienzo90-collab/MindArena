"""
AI Engine URL Configuration
=============================
All endpoints are prefixed with ``api/ai/`` in the project-level urls.py.
"""
from django.urls import path

from . import views

app_name = 'ai_engine'

urlpatterns = [
    # Player insights dashboard
    path('insights/', views.PlayerInsightsView.as_view(), name='insights'),

    # Challenge recommendation
    path('next-challenge/', views.NextChallengeView.as_view(), name='next-challenge'),
    path('recommendations/', views.RecommendationsView.as_view(), name='recommendations'),

    # Learning path and weekly plan
    path('learning-path/', views.LearningPathView.as_view(), name='learning-path'),
    path('weekly-plan/', views.WeeklyPlanView.as_view(), name='weekly-plan'),

    # Knowledge and mastery
    path('knowledge-state/', views.KnowledgeStateView.as_view(), name='knowledge-state'),
    path('difficulty/', views.DifficultyView.as_view(), name='difficulty'),

    # Spaced repetition
    path('srs-due/', views.SRSDueView.as_view(), name='srs-due'),

    # Engagement metrics
    path('engagement/', views.EngagementView.as_view(), name='engagement'),

    # Smart Noor companion
    path('companion/smart-chat/', views.SmartChatView.as_view(), name='smart-chat'),

    # Session lifecycle
    path('session/start/', views.SessionStartView.as_view(), name='session-start'),
    path('session/end/', views.SessionEndView.as_view(), name='session-end'),
]
