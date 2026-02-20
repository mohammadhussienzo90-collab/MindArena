from django.urls import path
from . import friends_views as views

urlpatterns = [
    path('', views.FriendListView.as_view(), name='friend-list'),
    path('request/', views.SendFriendRequestView.as_view(), name='friend-request-send'),
    path('requests/', views.FriendRequestListView.as_view(), name='friend-request-list'),
    path('respond/', views.RespondFriendRequestView.as_view(), name='friend-request-respond'),
    path('<int:player_id>/', views.RemoveFriendView.as_view(), name='friend-remove'),
]
