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
]
