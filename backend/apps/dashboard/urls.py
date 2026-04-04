"""
SaiSuite -- Dashboard: URLs
Endpoints para dashboard CRUD, cards, shares, reports, catalog, filters, trial.
"""
from django.urls import path

from apps.dashboard.views import (
    # Dashboard CRUD
    DashboardListCreateView,
    DashboardDetailView,
    DashboardSetDefaultView,
    DashboardToggleFavoriteView,
    DashboardSharedWithMeView,
    # Cards
    DashboardCardListCreateView,
    DashboardCardDetailView,
    DashboardCardLayoutView,
    # Share
    DashboardShareView,
    DashboardShareRevokeView,
    # Reports
    CardDataView,
    # Catalog
    CatalogCardsView,
    CatalogCategoriesView,
    # Filters
    FilterTercerosView,
    FilterProyectosView,
    FilterDepartamentosView,
    FilterPeriodosView,
    # Trial
    TrialActivateView,
    TrialStatusView,
)

app_name = 'dashboard'

urlpatterns = [
    # ── Dashboard CRUD ──
    path('', DashboardListCreateView.as_view(), name='dashboard-list-create'),
    path('compartidos-conmigo/', DashboardSharedWithMeView.as_view(), name='shared-with-me'),
    path('<uuid:dashboard_id>/', DashboardDetailView.as_view(), name='dashboard-detail'),
    path('<uuid:dashboard_id>/set-default/', DashboardSetDefaultView.as_view(), name='set-default'),
    path('<uuid:dashboard_id>/toggle-favorite/', DashboardToggleFavoriteView.as_view(), name='toggle-favorite'),

    # ── Cards ──
    path('<uuid:dashboard_id>/cards/', DashboardCardListCreateView.as_view(), name='card-list-create'),
    path('<uuid:dashboard_id>/cards/layout/', DashboardCardLayoutView.as_view(), name='card-layout'),
    path('<uuid:dashboard_id>/cards/<int:card_id>/', DashboardCardDetailView.as_view(), name='card-detail'),

    # ── Share ──
    path('<uuid:dashboard_id>/share/', DashboardShareView.as_view(), name='share'),
    path('<uuid:dashboard_id>/share/<uuid:user_id>/', DashboardShareRevokeView.as_view(), name='share-revoke'),

    # ── Reports ──
    path('report/card-data/', CardDataView.as_view(), name='card-data'),

    # ── Catalog ──
    path('catalog/cards/', CatalogCardsView.as_view(), name='catalog-cards'),
    path('catalog/categories/', CatalogCategoriesView.as_view(), name='catalog-categories'),

    # ── Filters ──
    path('filters/terceros/', FilterTercerosView.as_view(), name='filter-terceros'),
    path('filters/proyectos/', FilterProyectosView.as_view(), name='filter-proyectos'),
    path('filters/departamentos/', FilterDepartamentosView.as_view(), name='filter-departamentos'),
    path('filters/periodos/', FilterPeriodosView.as_view(), name='filter-periodos'),

    # ── Trial ──
    path('trial/activate/', TrialActivateView.as_view(), name='trial-activate'),
    path('trial/status/', TrialStatusView.as_view(), name='trial-status'),
]
