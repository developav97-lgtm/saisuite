"""
SaiSuite — Chat: URLs
Montado en: /api/v1/chat/

Endpoints:
  GET    /api/v1/chat/conversaciones/                                — listar conversaciones
  POST   /api/v1/chat/conversaciones/                                — crear/obtener conversacion
  GET    /api/v1/chat/conversaciones/<uuid>/mensajes/                — listar mensajes (paginado)
  POST   /api/v1/chat/conversaciones/<uuid>/mensajes/enviar/         — enviar mensaje
  POST   /api/v1/chat/mensajes/<uuid>/marcar-leido/                  — marcar mensaje como leido
  GET    /api/v1/chat/autocomplete/entidades/?query=PRY              — autocomplete entidades
  GET    /api/v1/chat/autocomplete/usuarios/?query=Juan              — autocomplete usuarios
"""
from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path(
        'conversaciones/',
        views.conversaciones_view,
        name='conversaciones',
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
        'autocomplete/entidades/',
        views.autocomplete_entidades_view,
        name='autocomplete-entidades',
    ),
    path(
        'autocomplete/usuarios/',
        views.autocomplete_usuarios_view,
        name='autocomplete-usuarios',
    ),
]
