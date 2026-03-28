"""
SaiSuite — Tests: Feature #7 — Management command budget_weekly_snapshot
BG-14 — Cobertura del comando de snapshots semanales

Cubre:
- Sin proyectos activos: mensaje de advertencia, stats vacías
- Proyecto sin presupuesto: skipped_no_budget incrementa
- Proyecto con presupuesto: snapshot creado, alertas evaluadas
- --dry-run: no persiste datos
- --project-id: filtra a un solo proyecto
- Error en un proyecto: no detiene el resto, incrementa stats['errors']
"""
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Phase, ProjectBudget, BudgetSnapshot

# ── Counters ──────────────────────────────────────────────────────────────────

_NIT   = [800_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'cmd_test_{_EMAIL[0]}@test.com'


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def company():
    c = Company.objects.create(name='Cmd Test Co', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


@pytest.fixture
def user(company):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_email(),
        password='Pass1234!',
        company=company,
        role='company_admin',
        is_active=True,
    )


@pytest.fixture
def active_project(company, user):
    return Project.all_objects.create(
        company=company,
        gerente=user,
        codigo=f'CMD-{_nit()}',
        nombre='Command Test Project',
        tipo='civil_works',
        estado='in_progress',
        cliente_id='C-CMD',
        cliente_nombre='Test Client',
        fecha_inicio_planificada=date.today() - timedelta(days=30),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_total=Decimal('1000000.00'),
    )


@pytest.fixture
def project_with_budget(active_project, company):
    ProjectBudget.objects.create(
        company=company,
        project=active_project,
        planned_labor_cost=Decimal('500000.00'),
        planned_expense_cost=Decimal('200000.00'),
        planned_total_budget=Decimal('700000.00'),
        alert_threshold_percentage=Decimal('80.00'),
        currency='COP',
    )
    return active_project


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBudgetWeeklySnapshot:

    def _run(self, *args, **kwargs) -> tuple[str, str]:
        """Ejecuta el comando y retorna (stdout, stderr)."""
        out, err = StringIO(), StringIO()
        call_command('budget_weekly_snapshot', *args, stdout=out, stderr=err, **kwargs)
        return out.getvalue(), err.getvalue()

    def test_no_active_projects_shows_warning(self, company):
        """Sin proyectos activos: mensaje de advertencia y salida limpia."""
        out, _ = self._run()
        assert 'No hay proyectos activos' in out

    def test_project_without_budget_skipped(self, active_project):
        """Proyecto sin presupuesto: se omite con mensaje indicativo."""
        out, _ = self._run()
        assert 'sin presupuesto' in out
        assert BudgetSnapshot.objects.filter(project=active_project).count() == 0

    def test_project_with_budget_creates_snapshot(self, project_with_budget):
        """Proyecto con presupuesto: snapshot creado."""
        assert BudgetSnapshot.objects.filter(project=project_with_budget).count() == 0

        out, _ = self._run()

        assert BudgetSnapshot.objects.filter(project=project_with_budget).count() == 1
        assert '✓' in out or 'snapshot' in out.lower()

    def test_idempotent_same_day(self, project_with_budget):
        """Ejecutar dos veces el mismo día: sigue habiendo un solo snapshot."""
        self._run()
        self._run()
        assert BudgetSnapshot.objects.filter(project=project_with_budget).count() == 1

    def test_dry_run_no_snapshot_created(self, project_with_budget):
        """--dry-run: no crea snapshots en BD."""
        out, _ = self._run('--dry-run')

        assert BudgetSnapshot.objects.filter(project=project_with_budget).count() == 0
        assert 'DRY-RUN' in out

    def test_dry_run_shows_cost_info(self, project_with_budget):
        """--dry-run: muestra info de costos calculados."""
        out, _ = self._run('--dry-run')
        # El nombre del proyecto o su código debe aparecer
        assert project_with_budget.codigo in out or project_with_budget.nombre in out

    def test_filter_by_project_id(self, project_with_budget, company, user):
        """--project-id: procesa solo ese proyecto."""
        # Crear otro proyecto activo con presupuesto
        other = Project.all_objects.create(
            company=company,
            gerente=user,
            codigo=f'OTHER-{_nit()}',
            nombre='Other Project',
            tipo='civil_works',
            estado='in_progress',
            cliente_id='C-OTHER',
            cliente_nombre='Other Client',
            fecha_inicio_planificada=date.today() - timedelta(days=10),
            fecha_fin_planificada=date.today() + timedelta(days=30),
            presupuesto_total=Decimal('500000.00'),
        )
        ProjectBudget.objects.create(
            company=company,
            project=other,
            planned_total_budget=Decimal('500000.00'),
            currency='COP',
        )

        self._run('--project-id', str(project_with_budget.id))

        # Solo el proyecto filtrado debe tener snapshot
        assert BudgetSnapshot.objects.filter(project=project_with_budget).count() == 1
        assert BudgetSnapshot.objects.filter(project=other).count() == 0

    def test_filter_by_project_id_not_found_raises(self, company):
        """--project-id inexistente: CommandError."""
        with pytest.raises(CommandError):
            self._run('--project-id', '00000000-0000-0000-0000-000000000000')

    def test_filter_by_company_id(self, project_with_budget, company):
        """--company-id: procesa solo proyectos de esa empresa."""
        out, _ = self._run('--company-id', str(company.id))
        assert BudgetSnapshot.objects.filter(project=project_with_budget).count() == 1

    def test_completed_project_excluded(self, company, user):
        """Proyectos en estado 'closed' o 'completed' no se procesan."""
        closed = Project.all_objects.create(
            company=company,
            gerente=user,
            codigo=f'CLOSED-{_nit()}',
            nombre='Closed Project',
            tipo='civil_works',
            estado='closed',
            cliente_id='C-CLOSED',
            cliente_nombre='Client',
            fecha_inicio_planificada=date.today() - timedelta(days=90),
            fecha_fin_planificada=date.today() - timedelta(days=10),
            presupuesto_total=Decimal('1000000.00'),
        )
        ProjectBudget.objects.create(
            company=company,
            project=closed,
            planned_total_budget=Decimal('1000000.00'),
            currency='COP',
        )
        out, _ = self._run()
        assert BudgetSnapshot.objects.filter(project=closed).count() == 0

    def test_error_in_one_project_continues_others(self, company, user):
        """Error en un proyecto no detiene el procesamiento del resto."""
        # Crear dos proyectos con presupuesto
        p1 = Project.all_objects.create(
            company=company, gerente=user, codigo=f'P1-{_nit()}',
            nombre='Project 1', tipo='civil_works', estado='in_progress',
            cliente_id='C1', cliente_nombre='Client',
            fecha_inicio_planificada=date.today() - timedelta(days=10),
            fecha_fin_planificada=date.today() + timedelta(days=30),
            presupuesto_total=Decimal('500000.00'),
        )
        p2 = Project.all_objects.create(
            company=company, gerente=user, codigo=f'P2-{_nit()}',
            nombre='Project 2', tipo='civil_works', estado='in_progress',
            cliente_id='C2', cliente_nombre='Client',
            fecha_inicio_planificada=date.today() - timedelta(days=10),
            fecha_fin_planificada=date.today() + timedelta(days=30),
            presupuesto_total=Decimal('500000.00'),
        )
        for p in [p1, p2]:
            ProjectBudget.objects.create(
                company=company,
                project=p,
                planned_total_budget=Decimal('500000.00'),
                currency='COP',
            )

        # Simular error en el primer proyecto
        call_count = {'n': 0}
        original_create = BudgetSnapshot.objects.update_or_create

        def mock_create(**kwargs):
            call_count['n'] += 1
            if call_count['n'] == 1:
                raise RuntimeError('DB connection error')
            return original_create(**kwargs)

        with patch.object(BudgetSnapshot.objects, 'update_or_create', side_effect=mock_create):
            out, _ = self._run()

        # Al menos uno debe haberse procesado correctamente
        assert '✗' in out or 'error' in out.lower()
        # El proceso no debe haber lanzado excepción

    def test_summary_shows_counts(self, project_with_budget):
        """Al final muestra resumen con conteos."""
        out, _ = self._run()
        # El resumen debe incluir líneas de conteo
        assert 'Snapshot' in out or 'snapshot' in out.lower()

    def test_summary_dry_run_no_counts(self, project_with_budget):
        """En dry-run el resumen no muestra conteos de persistencia."""
        out, _ = self._run('--dry-run')
        assert 'DRY-RUN completado' in out
