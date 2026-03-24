"""
SaiSuite — Notifications: URLs
Montado en: /api/v1/notificaciones/

Endpoints:
  GET    /api/v1/notificaciones/                        — lista notificaciones del usuario
  GET    /api/v1/notificaciones/?leida=false            — solo sin leer
  GET    /api/v1/notificaciones/<id>/                   — detalle
  POST   /api/v1/notificaciones/<id>/leer/              — marcar leída
  POST   /api/v1/notificaciones/leer-todas/             — marcar todas leídas
  GET    /api/v1/notificaciones/no-leidas/              — conteo sin leer

  GET    /api/v1/notificaciones/comentarios/            — lista (filtrar con ?content_type_model=tarea&object_id=<uuid>)
  POST   /api/v1/notificaciones/comentarios/            — crear comentario
  PATCH  /api/v1/notificaciones/comentarios/<id>/       — editar comentario (solo autor)
  DELETE /api/v1/notificaciones/comentarios/<id>/       — eliminar comentario

  GET    /api/v1/notificaciones/preferencias/           — lista preferencias
  PATCH  /api/v1/notificaciones/preferencias/<tipo>/    — actualizar preferencia
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificacionViewSet, ComentarioViewSet, PreferenciaNotificacionViewSet

router = DefaultRouter()
# Los prefijos específicos DEBEN ir antes del prefijo vacío r'',
# porque DefaultRouter genera el patrón ^(?P<pk>[^/.]+)/$ para r''
# que capturaría /comentarios/ y /preferencias/ si va primero.
router.register(r'comentarios',  ComentarioViewSet,               basename='comentario')
router.register(r'preferencias', PreferenciaNotificacionViewSet,  basename='preferencia-notificacion')
router.register(r'',             NotificacionViewSet,             basename='notificacion')

urlpatterns = [
    path('', include(router.urls)),
]
