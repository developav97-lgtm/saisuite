"""
SaiSuite — Admin URLs: Gestión de Tenants
Rutas bajo /api/v1/admin/tenants/
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
]
