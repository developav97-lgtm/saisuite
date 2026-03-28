"""
SaiSuite — Feature #6: Advanced Scheduling — Views
16 endpoints REST bajo /api/v1/projects/

Regla: las views solo orquestan (request → service → response).
Sin lógica de negocio aquí.
"""
import logging
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.proyectos.models import (
    Task,
    TaskConstraint,
    TaskDependency,
    ProjectBaseline,
    WhatIfScenario,
)
from apps.proyectos.permissions import CanAccessProyectos
from apps.proyectos.scheduling_serializers import (
    ProjectBaselineListSerializer,
    ProjectBaselineDetailSerializer,
    ProjectBaselineCreateSerializer,
    TaskConstraintSerializer,
    TaskConstraintCreateSerializer,
    WhatIfScenarioListSerializer,
    WhatIfScenarioDetailSerializer,
    WhatIfScenarioCreateSerializer,
    BaselineComparisonSerializer,
)
from apps.proyectos.scheduling_services import (
    SchedulingService,
    ResourceLevelingService,
    BaselineService,
    WhatIfService,
)

logger = logging.getLogger(__name__)


def _company_id(request) -> str:
    return str(request.user.company_id)


# ─────────────────────────────────────────────────────────────────────────────
# Auto-Scheduling
# ─────────────────────────────────────────────────────────────────────────────

class AutoScheduleView(APIView):
    """
    SK-21-01 — Reprogramar automáticamente todas las tareas del proyecto.

    POST /api/v1/projects/<project_pk>/scheduling/auto-schedule/

    Body (JSON):
        {
            "scheduling_mode":      "asap" | "alap",    default "asap"
            "respect_constraints":  bool,               default true
            "dry_run":              bool                default false
        }

    Respuesta:
        {
            "tasks_rescheduled":    int,
            "tasks_excluded":       [str],
            "new_project_end_date": "YYYY-MM-DD" | null,
            "critical_path":        [str],
            "warnings":             [str],
            "dry_run":              bool,
            "preview":              {...}    solo si dry_run=true
        }
    """
    permission_classes = [CanAccessProyectos]

    def post(self, request, project_pk=None):
        mode               = request.data.get('scheduling_mode', 'asap')
        respect            = request.data.get('respect_constraints', True)
        dry_run            = request.data.get('dry_run', False)

        try:
            result = SchedulingService.auto_schedule_project(
                project_id=str(project_pk),
                company_id=_company_id(request),
                scheduling_mode=mode,
                respect_constraints=bool(respect),
                dry_run=bool(dry_run),
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serializar fecha a str para JSON
        result = dict(result)
        if result.get('new_project_end_date'):
            result['new_project_end_date'] = str(result['new_project_end_date'])

        return Response(result, status=status.HTTP_200_OK)


class ResourceLevelingView(APIView):
    """
    SK-21-02 — Nivelar recursos del proyecto moviendo tareas con float > 0.

    POST /api/v1/projects/<project_pk>/scheduling/level-resources/

    Body (JSON):
        {
            "dry_run":        bool   default false
            "max_iterations": int    default 500
        }
    """
    permission_classes = [CanAccessProyectos]

    def post(self, request, project_pk=None):
        dry_run        = bool(request.data.get('dry_run', False))
        max_iterations = int(request.data.get('max_iterations', 500))

        try:
            result = ResourceLevelingService.level_resources(
                project_id=str(project_pk),
                company_id=_company_id(request),
                dry_run=dry_run,
                max_iterations=min(max_iterations, 1000),  # Límite seguro
            )
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)


class CriticalPathView(APIView):
    """
    SK-21-03 — Ruta crítica del proyecto. Resultado cacheado 5 minutos.

    GET /api/v1/projects/<project_pk>/scheduling/critical-path/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        from django.core.cache import cache

        project_id = str(project_pk)
        company_id = _company_id(request)

        cache_key = f'critical_path:{project_id}:{company_id}'
        cached    = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        try:
            cpm = SchedulingService.run_cpm(project_id, company_id)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enriquecer con datos de tareas para el frontend
        task_ids = cpm['critical_path']
        tasks_data = {
            str(t.id): {'codigo': t.codigo, 'nombre': t.nombre}
            for t in Task.objects.filter(
                id__in=task_ids,
                company_id=company_id,
            )
        }

        response_data = {
            'critical_path': task_ids,
            'tasks': [
                {
                    'task_id': tid,
                    **tasks_data.get(tid, {'codigo': '', 'nombre': ''}),
                    'early_start':  str(cpm['forward_data'][tid]['early_start'])
                                    if tid in cpm['forward_data'] else None,
                    'early_finish': str(cpm['forward_data'][tid]['early_finish'])
                                    if tid in cpm['forward_data'] else None,
                }
                for tid in task_ids
            ],
            'project_end_date': str(cpm['project_end_date']) if cpm['project_end_date'] else None,
            'tasks_excluded':   cpm['tasks_excluded'],
        }

        cache.set(cache_key, response_data, timeout=300)  # SK-29: 5 minutos
        return Response(response_data)


class TaskFloatView(APIView):
    """
    SK-21-04 — Holgura (float) de una tarea específica.

    GET /api/v1/projects/tasks/<task_pk>/scheduling/float/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, task_pk=None):
        company_id = _company_id(request)

        try:
            task = Task.objects.select_related('fase__proyecto').get(
                id=task_pk,
                company_id=company_id,
            )
        except Task.DoesNotExist:
            return Response(
                {'detail': 'Tarea no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        project_id = str(task.proyecto_id)

        try:
            cpm = SchedulingService.run_cpm(project_id, company_id)
        except ValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tid = str(task_pk)
        dependencies = list(
            TaskDependency.objects.filter(
                company_id=company_id,
                tarea_predecesora__proyecto_id=project_id,
            )
        )

        float_data = SchedulingService.calculate_float(
            task_id=tid,
            forward_data=cpm['forward_data'],
            backward_data=cpm['backward_data'],
            dependencies=dependencies,
        )

        return Response({
            'task_id':     tid,
            'task_codigo': task.codigo,
            'task_nombre': task.nombre,
            **float_data,
            'early_start':  str(cpm['forward_data'][tid]['early_start'])
                            if tid in cpm['forward_data'] else None,
            'early_finish': str(cpm['forward_data'][tid]['early_finish'])
                            if tid in cpm['forward_data'] else None,
            'late_start':   str(cpm['backward_data'][tid]['late_start'])
                            if tid in cpm['backward_data'] else None,
            'late_finish':  str(cpm['backward_data'][tid]['late_finish'])
                            if tid in cpm['backward_data'] else None,
        })


# ─────────────────────────────────────────────────────────────────────────────
# Task Constraints
# ─────────────────────────────────────────────────────────────────────────────

class TaskConstraintListView(APIView):
    """
    SK-21-05/06 — Listar y crear restricciones de scheduling de una tarea.

    GET  /api/v1/projects/tasks/<task_pk>/constraints/
    POST /api/v1/projects/tasks/<task_pk>/constraints/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, task_pk=None):
        company_id = _company_id(request)
        constraints = TaskConstraint.objects.filter(
            task_id=task_pk,
            company_id=company_id,
        ).select_related('task')
        serializer = TaskConstraintSerializer(constraints, many=True)
        return Response(serializer.data)

    def post(self, request, task_pk=None):
        company_id = _company_id(request)

        # Verificar que la tarea existe y pertenece a la company
        try:
            task = Task.objects.get(id=task_pk, company_id=company_id)
        except Task.DoesNotExist:
            return Response(
                {'detail': 'Tarea no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TaskConstraintCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        constraint, created = TaskConstraint.objects.get_or_create(
            company_id=company_id,
            task=task,
            constraint_type=data['constraint_type'],
            defaults={'constraint_date': data.get('constraint_date')},
        )

        if not created:
            # Actualizar constraint_date si el tipo ya existe
            constraint.constraint_date = data.get('constraint_date')
            constraint.save(update_fields=['constraint_date', 'updated_at'])

        out = TaskConstraintSerializer(constraint)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TaskConstraintDeleteView(APIView):
    """
    SK-21-07 — Eliminar una restricción de scheduling.

    DELETE /api/v1/projects/constraints/<pk>/
    """
    permission_classes = [CanAccessProyectos]

    def delete(self, request, pk=None):
        company_id = _company_id(request)
        try:
            constraint = TaskConstraint.objects.get(id=pk, company_id=company_id)
        except TaskConstraint.DoesNotExist:
            return Response(
                {'detail': 'Restricción no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        constraint.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────────────────
# Baselines
# ─────────────────────────────────────────────────────────────────────────────

class ProjectBaselineListView(APIView):
    """
    SK-21-08/09 — Listar y crear baselines de un proyecto.

    GET  /api/v1/projects/<project_pk>/baselines/
    POST /api/v1/projects/<project_pk>/baselines/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        company_id = _company_id(request)
        baselines  = ProjectBaseline.objects.filter(
            project_id=project_pk,
            company_id=company_id,
        ).select_related('project').order_by('-created_at')
        serializer = ProjectBaselineListSerializer(baselines, many=True)
        return Response(serializer.data)

    def post(self, request, project_pk=None):
        company_id = _company_id(request)
        serializer = ProjectBaselineCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            baseline = BaselineService.create_baseline(
                project_id=str(project_pk),
                company_id=company_id,
                name=data['name'],
                description=data.get('description', ''),
                set_as_active=data.get('set_as_active', True),
            )
        except (ValidationError, Exception) as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out = ProjectBaselineDetailSerializer(baseline)
        return Response(out.data, status=status.HTTP_201_CREATED)


class BaselineDetailView(APIView):
    """
    SK-21-10/12 — Obtener y eliminar un baseline.

    GET    /api/v1/projects/baselines/<pk>/
    DELETE /api/v1/projects/baselines/<pk>/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, pk=None):
        company_id = _company_id(request)
        try:
            baseline = ProjectBaseline.objects.select_related('project').get(
                id=pk,
                company_id=company_id,
            )
        except ProjectBaseline.DoesNotExist:
            return Response(
                {'detail': 'Baseline no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProjectBaselineDetailSerializer(baseline)
        return Response(serializer.data)

    def delete(self, request, pk=None):
        company_id = _company_id(request)
        try:
            baseline = ProjectBaseline.objects.get(id=pk, company_id=company_id)
        except ProjectBaseline.DoesNotExist:
            return Response(
                {'detail': 'Baseline no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if baseline.is_active_baseline:
            return Response(
                {'detail': 'No se puede eliminar el baseline activo. Activa otro primero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        baseline.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaselineCompareView(APIView):
    """
    SK-21-11 — Comparar plan actual vs un baseline.

    GET /api/v1/projects/baselines/<pk>/compare/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, pk=None):
        company_id = _company_id(request)
        try:
            baseline = ProjectBaseline.objects.get(id=pk, company_id=company_id)
        except ProjectBaseline.DoesNotExist:
            return Response(
                {'detail': 'Baseline no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            comparison = BaselineService.compare_to_baseline(
                project_id=str(baseline.project_id),
                company_id=company_id,
                baseline_id=str(pk),
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BaselineComparisonSerializer(data=comparison)
        serializer.is_valid()
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# What-If Scenarios
# ─────────────────────────────────────────────────────────────────────────────

class WhatIfScenarioListView(APIView):
    """
    SK-21-13/14 — Listar y crear escenarios what-if de un proyecto.

    GET  /api/v1/projects/<project_pk>/scenarios/
    POST /api/v1/projects/<project_pk>/scenarios/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        company_id = _company_id(request)
        scenarios  = WhatIfScenario.objects.filter(
            project_id=project_pk,
            company_id=company_id,
        ).select_related('project', 'created_by').order_by('-created_at')
        serializer = WhatIfScenarioListSerializer(scenarios, many=True)
        return Response(serializer.data)

    def post(self, request, project_pk=None):
        company_id = _company_id(request)
        serializer = WhatIfScenarioCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            scenario = WhatIfService.create_scenario(
                project_id=str(project_pk),
                company_id=company_id,
                user_id=str(request.user.id),
                name=data['name'],
                description=data.get('description', ''),
                task_changes=data.get('task_changes', {}),
                resource_changes=data.get('resource_changes', {}),
                dependency_changes=data.get('dependency_changes', {}),
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out = WhatIfScenarioDetailSerializer(scenario)
        return Response(out.data, status=status.HTTP_201_CREATED)


class WhatIfScenarioDetailView(APIView):
    """
    SK-21-15/17 — Obtener y eliminar un escenario what-if.

    GET    /api/v1/projects/scenarios/<pk>/
    DELETE /api/v1/projects/scenarios/<pk>/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, pk=None):
        company_id = _company_id(request)
        try:
            scenario = WhatIfScenario.objects.select_related(
                'project', 'created_by'
            ).get(id=pk, company_id=company_id)
        except WhatIfScenario.DoesNotExist:
            return Response(
                {'detail': 'Escenario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = WhatIfScenarioDetailSerializer(scenario)
        return Response(serializer.data)

    def delete(self, request, pk=None):
        company_id = _company_id(request)
        try:
            scenario = WhatIfScenario.objects.get(id=pk, company_id=company_id)
        except WhatIfScenario.DoesNotExist:
            return Response(
                {'detail': 'Escenario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        scenario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RunSimulationView(APIView):
    """
    SK-21-16 — Ejecutar la simulación CPM de un escenario what-if.

    POST /api/v1/projects/scenarios/<pk>/run-simulation/

    No modifica datos reales. Los resultados se guardan en el escenario.
    """
    permission_classes = [CanAccessProyectos]

    def post(self, request, pk=None):
        company_id = _company_id(request)
        try:
            scenario = WhatIfService.run_simulation(
                scenario_id=str(pk),
                company_id=company_id,
            )
        except WhatIfScenario.DoesNotExist:
            return Response(
                {'detail': 'Escenario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WhatIfScenarioDetailSerializer(scenario)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompareScenariosView(APIView):
    """
    SK-21-18 — Tabla comparativa de múltiples escenarios.

    POST /api/v1/projects/scenarios/compare/

    Body: { "scenario_ids": ["uuid", "uuid", ...] }
    """
    permission_classes = [CanAccessProyectos]

    def post(self, request):
        scenario_ids = request.data.get('scenario_ids', [])
        if not scenario_ids or not isinstance(scenario_ids, list):
            return Response(
                {'detail': 'Se requiere scenario_ids como lista de UUIDs.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(scenario_ids) > 10:
            return Response(
                {'detail': 'Máximo 10 escenarios por comparación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company_id = _company_id(request)
        try:
            result = WhatIfService.compare_scenarios(
                scenario_ids=[str(sid) for sid in scenario_ids],
                company_id=company_id,
            )
        except Exception as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_200_OK)
