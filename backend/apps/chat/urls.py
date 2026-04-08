"""
SaiSuite — Chat: URLs
Montado en: /api/v1/chat/

Endpoints:
  GET    /api/v1/chat/conversaciones/                                — listar conversaciones
  POST   /api/v1/chat/conversaciones/                                — crear/obtener conversacion
  GET    /api/v1/chat/conversaciones/<uuid>/mensajes/                — listar mensajes (paginado)
  POST   /api/v1/chat/conversaciones/<uuid>/mensajes/enviar/         — enviar mensaje
  GET    /api/v1/chat/conversaciones/<uuid>/buscar/?q=texto          — buscar mensajes
  POST   /api/v1/chat/mensajes/<uuid>/marcar-leido/                  — marcar mensaje como leido
  PATCH  /api/v1/chat/mensajes/<uuid>/editar/                        — editar mensaje propio (<15 min)
  GET    /api/v1/chat/presencia/                                      — estado online/offline de peers
  POST   /api/v1/chat/upload-archivo/                                — subir archivo a R2
  POST   /api/v1/chat/upload-imagen/                                — subir imagen a R2 (con thumbnail)
  GET    /api/v1/chat/autocomplete/entidades/?query=PRY              — autocomplete entidades
  GET    /api/v1/chat/autocomplete/usuarios/?query=Juan              — autocomplete usuarios
"""
from django.urls import path

from . import views
from .views import BotConversacionView

app_name = 'chat'

urlpatterns = [
    path(
        'conversaciones/',
        views.conversaciones_view,
        name='conversaciones',
    ),
    path(
        'conversaciones/bot/',
        BotConversacionView.as_view(),
        name='chat-bot-conversation',
    ),
    path(
        'conversaciones/<uuid:conversacion_id>/mensajes/',
        views.mensajes_view,
        name='mensajes',
    ),
    path(
        'conversaciones/<uuid:conversacion_id>/mensajes/enviar/',
        views.enviar_mensaje_view,
        name='enviar-mensaje',
    ),
    path(
        'mensajes/<uuid:mensaje_id>/marcar-leido/',
        views.marcar_leido_view,
        name='marcar-leido',
    ),
    path(
        'mensajes/<uuid:mensaje_id>/editar/',
        views.editar_mensaje_view,
        name='editar-mensaje',
    ),
    path(
        'presencia/',
        views.presencia_view,
        name='presencia',
    ),
    path(
        'upload-archivo/',
        views.upload_archivo_view,
        name='upload-archivo',
    ),
    path(
        'upload-imagen/',
        views.upload_imagen_view,
        name='upload-imagen',
    ),
    path(
        'conversaciones/<uuid:conversacion_id>/buscar/',
        views.buscar_mensajes_view,
        name='buscar-mensajes',
    ),
    path(
        'autocomplete/entidades/',
        views.autocomplete_entidades_view,
        name='autocomplete-entidades',
    ),
    path(
        'autocomplete/usuarios/',
        views.autocomplete_usuarios_view,
        name='autocomplete-usuarios',
    ),
    path(
        'conversaciones/bot/limpiar/',
        views.limpiar_chat_bot_view,
        name='limpiar-chat-bot',
    ),
]
