"""
SaiSuite — Chat: WebSocket URL routing.
Maps ws/chat/ to the real-time chat consumer.
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
]
