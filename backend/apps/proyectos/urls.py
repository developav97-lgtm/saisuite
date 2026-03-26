"""
SaiSuite — Projects: URLs
REFT-09: URL prefixes migrated to English. Spanish prefix kept as deprecated alias.

Catalog of activities:
  GET/POST       /api/v1/projects/activities/
  GET/PATCH/DEL  /api/v1/projects/activities/{id}/

Phase A routes:
  GET/POST       /api/v1/projects/
  GET/PATCH/DEL  /api/v1/projects/{id}/
  POST           /api/v1/projects/{id}/change-status/
  GET            /api/v1/projects/{id}/financial-status/
  GET/POST       /api/v1/projects/{id}/phases/
  GET/PATCH/DEL  /api/v1/projects/phases/{id}/

Phase B routes:
  GET/POST       /api/v1/projects/{id}/stakeholders/
  DELETE         /api/v1/projects/{id}/stakeholders/{pk}/
  GET            /api/v1/projects/{id}/documents/
  GET            /api/v1/projects/{id}/documents/{pk}/
  GET/POST       /api/v1/projects/{id}/milestones/
  POST           /api/v1/projects/{id}/milestones/{pk}/generate-invoice/

Activity routes per project:
  GET/POST       /api/v1/projects/{id}/activities/
  PATCH/DELETE   /api/v1/projects/{id}/activities/{pk}/

Task routes:
  GET/POST       /api/v1/projects/tasks/
  GET/PATCH/DEL  /api/v1/projects/tasks/{id}/
  POST           /api/v1/projects/tasks/{id}/add-follower/
  DELETE         /api/v1/projects/tasks/{id}/remove-follower/{user_id}/
  POST           /api/v1/projects/tasks/{id}/change-status/
  GET/POST       /api/v1/projects/tags/
  GET/PATCH/DEL  /api/v1/projects/tags/{id}/

Deprecated aliases (REFT-09 — remove in REFT-21):
  All of the above are also served under /api/v1/proyectos/ for backwards compatibility.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter

# NOTE: ViewSet classes are still named with Spanish identifiers pending REFT-10.
# English aliases (ProjectViewSet, PhaseViewSet, …) will be importable once REFT-10
# renames the classes in views.py. Until then we import the existing names.
from apps.proyectos.views import (
    ProyectoViewSet,
    FaseViewSet,
    TerceroProyectoViewSet,
    DocumentoContableViewSet,
    HitoViewSet,
    ActividadViewSet,
    ActividadProyectoViewSet,
    ActividadSaiopenViewSet,
    ModuleSettingsView,
    TareaViewSet,
    TareaTagViewSet,
    TimesheetViewSet,
)

# ── Main project router ────────────────────────────────────────────────────────
project_router = DefaultRouter()
project_router.register(r'', ProyectoViewSet, basename='project')

# ── Activity catalog router ────────────────────────────────────────────────────
# SimpleRouter: avoids a root '' conflict with project_router
activity_router = SimpleRouter()
activity_router.register(r'activities', ActividadViewSet, basename='activity')
activity_router.register(r'activities-saiopen', ActividadSaiopenViewSet, basename='activity-saiopen')

# ── Task, tag and timesheet router ────────────────────────────────────────────
task_router = SimpleRouter()
task_router.register(r'tasks', TareaViewSet, basename='task')
task_router.register(r'tags', TareaTagViewSet, basename='task-tag')
task_router.register(r'timesheets', TimesheetViewSet, basename='timesheet')

urlpatterns = [
    # ── Activity catalog ──────────────────────────────────────────────────
    path('', include(activity_router.urls)),

    # ── Tasks and Tags ────────────────────────────────────────────────────
    path('', include(task_router.urls)),

    # ── Phases ────────────────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/phases/',
        FaseViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-phases-list',
    ),
    path(
        'phases/<uuid:pk>/',
        FaseViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='phase-detail',
    ),
    path(
        'phases/<uuid:pk>/activate/',
        FaseViewSet.as_view({'post': 'activar'}),
        name='phase-activate',
    ),
    path(
        'phases/<uuid:pk>/complete/',
        FaseViewSet.as_view({'post': 'completar'}),
        name='phase-complete',
    ),

    # ── Stakeholders ──────────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/stakeholders/',
        TerceroProyectoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-stakeholders-list',
    ),
    path(
        '<uuid:proyecto_pk>/stakeholders/<uuid:pk>/',
        TerceroProyectoViewSet.as_view({'delete': 'destroy'}),
        name='project-stakeholders-detail',
    ),

    # ── Accounting documents ──────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/documents/',
        DocumentoContableViewSet.as_view({'get': 'list'}),
        name='project-documents-list',
    ),
    path(
        '<uuid:proyecto_pk>/documents/<uuid:pk>/',
        DocumentoContableViewSet.as_view({'get': 'retrieve'}),
        name='project-documents-detail',
    ),

    # ── Milestones ────────────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/milestones/',
        HitoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-milestones-list',
    ),
    path(
        '<uuid:proyecto_pk>/milestones/<uuid:pk>/generate-invoice/',
        HitoViewSet.as_view({'post': 'generar_factura'}),
        name='project-milestones-generate-invoice',
    ),

    # ── Activities per project ────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/activities/',
        ActividadProyectoViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-activities-list',
    ),
    path(
        '<uuid:proyecto_pk>/activities/<uuid:pk>/',
        ActividadProyectoViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy'}),
        name='project-activities-detail',
    ),

    # ── Module configuration ──────────────────────────────────────────────
    path('config/', ModuleSettingsView.as_view(), name='projects-config'),

    # ── Main project router ───────────────────────────────────────────────
    path('', include(project_router.urls)),
]
