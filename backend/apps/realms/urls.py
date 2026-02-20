from django.urls import path
from . import views

# Explicit URL patterns to avoid double prefix (api/v1/realms/realms/)
# since root urls.py already has path('api/v1/realms/', include(...))

realm_list = views.RealmViewSet.as_view({'get': 'list'})
realm_detail = views.RealmViewSet.as_view({'get': 'retrieve'})
realm_challenges = views.RealmViewSet.as_view({'get': 'challenges'})

challenge_list = views.ChallengeViewSet.as_view({'get': 'list'})
challenge_detail = views.ChallengeViewSet.as_view({'get': 'retrieve'})
challenge_submit = views.ChallengeViewSet.as_view({'post': 'submit'})

quest_list = views.QuestViewSet.as_view({'get': 'list'})
quest_detail = views.QuestViewSet.as_view({'get': 'retrieve'})
quest_start = views.QuestViewSet.as_view({'post': 'start'})

urlpatterns = [
    # Realms
    path('', realm_list, name='realm-list'),
    path('<slug:slug>/', realm_detail, name='realm-detail'),
    path('<slug:slug>/challenges/', realm_challenges, name='realm-challenges'),

    # Challenges
    path('challenges/', challenge_list, name='challenge-list'),
    path('challenges/<int:pk>/', challenge_detail, name='challenge-detail'),
    path('challenges/<int:pk>/submit/', challenge_submit, name='challenge-submit'),

    # Quests
    path('quests/', quest_list, name='quest-list'),
    path('quests/<int:pk>/', quest_detail, name='quest-detail'),
    path('quests/<int:pk>/start/', quest_start, name='quest-start'),
]
