from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('mark-read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('<int:notification_id>/', views.NotificationDeleteView.as_view(), name='notification-delete'),
]
