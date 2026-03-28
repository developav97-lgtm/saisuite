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
    ProjectViewSet,
    PhaseViewSet,
    ProjectStakeholderViewSet,
    AccountingDocumentViewSet,
    MilestoneViewSet,
    ActivityViewSet,
    ProjectActivityViewSet,
    SaiopenActivityViewSet,
    ModuleSettingsView,
    TaskViewSet,
    TaskTagViewSet,
    TimesheetViewSet,
    ResourceAssignmentViewSet,
    ResourceCapacityViewSet,
    ResourceAvailabilityViewSet,
    WorkloadView,
    TeamAvailabilityView,
    UserCalendarView,
)
from apps.proyectos.analytics_views import (
    ProjectKPIsView,
    ProjectTaskDistributionView,
    ProjectVelocityView,
    ProjectBurnRateView,
    ProjectBurnDownView,
    ProjectResourceUtilizationView,
    ProjectTimelineView,
    CompareProjectsView,
    ExportExcelView,
)
from apps.proyectos.scheduling_views import (
    AutoScheduleView,
    ResourceLevelingView,
    CriticalPathView,
    TaskFloatView,
    TaskConstraintListView,
    TaskConstraintDeleteView,
    ProjectBaselineListView,
    BaselineDetailView,
    BaselineCompareView,
    WhatIfScenarioListView,
    WhatIfScenarioDetailView,
    RunSimulationView,
    CompareScenariosView,
)
from apps.proyectos.budget_views import (
    ProjectBudgetView,
    BudgetApproveView,
    BudgetVarianceView,
    BudgetAlertsView,
    BudgetSnapshotListView,
    CostTotalView,
    CostByResourceView,
    CostByTaskView,
    EVMMetricsView,
    InvoiceDataView,
    ProjectExpenseListView,
    ProjectExpenseDetailView,
    ExpenseApproveView,
    CostRateListView,
    CostRateDetailView,
)

# ── Main project router ────────────────────────────────────────────────────────
project_router = DefaultRouter()
project_router.register(r'', ProjectViewSet, basename='project')

# ── Activity catalog router ────────────────────────────────────────────────────
# SimpleRouter: avoids a root '' conflict with project_router
activity_router = SimpleRouter()
activity_router.register(r'activities', ActivityViewSet, basename='activity')
activity_router.register(r'activities-saiopen', SaiopenActivityViewSet, basename='activity-saiopen')

# ── Task, tag and timesheet router ────────────────────────────────────────────
task_router = SimpleRouter()
task_router.register(r'tasks', TaskViewSet, basename='task')
task_router.register(r'tags', TaskTagViewSet, basename='task-tag')
task_router.register(r'timesheets', TimesheetViewSet, basename='timesheet')

urlpatterns = [
    # ── Activity catalog ──────────────────────────────────────────────────
    path('', include(activity_router.urls)),

    # ── Tasks and Tags ────────────────────────────────────────────────────
    path('', include(task_router.urls)),

    # ── Phases ────────────────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/phases/',
        PhaseViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-phases-list',
    ),
    path(
        'phases/<uuid:pk>/',
        PhaseViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='phase-detail',
    ),
    path(
        'phases/<uuid:pk>/activate/',
        PhaseViewSet.as_view({'post': 'activar'}),
        name='phase-activate',
    ),
    path(
        'phases/<uuid:pk>/complete/',
        PhaseViewSet.as_view({'post': 'completar'}),
        name='phase-complete',
    ),

    # ── Stakeholders ──────────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/stakeholders/',
        ProjectStakeholderViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-stakeholders-list',
    ),
    path(
        '<uuid:proyecto_pk>/stakeholders/<uuid:pk>/',
        ProjectStakeholderViewSet.as_view({'delete': 'destroy'}),
        name='project-stakeholders-detail',
    ),

    # ── Accounting documents ──────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/documents/',
        AccountingDocumentViewSet.as_view({'get': 'list'}),
        name='project-documents-list',
    ),
    path(
        '<uuid:proyecto_pk>/documents/<uuid:pk>/',
        AccountingDocumentViewSet.as_view({'get': 'retrieve'}),
        name='project-documents-detail',
    ),

    # ── Milestones ────────────────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/milestones/',
        MilestoneViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-milestones-list',
    ),
    path(
        '<uuid:proyecto_pk>/milestones/<uuid:pk>/generate-invoice/',
        MilestoneViewSet.as_view({'post': 'generar_factura'}),
        name='project-milestones-generate-invoice',
    ),

    # ── Activities per project ────────────────────────────────────────────
    path(
        '<uuid:proyecto_pk>/activities/',
        ProjectActivityViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='project-activities-list',
    ),
    path(
        '<uuid:proyecto_pk>/activities/<uuid:pk>/',
        ProjectActivityViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy'}),
        name='project-activities-detail',
    ),

    # ── Module configuration ──────────────────────────────────────────────
    path('config/', ModuleSettingsView.as_view(), name='projects-config'),

    # ── Resource Management — Feature #4 ─────────────────────────────────
    # Assignments (nested under task)
    path(
        'tasks/<uuid:task_pk>/assignments/',
        ResourceAssignmentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='task-assignments-list',
    ),
    path(
        'tasks/<uuid:task_pk>/assignments/<uuid:pk>/',
        ResourceAssignmentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
        name='task-assignments-detail',
    ),
    path(
        'tasks/<uuid:task_pk>/assignments/check-overallocation/',
        ResourceAssignmentViewSet.as_view({'get': 'check_overallocation'}),
        name='task-assignments-check-overallocation',
    ),

    # Capacity
    path(
        'resources/capacity/',
        ResourceCapacityViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='resource-capacity-list',
    ),
    path(
        'resources/capacity/<uuid:pk>/',
        ResourceCapacityViewSet.as_view({
            'get': 'retrieve',
            'patch': 'partial_update',
            'delete': 'destroy',
        }),
        name='resource-capacity-detail',
    ),

    # Availability (ausencias)
    path(
        'resources/availability/',
        ResourceAvailabilityViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='resource-availability-list',
    ),
    path(
        'resources/availability/<uuid:pk>/',
        ResourceAvailabilityViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
        name='resource-availability-detail',
    ),
    path(
        'resources/availability/<uuid:pk>/approve/',
        ResourceAvailabilityViewSet.as_view({'post': 'approve'}),
        name='resource-availability-approve',
    ),

    # Workload summary
    path(
        'resources/workload/',
        WorkloadView.as_view(),
        name='resource-workload',
    ),

    # User calendar
    path(
        'resources/calendar/',
        UserCalendarView.as_view(),
        name='resource-calendar',
    ),

    # Team availability timeline (nested under project)
    path(
        '<uuid:proyecto_pk>/team-availability/',
        TeamAvailabilityView.as_view(),
        name='project-team-availability',
    ),

    # ── Analytics — Feature #5 ────────────────────────────────────────────
    # Project-scoped analytics
    path(
        '<uuid:project_pk>/analytics/kpis/',
        ProjectKPIsView.as_view(),
        name='project-analytics-kpis',
    ),
    path(
        '<uuid:project_pk>/analytics/task-distribution/',
        ProjectTaskDistributionView.as_view(),
        name='project-analytics-task-distribution',
    ),
    path(
        '<uuid:project_pk>/analytics/velocity/',
        ProjectVelocityView.as_view(),
        name='project-analytics-velocity',
    ),
    path(
        '<uuid:project_pk>/analytics/burn-rate/',
        ProjectBurnRateView.as_view(),
        name='project-analytics-burn-rate',
    ),
    path(
        '<uuid:project_pk>/analytics/burn-down/',
        ProjectBurnDownView.as_view(),
        name='project-analytics-burn-down',
    ),
    path(
        '<uuid:project_pk>/analytics/resource-utilization/',
        ProjectResourceUtilizationView.as_view(),
        name='project-analytics-resource-utilization',
    ),
    path(
        '<uuid:project_pk>/analytics/timeline/',
        ProjectTimelineView.as_view(),
        name='project-analytics-timeline',
    ),

    # Cross-project analytics (no project_pk)
    path(
        'analytics/compare/',
        CompareProjectsView.as_view(),
        name='analytics-compare-projects',
    ),
    path(
        'analytics/export-excel/',
        ExportExcelView.as_view(),
        name='analytics-export-excel',
    ),

    # ── Scheduling — Feature #6 ───────────────────────────────────────────

    # Auto-scheduling (project-scoped)
    path(
        '<uuid:project_pk>/scheduling/auto-schedule/',
        AutoScheduleView.as_view(),
        name='project-scheduling-auto-schedule',
    ),
    path(
        '<uuid:project_pk>/scheduling/level-resources/',
        ResourceLevelingView.as_view(),
        name='project-scheduling-level-resources',
    ),
    path(
        '<uuid:project_pk>/scheduling/critical-path/',
        CriticalPathView.as_view(),
        name='project-scheduling-critical-path',
    ),

    # Task float (task-scoped)
    path(
        'tasks/<uuid:task_pk>/scheduling/float/',
        TaskFloatView.as_view(),
        name='task-scheduling-float',
    ),

    # Task constraints
    path(
        'tasks/<uuid:task_pk>/constraints/',
        TaskConstraintListView.as_view(),
        name='task-constraints-list',
    ),
    path(
        'constraints/<uuid:pk>/',
        TaskConstraintDeleteView.as_view(),
        name='task-constraint-detail',
    ),

    # Baselines
    path(
        '<uuid:project_pk>/baselines/',
        ProjectBaselineListView.as_view(),
        name='project-baselines-list',
    ),
    path(
        'baselines/<uuid:pk>/',
        BaselineDetailView.as_view(),
        name='baseline-detail',
    ),
    path(
        'baselines/<uuid:pk>/compare/',
        BaselineCompareView.as_view(),
        name='baseline-compare',
    ),

    # What-If Scenarios
    path(
        '<uuid:project_pk>/scenarios/',
        WhatIfScenarioListView.as_view(),
        name='project-scenarios-list',
    ),
    path(
        'scenarios/<uuid:pk>/',
        WhatIfScenarioDetailView.as_view(),
        name='scenario-detail',
    ),
    path(
        'scenarios/<uuid:pk>/run-simulation/',
        RunSimulationView.as_view(),
        name='scenario-run-simulation',
    ),
    path(
        'scenarios/compare/',
        CompareScenariosView.as_view(),
        name='scenarios-compare',
    ),

    # ── Budget & Cost Tracking — Feature #7 ──────────────────────────────

    # Budget CRUD + approve
    path(
        '<uuid:project_pk>/budget/',
        ProjectBudgetView.as_view(),
        name='project-budget',
    ),
    path(
        '<uuid:project_pk>/budget/approve/',
        BudgetApproveView.as_view(),
        name='project-budget-approve',
    ),
    path(
        '<uuid:project_pk>/budget/variance/',
        BudgetVarianceView.as_view(),
        name='project-budget-variance',
    ),
    path(
        '<uuid:project_pk>/budget/alerts/',
        BudgetAlertsView.as_view(),
        name='project-budget-alerts',
    ),
    path(
        '<uuid:project_pk>/budget/snapshots/',
        BudgetSnapshotListView.as_view(),
        name='project-budget-snapshots',
    ),

    # Cost summaries
    path(
        '<uuid:project_pk>/costs/total/',
        CostTotalView.as_view(),
        name='project-costs-total',
    ),
    path(
        '<uuid:project_pk>/costs/by-resource/',
        CostByResourceView.as_view(),
        name='project-costs-by-resource',
    ),
    path(
        '<uuid:project_pk>/costs/by-task/',
        CostByTaskView.as_view(),
        name='project-costs-by-task',
    ),
    path(
        '<uuid:project_pk>/costs/evm/',
        EVMMetricsView.as_view(),
        name='project-costs-evm',
    ),
    path(
        '<uuid:project_pk>/invoice-data/',
        InvoiceDataView.as_view(),
        name='project-invoice-data',
    ),

    # Expenses (nested under project for creation/list; flat for detail)
    path(
        '<uuid:project_pk>/expenses/',
        ProjectExpenseListView.as_view(),
        name='project-expenses-list',
    ),
    path(
        'expenses/<uuid:pk>/',
        ProjectExpenseDetailView.as_view(),
        name='expense-detail',
    ),
    path(
        'expenses/<uuid:pk>/approve/',
        ExpenseApproveView.as_view(),
        name='expense-approve',
    ),

    # Cost rates (company-wide resource rates)
    path(
        'resources/cost-rates/',
        CostRateListView.as_view(),
        name='resource-cost-rates-list',
    ),
    path(
        'resources/cost-rates/<uuid:pk>/',
        CostRateDetailView.as_view(),
        name='resource-cost-rate-detail',
    ),

    # ── Main project router ───────────────────────────────────────────────
    path('', include(project_router.urls)),
]
