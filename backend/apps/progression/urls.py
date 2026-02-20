from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'achievements', views.AchievementViewSet)

# Explicit URL patterns to avoid double prefix (progression/progression/)
urlpatterns = [
    # Stats and history — direct paths
    path('stats/', views.ProgressionViewSet.as_view({'get': 'stats'}), name='progression-stats'),
    path('history/', views.ProgressionViewSet.as_view({'get': 'history'}), name='progression-history'),
    path('quests/', views.ProgressionViewSet.as_view({'get': 'quests'}), name='progression-quests'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('daily-challenge/', views.DailyChallengeView.as_view(), name='daily-challenge'),

    # Achievements — router handles list, detail, earned
    path('', include(router.urls)),
]
