"""
SaiSuite — Proyectos: Views
Las views SOLO orquestan: reciben request → llaman service → retornan response.
"""
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.proyectos.models import (
    Project, Phase, ProjectStakeholder, AccountingDocument, Milestone,
    Activity, ProjectActivity, Task, TaskTag, WorkSession,
    SaiopenActivity, TaskDependency, TimesheetEntry,
    ResourceAssignment, ResourceCapacity, ResourceAvailability,
)
from apps.proyectos.serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateUpdateSerializer,
    ChangeStatusSerializer,
    PhaseListSerializer,
    PhaseDetailSerializer,
    PhaseCreateUpdateSerializer,
    ProjectStakeholderSerializer,
    ProjectStakeholderCreateSerializer,
    AccountingDocumentListSerializer,
    AccountingDocumentDetailSerializer,
    MilestoneSerializer,
    MilestoneCreateSerializer,
    GenerateInvoiceSerializer,
    ActivityListSerializer,
    ActivityDetailSerializer,
    ActivityCreateUpdateSerializer,
    ProjectActivitySerializer,
    ProjectActivityCreateSerializer,
    SaiopenActivitySerializer,
    SaiopenActivityDetailSerializer,
    SaiopenActivityCreateUpdateSerializer,
    ModuleSettingsSerializer,
    TaskDetailSerializer,
    TaskDependencySerializer,
    TaskTagSerializer,
    WorkSessionSerializer,
    TimesheetEntrySerializer,
    TimesheetEntryCreateSerializer,
    ResourceAssignmentListSerializer,
    ResourceAssignmentDetailSerializer,
    ResourceAssignmentCreateSerializer,
    ResourceCapacitySerializer,
    ResourceAvailabilitySerializer,
    ResourceAvailabilityCreateSerializer,
    WorkloadSummarySerializer,
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
from apps.proyectos.tarea_services import TimesheetService, DependencyService, TimesheetEntryService
from apps.notifications.services import NotificacionService
from apps.proyectos.filters import ProjectFilter, TaskFilter
from apps.proyectos.permissions import CanAccessProyectos, CanEditProyecto, TaskPermission

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD de proyectos + acciones de cambio de estado y reporte financiero.
    """
    filter_backends  = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class  = ProjectFilter
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
            return ProjectListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProjectCreateUpdateSerializer
        if self.action == 'cambiar_estado':
            return ChangeStatusSerializer
        return ProjectDetailSerializer

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
        serializer = ChangeStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proyecto_actualizado = ProyectoService.cambiar_estado(
            proyecto,
            nuevo_estado=serializer.validated_data['nuevo_estado'],
            forzar=serializer.validated_data.get('forzar', False),
        )
        return Response(
            ProjectDetailSerializer(proyecto_actualizado).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='iniciar-ejecucion')
    def iniciar_ejecucion(self, request, pk=None):
        """
        POST /api/v1/proyectos/{id}/iniciar-ejecucion/
        Inicia la ejecución del proyecto validando configuración del módulo.
        """
        from apps.proyectos.models import ProjectStatus
        proyecto = self.get_object()
        proyecto_actualizado = ProyectoService.cambiar_estado(
            proyecto, nuevo_estado=ProjectStatus.IN_PROGRESS
        )
        return Response(
            ProjectDetailSerializer(proyecto_actualizado).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='estado-financiero')
    def estado_financiero(self, request, pk=None):
        """GET /api/v1/proyectos/{id}/estado-financiero/"""
        proyecto = self.get_object()
        data     = ProyectoService.get_estado_financiero(proyecto)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='gantt-data')
    def gantt_data(self, request, pk=None):
        """
        GET /api/v1/projects/{id}/gantt-data/
        Retorna tareas del proyecto en formato compatible con Frappe Gantt.
        Incluye tareas que tengan al menos fecha_fin o fecha_limite.
        Si fecha_inicio no está definida se calcula como end - max(horas_estimadas/8, 1) días.
        """
        from django.db.models import Q
        proyecto = self.get_object()
        tareas = (
            proyecto.tasks
            .filter(
                Q(fecha_fin__isnull=False) | Q(fecha_limite__isnull=False)
            )
            .select_related('fase', 'responsable')
            .order_by('fecha_limite', 'fecha_fin', 'nombre')
        )

        tasks = []
        for tarea in tareas:
            end_date   = tarea.fecha_fin or tarea.fecha_limite
            dias_est   = max(int(float(tarea.horas_estimadas) / 8), 1) if tarea.horas_estimadas else 1
            start_date = tarea.fecha_inicio or (end_date - timedelta(days=dias_est))
            # Garantizar que start < end
            if start_date >= end_date:
                start_date = end_date - timedelta(days=1)
            tasks.append({
                'id':           str(tarea.id),
                'name':         tarea.nombre,
                'start':        start_date.isoformat(),
                'end':          end_date.isoformat(),
                'progress':     tarea.porcentaje_completado,
                'custom_class': f'estado-{tarea.estado}',
            })

        logger.info('gantt_data_consultado', extra={
            'proyecto_id': str(proyecto.id),
            'tareas_count': len(tasks),
        })
        return Response({'tasks': tasks}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='camino-critico')
    def camino_critico(self, request, pk=None):
        """
        GET /api/v1/proyectos/{id}/camino-critico/
        Retorna lista de IDs de tareas que están en el camino crítico del proyecto.
        """
        proyecto = self.get_object()
        company  = getattr(request.user, 'company', None)
        criticas = DependencyService.calcular_camino_critico(
            str(proyecto.id), company
        )
        return Response({'tareas_criticas': criticas}, status=status.HTTP_200_OK)


class PhaseViewSet(viewsets.ModelViewSet):
    """
    CRUD de fases.
    - Listado y creación via /proyectos/{id}/fases/
    - Actualización y eliminación via /fases/{id}/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def get_serializer_class(self):
        if self.action == 'list':
            return PhaseListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return PhaseCreateUpdateSerializer
        return PhaseDetailSerializer

    def get_queryset(self):
        proyecto_pk = self.kwargs.get('proyecto_pk')
        if proyecto_pk:
            proyecto = Project.all_objects.get(id=proyecto_pk)
            return FaseService.list_fases(proyecto)
        return Phase.all_objects.filter(activo=True).select_related('proyecto')

    def perform_create(self, serializer):
        proyecto_pk = self.kwargs.get('proyecto_pk')
        proyecto    = Project.all_objects.get(id=proyecto_pk)
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
        return Response(PhaseDetailSerializer(fase_actualizada).data)

    @action(detail=True, methods=['post'], url_path='completar')
    def completar(self, request, pk=None, **kwargs):
        """POST /api/v1/fases/{id}/completar/"""
        fase = self.get_object()
        try:
            fase_actualizada = FaseService.completar_fase(fase)
        except ProyectoException as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PhaseDetailSerializer(fase_actualizada).data)


class SaiopenActivityViewSet(viewsets.ModelViewSet):
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
        qs = SaiopenActivity.all_objects.filter(activo=True)
        if company:
            qs = qs.filter(company=company)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return SaiopenActivitySerializer
        if self.action in ('create', 'update', 'partial_update'):
            return SaiopenActivityCreateUpdateSerializer
        return SaiopenActivityDetailSerializer

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company', None)
        serializer.save(company=company)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.activo = False
        obj.save(update_fields=['activo', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectStakeholderViewSet(viewsets.GenericViewSet):
    """
    Terceros vinculados a un proyecto.
    - GET/POST  /api/v1/proyectos/{proyecto_pk}/terceros/
    - DELETE    /api/v1/proyectos/{proyecto_pk}/terceros/{pk}/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def _get_proyecto(self):
        proyecto_pk = self.kwargs['proyecto_pk']
        return Project.all_objects.get(id=proyecto_pk)

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectStakeholderCreateSerializer
        return ProjectStakeholderSerializer

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/terceros/?fase=UUID"""
        proyecto = self._get_proyecto()
        fase_id  = request.query_params.get('fase') or None
        qs       = TerceroProyectoService.list_terceros(proyecto, fase_id=fase_id)
        serializer = ProjectStakeholderSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, proyecto_pk=None):
        """POST /api/v1/proyectos/{id}/terceros/"""
        proyecto   = self._get_proyecto()
        serializer = ProjectStakeholderCreateSerializer(
            data=request.data, context={'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        tercero = TerceroProyectoService.vincular_tercero(proyecto, serializer.validated_data)
        return Response(
            ProjectStakeholderSerializer(tercero).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, proyecto_pk=None, pk=None):
        """DELETE /api/v1/proyectos/{id}/terceros/{pk}/"""
        tercero = ProjectStakeholder.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        TerceroProyectoService.desvincular_tercero(tercero)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountingDocumentViewSet(viewsets.GenericViewSet):
    """
    Documentos contables del proyecto (solo lectura — los crea el agente Go).
    - GET  /api/v1/proyectos/{proyecto_pk}/documentos/
    - GET  /api/v1/proyectos/{proyecto_pk}/documentos/{pk}/
    """
    permission_classes = [CanAccessProyectos]

    def _get_proyecto(self):
        return Project.all_objects.get(id=self.kwargs['proyecto_pk'])

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/documentos/"""
        proyecto = self._get_proyecto()
        fase_id  = request.query_params.get('fase')
        qs       = DocumentoContableService.list_documentos(proyecto, fase_id=fase_id)
        serializer = AccountingDocumentListSerializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, proyecto_pk=None, pk=None):
        """GET /api/v1/proyectos/{id}/documentos/{pk}/"""
        documento  = DocumentoContableService.get_documento(pk)
        serializer = AccountingDocumentDetailSerializer(documento)
        return Response(serializer.data)


class MilestoneViewSet(viewsets.GenericViewSet):
    """
    Hitos facturables del proyecto.
    - GET/POST  /api/v1/proyectos/{proyecto_pk}/hitos/
    - POST      /api/v1/proyectos/{proyecto_pk}/hitos/{pk}/generar-factura/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def _get_proyecto(self):
        return Project.all_objects.get(id=self.kwargs['proyecto_pk'])

    def get_serializer_class(self):
        if self.action == 'create':
            return MilestoneCreateSerializer
        if self.action == 'generar_factura':
            return GenerateInvoiceSerializer
        return MilestoneSerializer

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/hitos/"""
        proyecto   = self._get_proyecto()
        qs         = HitoService.list_hitos(proyecto)
        serializer = MilestoneSerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, proyecto_pk=None):
        """POST /api/v1/proyectos/{id}/hitos/"""
        proyecto   = self._get_proyecto()
        serializer = MilestoneCreateSerializer(
            data=request.data, context={'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        hito = HitoService.create_hito(proyecto, serializer.validated_data)
        return Response(MilestoneSerializer(hito).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='generar-factura')
    def generar_factura(self, request, proyecto_pk=None, pk=None):
        """POST /api/v1/proyectos/{id}/hitos/{pk}/generar-factura/"""
        hito       = Milestone.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        serializer = GenerateInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hito_actualizado = HitoService.generar_factura(hito, request.user)
        return Response(MilestoneSerializer(hito_actualizado).data, status=status.HTTP_200_OK)


class ActivityViewSet(viewsets.ModelViewSet):
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
            return ActivityListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ActivityCreateUpdateSerializer
        return ActivityDetailSerializer

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


class ProjectActivityViewSet(viewsets.GenericViewSet):
    """
    Actividades asignadas a un proyecto.
    - GET/POST    /api/v1/proyectos/{proyecto_pk}/actividades/
    - PATCH/DEL   /api/v1/proyectos/{proyecto_pk}/actividades/{pk}/
    """
    permission_classes = [CanAccessProyectos, CanEditProyecto]

    def _get_proyecto(self):
        return Project.all_objects.get(id=self.kwargs['proyecto_pk'])

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return ProjectActivityCreateSerializer
        return ProjectActivitySerializer

    def list(self, request, proyecto_pk=None):
        """GET /api/v1/proyectos/{id}/actividades/"""
        proyecto = self._get_proyecto()
        fase_id  = request.query_params.get('fase')
        qs       = ActividadProyectoService.list_actividades_proyecto(proyecto, fase_id=fase_id)
        serializer = ProjectActivitySerializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, proyecto_pk=None):
        """POST /api/v1/proyectos/{id}/actividades/"""
        proyecto   = self._get_proyecto()
        serializer = ProjectActivityCreateSerializer(
            data=request.data, context={'proyecto': proyecto}
        )
        serializer.is_valid(raise_exception=True)
        ap = ActividadProyectoService.asignar_actividad(proyecto, serializer.validated_data)
        return Response(ProjectActivitySerializer(ap).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, proyecto_pk=None, pk=None):
        """PATCH /api/v1/proyectos/{id}/actividades/{pk}/"""
        ap = ProjectActivity.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        serializer = ProjectActivityCreateSerializer(
            ap, data=request.data, partial=True,
            context={'proyecto': ap.proyecto},
        )
        serializer.is_valid(raise_exception=True)
        ap = ActividadProyectoService.update_actividad_proyecto(ap, serializer.validated_data)
        return Response(ProjectActivitySerializer(ap).data)

    def destroy(self, request, proyecto_pk=None, pk=None):
        """DELETE /api/v1/proyectos/{id}/actividades/{pk}/"""
        ap = ProjectActivity.all_objects.get(id=pk, proyecto_id=proyecto_pk)
        ActividadProyectoService.desasignar_actividad(ap)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModuleSettingsView(APIView):
    """
    GET/PATCH de la configuración del módulo de proyectos para la empresa del usuario.
    GET   /api/v1/proyectos/config/
    PATCH /api/v1/proyectos/config/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request):
        config = ConfiguracionModuloService.get_or_create(request.user.company)
        return Response(ModuleSettingsSerializer(config).data)

    def patch(self, request):
        config     = ConfiguracionModuloService.get_or_create(request.user.company)
        serializer = ModuleSettingsSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = ConfiguracionModuloService.update(request.user.company, serializer.validated_data)
        return Response(ModuleSettingsSerializer(updated).data)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Task con filtros avanzados.

    Endpoints:
      GET/POST        /api/v1/proyectos/tareas/
      GET/PATCH/DEL   /api/v1/proyectos/tareas/{id}/
      POST            /api/v1/proyectos/tareas/{id}/agregar-follower/
      DELETE          /api/v1/proyectos/tareas/{id}/quitar-follower/{user_id}/
      POST            /api/v1/proyectos/tareas/{id}/cambiar-estado/
    """

    serializer_class   = TaskDetailSerializer
    permission_classes = [TaskPermission]
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_class    = TaskFilter
    ordering_fields    = ['prioridad', 'fecha_limite', 'created_at', 'nombre']
    ordering           = ['-prioridad', 'fecha_limite']

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = Task.all_objects.select_related(
            'proyecto', 'fase', 'responsable', 'tarea_padre', 'cliente',
            'actividad_saiopen', 'actividad_proyecto__actividad',
        ).prefetch_related('followers', 'tags', 'subtasks')

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
                url_accion=f'/projects/tasks/{instance.id}',
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

        estados_validos = [c[0] for c in Task._meta.get_field('estado').choices]
        if nuevo_estado not in estados_validos:
            return Response(
                {'error': f'Estado inválido. Opciones: {estados_validos}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # No se puede completar si hay subtareas pendientes
        if nuevo_estado == 'completed' and tarea.tiene_subtareas:
            pendientes = tarea.subtasks.exclude(estado__in=['completed', 'cancelled'])
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
        url     = f'/projects/tasks/{tarea.id}'
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
                data['sesion_activa'] = WorkSessionSerializer(sesion_activa).data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            WorkSessionSerializer(sesion).data,
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
        return Response(WorkSessionSerializer(sesion).data)

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
        return Response(WorkSessionSerializer(sesion).data)

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
        return Response(WorkSessionSerializer(sesion).data)

    @action(detail=True, methods=['get'], url_path='sesiones')
    def listar_sesiones(self, request, pk=None):
        """
        GET /api/v1/proyectos/tareas/{id}/sesiones/
        Query params: ?estado=activa|pausada|finalizada  ?usuario=<uuid>
        """
        tarea = self.get_object()
        qs = WorkSession.objects.filter(tarea=tarea).select_related('usuario')

        estado = request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        usuario_id = request.query_params.get('usuario')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)

        return Response(WorkSessionSerializer(qs, many=True).data)

    # ── Dependencias entre tareas ─────────────────────────────

    @action(detail=True, methods=['post'], url_path='crear-dependencia')
    def crear_dependencia(self, request, pk=None):
        """
        POST /api/v1/proyectos/tareas/{id}/crear-dependencia/
        Body: {"predecesora_id": "uuid", "tipo": "FS", "retraso_dias": 0}
        La tarea {id} es la SUCESORA.
        """
        tarea = self.get_object()
        predecesora_id = request.data.get('predecesora_id')
        tipo           = request.data.get('tipo', 'FS')
        retraso_dias   = request.data.get('retraso_dias', 0)
        company        = getattr(request.user, 'company', None)

        if not predecesora_id:
            return Response(
                {'detail': 'predecesora_id es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            retraso_dias = int(retraso_dias)
        except (TypeError, ValueError):
            retraso_dias = 0

        try:
            dependencia = DependencyService.crear_dependencia(
                predecesora_id=predecesora_id,
                sucesora_id=str(tarea.id),
                company=company,
                tipo=tipo,
                retraso_dias=retraso_dias,
            )
        except ValidationError as exc:
            msgs = exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages}
            return Response(msgs, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskDependencySerializer(dependencia, context={'request': request})
        logger.info('dependencia_creada_via_api', extra={
            'tarea_id': str(tarea.id),
            'predecesora_id': str(predecesora_id),
        })
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='eliminar-dependencia')
    def eliminar_dependencia(self, request, pk=None):
        """
        DELETE /api/v1/proyectos/tareas/{id}/eliminar-dependencia/?dependencia_id=uuid
        """
        tarea          = self.get_object()
        dependencia_id = request.query_params.get('dependencia_id')
        company        = getattr(request.user, 'company', None)

        if not dependencia_id:
            return Response(
                {'detail': 'dependencia_id es requerido como query param.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dep = TaskDependency.objects.get(
                id=dependencia_id,
                company=company,
                tarea_sucesora=tarea,
            )
        except TaskDependency.DoesNotExist:
            return Response(
                {'detail': 'Dependencia no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        dep.delete()
        logger.info('dependencia_eliminada', extra={
            'dependencia_id': str(dependencia_id),
            'tarea_id': str(tarea.id),
        })
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='sesion-activa')
    def sesion_activa(self, request):
        """
        GET /api/v1/proyectos/tareas/sesion-activa/
        Retorna la sesión activa/pausada del usuario para restaurar el cronómetro.
        """
        sesion = TimesheetService.sesion_activa_usuario(request.user)
        if sesion:
            return Response(WorkSessionSerializer(sesion).data)
        return Response(
            {'detail': 'No hay sesión activa.'},
            status=status.HTTP_404_NOT_FOUND,
        )


class TaskTagViewSet(viewsets.ModelViewSet):
    """
    CRUD de etiquetas de tareas por empresa.
    GET/POST       /api/v1/proyectos/tags/
    GET/PATCH/DEL  /api/v1/proyectos/tags/{id}/
    """

    serializer_class   = TaskTagSerializer
    permission_classes = [CanAccessProyectos]

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = TaskTag.all_objects.all()
        if company:
            qs = qs.filter(company=company)
        return qs

    def perform_create(self, serializer):
        company = getattr(self.request.user, 'company', None)
        serializer.save(company=company)


class TimesheetViewSet(viewsets.GenericViewSet):
    """
    Gestión de registros diarios de horas (TimesheetEntry).

    GET    /api/v1/proyectos/timesheets/                                 — listar mis timesheets
    POST   /api/v1/proyectos/timesheets/                                 — crear registro manual
    PATCH  /api/v1/proyectos/timesheets/{id}/                            — editar (no validado)
    DELETE /api/v1/proyectos/timesheets/{id}/                            — eliminar (no validado)
    GET    /api/v1/proyectos/timesheets/mis_horas/?fecha_inicio=&fecha_fin=
    POST   /api/v1/proyectos/timesheets/{id}/validar/
    """
    serializer_class   = TimesheetEntrySerializer
    permission_classes = [CanAccessProyectos]

    def get_queryset(self):
        company = getattr(self.request.user, 'company', None)
        qs = TimesheetEntry.objects.select_related(
            'tarea', 'usuario', 'validado_por',
        ).filter(usuario=self.request.user)
        if company:
            qs = qs.filter(company=company)
        return qs

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def list(self, request):
        """GET /api/v1/proyectos/timesheets/"""
        qs = self.get_queryset()
        tarea_id = request.query_params.get('tarea')
        if tarea_id:
            qs = qs.filter(tarea_id=tarea_id)
        validado = request.query_params.get('validado')
        if validado is not None:
            qs = qs.filter(validado=(validado.lower() == 'true'))
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin    = request.query_params.get('fecha_fin')
        if fecha_inicio:
            qs = qs.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            qs = qs.filter(fecha__lte=fecha_fin)
        return Response(self.get_serializer(qs, many=True).data)

    def create(self, request):
        """POST /api/v1/proyectos/timesheets/"""
        ser = TimesheetEntryCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        company = getattr(request.user, 'company', None)
        try:
            entry = TimesheetEntryService.registrar_horas(
                tarea_id=str(d['tarea_id']),
                usuario=request.user,
                fecha=d['fecha'],
                horas=d['horas'],
                descripcion=d.get('descripcion', ''),
                company=company,
            )
        except (ValidationError, Exception) as exc:
            msg = exc.message if hasattr(exc, 'message') else str(exc)
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            TimesheetEntrySerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, pk=None):
        """PATCH /api/v1/proyectos/timesheets/{id}/"""
        company = getattr(request.user, 'company', None)
        try:
            entry = TimesheetEntry.objects.get(
                id=pk, usuario=request.user, company=company,
            )
        except TimesheetEntry.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if entry.validado:
            return Response(
                {'detail': 'No se puede editar un registro ya validado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = TimesheetEntrySerializer(entry, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def destroy(self, request, pk=None):
        """DELETE /api/v1/proyectos/timesheets/{id}/"""
        try:
            TimesheetEntryService.eliminar_entry(pk, request.user)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='mis_horas')
    def mis_horas(self, request):
        """GET /api/v1/proyectos/timesheets/mis_horas/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD"""
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin    = request.query_params.get('fecha_fin')
        if not fecha_inicio or not fecha_fin:
            return Response(
                {'detail': 'Se requieren fecha_inicio y fecha_fin (YYYY-MM-DD).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            from datetime import date
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
        except ValueError:
            return Response(
                {'detail': 'Formato de fecha inválido. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        company = getattr(request.user, 'company', None)
        qs = TimesheetEntryService.mis_horas(request.user, fi, ff, company)
        return Response(TimesheetEntrySerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='validar')
    def validar(self, request, pk=None):
        """POST /api/v1/proyectos/timesheets/{id}/validar/"""
        try:
            entry = TimesheetEntryService.validar_timesheet(pk, request.user)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(TimesheetEntrySerializer(entry).data)


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #4 — RESOURCE MANAGEMENT VIEWS  (BK-19 a BK-24)
# ──────────────────────────────────────────────────────────────────────────────

from apps.proyectos.resource_services import (
    assign_resource_to_task,
    remove_resource_from_task,
    detect_overallocation_conflicts,
    calculate_user_workload,
    get_team_availability_timeline,
    set_user_capacity,
    register_availability,
    approve_availability,
)


def _parse_date(value: str, field_name: str):
    """Parsea una fecha ISO 8601 y devuelve datetime.date. Lanza ValidationError si es inválida."""
    from datetime import date as date_type
    try:
        return date_type.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValidationError({field_name: f'Formato inválido. Use YYYY-MM-DD.'})


class ResourceAssignmentViewSet(viewsets.ViewSet):
    """
    BK-19 — CRUD de asignaciones de recursos, anidado bajo una tarea.

    Rutas:
      GET    /api/v1/projects/tasks/{task_pk}/assignments/
      POST   /api/v1/projects/tasks/{task_pk}/assignments/
      GET    /api/v1/projects/tasks/{task_pk}/assignments/{pk}/
      DELETE /api/v1/projects/tasks/{task_pk}/assignments/{pk}/
      GET    /api/v1/projects/tasks/{task_pk}/assignments/check-overallocation/
    """
    permission_classes = [CanAccessProyectos]

    def _get_tarea(self, request, task_pk):
        company = getattr(request.user, 'company', None)
        try:
            return Task.objects.select_related('proyecto').get(
                id=task_pk, company=company
            )
        except Task.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Tarea no encontrada.')

    def list(self, request, task_pk=None):
        """GET /api/v1/projects/tasks/{task_pk}/assignments/"""
        tarea   = self._get_tarea(request, task_pk)
        company = getattr(request.user, 'company', None)
        qs = ResourceAssignment.objects.filter(
            company=company, tarea=tarea
        ).select_related('usuario').order_by('fecha_inicio')
        return Response(ResourceAssignmentListSerializer(qs, many=True).data)

    def create(self, request, task_pk=None):
        """POST /api/v1/projects/tasks/{task_pk}/assignments/"""
        tarea      = self._get_tarea(request, task_pk)
        serializer = ResourceAssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            asignacion = assign_resource_to_task(
                tarea=tarea,
                usuario_id=str(d['usuario_id']),
                porcentaje_asignacion=d['porcentaje_asignacion'],
                fecha_inicio=d['fecha_inicio'],
                fecha_fin=d['fecha_fin'],
                notas=d.get('notas', ''),
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ResourceAssignmentDetailSerializer(asignacion).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None, task_pk=None):
        """GET /api/v1/projects/tasks/{task_pk}/assignments/{pk}/"""
        self._get_tarea(request, task_pk)
        company = getattr(request.user, 'company', None)
        try:
            asignacion = ResourceAssignment.objects.select_related(
                'usuario', 'tarea'
            ).get(id=pk, company=company)
        except ResourceAssignment.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Asignación no encontrada.')
        return Response(ResourceAssignmentDetailSerializer(asignacion).data)

    def destroy(self, request, pk=None, task_pk=None):
        """DELETE /api/v1/projects/tasks/{task_pk}/assignments/{pk}/ — soft delete"""
        self._get_tarea(request, task_pk)
        company = getattr(request.user, 'company', None)
        try:
            remove_resource_from_task(
                asignacion_id=str(pk),
                company_id=str(company.id),
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='check-overallocation')
    def check_overallocation(self, request, task_pk=None):
        """
        GET /api/v1/projects/tasks/{task_pk}/assignments/check-overallocation/
        Query params: usuario_id, start_date, end_date, threshold (opcional)
        """
        usuario_id  = request.query_params.get('usuario_id')
        start_str   = request.query_params.get('start_date')
        end_str     = request.query_params.get('end_date')
        threshold   = request.query_params.get('threshold', '100.00')

        if not all([usuario_id, start_str, end_str]):
            return Response(
                {'detail': 'Se requieren usuario_id, start_date y end_date.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = _parse_date(start_str, 'start_date')
            end_date   = _parse_date(end_str,   'end_date')
            th_decimal = Decimal(threshold)
        except (ValidationError, InvalidOperation):
            return Response(
                {'detail': 'Parámetros inválidos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company    = getattr(request.user, 'company', None)
        conflicts  = detect_overallocation_conflicts(
            usuario_id=usuario_id,
            company_id=str(company.id),
            start_date=start_date,
            end_date=end_date,
            threshold=th_decimal,
        )

        data = [
            {
                'fecha':            str(c.fecha),
                'porcentaje_total': str(c.porcentaje_total),
                'asignaciones':     c.asignaciones,
            }
            for c in conflicts
        ]
        return Response({'conflictos': data, 'total': len(data)})


class ResourceCapacityViewSet(viewsets.ViewSet):
    """
    BK-20 — CRUD de capacidad laboral de usuarios.

    Rutas:
      GET    /api/v1/projects/resources/capacity/
      POST   /api/v1/projects/resources/capacity/
      GET    /api/v1/projects/resources/capacity/{pk}/
      PATCH  /api/v1/projects/resources/capacity/{pk}/
      DELETE /api/v1/projects/resources/capacity/{pk}/
    """
    permission_classes = [CanAccessProyectos]

    def _get_company(self, request):
        return getattr(request.user, 'company', None)

    def list(self, request):
        """GET — filtra por usuario_id si se pasa como query param."""
        company    = self._get_company(request)
        qs = ResourceCapacity.objects.filter(
            company=company
        ).select_related('usuario').order_by('usuario__last_name', 'fecha_inicio')

        usuario_id = request.query_params.get('usuario_id')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)

        return Response(ResourceCapacitySerializer(qs, many=True).data)

    def create(self, request):
        company    = self._get_company(request)
        serializer = ResourceCapacitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            capacidad = set_user_capacity(
                usuario_id=str(d['usuario'].id),
                company_id=str(company.id),
                horas_por_semana=d['horas_por_semana'],
                fecha_inicio=d['fecha_inicio'],
                fecha_fin=d.get('fecha_fin'),
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ResourceCapacitySerializer(capacidad).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        company = self._get_company(request)
        try:
            capacidad = ResourceCapacity.objects.select_related('usuario').get(
                id=pk, company=company
            )
        except ResourceCapacity.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Capacidad no encontrada.')
        return Response(ResourceCapacitySerializer(capacidad).data)

    def partial_update(self, request, pk=None):
        company = self._get_company(request)
        try:
            ResourceCapacity.objects.get(id=pk, company=company)
        except ResourceCapacity.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Capacidad no encontrada.')

        serializer = ResourceCapacitySerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            capacidad = set_user_capacity(
                usuario_id=str(d['usuario'].id) if 'usuario' in d else None,
                company_id=str(company.id),
                horas_por_semana=d.get('horas_por_semana'),
                fecha_inicio=d.get('fecha_inicio'),
                fecha_fin=d.get('fecha_fin'),
                capacity_id=str(pk),
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(ResourceCapacitySerializer(capacidad).data)

    def destroy(self, request, pk=None):
        company = self._get_company(request)
        updated = ResourceCapacity.objects.filter(
            id=pk, company=company
        ).update(activo=False)
        if not updated:
            from rest_framework.exceptions import NotFound
            raise NotFound('Capacidad no encontrada.')
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResourceAvailabilityViewSet(viewsets.ViewSet):
    """
    BK-21 — CRUD de ausencias + acción de aprobación.

    Rutas:
      GET    /api/v1/projects/resources/availability/
      POST   /api/v1/projects/resources/availability/
      GET    /api/v1/projects/resources/availability/{pk}/
      DELETE /api/v1/projects/resources/availability/{pk}/
      POST   /api/v1/projects/resources/availability/{pk}/approve/
    """
    permission_classes = [CanAccessProyectos]

    def _get_company(self, request):
        return getattr(request.user, 'company', None)

    def list(self, request):
        """GET — query params: usuario_id, aprobado, tipo."""
        company = self._get_company(request)
        qs = ResourceAvailability.objects.filter(
            company=company
        ).select_related('usuario', 'aprobado_por').order_by('-fecha_inicio')

        usuario_id = request.query_params.get('usuario_id')
        aprobado   = request.query_params.get('aprobado')
        tipo       = request.query_params.get('tipo')

        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)
        if aprobado is not None:
            qs = qs.filter(aprobado=(aprobado.lower() == 'true'))
        if tipo:
            qs = qs.filter(tipo=tipo)

        return Response(ResourceAvailabilitySerializer(qs, many=True).data)

    def create(self, request):
        company    = self._get_company(request)
        serializer = ResourceAvailabilityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            ausencia = register_availability(
                usuario_id=str(d['usuario_id']),
                company_id=str(company.id),
                tipo=d['tipo'],
                fecha_inicio=d['fecha_inicio'],
                fecha_fin=d['fecha_fin'],
                descripcion=d.get('descripcion', ''),
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ResourceAvailabilitySerializer(ausencia).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        company = self._get_company(request)
        try:
            ausencia = ResourceAvailability.objects.select_related(
                'usuario', 'aprobado_por'
            ).get(id=pk, company=company)
        except ResourceAvailability.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Ausencia no encontrada.')
        return Response(ResourceAvailabilitySerializer(ausencia).data)

    def destroy(self, request, pk=None):
        company = self._get_company(request)
        updated = ResourceAvailability.objects.filter(
            id=pk, company=company
        ).update(activo=False)
        if not updated:
            from rest_framework.exceptions import NotFound
            raise NotFound('Ausencia no encontrada.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """POST /api/v1/projects/resources/availability/{pk}/approve/
        Body: { "aprobar": true|false }
        """
        company    = self._get_company(request)
        aprobar_raw = request.data.get('aprobar', True)
        # Normalizar: string 'false'/'0' → False; cualquier otro truthy → True
        if isinstance(aprobar_raw, str):
            aprobar = aprobar_raw.lower() not in ('false', '0', 'no', '')
        else:
            aprobar = bool(aprobar_raw)

        try:
            ausencia = approve_availability(
                ausencia_id=str(pk),
                company_id=str(company.id),
                aprobador_id=str(request.user.id),
                aprobar=aprobar,
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(ResourceAvailabilitySerializer(ausencia).data)


class WorkloadView(APIView):
    """
    BK-22 — Carga de trabajo de un usuario en un período.

    GET /api/v1/projects/resources/workload/
    Query params: usuario_id (req), start_date (req), end_date (req)
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request):
        usuario_id = request.query_params.get('usuario_id')
        start_str  = request.query_params.get('start_date')
        end_str    = request.query_params.get('end_date')

        if not all([usuario_id, start_str, end_str]):
            return Response(
                {'detail': 'Se requieren usuario_id, start_date y end_date.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = _parse_date(start_str, 'start_date')
            end_date   = _parse_date(end_str,   'end_date')
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        company = getattr(request.user, 'company', None)

        try:
            workload = calculate_user_workload(
                usuario_id=usuario_id,
                company_id=str(company.id),
                start_date=start_date,
                end_date=end_date,
            )
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'usuario_id':            workload.usuario_id,
            'periodo_inicio':        str(workload.periodo_inicio),
            'periodo_fin':           str(workload.periodo_fin),
            'horas_capacidad':       str(workload.horas_capacidad),
            'horas_asignadas':       str(workload.horas_asignadas),
            'horas_registradas':     str(workload.horas_registradas),
            'porcentaje_utilizacion': str(workload.porcentaje_utilizacion),
            'conflictos':            workload.conflictos,
        }
        serializer = WorkloadSummarySerializer(data=data)
        serializer.is_valid()
        return Response(serializer.data)


class TeamAvailabilityView(APIView):
    """
    BK-23 — Timeline de disponibilidad del equipo de un proyecto.

    GET /api/v1/projects/{proyecto_pk}/team-availability/
    Query params: start_date (req), end_date (req)
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, proyecto_pk=None):
        start_str = request.query_params.get('start_date')
        end_str   = request.query_params.get('end_date')

        if not all([start_str, end_str]):
            return Response(
                {'detail': 'Se requieren start_date y end_date.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = _parse_date(start_str, 'start_date')
            end_date   = _parse_date(end_str,   'end_date')
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        company = getattr(request.user, 'company', None)

        timeline = get_team_availability_timeline(
            proyecto_id=str(proyecto_pk),
            company_id=str(company.id),
            start_date=start_date,
            end_date=end_date,
        )

        data = [
            {
                'usuario_id':     t.usuario_id,
                'usuario_nombre': t.usuario_nombre,
                'usuario_email':  t.usuario_email,
                'asignaciones':   t.asignaciones,
                'ausencias':      t.ausencias,
            }
            for t in timeline
        ]
        return Response(data)


class UserCalendarView(APIView):
    """
    BK-24 — Calendario de asignaciones y ausencias de un usuario.

    GET /api/v1/projects/resources/calendar/
    Query params: usuario_id (req), start_date (req), end_date (req)

    Retorna los mismos datos que WorkloadView + la lista detallada de eventos
    (asignaciones + ausencias) para renderizar en el calendario mensual.
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request):
        usuario_id = request.query_params.get('usuario_id')
        start_str  = request.query_params.get('start_date')
        end_str    = request.query_params.get('end_date')

        if not all([usuario_id, start_str, end_str]):
            return Response(
                {'detail': 'Se requieren usuario_id, start_date y end_date.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_date = _parse_date(start_str, 'start_date')
            end_date   = _parse_date(end_str,   'end_date')
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        company = getattr(request.user, 'company', None)

        # Asignaciones activas en el período
        asignaciones = list(
            ResourceAssignment.objects.filter(
                company=company,
                usuario_id=usuario_id,
                activo=True,
                fecha_inicio__lte=end_date,
                fecha_fin__gte=start_date,
            ).select_related('tarea', 'tarea__proyecto').order_by('fecha_inicio')
        )

        # Ausencias aprobadas en el período
        ausencias = list(
            ResourceAvailability.objects.filter(
                company=company,
                usuario_id=usuario_id,
                aprobado=True,
                activo=True,
                fecha_inicio__lte=end_date,
                fecha_fin__gte=start_date,
            ).order_by('fecha_inicio')
        )

        return Response({
            'usuario_id':    usuario_id,
            'periodo_inicio': str(start_date),
            'periodo_fin':    str(end_date),
            'asignaciones': [
                {
                    'id':                    str(a.id),
                    'tarea_id':              str(a.tarea_id),
                    'tarea_codigo':          a.tarea.codigo,
                    'tarea_nombre':          a.tarea.nombre,
                    'proyecto_id':           str(a.tarea.proyecto_id),
                    'proyecto_codigo':       a.tarea.proyecto.codigo,
                    'porcentaje_asignacion': str(a.porcentaje_asignacion),
                    'fecha_inicio':          str(a.fecha_inicio),
                    'fecha_fin':             str(a.fecha_fin),
                    'notas':                 a.notas,
                }
                for a in asignaciones
            ],
            'ausencias': [
                {
                    'id':           str(av.id),
                    'tipo':         av.tipo,
                    'tipo_display': av.get_tipo_display(),
                    'fecha_inicio': str(av.fecha_inicio),
                    'fecha_fin':    str(av.fecha_fin),
                    'descripcion':  av.descripcion,
                }
                for av in ausencias
            ],
        })

