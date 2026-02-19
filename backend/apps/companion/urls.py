from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.CompanionChatView.as_view(), name='companion-chat'),
    path('history/<int:conversation_id>/', views.CompanionHistoryView.as_view(), name='companion-history'),
]
