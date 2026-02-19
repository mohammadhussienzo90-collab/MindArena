from django.urls import path
from . import views

urlpatterns = [
    path('', views.FeedListView.as_view(), name='feed-list'),
    path('<int:item_id>/interact/', views.FeedInteractView.as_view(), name='feed-interact'),
]
