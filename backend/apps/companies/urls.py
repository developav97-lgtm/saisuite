from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CompanyViewSet, CompanyMeView, ModuleActivateView, ModuleDeactivateView

router = DefaultRouter()
router.register('', CompanyViewSet, basename='company')

urlpatterns = [
    path('me/', CompanyMeView.as_view(), name='company-me'),
    path('<uuid:pk>/modules/activate/', ModuleActivateView.as_view(), name='company-module-activate'),
    path('<uuid:pk>/modules/deactivate/', ModuleDeactivateView.as_view(), name='company-module-deactivate'),
    path('', include(router.urls)),
]
