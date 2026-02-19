from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.ArenaStatusView.as_view(), name='arena-status'),
]
