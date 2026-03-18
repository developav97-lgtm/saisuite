"""
SaiSuite — Proyectos: URLs

Rutas principales:
  GET/POST       /api/v1/proyectos/
  GET/PATCH/DEL  /api/v1/proyectos/{id}/
  POST           /api/v1/proyectos/{id}/cambiar-estado/
  GET            /api/v1/proyectos/{id}/estado-financiero/
  GET/POST       /api/v1/proyectos/{id}/fases/
  GET/PATCH/DEL  /api/v1/fases/{id}/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.proyectos.views import ProyectoViewSet, FaseViewSet

router = DefaultRouter()
router.register(r'', ProyectoViewSet, basename='proyecto')

# Rutas standalone de fases (update/delete sin proyecto_pk)
fase_router = DefaultRouter()
fase_router.register(r'fases', FaseViewSet, basename='fase')

urlpatterns = [
    # /api/v1/proyectos/{id}/fases/ — listado y creación de fases
    path(
        '<uuid:proyecto_pk>/fases/',
        FaseViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='proyecto-fases-list',
    ),
    # /api/v1/fases/{id}/ — detalle, actualización y eliminación
    path(
        'fases/<uuid:pk>/',
        FaseViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='fase-detail',
    ),
    # Router principal de proyectos (incluye acciones custom)
    path('', include(router.urls)),
]
