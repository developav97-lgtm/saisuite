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
    MovimientoContableSerializer,
)
from apps.contabilidad.services import SyncService
from apps.contabilidad.models import MovimientoContable

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


class GLMovimientoListView(APIView):
    """
    GET /api/v1/contabilidad/movimientos/

    Lista movimientos contables de la empresa del usuario autenticado.
    Filtros opcionales via query params:
      - periodo (YYYY-MM)
      - titulo_codigo (int: 1=Activo, 2=Pasivo, 3=Patrimonio, 4=Ingresos, 5=Gastos, 6=Costos)
      - tercero_id (string)
      - tipo (string)
      - fecha_inicio / fecha_fin (YYYY-MM-DD)
      - search (busca en auxiliar_nombre, tercero_nombre, descripcion)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = getattr(request.user, 'effective_company', None) or request.user.company
        if not company:
            return Response({'error': 'Usuario sin empresa'}, status=status.HTTP_400_BAD_REQUEST)

        qs = MovimientoContable.objects.filter(company=company)

        periodo = request.query_params.get('periodo')
        if periodo:
            qs = qs.filter(periodo=periodo)

        titulo_codigo = request.query_params.get('titulo_codigo')
        if titulo_codigo:
            qs = qs.filter(titulo_codigo=titulo_codigo)

        tercero_id = request.query_params.get('tercero_id')
        if tercero_id:
            qs = qs.filter(tercero_id=tercero_id)

        tipo = request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)

        fecha_inicio = request.query_params.get('fecha_inicio')
        if fecha_inicio:
            qs = qs.filter(fecha__gte=fecha_inicio)

        fecha_fin = request.query_params.get('fecha_fin')
        if fecha_fin:
            qs = qs.filter(fecha__lte=fecha_fin)

        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(auxiliar_nombre__icontains=search) |
                Q(tercero_nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )

        # Limit for performance; full export handled separately if needed
        qs = qs.order_by('-fecha', '-conteo')[:500]

        data = MovimientoContableSerializer(qs, many=True).data
        return Response({'count': len(data), 'results': data})
