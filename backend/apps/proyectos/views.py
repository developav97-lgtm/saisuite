"""
SaiSuite — Proyectos: Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.proyectos.models import (
    Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito,
    Actividad, ActividadProyecto, Tarea, TareaTag, SesionTrabajo,
    ActividadSaiopen,
)
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
    ActividadSaiopenListSerializer,
    ActividadSaiopenDetailSerializer,
    ActividadSaiopenCreateUpdateSerializer,
    ConfiguracionModuloSerializer,
    TareaSerializer,
    TareaTagSerializer,
    SesionTrabajoSerializer,
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
    calcular_avance_fase_desde_tareas,
)
from apps.proyectos.tarea_services import TimesheetService
from apps.notifications.services import NotificacionService
from apps.proyectos.filters import ProyectoFilter, TareaFilter
from apps.proyectos.permissions import CanAccessProyectos, CanEditProyecto, TareaPermission

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

    @action(detail=True, methods=['post'], url_path='activar')
    def activar(self, request, pk=None, **kwargs):
        """POST /api/v1/fases/{id}/activar/"""
        fase = self.get_object()
        try:
            fase_actualizada = FaseService.activar_fase(fase)
        except ProyectoException as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FaseDetailSerializer(fase_actualizada).data)

    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None, **kwargs):
        """POST /api/v1/fases/{id}/completar/"""
        fase = self.get_object()
        try:
            fase_actualizada = FaseService.completar_fase(fase)
        except ProyectoException as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(FaseDetailSerializer(fase_actualizada).data)


class ActividadSaiopenViewSet(viewsets.ModelViewSet):
    """
    CRUD del catálogo de actividades Saiopen.
    GET/POST  /api/v1/proyectos/actividades-saiopen/
    GET/PATCH/PUT/DELETE  /api/v1/proyectos/actividades-saiopen/{id}/
    """
    permission_classes = [CanAccessProyectos]
    filter_backends    = [SearchFilter, OrderingFilter]
    search_fields      = ['codigo', 'nombre']
    ordering_fields    = ['codigo', 'nombre', 'unidad_medida', 'created_at']
    ordering           = ['codigo']

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = ActividadSaiopen.all_objects.filter(activo=True)
        if company:
            qs = qs.filter(company=company)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return ActividadSaiopenListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ActividadSaiopenCreateUpdateSerializer
        return ActividadSaiopenDetailSerializer

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company', None)
        serializer.save(company=company)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.activo = False
        obj.save(update_fields=['activo', 'updated_at'])
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


class TareaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Tarea con filtros avanzados.

    Endpoints:
      GET/POST        /api/v1/proyectos/tareas/
      GET/PATCH/DEL   /api/v1/proyectos/tareas/{id}/
      POST            /api/v1/proyectos/tareas/{id}/agregar-follower/
      DELETE          /api/v1/proyectos/tareas/{id}/quitar-follower/{user_id}/
      POST            /api/v1/proyectos/tareas/{id}/cambiar-estado/
    """

    serializer_class   = TareaSerializer
    permission_classes = [TareaPermission]
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = TareaFilter
    ordering_fields    = ['prioridad', 'fecha_limite', 'created_at', 'nombre']
    ordering           = ['-prioridad', 'fecha_limite']

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = Tarea.all_objects.select_related(
            'proyecto', 'fase', 'responsable', 'tarea_padre', 'cliente',
            'actividad_saiopen', 'actividad_proyecto__actividad',
        ).prefetch_related('followers', 'tags', 'subtareas')

        if company:
            qs = qs.filter(proyecto__company=company)

        # Filtrar por proyecto si viene en query params o kwargs de URL anidada
        proyecto_id = (
            self.request.query_params.get('proyecto_id') or
            self.kwargs.get('proyecto_pk')
        )
        if proyecto_id:
            qs = qs.filter(proyecto_id=proyecto_id)

        return qs

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company', None)
        serializer.save(company=company)

    def update(self, request, *args, **kwargs):
        """Override para notificar cuando cambia el responsable."""
        instance = self.get_object()
        responsable_anterior_id = instance.responsable_id

        response = super().update(request, *args, **kwargs)

        instance.refresh_from_db()
        responsable_nuevo = instance.responsable
        if (
            responsable_nuevo
            and responsable_nuevo.id != responsable_anterior_id
            and responsable_nuevo != request.user
        ):
            NotificacionService.crear(
                usuario=responsable_nuevo,
                tipo='asignacion',
                titulo='Nueva tarea asignada',
                mensaje=(
                    f'{request.user.full_name or request.user.email} '
                    f'te asignó la tarea "{instance.nombre}"'
                ),
                objeto_relacionado=instance,
                url_accion=f'/proyectos/tareas/{instance.id}',
            )

        return response

    @action(detail=True, methods=['post'], url_path='agregar-follower')
    def agregar_follower(self, request, pk=None):
        """POST /api/v1/proyectos/tareas/{id}/agregar-follower/"""
        tarea   = self.get_object()
        user_id = request.data.get('user_id')

        if not user_id:
            return Response(
                {'error': 'user_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.users.models import User as UserModel
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        tarea.followers.add(user)
        logger.info('tarea_follower_agregado', extra={
            'tarea_id': str(tarea.id), 'user_id': str(user.id)
        })
        return Response({
            'message': f'Follower {user.full_name} agregado',
            'followers_count': tarea.followers.count(),
        })

    @action(
        detail=True, methods=['delete'],
        url_path=r'quitar-follower/(?P<user_id>[^/.]+)',
    )
    def quitar_follower(self, request, pk=None, user_id=None):
        """DELETE /api/v1/proyectos/tareas/{id}/quitar-follower/{user_id}/"""
        tarea = self.get_object()

        from apps.users.models import User as UserModel
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        tarea.followers.remove(user)
        logger.info('tarea_follower_quitado', extra={
            'tarea_id': str(tarea.id), 'user_id': str(user.id)
        })
        return Response({
            'message': f'Follower {user.full_name} quitado',
            'followers_count': tarea.followers.count(),
        })

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """POST /api/v1/proyectos/tareas/{id}/cambiar-estado/"""
        tarea        = self.get_object()
        nuevo_estado = request.data.get('estado')

        if not nuevo_estado:
            return Response(
                {'error': 'estado es requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estados_validos = [c[0] for c in Tarea._meta.get_field('estado').choices]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # No se puede completar si hay subtareas pendientes
        if nuevo_estado == 'completada' and tarea.tiene_subtareas:
            pendientes = tarea.subtareas.exclude(estado__in=['completada', 'cancelada'])
            if pendientes.exists():
                return Response(
                    {'error': 'No se puede completar: hay subtareas pendientes'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        estado_anterior = tarea.estado
        tarea.estado = nuevo_estado
        tarea.save()
        logger.info('tarea_estado_cambiado', extra={
            'tarea_id': str(tarea.id), 'nuevo_estado': nuevo_estado
        })

        # ── Notificaciones ────────────────────────────────────────
        titulo  = 'Estado de tarea actualizado'
        mensaje = (
            f'{request.user.full_name or request.user.email} '
            f'cambió el estado de "{tarea.nombre}" a {nuevo_estado.replace("_", " ").title()}'
        )
        url     = f'/proyectos/tareas/{tarea.id}'
        meta    = {'estado_anterior': estado_anterior, 'estado_nuevo': nuevo_estado}

        destinatarios = set()
        if tarea.responsable_id and tarea.responsable != request.user:
            destinatarios.add(tarea.responsable)
        for follower in tarea.followers.exclude(id=request.user.id):
            destinatarios.add(follower)

        for dest in destinatarios:
            NotificacionService.crear(
                usuario=dest,
                tipo='cambio_estado',
                titulo=titulo,
                mensaje=mensaje,
                objeto_relacionado=tarea,
                url_accion=url,
                metadata=meta,
            )
        # ─────────────────────────────────────────────────────────

        return Response(self.get_serializer(tarea).data)

    # ── Timesheet: modo manual ────────────────────────────────

    @action(detail=True, methods=['post'], url_path='agregar-horas')
    def agregar_horas(self, request, pk=None):
        """
        POST /api/v1/proyectos/tareas/{id}/agregar-horas/
        Body: {"horas": 2.5}
        Suma horas trabajadas manualmente a la tarea.
        """
        tarea = self.get_object()
        try:
            horas = Decimal(str(request.data.get('horas', 0)))
        except InvalidOperation:
            return Response(
                {'detail': 'Formato de horas inválido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            tarea = TimesheetService.agregar_horas(tarea, horas)
        except ValidationError as exc:
            return Response(
                exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self.get_serializer(tarea).data)

    @action(detail=True, methods=['post'], url_path='agregar-cantidad')
    def agregar_cantidad(self, request, pk=None):
        """
        POST /api/v1/proyectos/tareas/{id}/agregar-cantidad/
        Body: {"cantidad": 2.5}
        Suma cantidad ejecutada manualmente a la tarea.
        """
        tarea = self.get_object()
        try:
            cantidad = Decimal(str(request.data.get('cantidad', 0)))
        except InvalidOperation:
            return Response(
                {'detail': 'Formato de cantidad inválido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            tarea = TimesheetService.agregar_cantidad(tarea, cantidad)
        except ValidationError as exc:
            return Response(
                exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self.get_serializer(tarea).data)

    # ── Timesheet: cronómetro ─────────────────────────────────

    @action(detail=True, methods=['post'], url_path='sesiones/iniciar')
    def iniciar_sesion(self, request, pk=None):
        """
        POST /api/v1/proyectos/tareas/{id}/sesiones/iniciar/
        Inicia el cronómetro para la tarea.
        """
        tarea = self.get_object()
        try:
            sesion = TimesheetService.iniciar_sesion(tarea, request.user)
        except ValidationError as exc:
            data = {'detail': exc.message if hasattr(exc, 'message') else str(exc)}
            # Adjuntar sesión activa existente para que el frontend la restaure
            sesion_activa = TimesheetService.sesion_activa_usuario(request.user)
            if sesion_activa:
                data['sesion_activa'] = SesionTrabajoSerializer(sesion_activa).data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            SesionTrabajoSerializer(sesion).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True, methods=['post'],
        url_path=r'sesiones/(?P<sesion_id>[^/.]+)/pausar',
    )
    def pausar_sesion(self, request, pk=None, sesion_id=None):
        """POST /api/v1/proyectos/tareas/{id}/sesiones/{sesion_id}/pausar/"""
        try:
            sesion = TimesheetService.pausar_sesion(sesion_id, request.user)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(SesionTrabajoSerializer(sesion).data)

    @action(
        detail=True, methods=['post'],
        url_path=r'sesiones/(?P<sesion_id>[^/.]+)/reanudar',
    )
    def reanudar_sesion(self, request, pk=None, sesion_id=None):
        """POST /api/v1/proyectos/tareas/{id}/sesiones/{sesion_id}/reanudar/"""
        try:
            sesion = TimesheetService.reanudar_sesion(sesion_id, request.user)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(SesionTrabajoSerializer(sesion).data)

    @action(
        detail=True, methods=['post'],
        url_path=r'sesiones/(?P<sesion_id>[^/.]+)/detener',
    )
    def detener_sesion(self, request, pk=None, sesion_id=None):
        """
        POST /api/v1/proyectos/tareas/{id}/sesiones/{sesion_id}/detener/
        Body opcional: {"notas": "Descripción del trabajo realizado"}
        """
        notas = request.data.get('notas', '')
        try:
            sesion = TimesheetService.detener_sesion(sesion_id, request.user, notas)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(SesionTrabajoSerializer(sesion).data)

    @action(detail=True, methods=['get'], url_path='sesiones')
    def listar_sesiones(self, request, pk=None):
        """
        GET /api/v1/proyectos/tareas/{id}/sesiones/
        Query params: ?estado=activa|pausada|finalizada  ?usuario=<uuid>
        """
        tarea = self.get_object()
        qs = SesionTrabajo.objects.filter(tarea=tarea).select_related('usuario')

        estado = request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        usuario_id = request.query_params.get('usuario')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)

        return Response(SesionTrabajoSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='sesion-activa')
    def sesion_activa(self, request):
        """
        GET /api/v1/proyectos/tareas/sesion-activa/
        Retorna la sesión activa/pausada del usuario para restaurar el cronómetro.
        """
        sesion = TimesheetService.sesion_activa_usuario(request.user)
        if sesion:
            return Response(SesionTrabajoSerializer(sesion).data)
        return Response(
            {'detail': 'No hay sesión activa.'},
            status=status.HTTP_404_NOT_FOUND,
        )


class TareaTagViewSet(viewsets.ModelViewSet):
    """
    CRUD de etiquetas de tareas por empresa.
    GET/POST       /api/v1/proyectos/tags/
    GET/PATCH/DEL  /api/v1/proyectos/tags/{id}/
    """

    serializer_class   = TareaTagSerializer
    permission_classes = [CanAccessProyectos]

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = TareaTag.all_objects.all()
        if company:
            qs = qs.filter(company=company)
        return qs

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company', None)
        serializer.save(company=company)
