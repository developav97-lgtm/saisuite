"""
SaiSuite — Admin URLs: Gestión de Tenants y Paquetes
Rutas bajo /api/v1/admin/tenants/ y /api/v1/admin/packages/
Solo accesibles por superadmins.
"""
from django.urls import path

from .views import (
    AdminTenantListView,
    AdminTenantDetailView,
    AdminTenantLicenseView,
    AdminLicenseHistoryView,
    AdminLicensePaymentView,
    AdminTenantActivateView,
    AdminLicenseRenewalView,
    AdminRenewalConfirmView,
    AdminRenewalCancelView,
    AdminPackageListView,
    AdminPackageDetailView,
    AdminLicensePackagesView,
    AdminLicensePackageRemoveView,
    AdminLicenseSnapshotsView,
    AdminAIUsageView,
    AdminAgentTokenListView,
    AdminAgentTokenRevokeView,
)

urlpatterns = [
    path('',                                    AdminTenantListView.as_view(),     name='admin-tenant-list'),
    path('<uuid:pk>/',                          AdminTenantDetailView.as_view(),   name='admin-tenant-detail'),
    path('<uuid:pk>/activate/',                 AdminTenantActivateView.as_view(), name='admin-tenant-activate'),
    path('<uuid:pk>/license/',                  AdminTenantLicenseView.as_view(),  name='admin-tenant-license'),
    path('<uuid:pk>/license/history/',          AdminLicenseHistoryView.as_view(), name='admin-license-history'),
    path('<uuid:pk>/license/payments/',         AdminLicensePaymentView.as_view(), name='admin-license-payments'),
    path('<uuid:pk>/license/renewal/',          AdminLicenseRenewalView.as_view(), name='admin-license-renewal'),
    path('<uuid:pk>/license/renewal/confirm/',  AdminRenewalConfirmView.as_view(), name='admin-renewal-confirm'),
    path('<uuid:pk>/license/renewal/cancel/',   AdminRenewalCancelView.as_view(),  name='admin-renewal-cancel'),
    path('<uuid:pk>/license/packages/',                    AdminLicensePackagesView.as_view(),       name='admin-license-packages'),
    path('<uuid:pk>/license/packages/<uuid:item_pk>/',     AdminLicensePackageRemoveView.as_view(),  name='admin-license-package-remove'),
    path('<uuid:pk>/license/snapshots/',                   AdminLicenseSnapshotsView.as_view(),      name='admin-license-snapshots'),
    path('<uuid:pk>/license/ai-usage/',                    AdminAIUsageView.as_view(),               name='admin-ai-usage'),
    path('<uuid:pk>/agent-tokens/',                        AdminAgentTokenListView.as_view(),         name='admin-agent-tokens'),
    path('<uuid:pk>/agent-tokens/<uuid:token_pk>/revoke/', AdminAgentTokenRevokeView.as_view(),       name='admin-agent-token-revoke'),
]
