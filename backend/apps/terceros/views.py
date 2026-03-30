"""
SaiSuite — Terceros Views
Views solo orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from .permissions import HasTerceroPermission


class TerceroPagination(PageNumberPagination):
    page_size             = 25
    page_size_query_param = 'page_size'
    max_page_size         = 100
from .models import Tercero, TerceroDireccion
from .serializers import (
    TerceroListSerializer,
    TerceroDetailSerializer,
    TerceroCreateUpdateSerializer,
    TerceroDireccionSerializer,
)
from .services import TerceroService, TerceroDireccionService

logger = logging.getLogger(__name__)


class TerceroViewSet(ViewSet):
    permission_classes = [IsAuthenticated, HasTerceroPermission]

    def list(self, request):
        search             = request.query_params.get('search', '')
        tipo_tercero       = request.query_params.get('tipo_tercero', '')
        tipo_identificacion = request.query_params.get('tipo_identificacion', '')
        activo_raw         = request.query_params.get('activo', None)
        activo             = None if activo_raw is None else activo_raw.lower() == 'true'

        qs = TerceroService.list(
            request.user.effective_company,
            search=search,
            tipo_tercero=tipo_tercero,
            tipo_identificacion=tipo_identificacion,
            activo=activo,
        )
        paginator = TerceroPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = TerceroListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = TerceroListSerializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            tercero = TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TerceroDetailSerializer(tercero).data)

    def create(self, request):
        serializer = TerceroCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            tercero = TerceroService.create(request.user.effective_company, serializer.validated_data)
        except Exception as exc:
            logger.error('error_crear_tercero', extra={'error': str(exc)})
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TerceroDetailSerializer(tercero).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        try:
            tercero = TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TerceroCreateUpdateSerializer(tercero, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        tercero = TerceroService.update(tercero, serializer.validated_data)
        return Response(TerceroDetailSerializer(tercero).data)

    def destroy(self, request, pk=None):
        try:
            tercero = TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        TerceroService.delete(tercero)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Direcciones nested ─────────────────────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='direcciones')
    def direcciones_list(self, request, pk=None):
        try:
            tercero = TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        direcciones = TerceroDireccionService.list_by_tercero(tercero.id, request.user.effective_company)
        return Response(TerceroDireccionSerializer(direcciones, many=True).data)

    @action(detail=True, methods=['post'], url_path='direcciones/crear')
    def direcciones_crear(self, request, pk=None):
        try:
            tercero = TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TerceroDireccionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        direccion = TerceroDireccionService.create(tercero, serializer.validated_data)
        return Response(TerceroDireccionSerializer(direccion).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path=r'direcciones/(?P<dir_pk>[^/.]+)')
    def direcciones_update(self, request, pk=None, dir_pk=None):
        try:
            TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            direccion = TerceroDireccion.objects.get(id=dir_pk, company=request.user.effective_company)
        except TerceroDireccion.DoesNotExist:
            return Response({'detail': 'Dirección no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = TerceroDireccionSerializer(direccion, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        direccion = TerceroDireccionService.update(direccion, serializer.validated_data)
        return Response(TerceroDireccionSerializer(direccion).data)

    @action(detail=True, methods=['delete'], url_path=r'direcciones/(?P<dir_pk>[^/.]+)/eliminar')
    def direcciones_delete(self, request, pk=None, dir_pk=None):
        try:
            TerceroService.get_by_id(pk, request.user.effective_company)
        except Tercero.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            direccion = TerceroDireccion.objects.get(id=dir_pk, company=request.user.effective_company)
        except TerceroDireccion.DoesNotExist:
            return Response({'detail': 'Dirección no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        TerceroDireccionService.delete(direccion)
        return Response(status=status.HTTP_204_NO_CONTENT)
