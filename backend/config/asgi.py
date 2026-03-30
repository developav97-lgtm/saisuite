"""
SaiSuite ASGI — HTTP + WebSocket routing.
Daphne / Channels entrypoint.

HTTP requests go to the standard Django ASGI app.
WebSocket connections are routed through JWTAuthMiddleware
for token-based authentication, then dispatched to the
notification and chat consumers.
"""
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Django ASGI app must be initialized before importing consumers/middleware
# so that the app registry is populated.
django_asgi_app = get_asgi_application()

from apps.notifications.middleware import JWTAuthMiddleware  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns as notification_ws  # noqa: E402
from apps.chat.routing import websocket_urlpatterns as chat_ws  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(
        URLRouter(notification_ws + chat_ws)
    ),
})
