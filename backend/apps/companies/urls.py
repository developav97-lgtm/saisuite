from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CompanyViewSet,
    CompanyMeView,
    ModuleActivateView,
    ModuleDeactivateView,
    LicenseListCreateView,
    LicenseDetailView,
    LicenseMeView,
    LicensePaymentCreateView,
)

router = DefaultRouter()
router.register('', CompanyViewSet, basename='company')

urlpatterns = [
    path('me/', CompanyMeView.as_view(), name='company-me'),
    path('<uuid:pk>/modules/activate/',   ModuleActivateView.as_view(),   name='company-module-activate'),
    path('<uuid:pk>/modules/deactivate/', ModuleDeactivateView.as_view(), name='company-module-deactivate'),
    # Licencias
    path('licenses/',                       LicenseListCreateView.as_view(),  name='license-list-create'),
    path('licenses/me/',                    LicenseMeView.as_view(),           name='license-me'),
    path('licenses/<uuid:pk>/',             LicenseDetailView.as_view(),       name='license-detail'),
    path('licenses/<uuid:pk>/payments/',    LicensePaymentCreateView.as_view(), name='license-payment-create'),
    path('', include(router.urls)),
]
