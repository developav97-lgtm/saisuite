"""
SaiSuite — Core Views
Las views SOLO orquestan: request → service → response.
"""
import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.models import ConfiguracionConsecutivo
from apps.core.serializers import (
    ConfiguracionConsecutivoSerializer,
    ConfiguracionConsecutivoCreateUpdateSerializer,
)

logger = logging.getLogger(__name__)


class ConfiguracionConsecutivoViewSet(viewsets.ModelViewSet):
    """
    CRUD de configuraciones de consecutivos por empresa.
    GET/POST   /api/v1/core/consecutivos/
    GET/PATCH/DELETE /api/v1/core/consecutivos/{id}/
    """
    permission_classes = [IsAuthenticated]
    pagination_class   = None  # Lista corta — sin paginación

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = ConfiguracionConsecutivo.all_objects.all()
        if company is not None:
            qs = qs.filter(company=company)
        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ConfiguracionConsecutivoCreateUpdateSerializer
        return ConfiguracionConsecutivoSerializer

    def perform_create(self, serializer):
        company = self.request.user.company
        serializer.save(company=company)
