"""
SaiSuite — Proyectos: Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
import logging
import re
from decimal import Decimal
from rest_framework import serializers

# Patrón compartido con el management command fix_cliente_id.
# Detecta UUIDs v4 que no deben guardarse en cliente_id.
_UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)
from apps.proyectos.models import (
    Project, Phase, ProjectStakeholder, AccountingDocument, Milestone,
    Activity, ProjectActivity, SaiopenActivity, TaskTag, Task,
    WorkSession, TimesheetEntry, TaskDependency, ModuleSettings,
    ProjectStatus, PhaseStatus, StakeholderRole, DocumentType,
    MeasurementMode, ActivityType, DependencyType,
    ResourceAssignment, ResourceCapacity, ResourceAvailability, AvailabilityType,
    PlantillaProyecto, PlantillaFase, PlantillaTarea,
    ProjectType,
)

logger = logging.getLogger(__name__)


class UserSummarySerializer(serializers.Serializer):
    """Representación mínima del usuario para lectura en proyectos."""
    id         = serializers.UUIDField()
    email      = serializers.EmailField()
    full_name  = serializers.CharField()


class PhaseListSerializer(serializers.ModelSerializer):
    """Serializer de listado de fases — campos mínimos."""
    presupuesto_total = serializers.SerializerMethodField()

    class Meta:
        model  = Phase
        fields = [
            'id', 'nombre', 'orden', 'estado', 'porcentaje_avance',
            'presupuesto_total', 'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_presupuesto_total(self, obj: Phase) -> str:
        total = (
            obj.presupuesto_mano_obra
            + obj.presupuesto_materiales
            + obj.presupuesto_subcontratos
            + obj.presupuesto_equipos
            + obj.presupuesto_otros
        )
        return str(total)


class PhaseDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de fase — todos los campos."""
    presupuesto_total = serializers.SerializerMethodField()

    class Meta:
        model  = Phase
        fields = [
            'id', 'proyecto', 'nombre', 'descripcion', 'orden', 'estado',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_mano_obra', 'presupuesto_materiales',
            'presupuesto_subcontratos', 'presupuesto_equipos',
            'presupuesto_otros', 'presupuesto_total',
            'porcentaje_avance', 'activo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at', 'updated_at']

    def get_presupuesto_total(self, obj: Phase) -> str:
        total = (
            obj.presupuesto_mano_obra
            + obj.presupuesto_materiales
            + obj.presupuesto_subcontratos
            + obj.presupuesto_equipos
            + obj.presupuesto_otros
        )
        return str(total)


class PhaseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para fases."""

    class Meta:
        model  = Phase
        fields = [
            'nombre', 'descripcion', 'orden',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_mano_obra', 'presupuesto_materiales',
            'presupuesto_subcontratos', 'presupuesto_equipos',
            'presupuesto_otros', 'porcentaje_avance',
        ]

    def validate_porcentaje_avance(self, value):
        if not (Decimal('0') <= value <= Decimal('100')):
            raise serializers.ValidationError(
                'El porcentaje de avance debe estar entre 0 y 100.'
            )
        return value

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio_planificada')
        fin    = attrs.get('fecha_fin_planificada')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {'fecha_fin_planificada': 'La fecha de fin no puede ser anterior a la fecha de inicio.'}
            )
        return attrs


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer de listado de proyectos — campos mínimos para tabla."""
    gerente = UserSummarySerializer(read_only=True)

    class Meta:
        model  = Project
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'estado',
            'cliente_nombre', 'gerente',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'presupuesto_total', 'porcentaje_avance', 'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de proyecto — todos los campos."""
    gerente             = UserSummarySerializer(read_only=True)
    coordinador         = UserSummarySerializer(read_only=True)
    fases_count         = serializers.SerializerMethodField()
    presupuesto_fases_total = serializers.SerializerMethodField()
    cliente_nit         = serializers.SerializerMethodField()

    class Meta:
        model  = Project
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'estado',
            'cliente_id', 'cliente_nombre', 'cliente_nit',
            'gerente', 'coordinador',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_total', 'porcentaje_avance',
            'porcentaje_administracion', 'porcentaje_imprevistos', 'porcentaje_utilidad',
            'saiopen_proyecto_id', 'sincronizado_con_saiopen', 'ultima_sincronizacion',
            'activo', 'fases_count', 'presupuesto_fases_total',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_fases_count(self, obj: Project) -> int:
        return obj.phases.filter(activo=True).count()

    def get_cliente_nit(self, obj: Project) -> str:
        """
        Retorna el número de identificación real del cliente.
        Si cliente_id ya es un NIT/cédula lo devuelve tal cual.
        Si cliente_id es un UUID (datos legacy), busca el Tercero y devuelve su numero_identificacion.
        """
        cid = obj.cliente_id or ''
        if not cid:
            return ''
        if _UUID_PATTERN.match(cid):
            from apps.terceros.models import Tercero
            try:
                tercero = Tercero.objects.filter(company=obj.company, id=cid).values('numero_identificacion').first()
                return tercero['numero_identificacion'] if tercero else cid
            except Exception:
                return cid
        return cid

    def get_presupuesto_fases_total(self, obj: Project) -> str:
        from django.db.models import Sum
        result = obj.phases.filter(activo=True).aggregate(
            total=Sum('presupuesto_mano_obra')
                + Sum('presupuesto_materiales')
                + Sum('presupuesto_subcontratos')
                + Sum('presupuesto_equipos')
                + Sum('presupuesto_otros')
        )
        total = result.get('total') or Decimal('0')
        return str(total)


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para proyectos."""
    # codigo es opcional — el service lo genera automáticamente si no se provee
    codigo          = serializers.CharField(max_length=50, required=False, allow_blank=True)
    gerente         = serializers.UUIDField()
    coordinador     = serializers.UUIDField(required=False, allow_null=True)
    # consecutivo_id: UUID del ConfiguracionConsecutivo a usar para generar el código
    consecutivo_id  = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Project
        fields = [
            'codigo', 'nombre', 'tipo',
            'cliente_id', 'cliente_nombre',
            'gerente', 'coordinador',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_total',
            'porcentaje_administracion', 'porcentaje_imprevistos', 'porcentaje_utilidad',
            'consecutivo_id',
        ]

    def validate_cliente_id(self, value: str) -> str:
        """
        Rechaza valores con formato UUID en cliente_id.
        El campo debe contener el número de identificación del cliente (NIT,
        cédula, etc.), no el UUID interno del Tercero en la BD.
        Solo valida cuando el campo tiene contenido (admite blank/null según modelo).
        """
        if value and _UUID_PATTERN.match(value):
            raise serializers.ValidationError(
                'cliente_id debe ser el número de identificación del cliente '
                '(NIT, cédula, etc.), no un UUID interno.'
            )
        return value

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio_planificada')
        fin    = attrs.get('fecha_fin_planificada')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {'fecha_fin_planificada': 'La fecha de fin no puede ser anterior a la fecha de inicio.'}
            )
        presupuesto = attrs.get('presupuesto_total', Decimal('0'))
        if presupuesto < Decimal('0'):
            raise serializers.ValidationError(
                {'presupuesto_total': 'El presupuesto total no puede ser negativo.'}
            )
        return attrs


class ChangeStatusSerializer(serializers.Serializer):
    """Serializer para la acción de cambio de estado del proyecto."""
    nuevo_estado = serializers.ChoiceField(choices=ProjectStatus.choices)
    forzar       = serializers.BooleanField(
        default=False,
        required=False,
        help_text='Permite cerrar proyecto con fases incompletas (requiere company_admin)',
    )


# ──────────────────────────────────────────────
# ProjectStakeholder
# ──────────────────────────────────────────────

class ProjectStakeholderSerializer(serializers.ModelSerializer):
    """Serializer de lectura para terceros vinculados al proyecto."""
    rol_display  = serializers.CharField(source='get_rol_display', read_only=True)
    fase_nombre  = serializers.CharField(source='fase.nombre', read_only=True, default=None)
    tercero_fk_nombre = serializers.CharField(
        source='tercero_fk.nombre_completo', read_only=True, default=None,
    )

    class Meta:
        model  = ProjectStakeholder
        fields = [
            'id', 'proyecto', 'tercero_id', 'tercero_nombre',
            'rol', 'rol_display', 'fase', 'fase_nombre',
            'tercero_fk', 'tercero_fk_nombre',
            'activo', 'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at', 'tercero_fk_nombre']


class ProjectStakeholderCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para vincular un tercero al proyecto."""

    class Meta:
        model  = ProjectStakeholder
        fields = ['tercero_id', 'tercero_nombre', 'rol', 'fase', 'tercero_fk']

    def validate_fase(self, fase):
        """La fase debe pertenecer al mismo proyecto."""
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase


# ──────────────────────────────────────────────
# AccountingDocument
# ──────────────────────────────────────────────

class AccountingDocumentListSerializer(serializers.ModelSerializer):
    """Serializer de listado de documentos contables — campos mínimos."""
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', read_only=True
    )

    class Meta:
        model  = AccountingDocument
        fields = [
            'id', 'tipo_documento', 'tipo_documento_display',
            'saiopen_doc_id', 'numero_documento', 'fecha_documento',
            'tercero_nombre', 'valor_neto',
            'sincronizado_desde_saiopen',
        ]
        read_only_fields = fields


class AccountingDocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de documento contable — todos los campos."""
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', read_only=True
    )

    class Meta:
        model  = AccountingDocument
        fields = [
            'id', 'proyecto', 'fase',
            'saiopen_doc_id', 'tipo_documento', 'tipo_documento_display',
            'numero_documento', 'fecha_documento',
            'tercero_id', 'tercero_nombre',
            'valor_bruto', 'valor_descuento', 'valor_neto',
            'observaciones', 'sincronizado_desde_saiopen',
        ]
        read_only_fields = fields


# ──────────────────────────────────────────────
# Milestone
# ──────────────────────────────────────────────

class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer de lectura para hitos del proyecto."""
    fase_nombre = serializers.CharField(source='fase.nombre', read_only=True, default=None)

    class Meta:
        model  = Milestone
        fields = [
            'id', 'proyecto', 'fase', 'fase_nombre',
            'nombre', 'descripcion',
            'porcentaje_proyecto', 'valor_facturar',
            'facturable', 'facturado',
            'documento_factura', 'fecha_facturacion',
            'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'facturado', 'documento_factura', 'fecha_facturacion', 'created_at']


class MilestoneCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para crear un hito."""

    class Meta:
        model  = Milestone
        fields = ['nombre', 'descripcion', 'fase', 'porcentaje_proyecto', 'valor_facturar', 'facturable']

    def validate_porcentaje_proyecto(self, value):
        if not (Decimal('0') < value <= Decimal('100')):
            raise serializers.ValidationError(
                'El porcentaje debe ser mayor a 0 y máximo 100.'
            )
        return value

    def validate_valor_facturar(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError(
                'El valor a facturar debe ser mayor a cero.'
            )
        return value

    def validate_fase(self, fase):
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase


class GenerateInvoiceSerializer(serializers.Serializer):
    """Serializer para la acción de generar factura desde un hito."""
    confirmar = serializers.BooleanField(
        help_text='Debe ser true para confirmar la solicitud de facturación.'
    )

    def validate_confirmar(self, value):
        if not value:
            raise serializers.ValidationError(
                'Debe confirmar la solicitud de facturación.'
            )
        return value


# ──────────────────────────────────────────────
# Activity — catálogo global
# ──────────────────────────────────────────────

class ActivityListSerializer(serializers.ModelSerializer):
    """Serializer de listado de actividades — campos mínimos para tabla."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Activity
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'tipo_display',
            'unidad_medida', 'costo_unitario_base', 'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ActivityDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de actividad — todos los campos."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Activity
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'tipo', 'tipo_display', 'unidad_medida', 'costo_unitario_base',
            'saiopen_actividad_id', 'sincronizado_con_saiopen',
            'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActivityCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para el catálogo de actividades."""
    codigo         = serializers.CharField(max_length=50, required=False, allow_blank=True)
    # consecutivo_id: UUID del ConfiguracionConsecutivo a usar para generar el código
    consecutivo_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Activity
        fields = [
            'codigo', 'nombre', 'descripcion',
            'tipo', 'unidad_medida', 'costo_unitario_base',
            'consecutivo_id',
        ]

    def validate_costo_unitario_base(self, value):
        from decimal import Decimal
        if value < Decimal('0'):
            raise serializers.ValidationError('El costo unitario no puede ser negativo.')
        return value


# ──────────────────────────────────────────────
# ProjectActivity — asignación a proyecto
# ──────────────────────────────────────────────

class ProjectActivitySerializer(serializers.ModelSerializer):
    """Serializer de lectura para actividades asignadas a un proyecto."""
    actividad_codigo       = serializers.CharField(source='actividad.codigo', read_only=True)
    actividad_nombre       = serializers.CharField(source='actividad.nombre', read_only=True)
    actividad_unidad_medida = serializers.CharField(source='actividad.unidad_medida', read_only=True)
    actividad_tipo         = serializers.CharField(source='actividad.tipo', read_only=True)
    fase_nombre            = serializers.CharField(source='fase.nombre', read_only=True, default=None)
    presupuesto_total      = serializers.SerializerMethodField()

    class Meta:
        model  = ProjectActivity
        fields = [
            'id', 'proyecto', 'actividad',
            'actividad_codigo', 'actividad_nombre',
            'actividad_unidad_medida', 'actividad_tipo',
            'fase', 'fase_nombre',
            'cantidad_planificada', 'cantidad_ejecutada',
            'costo_unitario', 'presupuesto_total',
            'porcentaje_avance', 'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at']

    def get_presupuesto_total(self, obj: ProjectActivity) -> str:
        return str(obj.presupuesto_total)


class ProjectActivityCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para asignar/actualizar actividades en un proyecto.
    porcentaje_avance es auto-calculado por señales — no se acepta en escritura.
    """

    class Meta:
        model  = ProjectActivity
        fields = [
            'actividad', 'fase',
            'cantidad_planificada', 'cantidad_ejecutada',
            'costo_unitario',
        ]

    def validate_fase(self, fase):
        """La fase debe pertenecer al mismo proyecto."""
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase

    def validate_cantidad_planificada(self, value):
        from decimal import Decimal
        if value < Decimal('0'):
            raise serializers.ValidationError('La cantidad no puede ser negativa.')
        return value

    def validate(self, attrs):
        cantidad_ejecutada = attrs.get('cantidad_ejecutada')
        proyecto = self.context.get('proyecto')
        if (
            cantidad_ejecutada is not None
            and Decimal(str(cantidad_ejecutada)) > Decimal('0')
            and proyecto
            and proyecto.estado not in ('in_progress', 'suspended')
        ):
            raise serializers.ValidationError({
                'cantidad_ejecutada': (
                    'Solo se puede registrar cantidad ejecutada cuando el proyecto '
                    'está en ejecución o suspendido.'
                )
            })
        return attrs


# ──────────────────────────────────────────────
# ModuleSettings
# ──────────────────────────────────────────────

class ModuleSettingsSerializer(serializers.ModelSerializer):
    """Serializer para la configuración del módulo de proyectos."""

    class Meta:
        model  = ModuleSettings
        fields = [
            'requiere_sync_saiopen_para_ejecucion',
            'dias_alerta_vencimiento',
            'modo_timesheet',
        ]


# ──────────────────────────────────────────────
# SaiopenActivity — catálogo
# ──────────────────────────────────────────────

class SaiopenActivitySerializer(serializers.ModelSerializer):
    """Serializer de listado de SaiopenActivity — campos mínimos para autocomplete."""
    unidad_medida_display = serializers.CharField(source='get_unidad_medida_display', read_only=True)

    class Meta:
        model  = SaiopenActivity
        fields = [
            'id', 'codigo', 'nombre', 'unidad_medida', 'unidad_medida_display',
            'costo_unitario_base', 'activo',
        ]
        read_only_fields = ['id']


class SaiopenActivityDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de SaiopenActivity — todos los campos."""
    unidad_medida_display = serializers.CharField(source='get_unidad_medida_display', read_only=True)

    class Meta:
        model  = SaiopenActivity
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'unidad_medida', 'unidad_medida_display',
            'costo_unitario_base', 'activo',
            'saiopen_actividad_id', 'sincronizado_con_saiopen',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SaiopenActivityCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para SaiopenActivity."""
    codigo = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model  = SaiopenActivity
        fields = [
            'codigo', 'nombre', 'descripcion',
            'unidad_medida', 'costo_unitario_base',
        ]

    def validate_costo_unitario_base(self, value):
        if value < Decimal('0'):
            raise serializers.ValidationError('El costo unitario no puede ser negativo.')
        return value


# ──────────────────────────────────────────────
# Task system
# ──────────────────────────────────────────────

class TaskTagSerializer(serializers.ModelSerializer):
    """Serializer para tags de tareas."""

    class Meta:
        model = TaskTag
        fields = ['id', 'nombre', 'color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskDependencySerializer(serializers.ModelSerializer):
    """
    Serializer para TaskDependency.
    Incluye datos básicos de predecesora/sucesora para el frontend.
    """
    tarea_predecesora_detail = serializers.SerializerMethodField()
    tarea_sucesora_detail    = serializers.SerializerMethodField()

    class Meta:
        model  = TaskDependency
        fields = [
            'id',
            'tarea_predecesora', 'tarea_predecesora_detail',
            'tarea_sucesora', 'tarea_sucesora_detail',
            'tipo_dependencia',
            'retraso_dias',
        ]
        read_only_fields = ['id']

    def get_tarea_predecesora_detail(self, obj: TaskDependency) -> dict:
        t = obj.tarea_predecesora
        return {'id': str(t.id), 'nombre': t.nombre, 'codigo': t.codigo}

    def get_tarea_sucesora_detail(self, obj: TaskDependency) -> dict:
        t = obj.tarea_sucesora
        return {'id': str(t.id), 'nombre': t.nombre, 'codigo': t.codigo}


class TaskDependencyCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para crear dependencias entre tareas."""

    class Meta:
        model  = TaskDependency
        fields = [
            'tarea_predecesora', 'tarea_sucesora',
            'tipo_dependencia', 'retraso_dias',
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para Task con nested subtareas y followers.
    """

    # Campos calculados (read-only)
    es_vencida          = serializers.BooleanField(read_only=True)
    tiene_subtareas     = serializers.BooleanField(read_only=True)
    nivel_jerarquia     = serializers.IntegerField(read_only=True)
    progreso_porcentaje = serializers.ReadOnlyField()
    es_camino_critico   = serializers.SerializerMethodField()

    # Nested serializers para lectura
    responsable_detail        = serializers.SerializerMethodField()
    proyecto_detail           = serializers.SerializerMethodField()
    fase_detail               = serializers.SerializerMethodField()
    cliente_detail            = serializers.SerializerMethodField()
    actividad_saiopen_detail  = serializers.SerializerMethodField()
    actividad_proyecto_detail = serializers.SerializerMethodField()
    tags_detail               = TaskTagSerializer(source='tags', many=True, read_only=True)
    subtareas_detail          = serializers.SerializerMethodField()
    followers_detail          = serializers.SerializerMethodField()
    modo_medicion             = serializers.ReadOnlyField()
    predecesoras_detail       = serializers.SerializerMethodField()
    sucesoras_detail          = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'proyecto', 'proyecto_detail',
            'fase', 'fase_detail',
            'tarea_padre',
            'cliente', 'cliente_detail',
            'actividad_saiopen', 'actividad_saiopen_detail',
            'actividad_proyecto', 'actividad_proyecto_detail',
            'cantidad_objetivo', 'cantidad_registrada',
            'responsable', 'responsable_detail',
            'followers', 'followers_detail',
            'prioridad', 'tags', 'tags_detail',
            'fecha_inicio', 'fecha_fin', 'fecha_limite',
            'estado', 'porcentaje_completado',
            'horas_estimadas', 'horas_registradas', 'progreso_porcentaje',
            'modo_medicion',
            'es_recurrente', 'frecuencia_recurrencia', 'proxima_generacion',
            'es_vencida', 'tiene_subtareas', 'nivel_jerarquia',
            'es_camino_critico',
            'predecesoras_detail', 'sucesoras_detail',
            'subtareas_detail',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'codigo', 'proyecto', 'es_vencida', 'tiene_subtareas',
            'nivel_jerarquia', 'progreso_porcentaje', 'modo_medicion',
            'es_camino_critico',
            'created_at', 'updated_at',
        ]

    def get_actividad_saiopen_detail(self, obj):
        if obj.actividad_saiopen_id and obj.actividad_saiopen:
            return {
                'id': str(obj.actividad_saiopen.id),
                'codigo': obj.actividad_saiopen.codigo,
                'nombre': obj.actividad_saiopen.nombre,
                'unidad_medida': obj.actividad_saiopen.unidad_medida,
            }
        return None

    def get_actividad_proyecto_detail(self, obj):
        if obj.actividad_proyecto_id and obj.actividad_proyecto:
            ap = obj.actividad_proyecto
            try:
                act = ap.actividad
                return {
                    'id': str(ap.id),
                    'actividad_id': str(act.id),
                    'actividad_codigo': act.codigo,
                    'actividad_nombre': act.nombre,
                    'actividad_unidad_medida': act.unidad_medida or '',
                }
            except Exception:
                return {'id': str(ap.id)}
        return None

    def get_cliente_detail(self, obj):
        if obj.cliente:
            return {
                'id': str(obj.cliente.id),
                'nombre': obj.cliente.nombre_completo,
                'numero_identificacion': obj.cliente.numero_identificacion,
            }
        return None

    def get_responsable_detail(self, obj):
        if obj.responsable:
            return {
                'id': str(obj.responsable.id),
                'nombre': obj.responsable.full_name,
                'email': obj.responsable.email,
            }
        return None

    def get_proyecto_detail(self, obj):
        return {
            'id': str(obj.proyecto.id),
            'nombre': obj.proyecto.nombre,
            'codigo': obj.proyecto.codigo,
        }

    def get_fase_detail(self, obj):
        if obj.fase:
            return {
                'id': str(obj.fase.id),
                'nombre': obj.fase.nombre,
                'orden': obj.fase.orden,
            }
        return None

    def get_followers_detail(self, obj):
        return [
            {
                'id': str(f.id),
                'nombre': f.full_name,
                'email': f.email,
            }
            for f in obj.followers.all()
        ]

    def get_subtareas_detail(self, obj):
        """Nested subtareas (máximo 2 niveles para performance)."""
        if obj.nivel_jerarquia >= 2:
            return []
        subtareas = obj.subtasks.all()
        return TaskDetailSerializer(subtareas, many=True, context=self.context).data

    def get_predecesoras_detail(self, obj):
        deps = obj.predecessors.select_related('tarea_predecesora').all()
        return TaskDependencySerializer(deps, many=True, context=self.context).data

    def get_sucesoras_detail(self, obj):
        deps = obj.successors.select_related('tarea_sucesora').all()
        return TaskDependencySerializer(deps, many=True, context=self.context).data

    def get_es_camino_critico(self, obj) -> bool:
        """
        Calcula si esta tarea está en el camino crítico de su proyecto.
        Se cachea en el contexto del request para no recalcular por cada tarea.
        """
        from apps.proyectos.tarea_services import DependencyService

        request = self.context.get('request')
        company = getattr(request.user, 'effective_company', None) if request else None
        if not company:
            return False

        cache_key = f'camino_critico_{obj.proyecto_id}'
        cache = self.context.setdefault('_cache', {})

        if cache_key not in cache:
            criticas = DependencyService.calcular_camino_critico(
                str(obj.proyecto_id), company
            )
            cache[cache_key] = set(criticas)

        return str(obj.id) in cache[cache_key]

    def validate(self, data):
        """Validaciones de negocio."""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin    = data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError({
                'fecha_fin': 'Fecha fin debe ser posterior a fecha inicio'
            })

        # Validar tarea_padre a través de la fase (DEC-021)
        tarea_padre = data.get('tarea_padre')
        fase        = data.get('fase')
        if tarea_padre and fase and tarea_padre.proyecto_id != fase.proyecto_id:
            raise serializers.ValidationError({
                'tarea_padre': 'Tarea padre debe pertenecer al mismo proyecto'
            })

        horas_estimadas   = data.get('horas_estimadas', 0)
        horas_registradas = data.get('horas_registradas', 0)
        if horas_estimadas and horas_registradas > horas_estimadas * 2:
            raise serializers.ValidationError({
                'horas_registradas': 'Horas registradas exceden significativamente las estimadas'
            })

        return data

    def create(self, validated_data):
        """Crear tarea y auto-agregar creador y responsable como followers.
        proyecto se auto-deriva de fase.proyecto (DEC-021).
        """
        followers = validated_data.pop('followers', [])
        tags      = validated_data.pop('tags', [])

        # Auto-derivar proyecto desde la fase
        fase = validated_data.get('fase')
        if fase and 'proyecto' not in validated_data:
            validated_data['proyecto'] = fase.proyecto

        tarea = Task.all_objects.create(**validated_data)

        # Auto-agregar creador como follower
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            tarea.followers.add(request.user)

        # Auto-agregar responsable como follower
        if tarea.responsable:
            tarea.followers.add(tarea.responsable)

        # Agregar followers y tags adicionales
        if followers:
            tarea.followers.add(*followers)
        if tags:
            tarea.tags.set(tags)

        return tarea

    def update(self, instance, validated_data):
        followers = validated_data.pop('followers', None)
        tags      = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if followers is not None:
            instance.followers.set(followers)
        if tags is not None:
            instance.tags.set(tags)

        return instance


class TaskListSerializer(serializers.ModelSerializer):
    """Serializer de listado de tareas — campos mínimos para tabla."""
    tags_detail = TaskTagSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'codigo', 'nombre', 'proyecto', 'fase',
            'responsable', 'prioridad', 'estado',
            'fecha_inicio', 'fecha_fin', 'fecha_limite',
            'porcentaje_completado', 'horas_estimadas', 'horas_registradas',
            'es_vencida', 'tiene_subtareas', 'nivel_jerarquia',
            'tags', 'tags_detail',
            'created_at',
        ]
        read_only_fields = ['id', 'codigo', 'created_at']


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para tareas."""

    class Meta:
        model  = Task
        fields = [
            'nombre', 'descripcion',
            'fase', 'tarea_padre',
            'cliente', 'actividad_saiopen', 'actividad_proyecto',
            'cantidad_objetivo',
            'responsable', 'followers',
            'prioridad', 'tags',
            'fecha_inicio', 'fecha_fin', 'fecha_limite',
            'estado', 'porcentaje_completado',
            'horas_estimadas',
            'es_recurrente', 'frecuencia_recurrencia',
        ]

    def validate(self, data):
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin    = data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError({
                'fecha_fin': 'Fecha fin debe ser posterior a fecha inicio'
            })
        return data


class TaskKanbanSerializer(serializers.ModelSerializer):
    """Serializer compacto para vista Kanban de tareas."""
    tags_detail        = TaskTagSerializer(source='tags', many=True, read_only=True)
    responsable_detail = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'codigo', 'nombre',
            'responsable', 'responsable_detail',
            'prioridad', 'estado',
            'fecha_limite', 'es_vencida',
            'porcentaje_completado',
            'tags', 'tags_detail',
        ]
        read_only_fields = ['id', 'codigo']

    def get_responsable_detail(self, obj):
        if obj.responsable:
            return {
                'id': str(obj.responsable.id),
                'nombre': obj.responsable.full_name,
                'email': obj.responsable.email,
            }
        return None


# ──────────────────────────────────────────────
# WorkSession
# ──────────────────────────────────────────────

class WorkSessionSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de trabajo (cronómetro)."""
    duracion_horas = serializers.SerializerMethodField()
    usuario_detail = UserSummarySerializer(source='usuario', read_only=True)
    tarea_detail   = serializers.SerializerMethodField()

    class Meta:
        model = WorkSession
        fields = [
            'id',
            'tarea', 'tarea_detail',
            'usuario', 'usuario_detail',
            'inicio', 'fin',
            'pausas',
            'duracion_segundos', 'duracion_horas',
            'estado', 'notas',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'duracion_segundos', 'duracion_horas',
            'created_at', 'updated_at',
        ]

    def get_duracion_horas(self, obj: WorkSession) -> str:
        return str(obj.duracion_horas.quantize(Decimal('0.01')))

    def get_tarea_detail(self, obj: WorkSession) -> dict:
        return {
            'id':     str(obj.tarea.id),
            'codigo': obj.tarea.codigo,
            'nombre': obj.tarea.nombre,
        }


# ──────────────────────────────────────────────
# TimesheetEntry
# ──────────────────────────────────────────────

class TimesheetEntrySerializer(serializers.ModelSerializer):
    """Serializer completo para registros diarios de horas."""
    tarea_detail       = serializers.SerializerMethodField()
    usuario_detail     = UserSummarySerializer(source='usuario', read_only=True)
    validado_por_detail = serializers.SerializerMethodField()

    class Meta:
        model  = TimesheetEntry
        fields = [
            'id',
            'tarea', 'tarea_detail',
            'usuario', 'usuario_detail',
            'fecha', 'horas', 'descripcion',
            'validado', 'validado_por', 'validado_por_detail', 'fecha_validacion',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id',
            'usuario', 'usuario_detail',
            'validado', 'validado_por', 'validado_por_detail', 'fecha_validacion',
            'created_at', 'updated_at',
        ]

    def validate_horas(self, value):
        if value <= 0:
            raise serializers.ValidationError('Las horas deben ser mayores a 0.')
        if value > 24:
            raise serializers.ValidationError('Las horas no pueden superar 24 por día.')
        return value

    def get_tarea_detail(self, obj: TimesheetEntry) -> dict:
        return {
            'id':     str(obj.tarea.id),
            'codigo': obj.tarea.codigo,
            'nombre': obj.tarea.nombre,
        }

    def get_validado_por_detail(self, obj: TimesheetEntry) -> dict | None:
        if not obj.validado_por:
            return None
        return {
            'id':     str(obj.validado_por.id),
            'nombre': obj.validado_por.full_name or obj.validado_por.email,
        }


class TimesheetEntryCreateSerializer(serializers.Serializer):
    """Serializer para crear/actualizar registros de horas."""
    tarea_id    = serializers.UUIDField()
    fecha       = serializers.DateField()
    horas       = serializers.DecimalField(max_digits=5, decimal_places=2)
    descripcion = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_horas(self, value):
        if value <= 0:
            raise serializers.ValidationError('Las horas deben ser mayores a 0.')
        if value > 24:
            raise serializers.ValidationError('Las horas no pueden superar 24 por día.')
        return value


# ===========================================================================
# FEATURE #4 — RESOURCE MANAGEMENT SERIALIZERS
# ===========================================================================

class ResourceAssignmentListSerializer(serializers.ModelSerializer):
    """
    Serializer de listado para ResourceAssignment.
    Campos mínimos para tablas y calendarios.
    """
    usuario_nombre = serializers.SerializerMethodField()
    usuario_email  = serializers.SerializerMethodField()
    tarea_codigo   = serializers.CharField(source='tarea.codigo', read_only=True)
    tarea_nombre   = serializers.CharField(source='tarea.nombre', read_only=True)

    class Meta:
        model  = ResourceAssignment
        fields = [
            'id', 'tarea', 'tarea_codigo', 'tarea_nombre',
            'usuario', 'usuario_nombre', 'usuario_email',
            'porcentaje_asignacion', 'fecha_inicio', 'fecha_fin',
            'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_usuario_nombre(self, obj: ResourceAssignment) -> str:
        return obj.usuario.full_name or obj.usuario.email

    def get_usuario_email(self, obj: ResourceAssignment) -> str:
        return obj.usuario.email


class ResourceAssignmentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer de detalle para ResourceAssignment.
    Incluye datos completos del usuario y la tarea para la vista de detalle.
    """
    usuario_detail = serializers.SerializerMethodField()
    tarea_detail   = serializers.SerializerMethodField()

    class Meta:
        model  = ResourceAssignment
        fields = [
            'id', 'tarea', 'tarea_detail',
            'usuario', 'usuario_detail',
            'porcentaje_asignacion', 'fecha_inicio', 'fecha_fin',
            'notas', 'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_usuario_detail(self, obj: ResourceAssignment) -> dict:
        return {
            'id':         str(obj.usuario.id),
            'email':      obj.usuario.email,
            'nombre':     obj.usuario.full_name or obj.usuario.email,
        }

    def get_tarea_detail(self, obj: ResourceAssignment) -> dict:
        return {
            'id':      str(obj.tarea.id),
            'codigo':  obj.tarea.codigo,
            'nombre':  obj.tarea.nombre,
            'estado':  obj.tarea.estado,
        }


class ResourceAssignmentCreateSerializer(serializers.Serializer):
    """
    Serializer de escritura para crear/actualizar asignaciones de recursos.
    La lógica de validación de solapamiento y conflictos va en ResourceService.
    """
    usuario_id            = serializers.UUIDField()
    porcentaje_asignacion = serializers.DecimalField(max_digits=5, decimal_places=2)
    fecha_inicio          = serializers.DateField()
    fecha_fin             = serializers.DateField()
    notas                 = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_porcentaje_asignacion(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'El porcentaje de asignación debe ser mayor a 0.'
            )
        if value > 100:
            raise serializers.ValidationError(
                'El porcentaje de asignación no puede superar 100.'
            )
        return value

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio')
        fin    = attrs.get('fecha_fin')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError({
                'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio.'
            })
        return attrs


class ResourceCapacitySerializer(serializers.ModelSerializer):
    """
    Serializer para ResourceCapacity — lectura y escritura.
    La validación de solapamiento de períodos va en ResourceCapacityService.
    """
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = ResourceCapacity
        fields = [
            'id', 'usuario', 'usuario_nombre',
            'horas_por_semana', 'fecha_inicio', 'fecha_fin',
            'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_usuario_nombre(self, obj: ResourceCapacity) -> str:
        return obj.usuario.full_name or obj.usuario.email

    def validate_horas_por_semana(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Las horas por semana deben ser mayores a 0.'
            )
        if value > 168:
            raise serializers.ValidationError(
                'Las horas por semana no pueden superar 168 (7 días × 24h).'
            )
        return value

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio')
        fin    = attrs.get('fecha_fin')
        if inicio and fin and fin <= inicio:
            raise serializers.ValidationError({
                'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
            })
        return attrs


class ResourceAvailabilitySerializer(serializers.ModelSerializer):
    """
    Serializer de lectura para ResourceAvailability.
    """
    usuario_nombre  = serializers.SerializerMethodField()
    tipo_display    = serializers.CharField(source='get_tipo_display', read_only=True)
    aprobado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = ResourceAvailability
        fields = [
            'id', 'usuario', 'usuario_nombre',
            'tipo', 'tipo_display',
            'fecha_inicio', 'fecha_fin', 'descripcion',
            'aprobado', 'aprobado_por', 'aprobado_por_nombre', 'fecha_aprobacion',
            'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'aprobado', 'aprobado_por', 'fecha_aprobacion',
            'created_at', 'updated_at',
        ]

    def get_usuario_nombre(self, obj: ResourceAvailability) -> str:
        return obj.usuario.full_name or obj.usuario.email

    def get_aprobado_por_nombre(self, obj: ResourceAvailability) -> str | None:
        if not obj.aprobado_por:
            return None
        return obj.aprobado_por.full_name or obj.aprobado_por.email


class ResourceAvailabilityCreateSerializer(serializers.Serializer):
    """
    Serializer de escritura para registrar ausencias.
    La validación de solapamiento del mismo tipo va en ResourceAvailabilityService.
    """
    usuario_id   = serializers.UUIDField()
    tipo         = serializers.ChoiceField(choices=AvailabilityType.choices)
    fecha_inicio = serializers.DateField()
    fecha_fin    = serializers.DateField()
    descripcion  = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio')
        fin    = attrs.get('fecha_fin')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError({
                'fecha_fin': 'La fecha de fin no puede ser anterior a la fecha de inicio.'
            })
        return attrs


class WorkloadSummarySerializer(serializers.Serializer):
    """
    Serializer de solo lectura para el resumen de carga de un usuario.
    Datos calculados por ResourceService.calculate_user_workload().
    """
    usuario_id           = serializers.UUIDField()
    periodo_inicio       = serializers.DateField()
    periodo_fin          = serializers.DateField()
    horas_capacidad      = serializers.DecimalField(max_digits=10, decimal_places=2)
    horas_asignadas      = serializers.DecimalField(max_digits=10, decimal_places=2)
    horas_registradas    = serializers.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_utilizacion = serializers.DecimalField(max_digits=6, decimal_places=2)
    conflictos           = serializers.ListField(child=serializers.DictField(), default=list)


class TeamAvailabilityUserSerializer(serializers.Serializer):
    """Entrada de un usuario en el timeline del equipo."""
    usuario_id     = serializers.UUIDField()
    usuario_nombre = serializers.CharField()
    usuario_email  = serializers.EmailField()
    asignaciones   = serializers.ListField(child=serializers.DictField())
    ausencias      = serializers.ListField(child=serializers.DictField())


class TeamAvailabilitySerializer(serializers.Serializer):
    """
    Serializer de solo lectura para el timeline del equipo de un proyecto.
    Datos calculados por ResourceService.get_team_availability_timeline().
    """
    periodo_inicio = serializers.DateField()
    periodo_fin    = serializers.DateField()
    usuarios       = TeamAvailabilityUserSerializer(many=True)


# ──────────────────────────────────────────────
# Feature #8 — Project Templates
# ──────────────────────────────────────────────

class PlantillaTareaSerializer(serializers.ModelSerializer):
    """Serializer de tarea de plantilla — solo lectura."""
    unidad_medida = serializers.SerializerMethodField()

    class Meta:
        model  = PlantillaTarea
        fields = [
            'id', 'nombre', 'descripcion', 'orden',
            'duracion_dias', 'prioridad',
            'actividad_saiopen_id', 'unidad_medida',
        ]
        read_only_fields = fields

    def get_unidad_medida(self, obj: PlantillaTarea) -> str | None:
        if obj.actividad_saiopen_id and obj.actividad_saiopen:
            return obj.actividad_saiopen.unidad_medida
        return None


class PlantillaFaseSerializer(serializers.ModelSerializer):
    """Serializer de fase de plantilla — incluye tareas anidadas."""
    tareas_count = serializers.SerializerMethodField()
    tareas       = PlantillaTareaSerializer(source='tareas_plantilla', many=True, read_only=True)

    class Meta:
        model  = PlantillaFase
        fields = [
            'id', 'nombre', 'descripcion', 'orden',
            'porcentaje_duracion', 'tareas_count', 'tareas',
        ]
        read_only_fields = fields

    def get_tareas_count(self, obj: PlantillaFase) -> int:
        # Evitar N+1: usar prefetch_related en la vista
        return obj.tareas_plantilla.count()


class PlantillaProyectoSerializer(serializers.ModelSerializer):
    """Serializer de listado de plantillas — incluye conteos."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    fases_count  = serializers.SerializerMethodField()
    fases        = PlantillaFaseSerializer(source='fases_plantilla', many=True, read_only=True)

    class Meta:
        model  = PlantillaProyecto
        fields = [
            'id', 'nombre', 'descripcion', 'tipo', 'tipo_display',
            'icono', 'duracion_estimada', 'is_active', 'fases_count', 'fases',
        ]
        read_only_fields = fields

    def get_fases_count(self, obj: PlantillaProyecto) -> int:
        return obj.fases_plantilla.count()


class PlantillaTareaWriteSerializer(serializers.Serializer):
    """Datos para crear/actualizar una tarea dentro de una fase de plantilla."""
    nombre               = serializers.CharField(max_length=200)
    descripcion          = serializers.CharField(required=False, allow_blank=True, default='')
    orden                = serializers.IntegerField(default=0)
    duracion_dias        = serializers.IntegerField(default=1, min_value=1)
    actividad_saiopen_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class PlantillaFaseWriteSerializer(serializers.Serializer):
    """Datos para crear/actualizar una fase dentro de una plantilla."""
    nombre               = serializers.CharField(max_length=255)
    descripcion          = serializers.CharField(required=False, allow_blank=True, default='')
    orden                = serializers.IntegerField(default=0)
    porcentaje_duracion  = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('100.00'),
    )
    tareas               = PlantillaTareaWriteSerializer(many=True, required=False, default=list)


class PlantillaProyectoWriteSerializer(serializers.Serializer):
    """Datos para crear/actualizar una plantilla de proyecto."""
    nombre              = serializers.CharField(max_length=200)
    descripcion         = serializers.CharField(required=False, allow_blank=True, default='')
    tipo                = serializers.ChoiceField(choices=ProjectType.choices)
    icono               = serializers.CharField(max_length=50, default='folder')
    duracion_estimada   = serializers.IntegerField(default=30, min_value=1)
    fases               = PlantillaFaseWriteSerializer(many=True, required=False, default=list)


class CreateFromTemplateSerializer(serializers.Serializer):
    """Datos necesarios para crear un proyecto a partir de una plantilla."""
    template_id   = serializers.UUIDField(
        required=True,
        help_text='UUID de la PlantillaProyecto a usar.',
    )
    nombre        = serializers.CharField(
        required=True,
        max_length=200,
        help_text='Nombre del nuevo proyecto.',
    )
    descripcion   = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text='Descripción del nuevo proyecto.',
    )
    planned_start = serializers.DateField(
        required=True,
        help_text='Fecha de inicio planificada del proyecto (YYYY-MM-DD).',
    )
    cliente_id    = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text='UUID del cliente (opcional).',
    )
