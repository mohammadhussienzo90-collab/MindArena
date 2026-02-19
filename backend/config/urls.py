"""MindArena — Root URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'mindarena-api'})

urlpatterns = [
    path('api/health/', health_check, name='health'),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/assessment/', include('apps.assessment.urls')),
    path('api/realms/', include('apps.realms.urls')),
    path('api/progression/', include('apps.progression.urls')),
    path('api/companion/', include('apps.companion.urls')),
    path('api/feed/', include('apps.feed.urls')),
    path('api/arena/', include('apps.arena.urls')),
    path('admin/', admin.site.urls),
]
