"""
SaiSuite — Chat: WebSocket Tests.

Tests for the ChatConsumer using channels.testing.WebsocketCommunicator.
Covers connection lifecycle, typing indicators, channel layer message
forwarding, and error handling.

Uses InMemoryChannelLayer configured in config.settings.testing
so no Redis instance is required during test runs.
"""
import asyncio

import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.urls import re_path
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.consumers import ChatConsumer
from apps.chat.routing import websocket_urlpatterns as chat_ws_urlpatterns
from apps.notifications.middleware import JWTAuthMiddleware

User = get_user_model()


def _build_application():
    """Build the ASGI application stack used by the chat consumer tests."""
    return JWTAuthMiddleware(URLRouter(chat_ws_urlpatterns))


# ── Async helper functions ───────────────────────────────────────


@database_sync_to_async
def _create_company(nit='900777001', name='Chat Test Co'):
    from apps.companies.models import Company

    company, _ = Company.objects.get_or_create(
        nit=nit,
        defaults={'name': name},
    )
    return company


@database_sync_to_async
def _create_user(email, company):
    return User.objects.create_user(
        email=email,
        password='TestPass123!',
        first_name='Chat',
        last_name='Tester',
        company=company,
    )


@database_sync_to_async
def _get_token(user):
    return str(AccessToken.for_user(user))


@database_sync_to_async
def _create_conversation(company, user_a, user_b):
    from apps.chat.models import Conversacion

    return Conversacion.objects.create(
        company=company,
        participante_1=user_a,
        participante_2=user_b,
    )


# ── Test: Authenticated Connection ───────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_connect_authenticated():
    """
    A WebSocket connection with a valid JWT token should be accepted.
    """
    company = await _create_company(nit='900770001')
    user = await _create_user('chat_ws_auth@test.com', company)
    token = await _get_token(user)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    await communicator.disconnect()


# ── Test: Unauthenticated Connection (no token) ─────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_unauthenticated_no_token():
    """
    A WebSocket connection without a token should be rejected.
    """
    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        '/ws/chat/',
    )

    connected, code = await communicator.connect()
    assert connected is False


# ── Test: Unauthenticated Connection (invalid token) ────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_unauthenticated_invalid_token():
    """
    A WebSocket connection with an invalid/malformed JWT should be rejected.
    """
    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        '/ws/chat/?token=invalid.jwt.garbage',
    )

    connected, code = await communicator.connect()
    assert connected is False


# ── Test: User joins conversation groups on connect ──────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_joins_conversation_groups():
    """
    When a user connects, the consumer should join channel groups
    for all of the user's existing conversations.
    """
    company = await _create_company(nit='900770002')
    user_a = await _create_user('chat_ws_join_a@test.com', company)
    user_b = await _create_user('chat_ws_join_b@test.com', company)
    conv = await _create_conversation(company, user_a, user_b)

    token_a = await _get_token(user_a)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token_a}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Verify by sending a message to the conversation group via channel layer.
    channel_layer = get_channel_layer()
    conv_id = str(conv.id)

    await channel_layer.group_send(
        f'chat_{conv_id}',
        {
            'type': 'chat.new_message',
            'data': {
                'id': 'test-msg-uuid',
                'conversacion_id': conv_id,
                'contenido': 'Hello via channel layer',
                'remitente_id': str(user_b.id),
            },
        },
    )

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'new_message'
    assert response['data']['contenido'] == 'Hello via channel layer'
    assert response['data']['conversacion_id'] == conv_id

    await communicator.disconnect()


# ── Test: Typing indicator broadcast ─────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_typing_indicator():
    """
    When User A sends a typing indicator, User B should receive it.
    User A should NOT receive their own typing indicator back.
    """
    company = await _create_company(nit='900770003')
    user_a = await _create_user('chat_ws_typing_a@test.com', company)
    user_b = await _create_user('chat_ws_typing_b@test.com', company)
    conv = await _create_conversation(company, user_a, user_b)

    token_a = await _get_token(user_a)
    token_b = await _get_token(user_b)

    application = _build_application()

    # Both users connect.
    comm_a = WebsocketCommunicator(application, f'/ws/chat/?token={token_a}')
    comm_b = WebsocketCommunicator(application, f'/ws/chat/?token={token_b}')

    connected_a, _ = await comm_a.connect()
    connected_b, _ = await comm_b.connect()
    assert connected_a is True
    assert connected_b is True

    # User A sends typing indicator.
    await comm_a.send_json_to({
        'type': 'chat.typing',
        'conversacion_id': str(conv.id),
    })

    # User B should receive the typing indicator.
    response = await comm_b.receive_json_from(timeout=3)
    assert response['type'] == 'typing'
    assert response['data']['conversacion_id'] == str(conv.id)
    assert response['data']['user_id'] == str(user_a.id)

    # User A should NOT receive their own typing indicator.
    assert await comm_a.receive_nothing(timeout=0.5) is True

    await comm_a.disconnect()
    await comm_b.disconnect()


# ── Test: New message via channel layer ──────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_new_message_via_channel_layer():
    """
    When a chat.new_message is sent to a conversation group via
    channel_layer.group_send, both participants should receive it.
    """
    company = await _create_company(nit='900770004')
    user_a = await _create_user('chat_ws_newmsg_a@test.com', company)
    user_b = await _create_user('chat_ws_newmsg_b@test.com', company)
    conv = await _create_conversation(company, user_a, user_b)

    token_a = await _get_token(user_a)
    token_b = await _get_token(user_b)

    application = _build_application()
    comm_a = WebsocketCommunicator(application, f'/ws/chat/?token={token_a}')
    comm_b = WebsocketCommunicator(application, f'/ws/chat/?token={token_b}')

    connected_a, _ = await comm_a.connect()
    connected_b, _ = await comm_b.connect()
    assert connected_a is True
    assert connected_b is True

    # Simulate a message push from the service layer.
    channel_layer = get_channel_layer()
    conv_id = str(conv.id)

    message_data = {
        'id': 'msg-uuid-5678',
        'conversacion_id': conv_id,
        'remitente_id': str(user_a.id),
        'remitente_nombre': 'Chat Tester',
        'contenido': 'Hola desde el servicio!',
        'imagen_url': '',
        'created_at': '2026-03-30T12:00:00Z',
    }

    await channel_layer.group_send(
        f'chat_{conv_id}',
        {
            'type': 'chat.new_message',
            'data': message_data,
        },
    )

    # Both users should receive the new message.
    msg_a = await comm_a.receive_json_from(timeout=3)
    assert msg_a['type'] == 'new_message'
    assert msg_a['data']['contenido'] == 'Hola desde el servicio!'

    msg_b = await comm_b.receive_json_from(timeout=3)
    assert msg_b['type'] == 'new_message'
    assert msg_b['data']['contenido'] == 'Hola desde el servicio!'

    await comm_a.disconnect()
    await comm_b.disconnect()


# ── Test: Read receipt via channel layer ─────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_read_receipt_via_channel_layer():
    """
    When a chat.message_read event is sent to a conversation group,
    the connected participants should receive the read receipt.
    """
    company = await _create_company(nit='900770005')
    user_a = await _create_user('chat_ws_read_a@test.com', company)
    user_b = await _create_user('chat_ws_read_b@test.com', company)
    conv = await _create_conversation(company, user_a, user_b)

    token_a = await _get_token(user_a)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token_a}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Simulate a read receipt push from the service layer.
    channel_layer = get_channel_layer()
    conv_id = str(conv.id)

    read_data = {
        'mensaje_id': 'msg-read-uuid-9999',
        'conversacion_id': conv_id,
        'leido_por': str(user_b.id),
        'leido_at': '2026-03-30T12:05:00Z',
    }

    await channel_layer.group_send(
        f'chat_{conv_id}',
        {
            'type': 'chat.message_read',
            'data': read_data,
        },
    )

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'message_read'
    assert response['data']['mensaje_id'] == 'msg-read-uuid-9999'
    assert response['data']['leido_por'] == str(user_b.id)

    await communicator.disconnect()


# ── Test: New conversation notification via user group ───────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_new_conversation_notification():
    """
    When a chat.new_conversation event is sent to the user's personal group,
    the consumer should automatically join the new conversation group and
    forward the event to the client.
    """
    company = await _create_company(nit='900770006')
    user_a = await _create_user('chat_ws_newconv_a@test.com', company)

    token_a = await _get_token(user_a)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token_a}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Simulate a new conversation notification via the user group.
    channel_layer = get_channel_layer()
    new_conv_id = 'new-conv-uuid-1234'

    await channel_layer.group_send(
        f'chat_user_{user_a.id}',
        {
            'type': 'chat.new_conversation',
            'conversacion_id': new_conv_id,
            'data': {
                'id': new_conv_id,
                'participante_nombre': 'Otro Usuario',
            },
        },
    )

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'new_conversation'
    assert response['data']['id'] == new_conv_id

    # Now the consumer should have joined the new conversation group.
    # Verify by sending a message to that group.
    await channel_layer.group_send(
        f'chat_{new_conv_id}',
        {
            'type': 'chat.new_message',
            'data': {
                'id': 'msg-in-new-conv',
                'conversacion_id': new_conv_id,
                'contenido': 'Mensaje en nueva conversacion',
            },
        },
    )

    msg = await communicator.receive_json_from(timeout=3)
    assert msg['type'] == 'new_message'
    assert msg['data']['contenido'] == 'Mensaje en nueva conversacion'

    await communicator.disconnect()


# ── Test: Send message without required fields returns error ─────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_send_message_missing_fields():
    """
    Sending a chat.send_message without conversacion_id or content
    should return an error message.
    """
    company = await _create_company(nit='900770007')
    user = await _create_user('chat_ws_err@test.com', company)
    token = await _get_token(user)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Missing conversacion_id.
    await communicator.send_json_to({
        'type': 'chat.send_message',
        'contenido': 'Hola',
    })

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'error'
    assert 'conversacion_id' in response['message']

    # Missing both contenido and imagen_url.
    await communicator.send_json_to({
        'type': 'chat.send_message',
        'conversacion_id': 'some-uuid',
    })

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'error'

    await communicator.disconnect()


# ── Test: Disconnect cleans up groups ────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_disconnect_cleans_up():
    """
    After disconnecting, the user should be removed from all groups.
    Messages sent to the conversation group should not reach the disconnected client.
    """
    company = await _create_company(nit='900770008')
    user_a = await _create_user('chat_ws_disc_a@test.com', company)
    user_b = await _create_user('chat_ws_disc_b@test.com', company)
    conv = await _create_conversation(company, user_a, user_b)

    token_a = await _get_token(user_a)

    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token_a}',
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # Disconnect.
    await communicator.disconnect()

    # Sending a message to the group after disconnect should not raise.
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'chat_{conv.id}',
        {
            'type': 'chat.new_message',
            'data': {'id': 'after-disconnect', 'contenido': 'Ghost'},
        },
    )

    # No error should occur — the group_send just goes to an empty group.


# ── Test: Join conversation dynamically ──────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_ws_join_conversation():
    """
    When a client sends chat.join_conversation for a conversation
    they participate in, they should start receiving messages from that group.
    """
    company = await _create_company(nit='900770009')
    user_a = await _create_user('chat_ws_joincv_a@test.com', company)
    user_b = await _create_user('chat_ws_joincv_b@test.com', company)

    # Connect user_a BEFORE the conversation exists.
    token_a = await _get_token(user_a)
    application = _build_application()
    communicator = WebsocketCommunicator(
        application,
        f'/ws/chat/?token={token_a}',
    )
    connected, _ = await communicator.connect()
    assert connected is True

    # Now create the conversation.
    conv = await _create_conversation(company, user_a, user_b)

    # User A explicitly joins the conversation.
    await communicator.send_json_to({
        'type': 'chat.join_conversation',
        'conversacion_id': str(conv.id),
    })

    # Allow the event loop to process the join (consumer runs _verify_participant
    # via database_sync_to_async before adding to the group).
    await asyncio.sleep(0.5)

    # Now send a message via channel layer to the conversation group.
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'chat_{conv.id}',
        {
            'type': 'chat.new_message',
            'data': {
                'id': 'msg-after-join',
                'conversacion_id': str(conv.id),
                'contenido': 'Mensaje post-join',
            },
        },
    )

    response = await communicator.receive_json_from(timeout=3)
    assert response['type'] == 'new_message'
    assert response['data']['contenido'] == 'Mensaje post-join'

    await communicator.disconnect()
