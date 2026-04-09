from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CompanyViewSet,
    CompanyMeView,
    CompanyMeLogoView,
    ModuleActivateView,
    ModuleDeactivateView,
    LicenseListCreateView,
    LicenseDetailView,
    LicenseMeView,
    LicensePaymentCreateView,
    # Panel Superadmin
    AdminTenantListView,
    AdminTenantDetailView,
    AdminTenantLicenseView,
    AdminLicenseHistoryView,
    AdminLicensePaymentView,
    AdminTenantActivateView,
    AdminLicenseRenewalView,
    AdminRenewalConfirmView,
    AdminRenewalCancelView,
    # Paquetes
    AdminPackageListView,
    AdminPackageDetailView,
    AdminLicensePackagesView,
    AdminLicensePackageRemoveView,
    AdminLicenseSnapshotsView,
    # Uso IA
    AIUsageMeView,
    AIUsageByUserView,
    AdminAIUsageView,
    # Tokens del agente (company_admin)
    MyAgentTokensView,
    # Trials de módulo
    ModuleTrialStatusView,
    ModuleTrialActivateView,
    AdminModuleTrialActivateView,
    AdminModuleTrialStatusView,
    # Calculadora de precio
    AdminLicensePriceCalculatorView,
    # Solicitudes de licencia
    LicenseRequestListCreateView,
    AdminLicenseRequestListView,
    AdminLicenseRequestApproveView,
    AdminLicenseRequestRejectView,
)

router = DefaultRouter()
router.register('', CompanyViewSet, basename='company')

urlpatterns = [
    path('me/', CompanyMeView.as_view(), name='company-me'),
    path('me/logo/', CompanyMeLogoView.as_view(), name='company-me-logo'),
    path('<uuid:pk>/modules/activate/',   ModuleActivateView.as_view(),   name='company-module-activate'),
    path('<uuid:pk>/modules/deactivate/', ModuleDeactivateView.as_view(), name='company-module-deactivate'),
    # Licencias (rutas legacy — mantenidas por compatibilidad)
    path('licenses/',                       LicenseListCreateView.as_view(),   name='license-list-create'),
    path('licenses/me/',                    LicenseMeView.as_view(),           name='license-me'),
    path('licenses/me/ai-usage/',           AIUsageMeView.as_view(),           name='ai-usage-me'),
    path('licenses/me/ai-usage/by-user/',   AIUsageByUserView.as_view(),       name='ai-usage-by-user'),
    path('agent-tokens/me/',               MyAgentTokensView.as_view(),       name='agent-tokens-me'),
    # Trials de módulo (genérico — para company_admin)
    path('modules/<str:module_code>/trial/status/',   ModuleTrialStatusView.as_view(),   name='module-trial-status'),
    path('modules/<str:module_code>/trial/activate/', ModuleTrialActivateView.as_view(), name='module-trial-activate'),
    # Solicitudes de licencia (company_admin)
    path('license-requests/', LicenseRequestListCreateView.as_view(), name='license-requests'),
    path('licenses/<uuid:pk>/',             LicenseDetailView.as_view(),       name='license-detail'),
    path('licenses/<uuid:pk>/payments/',    LicensePaymentCreateView.as_view(), name='license-payment-create'),
    path('', include(router.urls)),
]

# Panel Superadmin — Tenants (bajo /api/v1/admin/tenants/)
admin_tenant_urlpatterns = [
    path('',                                   AdminTenantListView.as_view(),    name='admin-tenant-list'),
    path('<uuid:pk>/',                         AdminTenantDetailView.as_view(),  name='admin-tenant-detail'),
    path('<uuid:pk>/activate/',                AdminTenantActivateView.as_view(), name='admin-tenant-activate'),
    path('<uuid:pk>/license/',                 AdminTenantLicenseView.as_view(), name='admin-tenant-license'),
    path('<uuid:pk>/license/history/',         AdminLicenseHistoryView.as_view(), name='admin-license-history'),
    path('<uuid:pk>/license/payments/',        AdminLicensePaymentView.as_view(), name='admin-license-payments'),
    path('<uuid:pk>/license/renewal/',         AdminLicenseRenewalView.as_view(), name='admin-license-renewal'),
    path('<uuid:pk>/license/renewal/confirm/', AdminRenewalConfirmView.as_view(), name='admin-renewal-confirm'),
    path('<uuid:pk>/license/renewal/cancel/',  AdminRenewalCancelView.as_view(), name='admin-renewal-cancel'),
    path('<uuid:pk>/license/packages/',        AdminLicensePackagesView.as_view(), name='admin-license-packages'),
    path('<uuid:pk>/license/packages/<uuid:item_pk>/', AdminLicensePackageRemoveView.as_view(), name='admin-license-package-remove'),
    path('<uuid:pk>/license/snapshots/',       AdminLicenseSnapshotsView.as_view(), name='admin-license-snapshots'),
    path('<uuid:pk>/license/ai-usage/',        AdminAIUsageView.as_view(), name='admin-ai-usage'),
    # Trials de módulo (superadmin)
    path('<uuid:pk>/modules/<str:module_code>/trial/status/',   AdminModuleTrialStatusView.as_view(),   name='admin-module-trial-status'),
    path('<uuid:pk>/modules/<str:module_code>/trial/activate/', AdminModuleTrialActivateView.as_view(), name='admin-module-trial-activate'),
]

# Paquetes globales (bajo /api/v1/admin/packages/)
admin_package_urlpatterns = [
    path('',            AdminPackageListView.as_view(),   name='admin-package-list'),
    path('<uuid:pk>/',  AdminPackageDetailView.as_view(), name='admin-package-detail'),
]

# Calculadora de licencia (bajo /api/v1/admin/license/)
admin_license_urlpatterns = [
    path('calculate-total/', AdminLicensePriceCalculatorView.as_view(), name='admin-license-calculate-total'),
]
