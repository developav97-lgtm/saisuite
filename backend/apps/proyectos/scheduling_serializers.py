"""
SaiSuite — Feature #6: Advanced Scheduling
Serializers para ProjectBaseline, TaskConstraint y WhatIfScenario.

Regla: solo transforman datos. Sin lógica de negocio ni efectos secundarios.
"""
import logging
from rest_framework import serializers
from apps.proyectos.models import (
    ProjectBaseline,
    TaskConstraint,
    ConstraintType,
    WhatIfScenario,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ProjectBaseline
# ─────────────────────────────────────────────────────────────────────────────

class ProjectBaselineListSerializer(serializers.ModelSerializer):
    """Listado de baselines — campos mínimos para tablas."""
    project_nombre = serializers.CharField(source='project.nombre', read_only=True)

    class Meta:
        model  = ProjectBaseline
        fields = [
            'id', 'project', 'project_nombre', 'name', 'description',
            'is_active_baseline',
            'project_end_date_snapshot', 'total_tasks_snapshot',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProjectBaselineDetailSerializer(serializers.ModelSerializer):
    """
    Detalle completo de un baseline.
    Incluye snapshots JSON para la vista de comparación.
    """
    project_nombre = serializers.CharField(source='project.nombre', read_only=True)

    class Meta:
        model  = ProjectBaseline
        fields = [
            'id', 'project', 'project_nombre', 'name', 'description',
            'is_active_baseline',
            'tasks_snapshot', 'resources_snapshot', 'critical_path_snapshot',
            'project_end_date_snapshot', 'total_tasks_snapshot',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'project', 'tasks_snapshot', 'resources_snapshot',
            'critical_path_snapshot', 'project_end_date_snapshot',
            'total_tasks_snapshot', 'created_at', 'updated_at',
        ]


class ProjectBaselineCreateSerializer(serializers.Serializer):
    """
    Serializer de escritura para crear un nuevo baseline.
    El snapshot JSON lo genera BaselineService.create_baseline().
    """
    name           = serializers.CharField(max_length=255)
    description    = serializers.CharField(required=False, allow_blank=True, default='')
    set_as_active  = serializers.BooleanField(default=True)


# ─────────────────────────────────────────────────────────────────────────────
# TaskConstraint
# ─────────────────────────────────────────────────────────────────────────────

class TaskConstraintSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura y detalle para TaskConstraint.
    Usado tanto en listados como en respuestas individuales.
    """
    constraint_type_display = serializers.CharField(
        source='get_constraint_type_display',
        read_only=True,
    )
    tarea_nombre = serializers.CharField(source='task.nombre', read_only=True)
    tarea_codigo = serializers.CharField(source='task.codigo', read_only=True)

    class Meta:
        model  = TaskConstraint
        fields = [
            'id', 'task', 'tarea_codigo', 'tarea_nombre',
            'constraint_type', 'constraint_type_display',
            'constraint_date',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'task', 'created_at', 'updated_at']


class TaskConstraintCreateSerializer(serializers.Serializer):
    """
    Serializer de escritura para crear restricciones de scheduling.
    El campo `task` proviene del URL (task_pk). La validación de
    constraint_date vs constraint_type va en el model.clean().
    """
    constraint_type = serializers.ChoiceField(choices=ConstraintType.choices)
    constraint_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        date_required = {
            ConstraintType.MUST_START_ON,
            ConstraintType.MUST_FINISH_ON,
            ConstraintType.START_NO_EARLIER_THAN,
            ConstraintType.START_NO_LATER_THAN,
            ConstraintType.FINISH_NO_EARLIER_THAN,
            ConstraintType.FINISH_NO_LATER_THAN,
        }
        if attrs['constraint_type'] in date_required and not attrs.get('constraint_date'):
            raise serializers.ValidationError({
                'constraint_date': (
                    f'constraint_date es obligatorio para el tipo '
                    f'"{attrs["constraint_type"]}".'
                )
            })
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# WhatIfScenario
# ─────────────────────────────────────────────────────────────────────────────

class WhatIfScenarioListSerializer(serializers.ModelSerializer):
    """Listado de escenarios — sin los JSONs de cambios ni resultados detallados."""
    project_nombre    = serializers.CharField(source='project.nombre', read_only=True)
    created_by_nombre = serializers.SerializerMethodField()
    simulation_done   = serializers.SerializerMethodField()

    class Meta:
        model  = WhatIfScenario
        fields = [
            'id', 'project', 'project_nombre',
            'name', 'description',
            'created_by', 'created_by_nombre',
            'simulated_end_date', 'days_delta', 'tasks_affected_count',
            'simulation_done', 'simulation_ran_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_created_by_nombre(self, obj: WhatIfScenario) -> str | None:
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None

    def get_simulation_done(self, obj: WhatIfScenario) -> bool:
        return obj.simulation_ran_at is not None


class WhatIfScenarioDetailSerializer(serializers.ModelSerializer):
    """
    Detalle completo de un escenario what-if.
    Incluye cambios propuestos y resultados de simulación.
    """
    project_nombre    = serializers.CharField(source='project.nombre', read_only=True)
    created_by_nombre = serializers.SerializerMethodField()
    simulation_done   = serializers.SerializerMethodField()

    class Meta:
        model  = WhatIfScenario
        fields = [
            'id', 'project', 'project_nombre',
            'name', 'description',
            'created_by', 'created_by_nombre',
            'task_changes', 'resource_changes', 'dependency_changes',
            'simulated_end_date', 'simulated_critical_path',
            'days_delta', 'tasks_affected_count',
            'simulation_done', 'simulation_ran_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'project', 'created_by',
            'simulated_end_date', 'simulated_critical_path',
            'days_delta', 'tasks_affected_count',
            'simulation_ran_at', 'created_at', 'updated_at',
        ]

    def get_created_by_nombre(self, obj: WhatIfScenario) -> str | None:
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None

    def get_simulation_done(self, obj: WhatIfScenario) -> bool:
        return obj.simulation_ran_at is not None


class WhatIfScenarioCreateSerializer(serializers.Serializer):
    """
    Serializer de escritura para crear escenarios what-if.

    Estructura de cambios esperada:
      task_changes:       {str(task_uuid): {field: value}}
      resource_changes:   {str(assignment_uuid): {field: value}}
      dependency_changes: {str(dep_uuid): {'retraso_dias': N}}
    """
    name               = serializers.CharField(max_length=255)
    description        = serializers.CharField(required=False, allow_blank=True, default='')
    task_changes       = serializers.DictField(required=False, default=dict)
    resource_changes   = serializers.DictField(required=False, default=dict)
    dependency_changes = serializers.DictField(required=False, default=dict)

    def validate(self, attrs):
        has_changes = (
            attrs.get('task_changes')
            or attrs.get('resource_changes')
            or attrs.get('dependency_changes')
        )
        if not has_changes:
            raise serializers.ValidationError(
                'El escenario debe incluir al menos un cambio '
                '(task_changes, resource_changes o dependency_changes).'
            )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# Respuestas de solo lectura para endpoints de scheduling
# ─────────────────────────────────────────────────────────────────────────────

class BaselineComparisonTaskSerializer(serializers.Serializer):
    """Fila de tarea en la tabla de comparación baseline vs actual."""
    task_id          = serializers.UUIDField()
    nombre           = serializers.CharField()
    codigo           = serializers.CharField()
    baseline_start   = serializers.DateField(allow_null=True)
    baseline_finish  = serializers.DateField(allow_null=True)
    current_start    = serializers.DateField(allow_null=True)
    current_finish   = serializers.DateField(allow_null=True)
    variance_days    = serializers.IntegerField()
    status           = serializers.ChoiceField(
        choices=['ahead', 'on_schedule', 'behind'],
    )


class BaselineComparisonSerializer(serializers.Serializer):
    """
    Serializer de solo lectura para la respuesta de BaselineService.compare_to_baseline().
    """
    baseline_name         = serializers.CharField()
    baseline_end_date     = serializers.DateField(allow_null=True)
    current_end_date      = serializers.DateField(allow_null=True)
    schedule_variance_days = serializers.IntegerField()
    tasks                 = BaselineComparisonTaskSerializer(many=True)
    summary               = serializers.DictField()
