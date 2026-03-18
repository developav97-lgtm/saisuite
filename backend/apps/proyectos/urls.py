"""
SaiSuite — Proyectos: URLs

Rutas Fase A:
  GET/POST       /api/v1/proyectos/
  GET/PATCH/DEL  /api/v1/proyectos/{id}/
  POST           /api/v1/proyectos/{id}/cambiar-estado/
  GET            /api/v1/proyectos/{id}/estado-financiero/
  GET/POST       /api/v1/proyectos/{id}/fases/
  GET/PATCH/DEL  /api/v1/fases/{id}/

Rutas Fase B:
  GET/POST       /api/v1/proyectos/{id}/terceros/
  DELETE         /api/v1/proyectos/{id}/terceros/{pk}/
  GET            /api/v1/proyectos/{id}/documentos/
  GET            /api/v1/proyectos/{id}/documentos/{pk}/
  GET/POST       /api/v1/proyectos/{id}/hitos/
  POST           /api/v1/proyectos/{id}/hitos/{pk}/generar-factura/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.proyectos.views import (
    ProyectoViewSet, FaseViewSet,
    TerceroProyectoViewSet, DocumentoContableViewSet, HitoViewSet,
)

router = DefaultRouter()
router.register(r'', ProyectoViewSet, basename='proyecto')

urlpatterns = [
    # ── Fases ──────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/fases/',
        FaseViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='proyecto-fases-list',
    ),
    path(
        'fases/<uuid:pk>/',
        FaseViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='fase-detail',
    ),

    # ── Terceros ───────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/terceros/',
        TerceroProyectoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='proyecto-terceros-list',
    ),
    path(
        '<uuid:proyecto_pk>/terceros/<uuid:pk>/',
        TerceroProyectoViewSet.as_view({'delete': 'destroy'}),
        name='proyecto-terceros-detail',
    ),

    # ── Documentos contables ───────────────────────────────────
    path(
        '<uuid:proyecto_pk>/documentos/',
        DocumentoContableViewSet.as_view({'get': 'list'}),
        name='proyecto-documentos-list',
    ),
    path(
        '<uuid:proyecto_pk>/documentos/<uuid:pk>/',
        DocumentoContableViewSet.as_view({'get': 'retrieve'}),
        name='proyecto-documentos-detail',
    ),

    # ── Hitos ──────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/hitos/',
        HitoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='proyecto-hitos-list',
    ),
    path(
        '<uuid:proyecto_pk>/hitos/<uuid:pk>/generar-factura/',
        HitoViewSet.as_view({'post': 'generar_factura'}),
        name='proyecto-hitos-generar-factura',
    ),

    # ── Router principal de proyectos ──────────────────────────
    path('', include(router.urls)),
]
