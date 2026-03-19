"""SaiSuite — Core URLs"""
from rest_framework.routers import SimpleRouter
from apps.core.views import ConfiguracionConsecutivoViewSet

router = SimpleRouter()
router.register('consecutivos', ConfiguracionConsecutivoViewSet, basename='consecutivos')

urlpatterns = router.urls
