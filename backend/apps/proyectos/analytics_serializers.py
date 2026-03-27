"""
SaiSuite — Proyectos: Analytics Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.

Todos son de solo lectura (read-only) ya que corresponden a datos calculados,
no a modelos persistibles directamente.
"""
import logging
from rest_framework import serializers

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AN-01: ProjectKPIsSerializer
# ---------------------------------------------------------------------------

class ProjectKPIsSerializer(serializers.Serializer):
    """Serializer para los KPIs principales de un proyecto."""
    total_tasks      = serializers.IntegerField(read_only=True)
    completed_tasks  = serializers.IntegerField(read_only=True)
    overdue_tasks    = serializers.IntegerField(read_only=True)
    completion_rate  = serializers.FloatField(read_only=True)
    on_time_rate     = serializers.FloatField(read_only=True)
    budget_variance  = serializers.FloatField(read_only=True)
    velocity         = serializers.FloatField(read_only=True)
    burn_rate        = serializers.FloatField(read_only=True)


# ---------------------------------------------------------------------------
# AN-02: TaskDistributionSerializer
# ---------------------------------------------------------------------------

class TaskDistributionPercentagesSerializer(serializers.Serializer):
    """Porcentajes de distribución de tareas por estado."""
    todo        = serializers.FloatField(read_only=True)
    in_progress = serializers.FloatField(read_only=True)
    in_review   = serializers.FloatField(read_only=True)
    completed   = serializers.FloatField(read_only=True)
    blocked     = serializers.FloatField(read_only=True)
    cancelled   = serializers.FloatField(read_only=True)


class TaskDistributionSerializer(serializers.Serializer):
    """Serializer para la distribución de tareas por estado."""
    todo        = serializers.IntegerField(read_only=True)
    in_progress = serializers.IntegerField(read_only=True)
    in_review   = serializers.IntegerField(read_only=True)
    completed   = serializers.IntegerField(read_only=True)
    blocked     = serializers.IntegerField(read_only=True)
    cancelled   = serializers.IntegerField(read_only=True)
    total       = serializers.IntegerField(read_only=True)
    percentages = TaskDistributionPercentagesSerializer(read_only=True)


# ---------------------------------------------------------------------------
# AN-03: VelocityDataPointSerializer + VelocityResponseSerializer
# ---------------------------------------------------------------------------

class VelocityDataPointSerializer(serializers.Serializer):
    """Punto de datos de velocidad semanal."""
    week_label      = serializers.CharField(read_only=True)
    week_start      = serializers.DateField(read_only=True)
    tasks_completed = serializers.IntegerField(read_only=True)


class VelocityResponseSerializer(serializers.Serializer):
    """Respuesta de la vista de velocidad."""
    periods = serializers.IntegerField(read_only=True)
    data    = VelocityDataPointSerializer(many=True, read_only=True)


# ---------------------------------------------------------------------------
# AN-04: BurnRateDataPointSerializer + BurnRateResponseSerializer
# ---------------------------------------------------------------------------

class BurnRateDataPointSerializer(serializers.Serializer):
    """Punto de datos de burn rate semanal."""
    week_label       = serializers.CharField(read_only=True)
    week_start       = serializers.DateField(read_only=True)
    hours_registered = serializers.FloatField(read_only=True)


class BurnRateResponseSerializer(serializers.Serializer):
    """Respuesta de la vista de burn rate."""
    periods = serializers.IntegerField(read_only=True)
    data    = BurnRateDataPointSerializer(many=True, read_only=True)


# ---------------------------------------------------------------------------
# AN-05: BurnDownDataPointSerializer + BurnDownResponseSerializer
# ---------------------------------------------------------------------------

class BurnDownDataPointSerializer(serializers.Serializer):
    """Punto de datos del gráfico Burn Down."""
    week_label               = serializers.CharField(read_only=True)
    week_start               = serializers.DateField(read_only=True)
    hours_registered         = serializers.FloatField(read_only=True)
    hours_actual_cumulative  = serializers.FloatField(read_only=True)
    hours_remaining          = serializers.FloatField(read_only=True)
    hours_ideal              = serializers.FloatField(read_only=True)


class BurnDownResponseSerializer(serializers.Serializer):
    """Respuesta de la vista de burn down."""
    total_hours_estimated = serializers.FloatField(read_only=True)
    data_points           = BurnDownDataPointSerializer(many=True, read_only=True)


# ---------------------------------------------------------------------------
# AN-06: ResourceUtilizationSerializer
# ---------------------------------------------------------------------------

class ResourceUtilizationSerializer(serializers.Serializer):
    """Serializer para la utilización de un recurso (usuario) en el proyecto."""
    user_id                = serializers.UUIDField(read_only=True)
    user_name              = serializers.CharField(read_only=True)
    user_email             = serializers.EmailField(read_only=True)
    assigned_hours         = serializers.FloatField(read_only=True)
    registered_hours       = serializers.FloatField(read_only=True)
    capacity_hours         = serializers.FloatField(read_only=True)
    utilization_percentage = serializers.FloatField(read_only=True)


# ---------------------------------------------------------------------------
# AN-07: ProjectComparisonSerializer
# ---------------------------------------------------------------------------

class ProjectComparisonSerializer(serializers.Serializer):
    """Serializer para comparación de proyectos."""
    project_id      = serializers.UUIDField(read_only=True)
    project_name    = serializers.CharField(read_only=True)
    project_code    = serializers.CharField(read_only=True)
    completion_rate = serializers.FloatField(read_only=True)
    on_time_rate    = serializers.FloatField(read_only=True)
    budget_variance = serializers.FloatField(read_only=True)
    velocity        = serializers.FloatField(read_only=True)
    total_tasks     = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    overdue_tasks   = serializers.IntegerField(read_only=True)


# ---------------------------------------------------------------------------
# AN-08: ProjectTimelineSerializer
# ---------------------------------------------------------------------------

class TimelineTaskSerializer(serializers.Serializer):
    """Tarea dentro del timeline de un proyecto."""
    task_id              = serializers.UUIDField(read_only=True)
    task_code            = serializers.CharField(read_only=True)
    task_name            = serializers.CharField(read_only=True)
    estado               = serializers.CharField(read_only=True)
    prioridad            = serializers.IntegerField(read_only=True)
    start_date           = serializers.DateField(allow_null=True, read_only=True)
    end_date             = serializers.DateField(allow_null=True, read_only=True)
    deadline             = serializers.DateField(allow_null=True, read_only=True)
    horas_estimadas      = serializers.FloatField(read_only=True)
    horas_registradas    = serializers.FloatField(read_only=True)
    porcentaje_completado = serializers.IntegerField(read_only=True)


class TimelinePhaseSerializer(serializers.Serializer):
    """Fase dentro del timeline de un proyecto."""
    phase_id        = serializers.UUIDField(read_only=True)
    phase_name      = serializers.CharField(read_only=True)
    phase_order     = serializers.IntegerField(read_only=True)
    estado          = serializers.CharField(read_only=True)
    start_planned   = serializers.DateField(read_only=True)
    end_planned     = serializers.DateField(read_only=True)
    start_actual    = serializers.DateField(allow_null=True, read_only=True)
    end_actual      = serializers.DateField(allow_null=True, read_only=True)
    progress        = serializers.FloatField(read_only=True)
    total_tasks     = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    tasks           = TimelineTaskSerializer(many=True, read_only=True)


class ProjectTimelineSerializer(serializers.Serializer):
    """Serializer para el timeline completo de un proyecto."""
    project_id       = serializers.UUIDField(read_only=True)
    project_name     = serializers.CharField(read_only=True)
    project_code     = serializers.CharField(read_only=True)
    start_planned    = serializers.DateField(read_only=True)
    end_planned      = serializers.DateField(read_only=True)
    start_actual     = serializers.DateField(allow_null=True, read_only=True)
    end_actual       = serializers.DateField(allow_null=True, read_only=True)
    overall_progress = serializers.FloatField(read_only=True)
    phases           = TimelinePhaseSerializer(many=True, read_only=True)


# ---------------------------------------------------------------------------
# Export: CompareProjectsRequestSerializer (validación del body del POST)
# ---------------------------------------------------------------------------

class CompareProjectsRequestSerializer(serializers.Serializer):
    """Valida el body del POST /projects/analytics/compare/"""
    project_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=20,
    )


# ---------------------------------------------------------------------------
# Export: ExportExcelRequestSerializer (validación del body del POST)
# ---------------------------------------------------------------------------

class ExportExcelRequestSerializer(serializers.Serializer):
    """Valida el body del POST /projects/analytics/export-excel/"""
    project_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=20,
    )
    metrics = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    date_range = serializers.DictField(
        required=False,
        default=dict,
        child=serializers.CharField(allow_null=True),
    )
