"""
SaiSuite — Proyectos: Analytics Services
TODA la lógica de negocio de Analytics va aquí.
Las views solo orquestan: reciben request → llaman service → retornan response.

Servicios implementados:
    - get_project_kpis()            AN-01
    - get_task_distribution()       AN-02
    - get_velocity_data()           AN-03
    - get_burn_rate_data()          AN-04
    - get_burn_down_data()          AN-05
    - get_resource_utilization()    AN-06
    - compare_projects()            AN-07
    - get_project_timeline()        AN-08
"""
import logging
from datetime import date, timedelta
from decimal import Decimal
from itertools import accumulate
from typing import Optional

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncWeek
from django.utils import timezone

from .models import Project, Task, Phase, TimesheetEntry
from .resource_services import calculate_user_workload

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AN-01: get_project_kpis
# ---------------------------------------------------------------------------

def get_project_kpis(project_id: str, company_id: str) -> dict:
    """
    Calcula los KPIs principales de un proyecto.

    Multi-tenant: filtra estrictamente por company_id.

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa

    Returns:
        dict con:
            - total_tasks: int
            - completed_tasks: int
            - overdue_tasks: int
            - completion_rate: float (0-100)
            - on_time_rate: float (0-100)
            - budget_variance: float (porcentaje de desviación)
            - velocity: float (tareas completadas por semana, últimas 4 semanas)
            - burn_rate: float (horas registradas por semana, últimas 4 semanas)
    """
    tasks_qs = Task.objects.filter(
        proyecto_id=project_id,
        company_id=company_id,
    )

    totals = tasks_qs.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(estado='completed')),
        horas_estimadas_total=Sum('horas_estimadas'),
        horas_registradas_total=Sum('horas_registradas'),
    )

    total_tasks = totals['total'] or 0
    completed_tasks = totals['completed'] or 0

    # Tasa de completitud
    completion_rate = (
        round(completed_tasks / total_tasks * 100, 2)
        if total_tasks > 0
        else 0.0
    )

    # Tareas vencidas: con fecha_limite en el pasado y no completadas/canceladas
    today = timezone.now().date()
    overdue_tasks = tasks_qs.filter(
        fecha_limite__lt=today,
        estado__in=['todo', 'in_progress', 'in_review', 'blocked'],
    ).count()

    # Tasa de puntualidad: tareas completadas cuya fecha_limite no ha pasado
    # En la actualización. Usamos updated_at como proxy de fecha de completion.
    # Calculamos en Python para evitar funciones de BD no portables.
    completed_with_deadline_qs = tasks_qs.filter(
        estado='completed',
        fecha_limite__isnull=False,
    ).values('updated_at', 'fecha_limite')

    completed_with_deadline_count = 0
    completed_on_time = 0
    for task in completed_with_deadline_qs:
        completed_with_deadline_count += 1
        # updated_at es un DateTimeField (TIMESTAMPTZ); comparamos la fecha
        completion_date = (
            task['updated_at'].date()
            if hasattr(task['updated_at'], 'date')
            else task['updated_at']
        )
        if completion_date <= task['fecha_limite']:
            completed_on_time += 1

    on_time_rate = (
        round(completed_on_time / completed_with_deadline_count * 100, 2)
        if completed_with_deadline_count > 0
        else 0.0
    )

    # Desviación presupuestaria (budget_variance)
    # Calculado como: (horas_registradas - horas_estimadas) / horas_estimadas * 100
    # Retorna None cuando no hay datos suficientes para calcular una varianza real:
    #   - horas_estimadas_total == 0: no hay línea base, división imposible.
    #   - horas_registradas_total == 0 y horas_estimadas_total > 0: sin timesheets
    #     registrados el resultado matemático sería -100 %, lo cual es engañoso
    #     porque el proyecto puede estar en etapas tempranas sin entradas aún.
    horas_estimadas_total = totals['horas_estimadas_total'] or Decimal('0')
    horas_registradas_total = totals['horas_registradas_total'] or Decimal('0')

    if horas_estimadas_total > 0 and horas_registradas_total > 0:
        budget_variance: Optional[float] = round(
            float(
                (horas_registradas_total - horas_estimadas_total)
                / horas_estimadas_total * 100
            ),
            2,
        )
    else:
        budget_variance = None

    # Velocidad: promedio de tareas completadas por semana (últimas 4 semanas)
    four_weeks_ago = today - timedelta(weeks=4)
    velocity_data = tasks_qs.filter(
        estado='completed',
        updated_at__date__gte=four_weeks_ago,
    ).annotate(
        week=TruncWeek('updated_at')
    ).values('week').annotate(
        tasks_completed=Count('id')
    ).order_by('week')

    if velocity_data:
        velocity = round(
            sum(v['tasks_completed'] for v in velocity_data) / max(len(velocity_data), 1),
            2,
        )
    else:
        velocity = 0.0

    # Burn rate: promedio de horas registradas por semana (últimas 4 semanas)
    timesheet_data = TimesheetEntry.objects.filter(
        tarea__proyecto_id=project_id,
        company_id=company_id,
        fecha__gte=four_weeks_ago,
    ).annotate(
        week=TruncWeek('fecha')
    ).values('week').annotate(
        hours=Sum('horas')
    ).order_by('week')

    if timesheet_data:
        burn_rate = round(
            float(sum(t['hours'] for t in timesheet_data)) / max(len(timesheet_data), 1),
            2,
        )
    else:
        burn_rate = 0.0

    logger.info(
        'analytics_kpis_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'total_tasks': total_tasks,
            'completion_rate': completion_rate,
        },
    )

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate,
        'on_time_rate': on_time_rate,
        'budget_variance': budget_variance,
        'velocity': velocity,
        'burn_rate': burn_rate,
    }


# ---------------------------------------------------------------------------
# AN-02: get_task_distribution
# ---------------------------------------------------------------------------

def get_task_distribution(project_id: str, company_id: str) -> dict:
    """
    Retorna la distribución de tareas por estado.

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa

    Returns:
        dict con conteos por estado y porcentajes:
            {todo, in_progress, in_review, completed, blocked, cancelled, total, percentages}
    """
    tasks_qs = Task.objects.filter(
        proyecto_id=project_id,
        company_id=company_id,
    )

    distribution = tasks_qs.values('estado').annotate(count=Count('id'))

    # Inicializar con ceros para todos los estados posibles
    result = {
        'todo': 0,
        'in_progress': 0,
        'in_review': 0,
        'completed': 0,
        'blocked': 0,
        'cancelled': 0,
    }

    for item in distribution:
        estado = item['estado']
        if estado in result:
            result[estado] = item['count']

    total = sum(result.values())
    result['total'] = total

    # Calcular porcentajes
    percentages = {}
    for estado in ['todo', 'in_progress', 'in_review', 'completed', 'blocked', 'cancelled']:
        percentages[estado] = (
            round(result[estado] / total * 100, 2) if total > 0 else 0.0
        )
    result['percentages'] = percentages

    logger.info(
        'analytics_distribution_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'total': total,
        },
    )

    return result


# ---------------------------------------------------------------------------
# AN-03: get_velocity_data
# ---------------------------------------------------------------------------

def get_velocity_data(
    project_id: str,
    company_id: str,
    periods: int = 8,
) -> list[dict]:
    """
    Retorna la velocidad semanal del equipo (tareas completadas por semana).

    La velocidad se define como el número de tareas que pasaron al estado
    'completed' en cada semana, usando updated_at como proxy de fecha de
    completitud.

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        periods: número de semanas a incluir (default 8)

    Returns:
        list[dict] con:
            [{week_label: str, week_start: date, tasks_completed: int}, ...]
        Siempre retorna exactamente `periods` elementos, con 0 para semanas sin datos.
    """
    today = timezone.now().date()
    # Inicio de la semana actual (lunes)
    current_week_start = today - timedelta(days=today.weekday())
    start_date = current_week_start - timedelta(weeks=periods - 1)

    velocity_qs = Task.objects.filter(
        proyecto_id=project_id,
        company_id=company_id,
        estado='completed',
        updated_at__date__gte=start_date,
    ).annotate(
        week=TruncWeek('updated_at')
    ).values('week').annotate(
        tasks_completed=Count('id')
    ).order_by('week')

    # Construir mapa semana → tareas completadas
    week_map: dict[date, int] = {}
    for item in velocity_qs:
        week_start = item['week'].date() if hasattr(item['week'], 'date') else item['week']
        week_map[week_start] = item['tasks_completed']

    # Generar lista completa con semanas vacías incluidas
    result = []
    for i in range(periods):
        week_start = start_date + timedelta(weeks=i)
        week_label = f'Week {i + 1}'
        result.append({
            'week_label': week_label,
            'week_start': week_start,
            'tasks_completed': week_map.get(week_start, 0),
        })

    logger.info(
        'analytics_velocity_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'periods': periods,
        },
    )

    return result


# ---------------------------------------------------------------------------
# AN-04: get_burn_rate_data
# ---------------------------------------------------------------------------

def get_burn_rate_data(
    project_id: str,
    company_id: str,
    periods: int = 8,
) -> list[dict]:
    """
    Retorna el burn rate semanal (horas registradas por semana).

    Usa TimesheetEntry.horas agrupado por semana para calcular el consumo
    real de horas del proyecto.

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        periods: número de semanas (default 8)

    Returns:
        list[dict] con:
            [{week_label: str, week_start: date, hours_registered: float}, ...]
    """
    today = timezone.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    start_date = current_week_start - timedelta(weeks=periods - 1)

    timesheet_qs = TimesheetEntry.objects.filter(
        tarea__proyecto_id=project_id,
        company_id=company_id,
        fecha__gte=start_date,
    ).annotate(
        week=TruncWeek('fecha')
    ).values('week').annotate(
        hours=Sum('horas')
    ).order_by('week')

    week_map: dict[date, float] = {}
    for item in timesheet_qs:
        week_start = item['week'].date() if hasattr(item['week'], 'date') else item['week']
        week_map[week_start] = float(item['hours'] or 0)

    result = []
    for i in range(periods):
        week_start = start_date + timedelta(weeks=i)
        result.append({
            'week_label': f'Week {i + 1}',
            'week_start': week_start,
            'hours_registered': week_map.get(week_start, 0.0),
        })

    logger.info(
        'analytics_burn_rate_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'periods': periods,
        },
    )

    return result


# ---------------------------------------------------------------------------
# AN-05: get_burn_down_data
# ---------------------------------------------------------------------------

def get_burn_down_data(
    project_id: str,
    company_id: str,
    granularity: str = 'week',
) -> dict:
    """
    Retorna los datos del gráfico Burn Down del proyecto.

    Estrategia:
    1. Obtener horas estimadas totales del proyecto
    2. Obtener horas registradas por semana (desde TimesheetEntry)
    3. Calcular el acumulativo en Python con itertools.accumulate
    4. Calcular línea ideal de quema (linear desde inicio hasta fin)

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        granularity: 'week' (actualmente solo se soporta 'week')

    Returns:
        dict con:
            - total_hours_estimated: float
            - data_points: list[dict] con:
                [{week_label, week_start, hours_remaining, hours_ideal, hours_actual_cumulative}]
    """
    # Paso 1: total de horas estimadas del proyecto
    totals = Task.objects.filter(
        proyecto_id=project_id,
        company_id=company_id,
    ).aggregate(
        total=Sum('horas_estimadas')
    )
    total_estimated = float(totals['total'] or Decimal('0'))

    # Paso 2: obtener rango de fechas del proyecto para calcular la línea ideal
    try:
        project = Project.objects.get(id=project_id, company_id=company_id)
        project_start = project.fecha_inicio_real or project.fecha_inicio_planificada
        project_end = project.fecha_fin_real or project.fecha_fin_planificada
    except Project.DoesNotExist:
        project_start = None
        project_end = None

    today = timezone.now().date()

    # Si no hay fechas definidas, usar las últimas 8 semanas como rango
    if not project_start or not project_end:
        current_week_start = today - timedelta(days=today.weekday())
        project_start_week = current_week_start - timedelta(weeks=7)
        project_end_week = current_week_start
    else:
        # Normalizar al lunes de la semana de inicio
        project_start_week = project_start - timedelta(days=project_start.weekday())
        project_end_week = project_end - timedelta(days=project_end.weekday())

    # Calcular número de semanas en el rango
    num_weeks = max(
        1,
        ((project_end_week - project_start_week).days // 7) + 1
    )

    # Paso 3: horas registradas por semana desde TimesheetEntry
    timesheet_qs = TimesheetEntry.objects.filter(
        tarea__proyecto_id=project_id,
        company_id=company_id,
        fecha__gte=project_start_week,
        fecha__lte=project_end_week + timedelta(days=6),
    ).annotate(
        week=TruncWeek('fecha')
    ).values('week').annotate(
        hours=Sum('horas')
    ).order_by('week')

    week_hours_map: dict[date, float] = {}
    for item in timesheet_qs:
        week_start = item['week'].date() if hasattr(item['week'], 'date') else item['week']
        week_hours_map[week_start] = float(item['hours'] or 0)

    # Construir lista de horas registradas en orden cronológico
    weekly_hours = []
    for i in range(num_weeks):
        week_start = project_start_week + timedelta(weeks=i)
        weekly_hours.append(week_hours_map.get(week_start, 0.0))

    # Paso 4: calcular acumulativo en Python con itertools.accumulate
    cumulative_hours = list(accumulate(weekly_hours))
    hours_remaining = [
        max(total_estimated - h, 0.0)
        for h in cumulative_hours
    ]

    # Línea ideal: disminuye linealmente desde total_estimated hasta 0
    ideal_step = total_estimated / num_weeks if num_weeks > 0 else 0
    hours_ideal = [
        max(total_estimated - ideal_step * (i + 1), 0.0)
        for i in range(num_weeks)
    ]

    # Construir data_points
    data_points = []
    for i in range(num_weeks):
        week_start = project_start_week + timedelta(weeks=i)
        data_points.append({
            'week_label': f'Week {i + 1}',
            'week_start': week_start,
            'hours_registered': weekly_hours[i],
            'hours_actual_cumulative': cumulative_hours[i],
            'hours_remaining': hours_remaining[i],
            'hours_ideal': round(hours_ideal[i], 2),
        })

    logger.info(
        'analytics_burn_down_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'total_estimated': total_estimated,
            'num_weeks': num_weeks,
        },
    )

    return {
        'total_hours_estimated': total_estimated,
        'data_points': data_points,
    }


# ---------------------------------------------------------------------------
# AN-06: get_resource_utilization
# ---------------------------------------------------------------------------

def get_resource_utilization(
    project_id: str,
    company_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[dict]:
    """
    Retorna la utilización de recursos del proyecto.

    Reutiliza calculate_user_workload() de resource_services para calcular
    la utilización individual de cada miembro del equipo del proyecto.

    Solo incluye usuarios que tienen asignaciones activas en el proyecto.

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa
        start_date: inicio del período (default: inicio planificado del proyecto)
        end_date: fin del período (default: hoy)

    Returns:
        list[dict] con por usuario:
            [{user_id, user_name, user_email, assigned_hours, registered_hours,
              capacity_hours, utilization_percentage}, ...]
    """
    from .models import ResourceAssignment

    # Determinar rango de fechas si no se especifica
    if not start_date or not end_date:
        try:
            project = Project.objects.get(id=project_id, company_id=company_id)
            start_date = start_date or (
                project.fecha_inicio_real or project.fecha_inicio_planificada
            )
            end_date = end_date or timezone.now().date()
        except Project.DoesNotExist:
            today = timezone.now().date()
            start_date = start_date or (today - timedelta(days=30))
            end_date = end_date or today

    # Obtener usuarios únicos con asignaciones activas en el proyecto
    usuario_ids = list(
        ResourceAssignment.objects.filter(
            company_id=company_id,
            tarea__proyecto_id=project_id,
            activo=True,
        ).values_list('usuario_id', flat=True).distinct()
    )

    if not usuario_ids:
        return []

    from django.contrib.auth import get_user_model
    User = get_user_model()

    usuarios = User.objects.filter(
        id__in=usuario_ids,
        company_id=company_id,
    ).values('id', 'email', 'first_name', 'last_name')

    result = []
    for usuario_data in usuarios:
        usuario_id = str(usuario_data['id'])
        user_name = f"{usuario_data.get('first_name', '')} {usuario_data.get('last_name', '')}".strip()
        if not user_name:
            user_name = usuario_data['email']

        try:
            workload = calculate_user_workload(
                usuario_id=usuario_id,
                company_id=str(company_id),
                start_date=start_date,
                end_date=end_date,
            )
            result.append({
                'user_id': usuario_id,
                'user_name': user_name,
                'user_email': usuario_data['email'],
                'assigned_hours': float(workload.horas_asignadas),
                'registered_hours': float(workload.horas_registradas),
                'capacity_hours': float(workload.horas_capacidad),
                'utilization_percentage': float(workload.porcentaje_utilizacion),
            })
        except Exception as exc:
            logger.warning(
                'analytics_resource_utilization_error',
                extra={
                    'usuario_id': usuario_id,
                    'project_id': str(project_id),
                    'company_id': str(company_id),
                    'error': str(exc),
                },
            )
            # Incluir usuario con datos parciales desde TimesheetEntry directo
            registered = TimesheetEntry.objects.filter(
                company_id=company_id,
                usuario_id=usuario_id,
                tarea__proyecto_id=project_id,
                fecha__gte=start_date,
                fecha__lte=end_date,
            ).aggregate(total=Sum('horas'))['total'] or Decimal('0')

            result.append({
                'user_id': usuario_id,
                'user_name': user_name,
                'user_email': usuario_data['email'],
                'assigned_hours': 0.0,
                'registered_hours': float(registered),
                'capacity_hours': 0.0,
                'utilization_percentage': 0.0,
            })

    logger.info(
        'analytics_resource_utilization_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'users_count': len(result),
        },
    )

    return result


# ---------------------------------------------------------------------------
# AN-07: compare_projects
# ---------------------------------------------------------------------------

def compare_projects(project_ids: list, company_id: str) -> list[dict]:
    """
    Compara múltiples proyectos por sus métricas principales.

    Multi-tenant estricto: solo proyectos de company_id son procesados,
    aunque project_ids contenga IDs de otras empresas.

    Args:
        project_ids: lista de UUIDs de proyectos a comparar
        company_id: UUID de la empresa (filtra todos los proyectos)

    Returns:
        list[dict] con por proyecto:
            [{project_id, project_name, project_code, completion_rate,
              on_time_rate, budget_variance, velocity, total_tasks}, ...]
    """
    # Multi-tenant: forzar filtro por company_id
    projects = Project.objects.filter(
        id__in=project_ids,
        company_id=company_id,
        activo=True,
    ).values('id', 'nombre', 'codigo')

    result = []
    for project in projects:
        project_id = str(project['id'])
        try:
            kpis = get_project_kpis(project_id, str(company_id))
            result.append({
                'project_id': project_id,
                'project_name': project['nombre'],
                'project_code': project['codigo'],
                'completion_rate': kpis['completion_rate'],
                'on_time_rate': kpis['on_time_rate'],
                'budget_variance': kpis['budget_variance'],
                'velocity': kpis['velocity'],
                'total_tasks': kpis['total_tasks'],
                'completed_tasks': kpis['completed_tasks'],
                'overdue_tasks': kpis['overdue_tasks'],
            })
        except Exception as exc:
            logger.warning(
                'analytics_compare_project_error',
                extra={
                    'project_id': project_id,
                    'company_id': str(company_id),
                    'error': str(exc),
                },
            )

    logger.info(
        'analytics_compare_projects_computed',
        extra={
            'company_id': str(company_id),
            'projects_requested': len(project_ids),
            'projects_returned': len(result),
        },
    )

    return result


# ---------------------------------------------------------------------------
# AN-08: get_project_timeline
# ---------------------------------------------------------------------------

def get_project_timeline(project_id: str, company_id: str) -> dict:
    """
    Retorna el timeline completo del proyecto con fases y sus tareas.

    Incluye fechas planificadas vs reales y porcentaje de avance por fase.

    Estrategia sin N+1:
    - 1 query para el proyecto
    - 1 query para todas las fases con prefetch de tasks

    Args:
        project_id: UUID del proyecto
        company_id: UUID de la empresa

    Returns:
        dict con:
            - project_id: str
            - project_name: str
            - project_code: str
            - start_planned: date
            - end_planned: date
            - start_actual: date | None
            - end_actual: date | None
            - overall_progress: float
            - phases: list[dict] con tareas agrupadas
    """
    from django.db.models import Prefetch

    try:
        project = Project.objects.get(id=project_id, company_id=company_id)
    except Project.DoesNotExist:
        return {}

    # Prefetch tareas por fase en una sola query
    # Nota: Prefetch no admite .values() — se usan model instances y se acceden como atributos
    tasks_prefetch = Prefetch(
        'tasks',
        queryset=Task.objects.filter(
            company_id=company_id,
        ).order_by('fecha_inicio', 'prioridad', 'nombre'),
        to_attr='phase_tasks',
    )

    phases = (
        Phase.objects.filter(
            proyecto_id=project_id,
            company_id=company_id,
            activo=True,
        )
        .prefetch_related(tasks_prefetch)
        .order_by('orden')
    )

    phases_data = []
    for phase in phases:
        # Calcular estadísticas de la fase
        phase_tasks = list(phase.phase_tasks)
        total_phase_tasks = len(phase_tasks)
        completed_phase_tasks = sum(
            1 for t in phase_tasks if t.estado == 'completed'
        )

        tasks_list = [
            {
                'task_id': str(t.id),
                'task_code': getattr(t, 'codigo', None),
                'task_name': t.nombre,
                'estado': t.estado,
                'prioridad': t.prioridad,
                'start_date': getattr(t, 'fecha_inicio', None),
                'end_date': getattr(t, 'fecha_fin', None),
                'deadline': t.fecha_limite,
                'horas_estimadas': float(t.horas_estimadas or 0),
                'horas_registradas': float(t.horas_registradas or 0),
                'porcentaje_completado': getattr(t, 'porcentaje_completado', 0),
            }
            for t in phase_tasks
        ]

        phases_data.append({
            'phase_id': str(phase.id),
            'phase_name': phase.nombre,
            'phase_order': phase.orden,
            'estado': phase.estado,
            'start_planned': phase.fecha_inicio_planificada,
            'end_planned': phase.fecha_fin_planificada,
            'start_actual': phase.fecha_inicio_real,
            'end_actual': phase.fecha_fin_real,
            'progress': float(phase.porcentaje_avance),
            'total_tasks': total_phase_tasks,
            'completed_tasks': completed_phase_tasks,
            'tasks': tasks_list,
        })

    logger.info(
        'analytics_timeline_computed',
        extra={
            'project_id': str(project_id),
            'company_id': str(company_id),
            'phases_count': len(phases_data),
        },
    )

    return {
        'project_id': str(project.id),
        'project_name': project.nombre,
        'project_code': project.codigo,
        'start_planned': project.fecha_inicio_planificada,
        'end_planned': project.fecha_fin_planificada,
        'start_actual': project.fecha_inicio_real,
        'end_actual': project.fecha_fin_real,
        'overall_progress': float(project.porcentaje_avance),
        'phases': phases_data,
    }
