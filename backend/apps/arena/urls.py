from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.ArenaStatusView.as_view(), name='arena-status'),
    path('matches/', views.ArenaMatchListView.as_view(), name='arena-match-list'),
    path('matches/create/', views.ArenaCreateMatchView.as_view(), name='arena-create-match'),
    path('matches/find/', views.ArenaFindMatchView.as_view(), name='arena-find-match'),
    path('matches/<int:match_id>/', views.ArenaMatchDetailView.as_view(), name='arena-match-detail'),
    path('matches/<int:match_id>/join/', views.ArenaJoinMatchView.as_view(), name='arena-join-match'),
    path('matches/<int:match_id>/challenge/', views.ArenaCurrentChallengeView.as_view(), name='arena-current-challenge'),
    path('matches/<int:match_id>/cancel/', views.ArenaCancelMatchView.as_view(), name='arena-cancel-match'),
    path('submit/', views.ArenaSubmitAnswerView.as_view(), name='arena-submit-answer'),
    path('stats/', views.ArenaStatsView.as_view(), name='arena-stats'),
    path('leaderboard/', views.ArenaLeaderboardView.as_view(), name='arena-leaderboard'),
]
