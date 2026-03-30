"""
SaiSuite — Notifications: WebSocket URL routing.
Maps ws/notifications/ to the real-time notification consumer.
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]
