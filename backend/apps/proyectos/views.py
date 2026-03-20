"""
SaiSuite — Proyectos: Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.proyectos.models import Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito, Actividad, ActividadProyecto
from apps.proyectos.serializers import (
    ProyectoListSerializer,
    ProyectoDetailSerializer,
    ProyectoCreateUpdateSerializer,
    CambiarEstadoSerializer,
    FaseListSerializer,
    FaseDetailSerializer,
    FaseCreateUpdateSerializer,
    TerceroProyectoSerializer,
    TerceroProyectoCreateSerializer,
    DocumentoContableListSerializer,
    DocumentoContableDetailSerializer,
    HitoSerializer,
    HitoCreateSerializer,
    GenerarFacturaSerializer,
    ActividadListSerializer,
    ActividadDetailSerializer,
    ActividadCreateUpdateSerializer,
    ActividadProyectoSerializer,
    ActividadProyectoCreateUpdateSerializer,
    ConfiguracionModuloSerializer,
)
from apps.proyectos.services import (
    ProyectoService,
    FaseService,
    TerceroProyectoService,
    DocumentoContableService,
    HitoService,
    ActividadService,
    ActividadProyectoService,
    ConfiguracionModuloService,
    ProyectoException,
)
from apps.proyectos.filters import ProyectoFilter
from apps.proyectos.permissions import CanAccessProyectos, CanEditProyecto

logger = logging.getLogger(__name__)


class ProyectoViewSet(viewsets.ModelViewSet):
    """
    CRUD de proyectos + acciones de cambio de estado y reporte financiero.
    """
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = ProyectoFilter
    search_fields    = ['codigo', 'nombre', 'cliente_nombre']
    ordering_fields  = ['codigo', 'nombre', 'estado', 'fecha_inicio_planificada', 'created_at']
    ordering         = ['-created_at']
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def get_queryset(self):
        # Pasar company explícitamente — el middleware no intercepta DRF/JWT auth
        company = getattr(self.request.user, 'company', None)
        return ProyectoService.list_proyectos(company=company)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProyectoListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProyectoCreateUpdateSerializer
        if self.action == 'cambiar_estado':
            return CambiarEstadoSerializer
        return ProyectoDetailSerializer

    def perform_create(self, serializer):
        proyecto = ProyectoService.create_proyecto(serializer.validated_data, self.request.user)
        serializer.instance = proyecto

    def perform_update(self, serializer):
        proyecto = ProyectoService.update_proyecto(
            self.get_object(), serializer.validated_data
        )
        serializer.instance = proyecto

    def destroy(self, request, *args, **kwargs):
        proyecto = self.get_object()
        ProyectoService.soft_delete_proyecto(proyecto)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """POST /api/v1/proyectos/{id}/cambiar-estado/"""
        proyecto   = self.get_object()
        serializer = CambiarEstadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proyecto_actualizado = ProyectoService.cambiar_estado(
            proyecto,
            nuevo_estado=serializer.validated_data['nuevo_estado'],
            forzar=serializer.validated_data.get('forzar', False),
        )
        return Response(
            ProyectoDetailSerializer(proyecto_actualizado).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='iniciar-ejecucion')
    def iniciar_ejecucion(self, request, pk=None):
        """
        POST /api/v1/proyectos/{id}/iniciar-ejecucion/
        Inicia la ejecución del proyecto validando configuración del módulo.
        """
        from apps.proyectos.models import EstadoProyecto
        proyecto = self.get_object()
        proyecto_actualizado = ProyectoService.cambiar_estado(
            proyecto, nuevo_estado=EstadoProyecto.EN_EJECUCION
        )
        return Response(
            ProyectoDetailSerializer(proyecto_actualizado).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='estado-financiero')
    def estado_financiero(self, request, pk=None):
        """GET /api/v1/proyectos/{id}/estado-financiero/"""
        proyecto = self.get_object()
        data     = ProyectoService.get_estado_financiero(proyecto)
        return Response(data, status=status.HTTP_200_OK)


class FaseViewSet(viewsets.ModelViewSet):
    """
    CRUD de fases.
    - Listado y creación via /proyectos/{id}/fases/
    - Actualización y eliminación via /fases/{id}/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def get_serializer_class(self):
        if self.action == 'list':
            return FaseListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return FaseCreateUpdateSerializer
        return FaseDetailSerializer

    def get_queryset(self):
        proyecto_pk = self.kwargs.get('proyecto_pk')
        if proyecto_pk:
            proyecto = Proyecto.all_objects.get(id=proyecto_pk)
            return FaseService.list_fases(proyecto)
        return Fase.all_objects.filter(activo=True).select_related('proyecto')

    def perform_create(self, serializer):
        proyecto_pk = self.kwargs.get('proyecto_pk')
        proyecto    = Proyecto.all_objects.get(id=proyecto_pk)
        fase = FaseService.create_fase(proyecto, serializer.validated_data)
        serializer.instance = fase

    def perform_update(self, serializer):
        fase = FaseService.update_fase(self.get_object(), serializer.validated_data)
        serializer.instance = fase

    def destroy(self, request, *args, **kwargs):
        fase = self.get_object()
        FaseService.soft_delete_fase(fase)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TerceroProyectoViewSet(viewsets.GenericViewSet):
    """
    Terceros vinculados a un proyecto.
    - GET/POST  /api/v1/proyectos/{proyecto_pk}/terceros/
    - DELETE    /api/v1/proyectos/{proyecto_pk}/terceros/{pk}/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def _get_proyecto(self):
        proyecto_pk = self.kwargs['proyecto_pk']
        return Proyecto.all_objects.get(id=proyecto_pk)

    def get_serializer_class(self):
        if self.action == 'create':
            return TerceroProyectoCreateSerializer
        return TerceroProyectoSerializer

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/terceros/?fase=UUID"""
        proyecto = self._get_proyecto()
        fase_id  = request.query_params.get('fase') or None
        qs       = TerceroProyectoService.list_terceros(proyecto, fase_id=fase_id)
        serializer = TerceroProyectoSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, proyecto_pk=None):
        """POST /api/v1/proyectos/{id}/terceros/"""
        proyecto   = self._get_proyecto()
        serializer = TerceroProyectoCreateSerializer(
            data=request.data, context={'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        tercero = TerceroProyectoService.vincular_tercero(proyecto, serializer.validated_data)
        return Response(
            TerceroProyectoSerializer(tercero).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, proyecto_pk=None, pk=None):
        """DELETE /api/v1/proyectos/{id}/terceros/{pk}/"""
        tercero = TerceroProyecto.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        TerceroProyectoService.desvincular_tercero(tercero)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentoContableViewSet(viewsets.GenericViewSet):
    """
    Documentos contables del proyecto (solo lectura — los crea el agente Go).
    - GET  /api/v1/proyectos/{proyecto_pk}/documentos/
    - GET  /api/v1/proyectos/{proyecto_pk}/documentos/{pk}/
    """
    permission_classes = [CanAccessProyectos]

    def _get_proyecto(self):
        return Proyecto.all_objects.get(id=self.kwargs['proyecto_pk'])

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/documentos/"""
        proyecto = self._get_proyecto()
        fase_id  = request.query_params.get('fase')
        qs       = DocumentoContableService.list_documentos(proyecto, fase_id=fase_id)
        serializer = DocumentoContableListSerializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, proyecto_pk=None, pk=None):
        """GET /api/v1/proyectos/{id}/documentos/{pk}/"""
        documento  = DocumentoContableService.get_documento(pk)
        serializer = DocumentoContableDetailSerializer(documento)
        return Response(serializer.data)


class HitoViewSet(viewsets.GenericViewSet):
    """
    Hitos facturables del proyecto.
    - GET/POST  /api/v1/proyectos/{proyecto_pk}/hitos/
    - POST      /api/v1/proyectos/{proyecto_pk}/hitos/{pk}/generar-factura/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def _get_proyecto(self):
        return Proyecto.all_objects.get(id=self.kwargs['proyecto_pk'])

    def get_serializer_class(self):
        if self.action == 'create':
            return HitoCreateSerializer
        if self.action == 'generar_factura':
            return GenerarFacturaSerializer
        return HitoSerializer

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/hitos/"""
        proyecto   = self._get_proyecto()
        qs         = HitoService.list_hitos(proyecto)
        serializer = HitoSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, proyecto_pk=None):
        """POST /api/v1/proyectos/{id}/hitos/"""
        proyecto   = self._get_proyecto()
        serializer = HitoCreateSerializer(
            data=request.data, context={'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        hito = HitoService.create_hito(proyecto, serializer.validated_data)
        return Response(HitoSerializer(hito).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='generar-factura')
    def generar_factura(self, request, proyecto_pk=None, pk=None):
        """POST /api/v1/proyectos/{id}/hitos/{pk}/generar-factura/"""
        hito       = Hito.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        serializer = GenerarFacturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hito_actualizado = HitoService.generar_factura(hito, request.user)
        return Response(HitoSerializer(hito_actualizado).data, status=status.HTTP_200_OK)


class ActividadViewSet(viewsets.ModelViewSet):
    """
    CRUD del catálogo global de actividades (por empresa).
    - GET/POST       /api/v1/proyectos/actividades/
    - GET/PATCH/DEL  /api/v1/proyectos/actividades/{id}/
    """
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields   = ['tipo']
    search_fields      = ['codigo', 'nombre', 'unidad_medida']
    ordering_fields    = ['codigo', 'nombre', 'tipo', 'created_at']
    ordering           = ['codigo']
    permission_classes = [CanAccessProyectos]

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        return ActividadService.list_actividades(company=company)

    def get_serializer_class(self):
        if self.action == 'list':
            return ActividadListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ActividadCreateUpdateSerializer
        return ActividadDetailSerializer

    def perform_create(self, serializer):
        actividad = ActividadService.create_actividad(serializer.validated_data, self.request.user)
        serializer.instance = actividad

    def perform_update(self, serializer):
        actividad = ActividadService.update_actividad(self.get_object(), serializer.validated_data)
        serializer.instance = actividad

    def destroy(self, request, *args, **kwargs):
        try:
            ActividadService.soft_delete_actividad(self.get_object())
        except Exception as exc:
            raise ProyectoException(str(exc)) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActividadProyectoViewSet(viewsets.GenericViewSet):
    """
    Actividades asignadas a un proyecto.
    - GET/POST    /api/v1/proyectos/{proyecto_pk}/actividades/
    - PATCH/DEL   /api/v1/proyectos/{proyecto_pk}/actividades/{pk}/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def _get_proyecto(self):
        return Proyecto.all_objects.get(id=self.kwargs['proyecto_pk'])

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return ActividadProyectoCreateUpdateSerializer
        return ActividadProyectoSerializer

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/actividades/"""
        proyecto = self._get_proyecto()
        fase_id  = request.query_params.get('fase')
        qs       = ActividadProyectoService.list_actividades_proyecto(proyecto, fase_id=fase_id)
        serializer = ActividadProyectoSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, proyecto_pk=None):
        """POST /api/v1/proyectos/{id}/actividades/"""
        proyecto   = self._get_proyecto()
        serializer = ActividadProyectoCreateUpdateSerializer(
            data=request.data, context={'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        ap = ActividadProyectoService.asignar_actividad(proyecto, serializer.validated_data)
        return Response(ActividadProyectoSerializer(ap).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, proyecto_pk=None, pk=None):
        """PATCH /api/v1/proyectos/{id}/actividades/{pk}/"""
        ap = ActividadProyecto.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        serializer = ActividadProyectoCreateUpdateSerializer(
            ap, data=request.data, partial=True,
            context={'proyecto': ap.proyecto},
        )
        serializer.is_valid(raise_exception=True)
        ap = ActividadProyectoService.update_actividad_proyecto(ap, serializer.validated_data)
        return Response(ActividadProyectoSerializer(ap).data)

    def destroy(self, request, proyecto_pk=None, pk=None):
        """DELETE /api/v1/proyectos/{id}/actividades/{pk}/"""
        ap = ActividadProyecto.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        ActividadProyectoService.desasignar_actividad(ap)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConfiguracionModuloView(APIView):
    """
    GET/PATCH de la configuración del módulo de proyectos para la empresa del usuario.
    GET   /api/v1/proyectos/config/
    PATCH /api/v1/proyectos/config/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request):
        config = ConfiguracionModuloService.get_or_create(request.user.company)
        return Response(ConfiguracionModuloSerializer(config).data)

    def patch(self, request):
        config     = ConfiguracionModuloService.get_or_create(request.user.company)
        serializer = ConfiguracionModuloSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = ConfiguracionModuloService.update(request.user.company, serializer.validated_data)
        return Response(ConfiguracionModuloSerializer(updated).data)
