"""MindArena — Root URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import TemplateView

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'mindarena-api'})

urlpatterns = [
    path('', TemplateView.as_view(template_name='demo.html'), name='demo'),
    path('api/health/', health_check, name='health'),

    # v1 API — matches Godot client base_url "http://localhost:8000/api/v1"
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/assessment/', include('apps.assessment.urls')),
    path('api/v1/realms/', include('apps.realms.urls')),
    path('api/v1/progression/', include('apps.progression.urls')),
    path('api/v1/companion/', include('apps.companion.urls')),
    path('api/v1/feed/', include('apps.feed.urls')),
    path('api/v1/arena/', include('apps.arena.urls')),
    path('api/v1/friends/', include('apps.accounts.friends_urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),

    path('admin/', admin.site.urls),
]
