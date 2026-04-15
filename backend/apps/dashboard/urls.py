"""
SaiSuite -- Dashboard: URLs
Endpoints para dashboard CRUD, cards, shares, reports, catalog, filters, trial.
"""
from django.urls import path

from apps.dashboard.views import (
    # CFO Virtual
    CfoVirtualView,
    # Dashboard CRUD
    DashboardListCreateView,
    DashboardDetailView,
    DashboardSetDefaultView,
    DashboardToggleFavoriteView,
    DashboardSharedWithMeView,
    DashboardSaveFiltersView,
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
    FilterTiposDocView,
    FilterCentrosCostoView,
    FilterActividadesView,
    # Trial
    TrialActivateView,
    TrialStatusView,
    # CFO BI Suggest
    CfoSuggestReportView,
    # Report BI
    ReportBIListCreateView,
    ReportBIDetailView,
    ReportBIToggleFavoriteView,
    ReportBIExecuteView,
    ReportBIExportPdfView,
    ReportBIPreviewView,
    ReportBIShareView,
    ReportBIShareRevokeView,
    ReportBIStaticCatalogView,
    ReportBITemplatesView,
    BISourcesView,
    BIFieldsView,
    BIFiltersView,
    BIJoinsView,
    ReportBIDuplicateView,
    # Sprint 4: bi_report cards
    BiCardExecuteView,
    BiSelectableReportsView,
)

app_name = 'dashboard'

urlpatterns = [
    # ── Dashboard CRUD ──
    path('', DashboardListCreateView.as_view(), name='dashboard-list-create'),
    path('compartidos-conmigo/', DashboardSharedWithMeView.as_view(), name='shared-with-me'),
    path('<uuid:dashboard_id>/', DashboardDetailView.as_view(), name='dashboard-detail'),
    path('<uuid:dashboard_id>/set-default/', DashboardSetDefaultView.as_view(), name='set-default'),
    path('<uuid:dashboard_id>/toggle-favorite/', DashboardToggleFavoriteView.as_view(), name='toggle-favorite'),
    path('<uuid:dashboard_id>/filters/', DashboardSaveFiltersView.as_view(), name='save-filters'),

    # ── Cards ──
    path('<uuid:dashboard_id>/cards/', DashboardCardListCreateView.as_view(), name='card-list-create'),
    path('<uuid:dashboard_id>/cards/layout/', DashboardCardLayoutView.as_view(), name='card-layout'),
    path('<uuid:dashboard_id>/cards/<int:card_id>/', DashboardCardDetailView.as_view(), name='card-detail'),
    path('<uuid:dashboard_id>/cards/<int:card_id>/bi-execute/', BiCardExecuteView.as_view(), name='bi-card-execute'),

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
    path('filters/tipos-doc/', FilterTiposDocView.as_view(), name='filter-tipos-doc'),
    path('filters/centros-costo/', FilterCentrosCostoView.as_view(), name='filter-centros-costo'),
    path('filters/actividades/', FilterActividadesView.as_view(), name='filter-actividades'),

    # ── Trial ──
    path('trial/activate/', TrialActivateView.as_view(), name='trial-activate'),
    path('trial/status/', TrialStatusView.as_view(), name='trial-status'),

    # ── CFO Virtual ──
    path('cfo-virtual/', CfoVirtualView.as_view(), name='cfo-virtual'),
    path('cfo-virtual/suggest-report/', CfoSuggestReportView.as_view(), name='cfo-suggest-report'),

    # ── Report BI CRUD ──
    path('reportes/', ReportBIListCreateView.as_view(), name='report-bi-list-create'),
    path('reportes/preview/', ReportBIPreviewView.as_view(), name='report-bi-preview'),
    path('reportes/catalogo/', ReportBIStaticCatalogView.as_view(), name='report-bi-static-catalog'),
    path('reportes/templates/', ReportBITemplatesView.as_view(), name='report-bi-templates'),
    path('reportes/seleccionables/', BiSelectableReportsView.as_view(), name='bi-selectable-reports'),
    path('reportes/meta/sources/', BISourcesView.as_view(), name='bi-sources'),
    path('reportes/meta/fields/', BIFieldsView.as_view(), name='bi-fields'),
    path('reportes/meta/filters/', BIFiltersView.as_view(), name='bi-filters'),
    path('reportes/meta/joins/', BIJoinsView.as_view(), name='bi-joins'),
    path('reportes/<uuid:report_id>/', ReportBIDetailView.as_view(), name='report-bi-detail'),
    path('reportes/<uuid:report_id>/toggle-favorite/', ReportBIToggleFavoriteView.as_view(), name='report-bi-toggle-favorite'),
    path('reportes/<uuid:report_id>/execute/', ReportBIExecuteView.as_view(), name='report-bi-execute'),
    path('reportes/<uuid:report_id>/export-pdf/', ReportBIExportPdfView.as_view(), name='report-bi-export-pdf'),
    path('reportes/<uuid:report_id>/duplicate/', ReportBIDuplicateView.as_view(), name='report-bi-duplicate'),
    path('reportes/<uuid:report_id>/share/', ReportBIShareView.as_view(), name='report-bi-share'),
    path('reportes/<uuid:report_id>/share/<uuid:user_id>/', ReportBIShareRevokeView.as_view(), name='report-bi-share-revoke'),
]
