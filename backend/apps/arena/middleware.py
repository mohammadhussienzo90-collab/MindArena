"""JWT authentication middleware for WebSocket connections.

WebSockets cannot send custom headers, so the JWT token is passed as a
query string parameter: ws://host/ws/arena/123/?token=<jwt_access_token>
"""
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_str):
    """Validate a JWT access token and return the associated user."""
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from django.contrib.auth import get_user_model

        User = get_user_model()
        access_token = AccessToken(token_str)
        user_id = access_token['user_id']
        return User.objects.select_related('player').get(id=user_id)
    except Exception as e:
        logger.warning("WebSocket JWT auth failed: %s", e)
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Extract JWT token from query string and attach user to scope."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)

        token_list = params.get('token', [])
        if token_list:
            scope['user'] = await get_user_from_token(token_list[0])
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
