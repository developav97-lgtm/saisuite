"""
SaiSuite — Notifications: WebSocket Consumer.

Manages real-time notification delivery per authenticated user.
Each connected user joins a private channel group ``notifications_{user_id}``
and receives JSON messages pushed via ``channel_layer.group_send``.

Business logic stays in services.py — this consumer only handles
connection lifecycle and message forwarding.
"""
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Protocol (server -> client):
        { "type": "unread_count", "count": int }
        { "type": "notification", "data": { ...notification payload... } }

    Protocol (client -> server):
        { "type": "mark_read", "notification_id": "<uuid>" }
    """

    # ── Connection lifecycle ─────────────────────────────────────

    async def connect(self):
        user = self.scope.get('user', AnonymousUser())

        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            logger.warning('ws_connect_rejected_unauthenticated')
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f'notifications_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

        # Send initial unread count so the UI can render the badge immediately.
        unread_count = await self._get_unread_count()
        await self.send_json({
            'type': 'unread_count',
            'count': unread_count,
        })

        logger.info(
            'ws_connected',
            extra={'user_id': str(self.user.id), 'group': self.group_name},
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )
            logger.info(
                'ws_disconnected',
                extra={
                    'user_id': str(self.user.id),
                    'group': self.group_name,
                    'close_code': close_code,
                },
            )

    # ── Client -> Server messages ────────────────────────────────

    async def receive_json(self, content, **kwargs):
        msg_type = content.get('type')

        if msg_type == 'mark_read':
            notification_id = content.get('notification_id')
            if notification_id:
                await self._mark_read(notification_id)
                unread_count = await self._get_unread_count()
                await self.send_json({
                    'type': 'unread_count',
                    'count': unread_count,
                })
        else:
            logger.warning(
                'ws_unknown_message_type',
                extra={'user_id': str(self.user.id), 'type': msg_type},
            )

    # ── Group message handlers (server -> client) ────────────────

    async def notification_message(self, event):
        """
        Handler for messages sent via:
            channel_layer.group_send(group, {
                'type': 'notification.message',
                'data': { ...serialized notification... },
            })
        """
        await self.send_json({
            'type': 'notification',
            'data': event['data'],
        })

    async def notification_count_update(self, event):
        """
        Handler for explicit unread-count refresh broadcasts.
            channel_layer.group_send(group, {
                'type': 'notification.count_update',
            })
        """
        unread_count = await self._get_unread_count()
        await self.send_json({
            'type': 'unread_count',
            'count': unread_count,
        })

    # ── Private helpers (DB access via sync_to_async) ────────────

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        from apps.notifications.services import NotificacionService
        return NotificacionService.contar_sin_leer(self.user)

    @database_sync_to_async
    def _mark_read(self, notification_id: str) -> None:
        from apps.notifications.services import NotificacionService
        try:
            NotificacionService.marcar_leida(notification_id, self.user)
        except Exception:
            logger.exception(
                'ws_mark_read_error',
                extra={
                    'user_id': str(self.user.id),
                    'notification_id': notification_id,
                },
            )
