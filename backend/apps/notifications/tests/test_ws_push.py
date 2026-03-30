"""
SaiSuite — Notifications: WebSocket Push Tests.

Verifies that NotificacionService.crear() pushes a real-time notification
and an unread_count update through the channel layer to connected clients.

Uses InMemoryChannelLayer configured in config.settings.testing
so no Redis instance is required during test runs.
"""
import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model

from apps.notifications.middleware import JWTAuthMiddleware
from apps.notifications.routing import websocket_urlpatterns
from apps.notifications.services import NotificacionService

User = get_user_model()


def _build_application():
    """Build the ASGI application stack used by the consumer tests."""
    return JWTAuthMiddleware(URLRouter(websocket_urlpatterns))


@database_sync_to_async
def _create_test_user(email='ws_push_test@example.com'):
    """Create a test user with a company for multi-tenant compatibility."""
    from apps.companies.models import Company

    company, _ = Company.objects.get_or_create(
        nit='900999003',
        defaults={'name': 'Test Company Push'},
    )
    return User.objects.create_user(
        email=email,
        password='testpass123',
        first_name='Push',
        last_name='Test',
        company=company,
    )


@database_sync_to_async
def _get_token(user) -> str:
    """Generate a valid JWT access token for the given user."""
    from rest_framework_simplejwt.tokens import AccessToken

    return str(AccessToken.for_user(user))


@database_sync_to_async
def _create_notification(user):
    """Create a notification using the service, which should also push via WS."""
    from apps.companies.models import Company

    company = Company.objects.get(id=user.company_id)
    return NotificacionService.crear(
        usuario=user,
        tipo='sistema',
        titulo='Test push notification',
        mensaje='This notification should arrive via WebSocket',
        objeto_relacionado=company,
        url_accion='/test',
    )


# ── Test: crear() pushes notification + count via WebSocket ──────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_pushes_via_websocket():
    """
    When NotificacionService.crear() is called, the connected WebSocket
    client should receive both a 'notification' message and an 'unread_count' update.
    """
    user = await _create_test_user()
    token = await _get_token(user)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/notifications/?token={token}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Consume the initial unread_count message sent on connect.
    initial = await communicator.receive_json_from(timeout=3)
    assert initial['type'] == 'unread_count'

    # Create notification via service (this should push via channel layer).
    notif = await _create_notification(user)
    assert notif is not None

    # Should receive the notification message.
    msg = await communicator.receive_json_from(timeout=3)
    assert msg['type'] == 'notification'
    assert msg['data']['titulo'] == 'Test push notification'
    assert msg['data']['tipo'] == 'sistema'

    # Should also receive an updated unread_count.
    count_msg = await communicator.receive_json_from(timeout=3)
    assert count_msg['type'] == 'unread_count'
    assert count_msg['count'] >= 1

    await communicator.disconnect()


# ── Test: crear() without WebSocket client does not fail ──────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_without_ws_client_does_not_fail():
    """
    NotificacionService.crear() should succeed even when no WebSocket
    client is connected (the channel layer push goes to an empty group).
    """
    user = await _create_test_user(email='ws_push_no_client@example.com')

    # Create notification without any WS client connected.
    notif = await _create_notification(user)
    assert notif is not None
    assert notif.titulo == 'Test push notification'
    assert notif.tipo == 'sistema'
