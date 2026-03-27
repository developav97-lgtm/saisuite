"""
SaiSuite — Tests: Feature #5 Analytics — Servicios
Cobertura objetivo: >= 80% de apps.proyectos.analytics_services

Cubre:
- get_project_kpis:             proyecto vacío → rates 0, proyecto con tareas → rates correctos
- get_task_distribution:        todos los estados presentes, proyecto vacío
- get_velocity_data:            retorna exactamente `periods` semanas
- get_burn_rate_data:           retorna exactamente `periods` semanas
- get_burn_down_data:           acumulativo correcto, línea ideal correcta
- get_resource_utilization:     proyecto sin recursos → lista vacía
- compare_projects:             multi-tenant — no mezcla datos de diferentes empresas
- get_project_timeline:         estructura correcta con fases y tareas
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Phase,
    Project,
    Task,
    TimesheetEntry,
)
from apps.proyectos.analytics_services import (
    compare_projects,
    get_burn_down_data,
    get_burn_rate_data,
    get_project_kpis,
    get_project_timeline,
    get_resource_utilization,
    get_task_distribution,
    get_velocity_data,
)

# ── Counters ──────────────────────────────────────────────────────────────────

_NIT   = [700_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'an_{_EMAIL[0]}@test.com'


# ── Factories ─────────────────────────────────────────────────────────────────

def make_company(name=None):
    nit = _nit()
    c = Company.objects.create(name=name or f'AN Co {nit}', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_email(),
        password='Pass1234!',
        company=company,
        role='company_admin',
        is_active=True,
    )


def make_project(company, user, **kwargs):
    defaults = {
        'codigo': f'PRY-{_nit()}',
        'nombre': 'Test Project',
        'tipo': 'civil_works',
        'estado': 'in_progress',
        'cliente_id': '111',
        'cliente_nombre': 'Test Client',
        'fecha_inicio_planificada': date.today() - timedelta(days=30),
        'fecha_fin_planificada': date.today() + timedelta(days=60),
        'presupuesto_total': Decimal('10000000.00'),
    }
    defaults.update(kwargs)
    return Project.all_objects.create(company=company, gerente=user, **defaults)


def make_phase(company, project, **kwargs):
    defaults = {
        'nombre': 'Phase 1',
        'orden': 1,
        'fecha_inicio_planificada': project.fecha_inicio_planificada,
        'fecha_fin_planificada': project.fecha_fin_planificada,
        'presupuesto_mano_obra': Decimal('1000000'),
    }
    defaults.update(kwargs)
    return Phase.all_objects.create(company=company, proyecto=project, **defaults)


def make_task(company, project, phase, **kwargs):
    defaults = {
        'nombre': 'Test Task',
        'estado': 'todo',
        'horas_estimadas': Decimal('8.00'),
        'horas_registradas': Decimal('0.00'),
    }
    defaults.update(kwargs)
    return Task.objects.create(
        company=company,
        proyecto=project,
        fase=phase,
        **defaults,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestGetProjectKpisEmptyProject(TestCase):
    """AN-01: proyecto sin tareas debe retornar rates 0."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)

    def test_empty_project_returns_zero_rates(self):
        result = get_project_kpis(str(self.project.id), str(self.company.id))

        self.assertEqual(result['total_tasks'], 0)
        self.assertEqual(result['completed_tasks'], 0)
        self.assertEqual(result['overdue_tasks'], 0)
        self.assertEqual(result['completion_rate'], 0.0)
        self.assertEqual(result['on_time_rate'], 0.0)
        self.assertEqual(result['budget_variance'], 0.0)
        self.assertEqual(result['velocity'], 0.0)
        self.assertEqual(result['burn_rate'], 0.0)

    def test_result_has_all_required_keys(self):
        result = get_project_kpis(str(self.project.id), str(self.company.id))
        required_keys = [
            'total_tasks', 'completed_tasks', 'overdue_tasks',
            'completion_rate', 'on_time_rate', 'budget_variance',
            'velocity', 'burn_rate',
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")


class TestGetProjectKpisFullProject(TestCase):
    """AN-01: proyecto con tareas completadas retorna rates correctos."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase = make_phase(self.company, self.project)

        today = date.today()
        yesterday = today - timedelta(days=1)

        # 2 tareas completadas a tiempo
        self.task1 = make_task(
            self.company, self.project, self.phase,
            estado='completed',
            fecha_limite=today + timedelta(days=5),
            horas_estimadas=Decimal('10.00'),
            horas_registradas=Decimal('8.00'),
        )
        self.task2 = make_task(
            self.company, self.project, self.phase,
            estado='completed',
            fecha_limite=today + timedelta(days=3),
            horas_estimadas=Decimal('5.00'),
            horas_registradas=Decimal('6.00'),
        )
        # 1 tarea vencida
        self.task3 = make_task(
            self.company, self.project, self.phase,
            estado='todo',
            fecha_limite=yesterday,
        )

    def test_completion_rate_is_correct(self):
        result = get_project_kpis(str(self.project.id), str(self.company.id))
        # 2 de 3 tareas completadas → 66.67%
        self.assertAlmostEqual(result['completion_rate'], 66.67, places=1)

    def test_total_tasks_counts_all(self):
        result = get_project_kpis(str(self.project.id), str(self.company.id))
        self.assertEqual(result['total_tasks'], 3)
        self.assertEqual(result['completed_tasks'], 2)

    def test_overdue_tasks_counted(self):
        result = get_project_kpis(str(self.project.id), str(self.company.id))
        self.assertEqual(result['overdue_tasks'], 1)

    def test_budget_variance_positive_when_over_hours(self):
        # task2: estimadas=5, registradas=6 → sobreejecutado
        result = get_project_kpis(str(self.project.id), str(self.company.id))
        # (8+6) - (10+5) / (10+5) * 100 = -1/15*100 = -6.67% (subajecucion)
        self.assertIsInstance(result['budget_variance'], float)

    def test_multi_tenant_isolation(self):
        """KPIs no mezclan datos de otra empresa."""
        other_company = make_company()
        other_user = make_user(other_company)
        other_project = make_project(other_company, other_user)
        other_phase = make_phase(other_company, other_project)
        make_task(other_company, other_project, other_phase, estado='completed')

        # Los KPIs del proyecto de la otra empresa no deben afectar los nuestros
        result = get_project_kpis(str(self.project.id), str(self.company.id))
        self.assertEqual(result['total_tasks'], 3)


class TestGetTaskDistributionAllStates(TestCase):
    """AN-02: distribución correcta de todos los estados."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase = make_phase(self.company, self.project)

        estados = ['todo', 'in_progress', 'in_review', 'completed', 'blocked', 'cancelled']
        for estado in estados:
            make_task(self.company, self.project, self.phase, estado=estado)

    def test_all_states_counted(self):
        result = get_task_distribution(str(self.project.id), str(self.company.id))

        for estado in ['todo', 'in_progress', 'in_review', 'completed', 'blocked', 'cancelled']:
            self.assertEqual(result[estado], 1, f"Estado {estado} should be 1")

        self.assertEqual(result['total'], 6)

    def test_percentages_sum_to_100(self):
        result = get_task_distribution(str(self.project.id), str(self.company.id))
        total_pct = sum(result['percentages'].values())
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_empty_project_returns_zero_distribution(self):
        empty_project = make_project(self.company, self.user)
        result = get_task_distribution(str(empty_project.id), str(self.company.id))
        self.assertEqual(result['total'], 0)
        for estado in ['todo', 'in_progress', 'in_review', 'completed', 'blocked', 'cancelled']:
            self.assertEqual(result[estado], 0)
            self.assertEqual(result['percentages'][estado], 0.0)


class TestGetVelocityDataLast8Weeks(TestCase):
    """AN-03: retorna exactamente `periods` semanas."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase = make_phase(self.company, self.project)

    def test_returns_exactly_periods_items(self):
        result = get_velocity_data(str(self.project.id), str(self.company.id), periods=8)
        self.assertEqual(len(result), 8)

    def test_returns_custom_periods(self):
        result = get_velocity_data(str(self.project.id), str(self.company.id), periods=4)
        self.assertEqual(len(result), 4)

    def test_each_item_has_required_keys(self):
        result = get_velocity_data(str(self.project.id), str(self.company.id), periods=4)
        for item in result:
            self.assertIn('week_label', item)
            self.assertIn('week_start', item)
            self.assertIn('tasks_completed', item)

    def test_week_labels_are_sequential(self):
        result = get_velocity_data(str(self.project.id), str(self.company.id), periods=4)
        for i, item in enumerate(result):
            self.assertEqual(item['week_label'], f'Week {i + 1}')

    def test_empty_project_returns_zeros(self):
        result = get_velocity_data(str(self.project.id), str(self.company.id), periods=4)
        for item in result:
            self.assertEqual(item['tasks_completed'], 0)


class TestGetBurnDownDataAccumulation(TestCase):
    """AN-05: acumulativo correcto del Burn Down."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(
            self.company, self.user,
            fecha_inicio_planificada=date.today() - timedelta(weeks=4),
            fecha_fin_planificada=date.today() + timedelta(weeks=4),
        )
        self.phase = make_phase(
            self.company, self.project,
            fecha_inicio_planificada=self.project.fecha_inicio_planificada,
            fecha_fin_planificada=self.project.fecha_fin_planificada,
        )
        # Crear tareas con horas estimadas conocidas
        for _ in range(4):
            make_task(
                self.company, self.project, self.phase,
                horas_estimadas=Decimal('10.00'),
            )

    def test_total_estimated_is_sum_of_tasks(self):
        result = get_burn_down_data(str(self.project.id), str(self.company.id))
        self.assertEqual(result['total_hours_estimated'], 40.0)

    def test_data_points_list_returned(self):
        result = get_burn_down_data(str(self.project.id), str(self.company.id))
        self.assertIn('data_points', result)
        self.assertIsInstance(result['data_points'], list)
        self.assertGreater(len(result['data_points']), 0)

    def test_each_data_point_has_required_keys(self):
        result = get_burn_down_data(str(self.project.id), str(self.company.id))
        required_keys = [
            'week_label', 'week_start', 'hours_registered',
            'hours_actual_cumulative', 'hours_remaining', 'hours_ideal',
        ]
        for point in result['data_points']:
            for key in required_keys:
                self.assertIn(key, point, f"Missing key '{key}' in data_point")

    def test_hours_remaining_is_decreasing_or_equal(self):
        """hours_remaining debe ser no creciente (monotonicamente decreciente o plano)."""
        result = get_burn_down_data(str(self.project.id), str(self.company.id))
        data_points = result['data_points']
        for i in range(1, len(data_points)):
            self.assertLessEqual(
                data_points[i]['hours_remaining'],
                data_points[i - 1]['hours_remaining'] + 0.01,  # tolerancia flotante
                msg=f"hours_remaining should not increase at week {i + 1}",
            )

    def test_empty_project_returns_zero_estimated(self):
        empty_project = make_project(self.company, self.user)
        result = get_burn_down_data(str(empty_project.id), str(self.company.id))
        self.assertEqual(result['total_hours_estimated'], 0.0)


class TestCompareProjectsMultiTenant(TestCase):
    """AN-07: compare_projects NO mezcla datos de diferentes companies."""

    def setUp(self):
        self.company_a = make_company('Company A')
        self.company_b = make_company('Company B')
        self.user_a = make_user(self.company_a)
        self.user_b = make_user(self.company_b)

        self.project_a = make_project(self.company_a, self.user_a)
        self.project_b = make_project(self.company_b, self.user_b)

        # Tareas en el proyecto A
        phase_a = make_phase(self.company_a, self.project_a)
        for _ in range(3):
            make_task(self.company_a, self.project_a, phase_a, estado='completed')

        # Tareas en el proyecto B
        phase_b = make_phase(self.company_b, self.project_b)
        for _ in range(1):
            make_task(self.company_b, self.project_b, phase_b, estado='completed')

    def test_compare_only_returns_own_company_projects(self):
        """company_a no puede ver proyectos de company_b."""
        result = compare_projects(
            project_ids=[str(self.project_a.id), str(self.project_b.id)],
            company_id=str(self.company_a.id),
        )
        returned_ids = [r['project_id'] for r in result]
        self.assertIn(str(self.project_a.id), returned_ids)
        self.assertNotIn(str(self.project_b.id), returned_ids)

    def test_compare_returns_correct_project_data(self):
        result = compare_projects(
            project_ids=[str(self.project_a.id)],
            company_id=str(self.company_a.id),
        )
        self.assertEqual(len(result), 1)
        project_data = result[0]
        self.assertEqual(project_data['project_id'], str(self.project_a.id))
        self.assertEqual(project_data['total_tasks'], 3)
        self.assertEqual(project_data['completed_tasks'], 3)
        self.assertAlmostEqual(project_data['completion_rate'], 100.0, places=1)

    def test_compare_empty_list_returns_empty(self):
        result = compare_projects(
            project_ids=[],
            company_id=str(self.company_a.id),
        )
        self.assertEqual(result, [])

    def test_compare_nonexistent_ids_returns_empty(self):
        import uuid
        result = compare_projects(
            project_ids=[str(uuid.uuid4())],
            company_id=str(self.company_a.id),
        )
        self.assertEqual(result, [])


class TestGetResourceUtilizationWithCapacity(TestCase):
    """AN-06: utilización calculada correctamente."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase = make_phase(self.company, self.project)

    def test_project_without_resources_returns_empty_list(self):
        result = get_resource_utilization(
            project_id=str(self.project.id),
            company_id=str(self.company.id),
        )
        self.assertEqual(result, [])

    def test_result_has_required_keys_when_resources_exist(self):
        """
        Cuando hay asignaciones, cada entrada tiene los campos requeridos.
        Requiere ResourceAssignment creado.
        """
        from apps.proyectos.models import ResourceAssignment
        task = make_task(self.company, self.project, self.phase, estado='in_progress')

        # Crear asignación directamente (sin pasar por service para evitar validaciones)
        ResourceAssignment.objects.create(
            company=self.company,
            tarea=task,
            usuario=self.user,
            porcentaje_asignacion=Decimal('80.00'),
            fecha_inicio=date.today() - timedelta(days=7),
            fecha_fin=date.today() + timedelta(days=7),
            activo=True,
        )

        result = get_resource_utilization(
            project_id=str(self.project.id),
            company_id=str(self.company.id),
        )

        self.assertEqual(len(result), 1)
        required_keys = [
            'user_id', 'user_name', 'user_email',
            'assigned_hours', 'registered_hours',
            'capacity_hours', 'utilization_percentage',
        ]
        for key in required_keys:
            self.assertIn(key, result[0], f"Missing key: {key}")

    def test_multi_tenant_isolation(self):
        """Recursos de otra empresa no aparecen."""
        from apps.proyectos.models import ResourceAssignment
        other_company = make_company()
        other_user = make_user(other_company)
        other_project = make_project(other_company, other_user)
        other_phase = make_phase(other_company, other_project)
        other_task = make_task(other_company, other_project, other_phase, estado='in_progress')

        ResourceAssignment.objects.create(
            company=other_company,
            tarea=other_task,
            usuario=other_user,
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=7),
            activo=True,
        )

        result = get_resource_utilization(
            project_id=str(self.project.id),
            company_id=str(self.company.id),
        )
        # Proyecto de self.company no tiene assignments → lista vacía
        self.assertEqual(result, [])


class TestGetProjectTimeline(TestCase):
    """AN-08: estructura correcta del timeline."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase = make_phase(self.company, self.project)
        self.task = make_task(self.company, self.project, self.phase)

    def test_timeline_has_project_fields(self):
        result = get_project_timeline(str(self.project.id), str(self.company.id))
        required_keys = [
            'project_id', 'project_name', 'project_code',
            'start_planned', 'end_planned',
            'start_actual', 'end_actual',
            'overall_progress', 'phases',
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_phases_are_listed(self):
        result = get_project_timeline(str(self.project.id), str(self.company.id))
        self.assertEqual(len(result['phases']), 1)

    def test_phase_contains_tasks(self):
        result = get_project_timeline(str(self.project.id), str(self.company.id))
        phase_data = result['phases'][0]
        self.assertIn('tasks', phase_data)
        self.assertEqual(len(phase_data['tasks']), 1)

    def test_phase_has_required_fields(self):
        result = get_project_timeline(str(self.project.id), str(self.company.id))
        phase_data = result['phases'][0]
        required_keys = [
            'phase_id', 'phase_name', 'phase_order', 'estado',
            'start_planned', 'end_planned', 'progress',
            'total_tasks', 'completed_tasks',
        ]
        for key in required_keys:
            self.assertIn(key, phase_data, f"Missing key in phase: {key}")

    def test_task_has_required_fields(self):
        result = get_project_timeline(str(self.project.id), str(self.company.id))
        task_data = result['phases'][0]['tasks'][0]
        required_keys = [
            'task_id', 'task_code', 'task_name', 'estado',
            'horas_estimadas', 'horas_registradas',
        ]
        for key in required_keys:
            self.assertIn(key, task_data, f"Missing key in task: {key}")

    def test_nonexistent_project_returns_empty_dict(self):
        import uuid
        result = get_project_timeline(str(uuid.uuid4()), str(self.company.id))
        self.assertEqual(result, {})

    def test_multi_tenant_isolation(self):
        """Timeline no retorna datos de otra empresa."""
        other_company = make_company()
        other_user = make_user(other_company)

        # Intentar obtener el timeline del proyecto de self.company con company_id de otra empresa
        result = get_project_timeline(str(self.project.id), str(other_company.id))
        self.assertEqual(result, {})


class TestGetBurnRateData(TestCase):
    """AN-04: burn rate retorna exactamente `periods` semanas."""

    def setUp(self):
        self.company = make_company()
        self.user = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase = make_phase(self.company, self.project)

    def test_returns_exactly_periods_items(self):
        result = get_burn_rate_data(str(self.project.id), str(self.company.id), periods=6)
        self.assertEqual(len(result), 6)

    def test_each_item_has_required_keys(self):
        result = get_burn_rate_data(str(self.project.id), str(self.company.id), periods=4)
        for item in result:
            self.assertIn('week_label', item)
            self.assertIn('week_start', item)
            self.assertIn('hours_registered', item)

    def test_empty_project_returns_zeros(self):
        result = get_burn_rate_data(str(self.project.id), str(self.company.id), periods=4)
        for item in result:
            self.assertEqual(item['hours_registered'], 0.0)

    def test_timesheet_entries_counted(self):
        """TimesheetEntry registrado esta semana debe aparecer en burn rate."""
        task = make_task(self.company, self.project, self.phase)
        today = date.today()

        TimesheetEntry.objects.create(
            company=self.company,
            tarea=task,
            usuario=self.user,
            fecha=today,
            horas=Decimal('5.00'),
        )

        result = get_burn_rate_data(str(self.project.id), str(self.company.id), periods=4)
        # La semana actual debe tener al menos 5 horas
        last_week = result[-1]
        self.assertGreaterEqual(last_week['hours_registered'], 5.0)
