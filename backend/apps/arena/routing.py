"""WebSocket URL routing for the arena app."""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/arena/matchmaking/$', consumers.MatchmakingConsumer.as_asgi()),
    re_path(r'ws/arena/(?P<match_id>\d+)/$', consumers.ArenaConsumer.as_asgi()),
]
