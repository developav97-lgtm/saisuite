"""
SaiSuite — Admin URLs: Catalogo de Paquetes
Rutas bajo /api/v1/admin/packages/
Solo accesibles por superadmins.
"""
from django.urls import path

from .views import AdminPackageListView, AdminPackageDetailView

urlpatterns = [
    path('',            AdminPackageListView.as_view(),   name='admin-package-list'),
    path('<uuid:pk>/',  AdminPackageDetailView.as_view(), name='admin-package-detail'),
]
