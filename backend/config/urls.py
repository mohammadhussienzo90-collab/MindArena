"""MindArena — Root URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'mindarena-api'})

urlpatterns = [
    path('api/health/', health_check, name='health'),

    # v1 API — matches Godot client base_url "http://localhost:8000/api/v1"
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/assessment/', include('apps.assessment.urls')),
    path('api/v1/realms/', include('apps.realms.urls')),
    path('api/v1/progression/', include('apps.progression.urls')),
    path('api/v1/companion/', include('apps.companion.urls')),
    path('api/v1/feed/', include('apps.feed.urls')),
    path('api/v1/arena/', include('apps.arena.urls')),

    path('admin/', admin.site.urls),
]
