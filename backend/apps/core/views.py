"""
SaiSuite — Core Views
Las views SOLO orquestan: request → service → response.
"""
import logging
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.core.models import ConfiguracionConsecutivo
from apps.core.serializers import (
    ConfiguracionConsecutivoSerializer,
    ConfiguracionConsecutivoCreateUpdateSerializer,
)

logger = logging.getLogger(__name__)


class ConsecutivoPagination(PageNumberPagination):
    page_size             = 25
    page_size_query_param = 'page_size'
    max_page_size         = 100


class ConfiguracionConsecutivoViewSet(viewsets.ModelViewSet):
    """
    CRUD de configuraciones de consecutivos por empresa.
    GET/POST   /api/v1/core/consecutivos/
    GET/PATCH/DELETE /api/v1/core/consecutivos/{id}/

    Query params (list):
      search    — búsqueda en nombre y prefijo
      tipo      — filtro exacto (proyecto | actividad | factura)
      activo    — true | false
      page      — número de página (default 1)
      page_size — items por página (default 25, max 100)
    """
    permission_classes = [IsAuthenticated]
    pagination_class   = ConsecutivoPagination
    filter_backends    = [SearchFilter, OrderingFilter]
    search_fields      = ['nombre', 'prefijo']
    ordering_fields    = ['tipo', 'nombre', 'prefijo']
    ordering           = ['tipo', 'nombre']

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = ConfiguracionConsecutivo.all_objects.all()
        if company is not None:
            qs = qs.filter(company=company)

        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)

        activo = self.request.query_params.get('activo')
        if activo is not None and activo != '':
            qs = qs.filter(activo=activo.lower() == 'true')

        return qs

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ConfiguracionConsecutivoCreateUpdateSerializer
        return ConfiguracionConsecutivoSerializer

    def perform_create(self, serializer):
        company = self.request.user.company
        serializer.save(company=company)
