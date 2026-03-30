"""
SaiSuite — Notifications: JWT Authentication Middleware for WebSocket.

Extracts a JWT access token from the WebSocket query string (?token=<jwt>),
validates it via simplejwt, and sets scope['user'] to the authenticated user.
If the token is missing or invalid the connection is closed with code 4001.
"""
import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_str: str):
    """
    Validate the raw JWT string and return the corresponding User.
    Returns AnonymousUser when the token is invalid or the user does not exist.
    """
    try:
        access_token = AccessToken(token_str)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        if not user.is_active:
            logger.warning(
                'ws_auth_inactive_user',
                extra={'user_id': str(user_id)},
            )
            return AnonymousUser()
        return user
    except (InvalidToken, TokenError) as exc:
        logger.warning(
            'ws_auth_invalid_token',
            extra={'error': str(exc)},
        )
        return AnonymousUser()
    except User.DoesNotExist:
        logger.warning(
            'ws_auth_user_not_found',
            extra={'token_payload': 'user_id missing or invalid'},
        )
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    ASGI middleware that authenticates WebSocket connections via JWT.

    Usage in asgi.py:
        JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

    The client connects with:
        ws://host/ws/notifications/?token=<access_token>
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        params = parse_qs(query_string)
        token_list = params.get('token', [])

        if token_list:
            scope['user'] = await get_user_from_token(token_list[0])
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
