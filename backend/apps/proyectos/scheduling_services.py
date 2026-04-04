"""
SaiSuite — Feature #6: Advanced Scheduling
Lógica de negocio para CPM (Critical Path Method), auto-scheduling,
resource leveling, baselines y simulaciones what-if.

Regla: toda la lógica de negocio va aquí. Las views solo orquestan.
"""
import logging
from collections import defaultdict, deque
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction

from django.contrib.auth import get_user_model

from apps.proyectos.models import (
    Project,
    Task,
    TaskDependency,
    TaskConstraint,
    ConstraintType,
    ProjectBaseline,
    WhatIfScenario,
    ResourceAssignment,
    ResourceCapacity,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Tipos internos (evitar dependencias circulares)
# ─────────────────────────────────────────────────────────────────────────────

# {task_id_str: {'early_start': date, 'early_finish': date}}
ForwardData = dict[str, dict[str, date]]

# {task_id_str: {'late_start': date, 'late_finish': date}}
BackwardData = dict[str, dict[str, date]]


# ─────────────────────────────────────────────────────────────────────────────
# SK-06 a SK-10: SchedulingService — CPM Core
# ─────────────────────────────────────────────────────────────────────────────

class SchedulingService:
    """
    Implementa el Método del Camino Crítico (CPM) para proyectos.

    Secuencia de uso:
      1. topological_sort()   → orden sin ciclos
      2. forward_pass()       → early_start / early_finish
      3. backward_pass()      → late_start / late_finish
      4. calculate_float()    → total_float / free_float / is_critical
      5. get_critical_path()  → lista de task_ids con float == 0

    Todas las funciones son @staticmethod para facilitar el testing unitario.
    """

    # ── SK-06: Kahn's Algorithm ───────────────────────────────────────────────

    @staticmethod
    def topological_sort(
        tasks: list[Task],
        dependencies: list[TaskDependency],
    ) -> list[Task]:
        """
        Ordena las tareas respetando sus dependencias (sin ciclos).

        Algoritmo: Kahn's (BFS sobre in-degrees).
        Complejidad: O(V + E) donde V = tareas, E = dependencias.

        Raises:
            ValidationError: si se detecta un ciclo. El detalle incluye
                             los IDs de tareas involucradas en el ciclo.
        """
        task_ids: set[str] = {str(t.id) for t in tasks}

        # in_degree[tid] = número de predecesores dentro del conjunto
        in_degree: dict[str, int] = {str(t.id): 0 for t in tasks}

        # graph[pred_id] = [succ_id, ...] — solo aristas dentro del conjunto
        graph: dict[str, list[str]] = {str(t.id): [] for t in tasks}

        for dep in dependencies:
            pred_id = str(dep.tarea_predecesora_id)
            succ_id = str(dep.tarea_sucesora_id)
            # Ignorar dependencias a tareas fuera del conjunto actual
            if pred_id not in task_ids or succ_id not in task_ids:
                continue
            graph[pred_id].append(succ_id)
            in_degree[succ_id] += 1

        # Cola inicial: nodos sin predecesores
        queue: deque[str] = deque(
            tid for tid, deg in in_degree.items() if deg == 0
        )
        sorted_ids: list[str] = []

        while queue:
            tid = queue.popleft()
            sorted_ids.append(tid)
            for succ_id in graph[tid]:
                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        if len(sorted_ids) != len(tasks):
            # Ciclo detectado: tareas que no llegaron al in_degree=0
            cycle_ids = [
                tid for tid in task_ids if tid not in sorted_ids
            ]
            logger.error(
                "CPM: ciclo detectado en dependencias",
                extra={"cycle_task_ids": cycle_ids},
            )
            raise ValidationError(
                f"Las dependencias forman un ciclo. "
                f"Tareas involucradas: {cycle_ids}"
            )

        task_map: dict[str, Task] = {str(t.id): t for t in tasks}
        return [task_map[tid] for tid in sorted_ids]

    # ── SK-07: Forward Pass ───────────────────────────────────────────────────

    @staticmethod
    def forward_pass(
        tasks_sorted: list[Task],
        dependencies: list[TaskDependency],
        project_start: date,
    ) -> ForwardData:
        """
        Calcula las fechas más tempranas (early_start, early_finish) por tarea.

        Lógica por tipo de dependencia:
          FS (Finish-to-Start): sucesora.es = predecesora.ef + lag
          SS (Start-to-Start):  sucesora.es = predecesora.es + lag
          FF (Finish-to-Finish): sucesora.ef = predecesora.ef + lag
                                  → sucesora.es = ef - duration

        Las tareas sin fecha_inicio o fecha_fin se saltan (sin duración definida).
        """
        # dep_by_succ[succ_id] = [{'pred_id', 'tipo', 'lag'}, ...]
        dep_by_succ: dict[str, list[dict]] = defaultdict(list)
        for dep in dependencies:
            dep_by_succ[str(dep.tarea_sucesora_id)].append({
                'pred_id': str(dep.tarea_predecesora_id),
                'tipo':    dep.tipo_dependencia,
                'lag':     dep.retraso_dias,
            })

        early: ForwardData = {}

        for task in tasks_sorted:
            tid = str(task.id)

            if not task.fecha_inicio or not task.fecha_fin:
                # Sin fechas → excluir del cálculo CPM
                logger.debug(
                    "CPM forward_pass: tarea sin fechas excluida",
                    extra={"task_id": tid, "task_codigo": task.codigo},
                )
                continue

            duration_days: int = (task.fecha_fin - task.fecha_inicio).days

            predecessors = [
                d for d in dep_by_succ[tid]
                if d['pred_id'] in early
            ]

            if not predecessors:
                es = project_start
            else:
                candidates: list[date] = []
                for dep in predecessors:
                    pred = early[dep['pred_id']]
                    lag  = timedelta(days=dep['lag'])

                    if dep['tipo'] == 'FS':
                        candidates.append(pred['early_finish'] + lag)
                    elif dep['tipo'] == 'SS':
                        candidates.append(pred['early_start'] + lag)
                    elif dep['tipo'] == 'FF':
                        # early_finish fijado por predecesora; es = ef - duration
                        ef_from_pred = pred['early_finish'] + lag
                        candidates.append(
                            ef_from_pred - timedelta(days=duration_days)
                        )
                    else:
                        candidates.append(pred['early_finish'] + lag)

                es = max(candidates + [project_start])

            ef = es + timedelta(days=duration_days)
            early[tid] = {'early_start': es, 'early_finish': ef}

        return early

    # ── SK-08: Backward Pass ──────────────────────────────────────────────────

    @staticmethod
    def backward_pass(
        tasks_sorted: list[Task],
        dependencies: list[TaskDependency],
        project_end: date,
    ) -> BackwardData:
        """
        Calcula las fechas más tardías (late_start, late_finish) por tarea.

        Se recorre en orden inverso al topológico.

        Lógica por tipo de dependencia (inversa al forward pass):
          FS: predecesora.lf = sucesora.ls - lag
          SS: predecesora.ls = sucesora.ls - lag  → lf = ls + duration
          FF: predecesora.lf = sucesora.lf - lag
        """
        # dep_by_pred[pred_id] = [{'succ_id', 'tipo', 'lag'}, ...]
        dep_by_pred: dict[str, list[dict]] = defaultdict(list)
        for dep in dependencies:
            dep_by_pred[str(dep.tarea_predecesora_id)].append({
                'succ_id': str(dep.tarea_sucesora_id),
                'tipo':    dep.tipo_dependencia,
                'lag':     dep.retraso_dias,
            })

        late: BackwardData = {}

        for task in reversed(tasks_sorted):
            tid = str(task.id)

            if not task.fecha_inicio or not task.fecha_fin:
                continue

            duration_days: int = (task.fecha_fin - task.fecha_inicio).days

            successors = [
                d for d in dep_by_pred[tid]
                if d['succ_id'] in late
            ]

            if not successors:
                lf = project_end
            else:
                candidates: list[date] = []
                for dep in successors:
                    succ = late[dep['succ_id']]
                    lag  = timedelta(days=dep['lag'])

                    if dep['tipo'] == 'FS':
                        candidates.append(succ['late_start'] - lag)
                    elif dep['tipo'] == 'SS':
                        # late_start de predecesora = late_start de sucesora - lag
                        # late_finish = late_start + duration
                        ls_pred = succ['late_start'] - lag
                        candidates.append(
                            ls_pred + timedelta(days=duration_days)
                        )
                    elif dep['tipo'] == 'FF':
                        candidates.append(succ['late_finish'] - lag)
                    else:
                        candidates.append(succ['late_start'] - lag)

                lf = min(candidates + [project_end])

            ls = lf - timedelta(days=duration_days)
            late[tid] = {'late_start': ls, 'late_finish': lf}

        return late

    # ── SK-09: Calculate Float ────────────────────────────────────────────────

    @staticmethod
    def calculate_float(
        task_id: str,
        forward_data: ForwardData,
        backward_data: BackwardData,
        dependencies: list[TaskDependency],
    ) -> dict:
        """
        Calcula la holgura de una tarea.

        total_float = late_start - early_start
            → días que puede retrasarse sin afectar la fecha de fin del proyecto.

        free_float = min(sucesor.early_start - lag) - early_finish  (FS/default)
            → días que puede retrasarse sin afectar al sucesor inmediato.

        is_critical = (total_float == 0)

        Retorna:
            {
                'total_float': int,
                'free_float':  int,
                'is_critical': bool,
            }

        Si la tarea no está en forward_data/backward_data (sin fechas), retorna
        total_float=None para indicar que no fue procesada.
        """
        tid = str(task_id)

        if tid not in forward_data or tid not in backward_data:
            return {
                'total_float': None,
                'free_float':  None,
                'is_critical': False,
            }

        es = forward_data[tid]['early_start']
        ef = forward_data[tid]['early_finish']
        ls = backward_data[tid]['late_start']

        total_float = (ls - es).days

        # Free float: mínima holgura hacia el sucesor inmediato
        succ_deps = [
            d for d in dependencies
            if str(d.tarea_predecesora_id) == tid
            and str(d.tarea_sucesora_id) in forward_data
        ]

        if succ_deps:
            ff_candidates: list[int] = []
            for dep in succ_deps:
                succ_id = str(dep.tarea_sucesora_id)
                lag     = timedelta(days=dep.retraso_dias)
                succ_ef = forward_data[succ_id]['early_finish']
                succ_es = forward_data[succ_id]['early_start']

                if dep.tipo_dependencia == 'FS':
                    ff = (succ_es - lag - ef).days
                elif dep.tipo_dependencia == 'SS':
                    ff = (succ_es - lag - es).days
                elif dep.tipo_dependencia == 'FF':
                    ff = (succ_ef - lag - ef).days
                else:
                    ff = (succ_es - lag - ef).days

                ff_candidates.append(ff)

            free_float = min(ff_candidates)
        else:
            # Sin sucesores → free_float == total_float
            free_float = total_float

        return {
            'total_float': total_float,
            'free_float':  free_float,
            'is_critical': total_float == 0,
        }

    # ── SK-10: Critical Path ──────────────────────────────────────────────────

    @staticmethod
    def get_critical_path(
        tasks: list[Task],
        forward_data: ForwardData,
        backward_data: BackwardData,
        dependencies: list[TaskDependency],
    ) -> list[str]:
        """
        Retorna la lista de task_ids (str) que forman la ruta crítica.

        Una tarea es crítica cuando total_float == 0.
        Solo incluye tareas presentes en forward_data (con fechas definidas).

        Retorna:
            [str(task_id), ...]  ordenados según forward_data (orden topológico).
        """
        critical: list[str] = []

        for task in tasks:
            tid = str(task.id)
            float_data = SchedulingService.calculate_float(
                task_id=tid,
                forward_data=forward_data,
                backward_data=backward_data,
                dependencies=dependencies,
            )
            if float_data['is_critical']:
                critical.append(tid)

        logger.info(
            "CPM: ruta crítica calculada",
            extra={"critical_count": len(critical), "total_tasks": len(tasks)},
        )
        return critical

    # ── Helper: full CPM run ──────────────────────────────────────────────────

    @staticmethod
    def run_cpm(
        project_id: str,
        company_id: str,
    ) -> dict:
        """
        Ejecuta el CPM completo sobre un proyecto.

        Carga tareas + dependencias desde BD y retorna:
        {
            'sorted_tasks':   list[Task],
            'forward_data':   ForwardData,
            'backward_data':  BackwardData,
            'critical_path':  [str(task_id), ...],
            'project_end_date': date | None,
            'tasks_excluded':  [str(task_id), ...],   # sin fecha_inicio/fin
        }

        Raises:
            ValidationError: si hay ciclos en las dependencias.
            Project.DoesNotExist: si el proyecto no pertenece a la company.
        """
        project = Project.objects.get(id=project_id, company_id=company_id)

        # Solo tareas con fechas (requisito CPM)
        all_tasks = list(
            Task.objects.filter(
                proyecto_id=project_id,
                company_id=company_id,
            ).exclude(estado__in=['cancelled', 'completed']).select_related('fase')
        )

        tasks_with_dates = [
            t for t in all_tasks
            if t.fecha_inicio and t.fecha_fin
        ]
        tasks_excluded = [
            str(t.id) for t in all_tasks
            if not (t.fecha_inicio and t.fecha_fin)
        ]

        if not tasks_with_dates:
            return {
                'sorted_tasks':    [],
                'forward_data':    {},
                'backward_data':   {},
                'critical_path':   [],
                'project_end_date': project.fecha_fin_planificada,
                'tasks_excluded':  [str(t.id) for t in all_tasks],
            }

        # Dependencias solo entre tareas con fechas
        task_ids_with_dates = {str(t.id) for t in tasks_with_dates}
        dependencies = list(
            TaskDependency.objects.filter(
                company_id=company_id,
                tarea_predecesora__proyecto_id=project_id,
            ).filter(
                tarea_predecesora_id__in=task_ids_with_dates,
                tarea_sucesora_id__in=task_ids_with_dates,
            )
        )

        project_start: date = project.fecha_inicio_planificada or date.today()

        sorted_tasks = SchedulingService.topological_sort(tasks_with_dates, dependencies)

        forward_data  = SchedulingService.forward_pass(sorted_tasks, dependencies, project_start)
        project_end: date = (
            max(v['early_finish'] for v in forward_data.values())
            if forward_data else project_start
        )
        backward_data = SchedulingService.backward_pass(sorted_tasks, dependencies, project_end)

        critical_path = SchedulingService.get_critical_path(
            sorted_tasks, forward_data, backward_data, dependencies
        )

        return {
            'sorted_tasks':    sorted_tasks,
            'forward_data':    forward_data,
            'backward_data':   backward_data,
            'critical_path':   critical_path,
            'project_end_date': project_end,
            'tasks_excluded':  tasks_excluded,
        }

    # ── SK-11 / SK-12: Auto-Schedule (ASAP + ALAP) ───────────────────────────

    @staticmethod
    @transaction.atomic
    def auto_schedule_project(
        project_id: str,
        company_id: str,
        scheduling_mode: str = 'asap',
        respect_constraints: bool = True,
        dry_run: bool = False,
    ) -> dict:
        """
        Reprograma todas las tareas del proyecto usando CPM.

        Modes:
          'asap' — As Soon As Possible: aplica early_start/early_finish.
          'alap' — As Late As Possible: aplica late_start/late_finish.

        Flujo:
          1. Cargar tareas con fechas (excluir sin fecha_inicio/fecha_fin).
          2. run_cpm() → topological_sort + forward + backward.
          3. Aplicar fechas según scheduling_mode.
          4. Si respect_constraints=True → apply_constraints().
          5. Si dry_run=False → bulk_update tasks + invalidar caché.

        Retorna:
            {
                'tasks_rescheduled':   int,
                'tasks_excluded':      [str(task_id), ...],
                'new_project_end_date': date,
                'critical_path':       [str(task_id), ...],
                'warnings':            [str, ...],
                'dry_run':             bool,
            }

        Raises:
            ValidationError: si hay ciclos en las dependencias.
            Project.DoesNotExist: si el proyecto no pertenece a la company.
        """
        if scheduling_mode not in ('asap', 'alap'):
            raise ValidationError(
                f'scheduling_mode inválido: "{scheduling_mode}". '
                'Use "asap" o "alap".'
            )

        cpm = SchedulingService.run_cpm(project_id, company_id)

        sorted_tasks: list[Task]    = cpm['sorted_tasks']
        forward_data:  ForwardData  = cpm['forward_data']
        backward_data: BackwardData = cpm['backward_data']
        critical_path: list[str]    = cpm['critical_path']
        project_end:   date         = cpm['project_end_date']
        tasks_excluded: list[str]   = cpm['tasks_excluded']
        warnings:       list[str]   = []

        if tasks_excluded:
            warnings.append(
                f'{len(tasks_excluded)} tarea(s) excluida(s) por no tener '
                f'fecha_inicio o fecha_fin.'
            )

        # Construir mapa de nuevas fechas según modo
        new_dates: dict[str, dict[str, date]] = {}

        for task in sorted_tasks:
            tid = str(task.id)
            if scheduling_mode == 'asap' and tid in forward_data:
                new_dates[tid] = {
                    'fecha_inicio': forward_data[tid]['early_start'],
                    'fecha_fin':    forward_data[tid]['early_finish'],
                }
            elif scheduling_mode == 'alap' and tid in backward_data:
                new_dates[tid] = {
                    'fecha_inicio': backward_data[tid]['late_start'],
                    'fecha_fin':    backward_data[tid]['late_finish'],
                }

        # Aplicar restricciones sobre las fechas calculadas
        if respect_constraints and new_dates:
            new_dates, constraint_warnings = SchedulingService.apply_constraints(
                tasks=sorted_tasks,
                company_id=company_id,
                dates=new_dates,
            )
            warnings.extend(constraint_warnings)

        if dry_run:
            task_map_preview: dict[str, Task] = {str(t.id): t for t in sorted_tasks}
            # Only include tasks whose dates actually change
            preview_data = {}
            for tid, d in new_dates.items():
                t = task_map_preview.get(tid)
                if not t:
                    continue
                if t.fecha_inicio == d['fecha_inicio'] and t.fecha_fin == d['fecha_fin']:
                    continue  # Skip unchanged tasks
                preview_data[tid] = {
                    'nombre':    t.nombre,
                    'old_start': str(t.fecha_inicio) if t.fecha_inicio else None,
                    'old_end':   str(t.fecha_fin) if t.fecha_fin else None,
                    'new_start': str(d['fecha_inicio']),
                    'new_end':   str(d['fecha_fin']),
                }
            return {
                'tasks_rescheduled':    len(preview_data),
                'tasks_excluded':       tasks_excluded,
                'new_project_end_date': project_end,
                'critical_path':        critical_path,
                'warnings':             warnings,
                'dry_run':              True,
                'preview':              preview_data,
            }

        # Aplicar fechas a los objetos Task y guardar en bulk (only changed)
        task_map: dict[str, Task] = {str(t.id): t for t in sorted_tasks}
        tasks_to_update: list[Task] = []

        for tid, dates in new_dates.items():
            task = task_map[tid]
            if task.fecha_inicio == dates['fecha_inicio'] and task.fecha_fin == dates['fecha_fin']:
                continue  # Skip unchanged
            task.fecha_inicio = dates['fecha_inicio']
            task.fecha_fin    = dates['fecha_fin']
            tasks_to_update.append(task)

        if tasks_to_update:
            Task.objects.bulk_update(tasks_to_update, ['fecha_inicio', 'fecha_fin'])

        # Invalidar caché de ruta crítica
        from django.core.cache import cache
        cache.delete(f'critical_path:{project_id}:{company_id}')

        logger.info(
            'auto_schedule: proyecto reprogramado',
            extra={
                'project_id':      project_id,
                'company_id':      company_id,
                'mode':            scheduling_mode,
                'tasks_updated':   len(tasks_to_update),
                'critical_path':   len(critical_path),
            },
        )

        return {
            'tasks_rescheduled':    len(tasks_to_update),
            'tasks_excluded':       tasks_excluded,
            'new_project_end_date': project_end,
            'critical_path':        critical_path,
            'warnings':             warnings,
            'dry_run':              False,
        }

    # ── SK-13: Apply Constraints ──────────────────────────────────────────────

    @staticmethod
    def apply_constraints(
        tasks: list[Task],
        company_id: str,
        dates: dict[str, dict[str, date]],
    ) -> tuple[dict[str, dict[str, date]], list[str]]:
        """
        Ajusta las fechas calculadas por CPM según las restricciones activas.

        Prioridad de resolución (de mayor a menor):
          1. MUST_START_ON / MUST_FINISH_ON   — absolutas
          2. START_NO_EARLIER/LATER_THAN       — límites de inicio
          3. FINISH_NO_EARLIER/LATER_THAN      — límites de fin
          4. ASAP / ALAP                       — ya resueltas por scheduling_mode

        Retorna:
            (dates_ajustadas, lista_de_warnings)
        """
        task_ids = {str(t.id) for t in tasks}

        constraints_qs = TaskConstraint.objects.filter(
            company_id=company_id,
            task_id__in=task_ids,
        ).select_related('task')

        # Agrupar por tarea
        by_task: dict[str, list[TaskConstraint]] = defaultdict(list)
        for c in constraints_qs:
            by_task[str(c.task_id)].append(c)

        adjusted = dict(dates)  # copia superficial de la estructura
        warnings: list[str] = []

        for tid, task_constraints in by_task.items():
            if tid not in adjusted:
                continue

            fi: date = adjusted[tid]['fecha_inicio']
            ff: date = adjusted[tid]['fecha_fin']
            duration: timedelta = ff - fi

            for constraint in task_constraints:
                ctype = constraint.constraint_type
                cdate = constraint.constraint_date

                if ctype == ConstraintType.ASAP or ctype == ConstraintType.ALAP:
                    # Ya resuelto por scheduling_mode; sin ajuste adicional
                    continue

                if not cdate:
                    # Sin fecha no se puede aplicar restricción con fecha
                    warnings.append(
                        f'Tarea {tid}: constraint {ctype} sin constraint_date — omitida.'
                    )
                    continue

                if ctype == ConstraintType.MUST_START_ON:
                    fi = cdate
                    ff = fi + duration

                elif ctype == ConstraintType.MUST_FINISH_ON:
                    ff = cdate
                    fi = ff - duration

                elif ctype == ConstraintType.START_NO_EARLIER_THAN:
                    if fi < cdate:
                        fi = cdate
                        ff = fi + duration

                elif ctype == ConstraintType.START_NO_LATER_THAN:
                    if fi > cdate:
                        fi = cdate
                        ff = fi + duration
                        warnings.append(
                            f'Tarea {tid}: START_NO_LATER_THAN forzó inicio '
                            f'a {cdate} (CPM calculó {adjusted[tid]["fecha_inicio"]}).'
                        )

                elif ctype == ConstraintType.FINISH_NO_EARLIER_THAN:
                    if ff < cdate:
                        ff = cdate
                        fi = ff - duration

                elif ctype == ConstraintType.FINISH_NO_LATER_THAN:
                    if ff > cdate:
                        ff = cdate
                        fi = ff - duration
                        warnings.append(
                            f'Tarea {tid}: FINISH_NO_LATER_THAN forzó fin '
                            f'a {cdate} (CPM calculó {adjusted[tid]["fecha_fin"]}).'
                        )

            adjusted[tid] = {'fecha_inicio': fi, 'fecha_fin': ff}

        return adjusted, warnings


# ─────────────────────────────────────────────────────────────────────────────
# SK-14 / SK-15: ResourceLevelingService
# ─────────────────────────────────────────────────────────────────────────────

class ResourceLevelingService:
    """
    Balancea la carga de recursos moviendo tareas con float positivo
    para eliminar períodos de sobreasignación.

    Limitación MVP: trabaja con porcentaje de asignación total por día.
    No descuenta ausencias aprobadas (ResourceAvailability) — mejora futura.
    """

    # ── SK-14: Detect Overload Periods ───────────────────────────────────────

    @staticmethod
    def calculate_daily_workload(
        project_id: str,
        company_id: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, dict[str, float]]:
        """
        Calcula la carga diaria (suma de porcentajes) por usuario en el rango.

        Retorna:
            {str(user_id): {str(date): total_pct}}

        Solo incluye asignaciones activas de tareas del proyecto.
        """
        assignments = ResourceAssignment.objects.filter(
            company_id=company_id,
            tarea__proyecto_id=project_id,
            activo=True,
            fecha_inicio__lte=end_date,
            fecha_fin__gte=start_date,
        ).exclude(
            tarea__estado__in=['completed', 'cancelled']
        ).select_related('tarea')

        workload: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        current = start_date
        while current <= end_date:
            day_str = str(current)
            for asgn in assignments:
                if asgn.fecha_inicio <= current <= asgn.fecha_fin:
                    uid = str(asgn.usuario_id)
                    workload[uid][day_str] += float(asgn.porcentaje_asignacion)
            current += timedelta(days=1)

        # Convertir defaultdicts a dicts normales
        return {uid: dict(days) for uid, days in workload.items()}

    @staticmethod
    def detect_overload_periods(
        project_id: str,
        company_id: str,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        """
        Identifica días donde la carga supera el 100% de capacidad.

        Retorna:
            [
                {
                    'user_id':           str,
                    'date':              str(YYYY-MM-DD),
                    'total_pct':         float,
                    'overload_pct':      float,   # total - 100
                    'task_ids':          [str, ...],
                },
                ...
            ]
        """
        workload = ResourceLevelingService.calculate_daily_workload(
            project_id, company_id, start_date, end_date
        )

        assignments = list(
            ResourceAssignment.objects.filter(
                company_id=company_id,
                tarea__proyecto_id=project_id,
                activo=True,
                fecha_inicio__lte=end_date,
                fecha_fin__gte=start_date,
            ).exclude(
                tarea__estado__in=['completed', 'cancelled']
            ).select_related('tarea')
        )

        overloads: list[dict] = []

        for uid, daily in workload.items():
            for day_str, total_pct in daily.items():
                if total_pct <= 100:
                    continue

                day = date.fromisoformat(day_str)
                task_ids = [
                    str(a.tarea_id)
                    for a in assignments
                    if str(a.usuario_id) == uid
                    and a.fecha_inicio <= day <= a.fecha_fin
                ]

                overloads.append({
                    'user_id':      uid,
                    'date':         day_str,
                    'total_pct':    round(total_pct, 2),
                    'overload_pct': round(total_pct - 100, 2),
                    'task_ids':     task_ids,
                })

        return sorted(overloads, key=lambda x: (x['date'], x['user_id']))

    # ── SK-15: Level Resources ────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def level_resources(
        project_id: str,
        company_id: str,
        dry_run: bool = False,
        max_iterations: int = 500,
    ) -> dict:
        """
        Mueve tareas con float > 0 para eliminar sobreasignación de recursos.

        Algoritmo greedy:
          1. Calcular carga diaria y detectar sobrecargas.
          2. Por cada sobrecarga, identificar tareas asignadas con float > 0.
          3. Ordenar por float descendente (mover primero las menos críticas).
          4. Retrasar la tarea un día; actualizar workload.
          5. Repetir hasta sin sobrecargas o max_iterations alcanzado.

        Retorna:
            {
                'tasks_moved':          int,
                'iterations_used':      int,
                'max_overload_before':  float,
                'max_overload_after':   float,
                'leveling_effective':   bool,
                'warnings':             [str, ...],
                'dry_run':              bool,
            }
        """
        cpm = SchedulingService.run_cpm(project_id, company_id)
        sorted_tasks: list[Task]    = cpm['sorted_tasks']
        forward_data:  ForwardData  = cpm['forward_data']
        backward_data: BackwardData = cpm['backward_data']
        dependencies                = TaskDependency.objects.filter(
            company_id=company_id,
            tarea_predecesora__proyecto_id=project_id,
        )

        if not sorted_tasks:
            return {
                'tasks_moved': 0, 'iterations_used': 0,
                'max_overload_before': 0.0, 'max_overload_after': 0.0,
                'leveling_effective': True, 'warnings': [], 'dry_run': dry_run,
            }

        project_start: date = min(
            (t.fecha_inicio for t in sorted_tasks if t.fecha_inicio),
            default=date.today(),
        )
        project_end: date = cpm['project_end_date'] or date.today()

        # Carga inicial antes de nivelar
        overloads_before = ResourceLevelingService.detect_overload_periods(
            project_id, company_id, project_start, project_end,
        )
        max_before = max((o['total_pct'] for o in overloads_before), default=0.0)

        if not overloads_before:
            return {
                'tasks_moved': 0, 'iterations_used': 0,
                'max_overload_before': 0.0, 'max_overload_after': 0.0,
                'leveling_effective': True,
                'warnings': ['No se detectaron sobrecargas. No se requiere nivelación.'],
                'dry_run': dry_run,
            }

        # Mapa mutable de fechas (no modificar BD hasta confirmar dry_run=False)
        mutable_dates: dict[str, dict[str, date]] = {
            str(t.id): {'fecha_inicio': t.fecha_inicio, 'fecha_fin': t.fecha_fin}
            for t in sorted_tasks
            if t.fecha_inicio and t.fecha_fin
        }

        tasks_moved:    set[str] = set()
        warnings:       list[str] = []
        iteration = 0

        # Precargar nombres de usuarios para mensajes legibles
        User = get_user_model()
        involved_user_ids = {o['user_id'] for o in overloads_before}
        user_names: dict[str, str] = {
            str(u.id): (
                f'{u.first_name} {u.last_name}'.strip() or u.email
            )
            for u in User.objects.filter(id__in=involved_user_ids)
        }
        # Usuarios con sobrecargas no resolubles (acumulador estructurado)
        unresolvable_data: dict[str, dict] = {}  # user_name → {dates, task_ids_by_date}

        while iteration < max_iterations:
            overloads = ResourceLevelingService.detect_overload_periods(
                project_id, company_id, project_start, project_end,
            )
            if not overloads:
                break

            moved_this_iter = False

            for overload in overloads:
                day      = date.fromisoformat(overload['date'])
                task_ids = overload['task_ids']

                # Calcular float de cada tarea implicada
                candidates: list[tuple[int, str]] = []
                for tid in task_ids:
                    f = SchedulingService.calculate_float(
                        task_id=tid,
                        forward_data=forward_data,
                        backward_data=backward_data,
                        dependencies=dependencies,
                    )
                    total_float = f['total_float']
                    if total_float is not None and total_float > 0:
                        candidates.append((total_float, tid))

                if not candidates:
                    uid = overload['user_id']
                    uname = user_names.get(uid, uid)
                    if uname not in unresolvable_data:
                        unresolvable_data[uname] = {
                            'dates': set(), 'task_ids_by_date': {}, 'max_pct': 0.0,
                        }
                    unresolvable_data[uname]['dates'].add(overload['date'])
                    unresolvable_data[uname]['task_ids_by_date'][overload['date']] = overload['task_ids']
                    unresolvable_data[uname]['max_pct'] = max(
                        unresolvable_data[uname]['max_pct'],
                        overload['total_pct'],
                    )
                    continue

                # Mover la tarea con mayor float (menos crítica) un día adelante
                candidates.sort(reverse=True)
                _, tid_to_move = candidates[0]

                if tid_to_move not in mutable_dates:
                    continue

                old_fi = mutable_dates[tid_to_move]['fecha_inicio']
                old_ff = mutable_dates[tid_to_move]['fecha_fin']
                duration = old_ff - old_fi

                new_fi = old_fi + timedelta(days=1)
                new_ff = new_fi + duration

                mutable_dates[tid_to_move] = {
                    'fecha_inicio': new_fi,
                    'fecha_fin':    new_ff,
                }
                tasks_moved.add(tid_to_move)
                moved_this_iter = True

                # Actualizar also ResourceAssignment en BD para que detect_overload_periods
                # refleje el cambio en la siguiente iteración
                if not dry_run:
                    ResourceAssignment.objects.filter(
                        company_id=company_id,
                        tarea_id=tid_to_move,
                        activo=True,
                    ).update(
                        fecha_inicio=new_fi,
                        fecha_fin=new_ff,
                    )

                break  # Recalcular overloads desde cero tras cada movimiento

            if not moved_this_iter:
                break  # No hay más candidatos a mover

            iteration += 1

        if iteration >= max_iterations:
            warnings.append(
                f'Nivelación detenida: se alcanzó el límite de {max_iterations} '
                'iteraciones. Pueden quedar sobrecargas sin resolver.'
            )

        # task_map usado tanto para unresolvable_overloads como para task_changes
        task_map = {str(t.id): t for t in sorted_tasks}

        # Construir datos estructurados de sobrecargas irresolubles
        unresolvable_overloads: list[dict] = []
        for uname, data in unresolvable_data.items():
            sorted_dates = sorted(data['dates'])
            all_task_ids: set[str] = set()
            for tids in data['task_ids_by_date'].values():
                all_task_ids.update(tids)
            tasks_info: list[dict] = []
            for tid in all_task_ids:
                t = task_map.get(tid)
                if not t:
                    continue
                asgn = ResourceAssignment.objects.filter(
                    tarea_id=tid, activo=True, company_id=company_id,
                ).first()
                pct = float(asgn.porcentaje_asignacion) if asgn else 0.0
                tasks_info.append({'task_name': t.nombre, 'porcentaje': round(pct, 1)})
            unresolvable_overloads.append({
                'user_name':     uname,
                'overload_days': len(sorted_dates),
                'date_from':     sorted_dates[0],
                'date_to':       sorted_dates[-1],
                'tasks':         tasks_info,
                'max_pct':       round(data['max_pct'], 1),
            })

        overloads_after = ResourceLevelingService.detect_overload_periods(
            project_id, company_id, project_start, project_end,
        )
        max_after = max((o['total_pct'] for o in overloads_after), default=0.0)

        # Build per-task change details
        task_changes: list[dict] = []
        for tid in tasks_moved:
            t = task_map.get(tid)
            md = mutable_dates.get(tid)
            if t and md:
                task_changes.append({
                    'task_id':       tid,
                    'task_name':     t.nombre,
                    'current_start': str(t.fecha_inicio),
                    'new_start':     str(md['fecha_inicio']),
                    'current_end':   str(t.fecha_fin),
                    'new_end':       str(md['fecha_fin']),
                })

        if not dry_run and tasks_moved:
            tasks_to_update: list[Task] = []
            for tid in tasks_moved:
                if tid in task_map and tid in mutable_dates:
                    t = task_map[tid]
                    t.fecha_inicio = mutable_dates[tid]['fecha_inicio']
                    t.fecha_fin    = mutable_dates[tid]['fecha_fin']
                    tasks_to_update.append(t)
            if tasks_to_update:
                Task.objects.bulk_update(tasks_to_update, ['fecha_inicio', 'fecha_fin'])

            logger.info(
                'level_resources: nivelación aplicada',
                extra={
                    'project_id':      project_id,
                    'tasks_moved':     len(tasks_moved),
                    'iterations':      iteration,
                    'max_before':      max_before,
                    'max_after':       max_after,
                },
            )

        return {
            'tasks_moved':            len(tasks_moved),
            'iterations_used':        iteration,
            'max_overload_before':    round(max_before, 2),
            'max_overload_after':     round(max_after, 2),
            'leveling_effective':     max_after <= 100,
            'warnings':               warnings,
            'dry_run':                dry_run,
            'task_changes':           task_changes,
            'unresolvable_overloads': unresolvable_overloads,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SK-16 / SK-17: BaselineService
# ─────────────────────────────────────────────────────────────────────────────

class BaselineService:
    """
    Gestiona snapshots del plan del proyecto (baselines).

    create_baseline() captura el estado actual y lo persiste en JSON.
    compare_to_baseline() calcula la desviación vs el plan original.
    """

    # ── SK-16 ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_baseline(
        project_id: str,
        company_id: str,
        name: str,
        description: str = '',
        set_as_active: bool = True,
    ) -> ProjectBaseline:
        """
        Captura un snapshot del proyecto y lo guarda como baseline.

        Si set_as_active=True desactiva el baseline activo anterior
        (garantizado por UniqueConstraint parcial en el modelo).

        Raises:
            Project.DoesNotExist: si el proyecto no pertenece a la company.
        """
        project = Project.objects.get(id=project_id, company_id=company_id)

        tasks = list(
            Task.objects.filter(
                proyecto_id=project_id,
                company_id=company_id,
            ).exclude(estado='cancelled').values(
                'id', 'nombre', 'codigo', 'estado',
                'fecha_inicio', 'fecha_fin', 'horas_estimadas',
            )
        )

        assignments = list(
            ResourceAssignment.objects.filter(
                company_id=company_id,
                tarea__proyecto_id=project_id,
                activo=True,
            ).values(
                'id', 'tarea_id', 'usuario_id',
                'porcentaje_asignacion', 'fecha_inicio', 'fecha_fin',
            )
        )

        # Serializar fechas a str para JSON
        def _serialize(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        tasks_snapshot = [
            {k: _serialize(v) if hasattr(v, 'isoformat') else str(v) if v is not None else None
             for k, v in row.items()}
            for row in tasks
        ]
        resources_snapshot = [
            {k: _serialize(v) if hasattr(v, 'isoformat') else str(v) if v is not None else None
             for k, v in row.items()}
            for row in assignments
        ]

        # Ruta crítica actual
        critical_path: list[str] = []
        project_end_date = project.fecha_fin_planificada
        try:
            cpm = SchedulingService.run_cpm(project_id, company_id)
            critical_path = cpm['critical_path']
            project_end_date = cpm['project_end_date'] or project.fecha_fin_planificada
        except Exception as exc:
            logger.warning(
                'create_baseline: CPM falló, critical_path vacío',
                extra={'project_id': project_id, 'error': str(exc)},
            )

        if set_as_active:
            ProjectBaseline.objects.filter(
                company_id=company_id,
                project_id=project_id,
                is_active_baseline=True,
            ).update(is_active_baseline=False)

        baseline = ProjectBaseline.objects.create(
            company_id=company_id,
            project_id=project_id,
            name=name,
            description=description,
            is_active_baseline=set_as_active,
            tasks_snapshot=tasks_snapshot,
            resources_snapshot=resources_snapshot,
            critical_path_snapshot=critical_path,
            project_end_date_snapshot=project_end_date,
            total_tasks_snapshot=len(tasks_snapshot),
        )

        logger.info(
            'create_baseline: baseline creado',
            extra={
                'baseline_id': str(baseline.id),
                'project_id':  project_id,
                'tasks':       len(tasks_snapshot),
                'active':      set_as_active,
            },
        )
        return baseline

    # ── SK-17 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def compare_to_baseline(
        project_id: str,
        company_id: str,
        baseline_id: str,
    ) -> dict:
        """
        Compara el plan actual del proyecto contra un baseline guardado.

        Retorna:
            {
                'baseline_name':          str,
                'baseline_end_date':      date | None,
                'current_end_date':       date | None,
                'schedule_variance_days': int,
                'tasks': [{
                    'task_id', 'nombre', 'codigo',
                    'baseline_start', 'baseline_finish',
                    'current_start', 'current_finish',
                    'variance_days': int,
                    'status': 'ahead' | 'on_schedule' | 'behind',
                }],
                'summary': {'ahead': int, 'on_schedule': int, 'behind': int},
            }

        Raises:
            ProjectBaseline.DoesNotExist: si el baseline no existe o no pertenece a la company.
        """
        from datetime import date as date_type

        baseline = ProjectBaseline.objects.get(
            id=baseline_id,
            company_id=company_id,
            project_id=project_id,
        )

        # Estado actual de las tareas
        current_tasks = {
            str(t['id']): t
            for t in Task.objects.filter(
                proyecto_id=project_id,
                company_id=company_id,
            ).exclude(estado='cancelled').values('id', 'nombre', 'codigo', 'fecha_inicio', 'fecha_fin')
        }

        # Fecha fin actual del proyecto
        current_end_date = None
        try:
            cpm = SchedulingService.run_cpm(project_id, company_id)
            current_end_date = cpm['project_end_date']
        except Exception:
            pass
        if not current_end_date:
            ends = [
                t['fecha_fin'] for t in current_tasks.values()
                if t['fecha_fin']
            ]
            current_end_date = max(ends) if ends else None

        # Parsear fecha del snapshot
        def _parse(val):
            if val is None:
                return None
            if isinstance(val, date_type):
                return val
            try:
                return date_type.fromisoformat(str(val))
            except (ValueError, TypeError):
                return None

        baseline_end = baseline.project_end_date_snapshot

        schedule_variance = 0
        if baseline_end and current_end_date:
            schedule_variance = (current_end_date - baseline_end).days

        task_rows: list[dict] = []
        summary = {'ahead': 0, 'on_schedule': 0, 'behind': 0}

        for snap in baseline.tasks_snapshot:
            tid = str(snap.get('id', ''))
            bl_start  = _parse(snap.get('fecha_inicio'))
            bl_finish = _parse(snap.get('fecha_fin'))
            current   = current_tasks.get(tid)
            cur_start  = _parse(current['fecha_inicio'])  if current else None
            cur_finish = _parse(current['fecha_fin'])     if current else None

            variance_days = 0
            if bl_finish and cur_finish:
                variance_days = (cur_finish - bl_finish).days

            if variance_days < 0:
                task_status = 'ahead'
                summary['ahead'] += 1
            elif variance_days == 0:
                task_status = 'on_schedule'
                summary['on_schedule'] += 1
            else:
                task_status = 'behind'
                summary['behind'] += 1

            task_rows.append({
                'task_id':         tid,
                'nombre':          snap.get('nombre', ''),
                'codigo':          snap.get('codigo', ''),
                'baseline_start':  str(bl_start)  if bl_start  else None,
                'baseline_finish': str(bl_finish) if bl_finish else None,
                'current_start':   str(cur_start)  if cur_start  else None,
                'current_finish':  str(cur_finish) if cur_finish else None,
                'variance_days':   variance_days,
                'status':          task_status,
            })

        return {
            'baseline_name':          baseline.name,
            'baseline_end_date':      str(baseline_end) if baseline_end else None,
            'current_end_date':       str(current_end_date) if current_end_date else None,
            'schedule_variance_days': schedule_variance,
            'tasks':                  task_rows,
            'summary':                summary,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SK-18 / SK-19 / SK-20: WhatIfService
# ─────────────────────────────────────────────────────────────────────────────

class WhatIfService:
    """
    Gestiona escenarios hipotéticos de scheduling.

    CRÍTICO: run_simulation() nunca modifica datos reales en BD.
    Aplica cambios sobre copias en memoria y ejecuta CPM sobre ellas.
    """

    # ── SK-18 ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_scenario(
        project_id: str,
        company_id: str,
        user_id: str,
        name: str,
        description: str = '',
        task_changes: dict | None = None,
        resource_changes: dict | None = None,
        dependency_changes: dict | None = None,
    ) -> WhatIfScenario:
        """
        Crea un escenario con los cambios propuestos. No ejecuta simulación.

        Raises:
            Project.DoesNotExist: si el proyecto no pertenece a la company.
        """
        Project.objects.get(id=project_id, company_id=company_id)

        scenario = WhatIfScenario.objects.create(
            company_id=company_id,
            project_id=project_id,
            created_by_id=user_id,
            name=name,
            description=description,
            task_changes=task_changes or {},
            resource_changes=resource_changes or {},
            dependency_changes=dependency_changes or {},
        )

        logger.info(
            'create_scenario: escenario creado',
            extra={'scenario_id': str(scenario.id), 'project_id': project_id},
        )
        return scenario

    # ── SK-19 ─────────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def run_simulation(
        scenario_id: str,
        company_id: str,
    ) -> WhatIfScenario:
        """
        Ejecuta el CPM sobre una copia en memoria con los cambios del escenario.

        ⚠️ CRÍTICO: nunca modifica Task, TaskDependency ni ResourceAssignment reales.
        Todos los cambios se aplican sobre objetos Python en memoria.

        Algoritmo:
          1. Cargar datos reales del proyecto.
          2. Aplicar task_changes sobre copias en memoria.
          3. Aplicar dependency_changes sobre copias en memoria.
          4. Ejecutar CPM sobre las copias.
          5. Guardar resultados en WhatIfScenario.

        Raises:
            WhatIfScenario.DoesNotExist: si el escenario no existe.
        """
        from datetime import date as date_type
        import copy as _copy

        scenario = WhatIfScenario.objects.select_related('project').get(
            id=scenario_id,
            company_id=company_id,
        )
        project_id = str(scenario.project_id)

        # ── Cargar datos reales ──────────────────────────────────────────────
        real_tasks = list(
            Task.objects.filter(
                proyecto_id=project_id,
                company_id=company_id,
                fecha_inicio__isnull=False,
                fecha_fin__isnull=False,
            ).exclude(estado='cancelled')
        )
        real_deps = list(
            TaskDependency.objects.filter(
                company_id=company_id,
                tarea_predecesora__proyecto_id=project_id,
            )
        )

        project = scenario.project
        project_start: date = project.fecha_inicio_planificada or date_type.today()

        # ── Copias en memoria (NO modificar objetos originales) ──────────────

        class _TaskProxy:
            """Proxy ligero de Task para el CPM en memoria."""
            __slots__ = ('id', 'codigo', 'nombre', 'fecha_inicio', 'fecha_fin')
            def __init__(self, task: Task):
                self.id           = task.id
                self.codigo       = task.codigo
                self.nombre       = task.nombre
                self.fecha_inicio = task.fecha_inicio
                self.fecha_fin    = task.fecha_fin

        class _DepProxy:
            """Proxy ligero de TaskDependency para el CPM en memoria."""
            __slots__ = ('tarea_predecesora_id', 'tarea_sucesora_id', 'tipo_dependencia', 'retraso_dias')
            def __init__(self, dep: TaskDependency):
                self.tarea_predecesora_id = dep.tarea_predecesora_id
                self.tarea_sucesora_id    = dep.tarea_sucesora_id
                self.tipo_dependencia     = dep.tipo_dependencia
                self.retraso_dias         = dep.retraso_dias

        sim_tasks: list[_TaskProxy] = [_TaskProxy(t) for t in real_tasks]
        sim_deps:  list[_DepProxy]  = [_DepProxy(d) for d in real_deps]

        task_map_sim: dict[str, _TaskProxy] = {str(t.id): t for t in sim_tasks}

        # ── Aplicar task_changes ─────────────────────────────────────────────
        date_fields = {'fecha_inicio', 'fecha_fin'}
        for tid_str, changes in scenario.task_changes.items():
            proxy = task_map_sim.get(tid_str)
            if proxy is None:
                continue
            for field, value in changes.items():
                if field in date_fields and isinstance(value, str):
                    try:
                        value = date_type.fromisoformat(value)
                    except (ValueError, TypeError):
                        continue
                if hasattr(proxy, field):
                    setattr(proxy, field, value)

        # ── Aplicar dependency_changes (solo retraso_dias) ───────────────────
        dep_map_sim: dict[str, _DepProxy] = {}
        for i, dep in enumerate(real_deps):
            dep_map_sim[str(dep.id) if hasattr(dep, 'id') else str(i)] = sim_deps[i]

        for dep_id_str, changes in scenario.dependency_changes.items():
            proxy = dep_map_sim.get(dep_id_str)
            if proxy and 'retraso_dias' in changes:
                proxy.retraso_dias = int(changes['retraso_dias'])

        # ── Ejecutar CPM en memoria ──────────────────────────────────────────
        warnings_sim: list[str] = []
        sim_end_date: date_type | None = None
        sim_critical_path: list[str]   = []
        tasks_affected = 0

        try:
            from django.core.exceptions import ValidationError as DjangoValError
            sorted_sim = SchedulingService.topological_sort(sim_tasks, sim_deps)
            fwd = SchedulingService.forward_pass(sorted_sim, sim_deps, project_start)

            if fwd:
                sim_end_date = max(v['early_finish'] for v in fwd.values())
                bwd = SchedulingService.backward_pass(sorted_sim, sim_deps, sim_end_date)
                sim_critical_path = SchedulingService.get_critical_path(
                    sorted_sim, fwd, bwd, sim_deps
                )
                # Tareas afectadas = tareas con fechas distintas al plan real
                real_task_dates = {
                    str(t.id): (t.fecha_inicio, t.fecha_fin) for t in real_tasks
                }
                for tid_str, fwd_data in fwd.items():
                    real_fi, real_ff = real_task_dates.get(tid_str, (None, None))
                    if (fwd_data['early_start'] != real_fi
                            or fwd_data['early_finish'] != real_ff):
                        tasks_affected += 1

        except Exception as exc:
            warnings_sim.append(f'Error en simulación CPM: {exc}')
            logger.warning(
                'run_simulation: CPM falló',
                extra={'scenario_id': scenario_id, 'error': str(exc)},
            )

        # Delta vs plan actual
        from datetime import date as date_type2
        real_cpm_end: date_type2 | None = None
        try:
            real_cpm = SchedulingService.run_cpm(project_id, company_id)
            real_cpm_end = real_cpm['project_end_date']
        except Exception:
            pass

        days_delta: int | None = None
        if sim_end_date and real_cpm_end:
            days_delta = (sim_end_date - real_cpm_end).days

        # ── Guardar resultados en el escenario (no tocar datos reales) ───────
        from django.utils import timezone
        scenario.simulated_end_date      = sim_end_date
        scenario.simulated_critical_path = sim_critical_path
        scenario.days_delta              = days_delta
        scenario.tasks_affected_count    = tasks_affected
        scenario.simulation_ran_at       = timezone.now()
        scenario.save(update_fields=[
            'simulated_end_date', 'simulated_critical_path',
            'days_delta', 'tasks_affected_count', 'simulation_ran_at',
        ])

        logger.info(
            'run_simulation: simulación completada',
            extra={
                'scenario_id':    scenario_id,
                'sim_end_date':   str(sim_end_date),
                'days_delta':     days_delta,
                'tasks_affected': tasks_affected,
            },
        )
        return scenario

    # ── SK-20 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def compare_scenarios(
        scenario_ids: list[str],
        company_id: str,
    ) -> dict:
        """
        Tabla comparativa de múltiples escenarios vs el plan actual.

        Retorna:
            {
                'current_plan': {'end_date': str | None},
                'scenarios': [{
                    'id', 'name',
                    'simulated_end_date': str | None,
                    'days_delta':         int | None,
                    'tasks_affected_count': int | None,
                    'simulation_done':    bool,
                }],
            }
        """
        scenarios = list(
            WhatIfScenario.objects.filter(
                id__in=scenario_ids,
                company_id=company_id,
            ).select_related('project')
        )

        # Fecha fin actual del primer proyecto encontrado (todos deberían ser del mismo)
        current_end: str | None = None
        if scenarios:
            try:
                cpm = SchedulingService.run_cpm(
                    str(scenarios[0].project_id), company_id
                )
                current_end = str(cpm['project_end_date']) if cpm['project_end_date'] else None
            except Exception:
                pass

        return {
            'current_plan': {'end_date': current_end},
            'scenarios': [
                {
                    'id':                   str(s.id),
                    'name':                 s.name,
                    'simulated_end_date':   str(s.simulated_end_date) if s.simulated_end_date else None,
                    'days_delta':           s.days_delta,
                    'tasks_affected_count': s.tasks_affected_count,
                    'simulation_done':      s.simulation_ran_at is not None,
                }
                for s in scenarios
            ],
        }
