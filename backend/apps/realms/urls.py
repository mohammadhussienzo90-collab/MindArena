from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'realms', views.RealmViewSet)
router.register(r'quests', views.QuestViewSet, basename='quest')
router.register(r'challenges', views.ChallengeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
