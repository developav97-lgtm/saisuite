"""
SaiSuite — CRM: Cotización Views + PDF + Sync callback.
"""
import logging
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from .models import CrmCotizacion, CrmLineaCotizacion, CrmProducto, CrmImpuesto
from .cotizacion_serializers import (
    CrmCotizacionListSerializer, CrmCotizacionDetailSerializer,
    CrmCotizacionCreateSerializer, CrmCotizacionUpdateSerializer,
    CrmCotizacionEnviarSerializer, CrmLineaCotizacionSerializer,
    CrmLineaCotizacionCreateSerializer, CrmProductoListSerializer,
    CrmImpuestoSerializer, CrmSyncConfirmSerializer,
)
from .cotizacion_services import CotizacionService, SyncCotizacionService
from .producto_services import ProductoSyncService
from .services import OportunidadService
from .permissions import CanAccessCrm, CrmBasePermission, CrmAdminPermission

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# COTIZACIONES
# ─────────────────────────────────────────────

class CotizacionViewSet(ViewSet):
    permission_classes = [CrmBasePermission]

    def list_by_oportunidad(self, request, oportunidad_pk=None):
        op = OportunidadService.get(oportunidad_pk, request.user.company)
        cotizaciones = CotizacionService.list(op)
        return Response(CrmCotizacionListSerializer(cotizaciones, many=True).data)

    def create(self, request, oportunidad_pk=None):
        op = OportunidadService.get(oportunidad_pk, request.user.company)
        ser = CrmCotizacionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Resolver contacto si viene por ID
        contacto_id = data.pop('contacto_id', None)
        if contacto_id:
            from apps.terceros.models import Tercero
            data['contacto'] = Tercero.objects.filter(id=contacto_id, company=request.user.company).first()

        cot = CotizacionService.create(op, data)
        return Response(CrmCotizacionDetailSerializer(cot).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        return Response(CrmCotizacionDetailSerializer(cot).data)

    def partial_update(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        ser = CrmCotizacionUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            cot = CotizacionService.update(cot, ser.validated_data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CrmCotizacionDetailSerializer(cot).data)

    def destroy(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        try:
            CotizacionService.delete(cot)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def enviar(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        ser = CrmCotizacionEnviarSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            cot = CotizacionService.enviar(
                cot,
                email_destino=ser.validated_data.get('email_destino'),
                usuario=request.user,
            )
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CrmCotizacionDetailSerializer(cot).data)

    def aceptar(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        try:
            cot = CotizacionService.aceptar(cot, usuario=request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CrmCotizacionDetailSerializer(cot).data)

    def rechazar(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        try:
            cot = CotizacionService.rechazar(cot, usuario=request.user)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CrmCotizacionDetailSerializer(cot).data)

    def pdf(self, request, pk=None):
        cot = CotizacionService.get(pk, request.user.company)
        try:
            pdf_bytes = CotizacionService.generar_pdf(cot)
        except Exception as e:
            logger.error('crm_pdf_error', extra={'cotizacion_id': str(cot.id), 'error': str(e)})
            return Response({'detail': f'Error generando PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="cotizacion_{cot.numero_interno}.pdf"'
        return response


# ─────────────────────────────────────────────
# LÍNEAS DE COTIZACIÓN
# ─────────────────────────────────────────────

class LineaCotizacionViewSet(ViewSet):
    permission_classes = [CrmBasePermission]

    def list(self, request, cotizacion_pk=None):
        cot = CotizacionService.get(cotizacion_pk, request.user.company)
        lineas = CrmLineaCotizacion.all_objects.filter(cotizacion=cot).order_by('conteo')
        return Response(CrmLineaCotizacionSerializer(lineas, many=True).data)

    def create(self, request, cotizacion_pk=None):
        cot = CotizacionService.get(cotizacion_pk, request.user.company)
        ser = CrmLineaCotizacionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        producto_id = data.pop('producto_id', None)
        impuesto_id = data.pop('impuesto_id', None)

        if producto_id:
            data['producto'] = CrmProducto.all_objects.filter(id=producto_id, company=request.user.company).first()
            if data['producto'] and not impuesto_id:
                data['impuesto'] = data['producto'].impuesto
        if impuesto_id:
            data['impuesto'] = CrmImpuesto.all_objects.filter(id=impuesto_id, company=request.user.company).first()

        try:
            linea = CotizacionService.add_linea(cot, data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CrmLineaCotizacionSerializer(linea).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None, cotizacion_pk=None):
        linea = CrmLineaCotizacion.all_objects.get(id=pk, cotizacion__company=request.user.company)
        ser = CrmLineaCotizacionCreateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if 'impuesto_id' in data:
            impuesto_id = data.pop('impuesto_id')
            data['impuesto'] = CrmImpuesto.all_objects.filter(id=impuesto_id, company=request.user.company).first() if impuesto_id else None
        linea = CotizacionService.update_linea(linea, data)
        return Response(CrmLineaCotizacionSerializer(linea).data)

    def destroy(self, request, pk=None, cotizacion_pk=None):
        linea = CrmLineaCotizacion.all_objects.get(id=pk, cotizacion__company=request.user.company)
        CotizacionService.delete_linea(linea)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# PRODUCTOS E IMPUESTOS
# ─────────────────────────────────────────────

class ProductoListView(APIView):
    permission_classes = [CanAccessCrm]

    def get(self, request):
        productos = ProductoSyncService.list(
            request.user.company,
            search=request.query_params.get('search', ''),
            grupo=request.query_params.get('grupo', ''),
            clase=request.query_params.get('clase', ''),
        )
        return Response(CrmProductoListSerializer(productos, many=True).data)


class ProductoSyncView(APIView):
    permission_classes = [CrmAdminPermission]

    def post(self, request):
        """Forzar sincronización manual de productos desde Saiopen."""
        from .producto_services import ProductoSyncService, ImpuestoSyncService
        items = request.data.get('items', [])
        taxauth = request.data.get('taxauth', [])

        resultado_imp = ImpuestoSyncService.sync_from_payload(request.user.company, taxauth)
        resultado_prod = ProductoSyncService.sync_from_payload(request.user.company, items)
        return Response({
            'impuestos': resultado_imp,
            'productos': resultado_prod,
        })


class ImpuestoListView(APIView):
    permission_classes = [CanAccessCrm]

    def get(self, request):
        impuestos = CrmImpuesto.objects.filter(company=request.user.company)
        return Response(CrmImpuestoSerializer(impuestos, many=True).data)


# ─────────────────────────────────────────────
# SYNC CALLBACK (desde agente Windows)
# ─────────────────────────────────────────────

class CotizacionSyncCallbackView(APIView):
    """
    Endpoint interno para que el agente Windows confirme
    la creación de COTIZACI en Saiopen.
    Solo accesible desde dentro de la red / con token interno.
    """
    def post(self, request):
        ser = CrmSyncConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            cot = SyncCotizacionService.recibir_confirmacion(
                cotizacion_id=str(d['cotizacion_id']),
                sai_numero=d['sai_numero'],
                sai_tipo=d['sai_tipo'],
                sai_empresa=d['sai_empresa'],
                sai_sucursal=d['sai_sucursal'],
            )
        except CrmCotizacion.DoesNotExist:
            return Response({'detail': 'Cotización no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'sai_key': cot.sai_key, 'status': 'synced'})
