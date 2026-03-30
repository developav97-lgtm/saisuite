"""
SaiSuite — Chat: WebSocket Consumer.

Manages real-time message delivery, typing indicators, and read receipts
for 1-to-1 chat conversations between users of the same company.

Each connected user joins:
- ``chat_{conversacion_id}`` groups for all their active conversations
- ``chat_user_{user_id}`` group for new-conversation notifications

Business logic stays in services.py — this consumer only handles
connection lifecycle, message routing, and forwarding.
"""
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time chat.

    Protocol (server -> client):
        { "type": "new_message",      "data": { ...message payload... } }
        { "type": "message_read",     "data": { ...read receipt... } }
        { "type": "typing",           "data": { "conversacion_id", "user_id", "user_name" } }
        { "type": "new_conversation", "data": { ...conversation payload... } }
        { "type": "error",            "message": "..." }

    Protocol (client -> server):
        { "type": "chat.send_message",     "conversacion_id", "contenido", "imagen_url"?, "responde_a_id"? }
        { "type": "chat.typing",           "conversacion_id" }
        { "type": "chat.mark_read",        "mensaje_id" }
        { "type": "chat.join_conversation", "conversacion_id" }
    """

    # ── Connection lifecycle ─────────────────────────────────────

    async def connect(self):
        user = self.scope.get('user', AnonymousUser())

        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            logger.warning('chat_ws_connect_rejected_unauthenticated')
            await self.close(code=4001)
            return

        self.user = user
        self.conversation_groups: list[str] = []

        # Join groups for all user's existing conversations.
        conversation_ids = await self._get_user_conversations()
        for conv_id in conversation_ids:
            group_name = f'chat_{conv_id}'
            await self.channel_layer.group_add(group_name, self.channel_name)
            self.conversation_groups.append(group_name)

        # Also join user-specific chat group for new conversation notifications.
        self.user_group = f'chat_user_{self.user.id}'
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()

        logger.info(
            'chat_ws_connected',
            extra={
                'user_id': str(self.user.id),
                'conversations': len(self.conversation_groups),
            },
        )

    async def disconnect(self, close_code):
        # Leave all conversation groups.
        for group_name in getattr(self, 'conversation_groups', []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

        if hasattr(self, 'user'):
            logger.info(
                'chat_ws_disconnected',
                extra={
                    'user_id': str(self.user.id),
                    'close_code': close_code,
                },
            )

    # ── Client -> Server messages ────────────────────────────────

    async def receive_json(self, content, **kwargs):
        """Handle incoming WebSocket messages from client."""
        msg_type = content.get('type')

        if msg_type == 'chat.send_message':
            await self._handle_send_message(content)
        elif msg_type == 'chat.typing':
            await self._handle_typing(content)
        elif msg_type == 'chat.mark_read':
            await self._handle_mark_read(content)
        elif msg_type == 'chat.join_conversation':
            await self._handle_join_conversation(content)
        else:
            logger.warning(
                'chat_ws_unknown_message_type',
                extra={'user_id': str(self.user.id), 'type': msg_type},
            )

    # ── Group message handlers (server -> client) ────────────────

    async def chat_new_message(self, event):
        """
        Handler for messages sent via:
            channel_layer.group_send(group, {
                'type': 'chat.new_message',
                'data': { ...serialized message... },
            })
        """
        await self.send_json({
            'type': 'new_message',
            'data': event['data'],
        })

    async def chat_message_read(self, event):
        """
        Handler for read receipt broadcasts via:
            channel_layer.group_send(group, {
                'type': 'chat.message_read',
                'data': { ...read receipt... },
            })
        """
        await self.send_json({
            'type': 'message_read',
            'data': event['data'],
        })

    async def chat_typing(self, event):
        """
        Broadcast typing indicator — only to the other participant,
        not back to the user who is typing.
        """
        if event.get('user_id') != str(self.user.id):
            await self.send_json({
                'type': 'typing',
                'data': {
                    'conversacion_id': event['conversacion_id'],
                    'user_id': event['user_id'],
                    'user_name': event.get('user_name', ''),
                },
            })

    async def chat_new_conversation(self, event):
        """
        Notification that a new conversation was created involving this user.
        Automatically joins the conversation group so future messages arrive.
        """
        conv_id = event['conversacion_id']
        group_name = f'chat_{conv_id}'
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.conversation_groups.append(group_name)
        await self.send_json({
            'type': 'new_conversation',
            'data': event.get('data', {}),
        })

    # ── Client message handlers ──────────────────────────────────

    async def _handle_send_message(self, content):
        """Handle message sent from WebSocket client."""
        conversacion_id = content.get('conversacion_id')
        contenido = content.get('contenido', '')
        imagen_url = content.get('imagen_url', '')
        responde_a_id = content.get('responde_a_id')

        if not conversacion_id or (not contenido and not imagen_url):
            await self.send_json({
                'type': 'error',
                'message': 'Se requiere conversacion_id y contenido o imagen_url',
            })
            return

        try:
            mensaje = await self._create_message(
                conversacion_id, self.user, contenido, imagen_url, responde_a_id,
            )
            logger.info(
                'chat_ws_message_sent',
                extra={
                    'user_id': str(self.user.id),
                    'conversacion_id': str(conversacion_id),
                    'mensaje_id': str(mensaje.id),
                },
            )
        except PermissionError as exc:
            await self.send_json({
                'type': 'error',
                'message': str(exc),
            })
        except Exception:
            logger.exception(
                'chat_ws_send_failed',
                extra={
                    'user_id': str(self.user.id),
                    'conversacion_id': str(conversacion_id),
                },
            )
            await self.send_json({
                'type': 'error',
                'message': 'Error al enviar mensaje',
            })

    async def _handle_typing(self, content):
        """Handle typing indicator from client."""
        conversacion_id = content.get('conversacion_id')
        if not conversacion_id:
            return

        group_name = f'chat_{conversacion_id}'
        await self.channel_layer.group_send(group_name, {
            'type': 'chat.typing',
            'conversacion_id': str(conversacion_id),
            'user_id': str(self.user.id),
            'user_name': await self._get_user_name(),
        })

    async def _handle_mark_read(self, content):
        """Handle mark-as-read from client."""
        mensaje_id = content.get('mensaje_id')
        if not mensaje_id:
            return

        try:
            await self._mark_message_read(mensaje_id, self.user)
        except PermissionError as exc:
            await self.send_json({
                'type': 'error',
                'message': str(exc),
            })
        except Exception:
            logger.exception(
                'chat_ws_mark_read_failed',
                extra={
                    'user_id': str(self.user.id),
                    'mensaje_id': str(mensaje_id),
                },
            )

    async def _handle_join_conversation(self, content):
        """Handle joining a new conversation group (e.g., after receiving new_conversation event)."""
        conversacion_id = content.get('conversacion_id')
        if not conversacion_id:
            return

        # Verify user is a participant before allowing the join.
        is_participant = await self._verify_participant(conversacion_id)
        if is_participant:
            group_name = f'chat_{conversacion_id}'
            if group_name not in self.conversation_groups:
                await self.channel_layer.group_add(group_name, self.channel_name)
                self.conversation_groups.append(group_name)

    # ── Private helpers (DB access via sync_to_async) ────────────

    @database_sync_to_async
    def _get_user_conversations(self):
        from apps.chat.models import Conversacion

        return list(
            Conversacion.all_objects.filter(
                Q(participante_1=self.user) | Q(participante_2=self.user),
            ).values_list('id', flat=True)
        )

    @database_sync_to_async
    def _create_message(self, conversacion_id, user, contenido, imagen_url, responde_a_id):
        from apps.chat.services import ChatService

        return ChatService.enviar_mensaje(
            conversacion_id=conversacion_id,
            remitente=user,
            contenido=contenido,
            imagen_url=imagen_url,
            responde_a_id=responde_a_id,
        )

    @database_sync_to_async
    def _mark_message_read(self, mensaje_id, user):
        from apps.chat.services import ChatService

        return ChatService.marcar_leido(mensaje_id, user)

    @database_sync_to_async
    def _get_user_name(self):
        return self.user.full_name

    @database_sync_to_async
    def _verify_participant(self, conversacion_id):
        from apps.chat.models import Conversacion

        return Conversacion.all_objects.filter(
            Q(participante_1=self.user) | Q(participante_2=self.user),
            id=conversacion_id,
        ).exists()
