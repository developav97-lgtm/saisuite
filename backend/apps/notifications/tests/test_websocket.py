"""
SaiSuite — Notifications: WebSocket Tests.

Tests for the NotificationConsumer and JWTAuthMiddleware using
channels.testing.WebsocketCommunicator.

Uses InMemoryChannelLayer configured in config.settings.testing
so no Redis instance is required during test runs.
"""
import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.notifications.middleware import JWTAuthMiddleware
from apps.notifications.routing import websocket_urlpatterns

User = get_user_model()


def _build_application():
    """Build the ASGI application stack used by the consumer tests."""
    return JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


@database_sync_to_async
def _create_test_user(email='wstest@example.com', password='testpass123'):
    """Create a test user with a company for multi-tenant compatibility."""
    from apps.companies.models import Company

    company, _ = Company.objects.get_or_create(
        nit='900999002',
        defaults={'name': 'Test Company WS'},
    )
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name='WS',
        last_name='Test',
        company=company,
    )
    return user


@database_sync_to_async
def _get_token_for_user(user) -> str:
    """Generate a valid JWT access token for the given user."""
    token = AccessToken.for_user(user)
    return str(token)


# ── Test: Authenticated Connection ───────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_authenticated_connection():
    """
    A WebSocket connection with a valid JWT token in the query string
    should be accepted and receive an initial unread_count message.
    """
    user = await _create_test_user(email='ws_auth@example.com')
    token = await _get_token_for_user(user)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/notifications/?token={token}',
    )

    connected, subprotocol = await communicator.connect()
    assert connected is True

    # The consumer sends an initial unread_count message on connect.
    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'unread_count'
    assert isinstance(response['count'], int)
    assert response['count'] >= 0

    await communicator.disconnect()


# ── Test: Unauthenticated Connection (no token) ─────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unauthenticated_connection_no_token():
    """
    A WebSocket connection without a token should be rejected with code 4001.
    """
    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/',
    )

    connected, code = await communicator.connect()
    assert connected is False


# ── Test: Unauthenticated Connection (invalid token) ────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unauthenticated_connection_invalid_token():
    """
    A WebSocket connection with an invalid/malformed JWT should be rejected.
    """
    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/?token=invalid.jwt.token',
    )

    connected, code = await communicator.connect()
    assert connected is False


# ── Test: Receive Notification via Channel Layer ─────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_receive_notification_via_channel_layer():
    """
    When a notification.message is sent to the user's group via
    channel_layer.group_send, the connected WebSocket should receive it.
    """
    user = await _create_test_user(email='ws_channel@example.com')
    token = await _get_token_for_user(user)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/notifications/?token={token}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Consume the initial unread_count message.
    initial_msg = await communicator.receive_json_from(timeout=3)
    assert initial_msg['type'] == 'unread_count'

    # Simulate a notification push from the backend (e.g., from services.py).
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user.id}'

    notification_data = {
        'id': 'test-uuid-1234',
        'tipo': 'comentario',
        'titulo': 'Nuevo comentario en Tarea',
        'mensaje': 'Juan escribio un comentario',
        'leida': False,
    }

    await channel_layer.group_send(
        group_name,
        {
            'type': 'notification.message',
            'data': notification_data,
        },
    )

    # The consumer should forward it as a 'notification' type message.
    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'notification'
    assert response['data']['id'] == 'test-uuid-1234'
    assert response['data']['tipo'] == 'comentario'
    assert response['data']['titulo'] == 'Nuevo comentario en Tarea'

    await communicator.disconnect()


# ── Test: Count Update via Channel Layer ─────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_receive_count_update_via_channel_layer():
    """
    When a notification.count_update is sent to the user's group,
    the consumer should respond with an updated unread_count.
    """
    user = await _create_test_user(email='ws_count@example.com')
    token = await _get_token_for_user(user)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/notifications/?token={token}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Consume the initial unread_count.
    await communicator.receive_json_from(timeout=3)

    # Trigger a count update via channel layer.
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user.id}'
    await channel_layer.group_send(
        group_name,
        {'type': 'notification.count_update'},
    )

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'unread_count'
    assert isinstance(response['count'], int)

    await communicator.disconnect()
