"""
SaiSuite -- Contabilidad: Views
Las views SOLO orquestan: reciben request -> llaman service -> retornan response.
Auth: JWT con validacion de company_id.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.contabilidad.serializers import (
    GLBatchSerializer,
    ACCTBatchSerializer,
    SyncStatusSerializer,
    SyncResultSerializer,
)
from apps.contabilidad.services import SyncService

logger = logging.getLogger(__name__)


class GLBatchSyncView(APIView):
    """
    POST /api/v1/contabilidad/sync/gl-batch/

    Recibe un batch de registros GL desde el agente de sync.
    El agente envia los registros nuevos/modificados desde el ultimo conteo.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, 'effective_company', None) or request.user.company
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GLBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = SyncService.process_gl_batch(
            company_id=company.id,
            records=serializer.validated_data['records'],
        )

        out = SyncResultSerializer(result)
        return Response(out.data, status=status.HTTP_200_OK)


class ACCTSyncView(APIView):
    """
    POST /api/v1/contabilidad/sync/acct/

    Recibe el plan de cuentas completo (full sync).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = getattr(request.user, 'effective_company', None) or request.user.company
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ACCTBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = SyncService.process_acct_full(
            company_id=company.id,
            records=serializer.validated_data['records'],
        )

        out = SyncResultSerializer(result)
        return Response(out.data, status=status.HTTP_200_OK)


class SyncStatusView(APIView):
    """
    GET /api/v1/contabilidad/sync/status/

    Retorna el estado actual de la sincronizacion contable de la empresa.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'effective_company', None) or request.user.company
        if not company:
            return Response(
                {'error': 'Usuario sin empresa asignada'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = SyncService.get_sync_status(company_id=company.id)

        out = SyncStatusSerializer(result)
        return Response(out.data, status=status.HTTP_200_OK)
