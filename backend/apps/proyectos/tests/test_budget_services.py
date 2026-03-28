"""
SaiSuite — Tests: Feature #7 Budget & Cost Tracking — Servicios
BG-53 a BG-58 — Cobertura objetivo: >= 85% de apps.proyectos.budget_services

Cubre:
- CostCalculationService: _build_rate_index, _resolve_rate, get_labor_cost,
  get_expense_cost, get_total_cost, get_budget_variance, get_cost_by_resource,
  get_cost_by_task
- EVMService: get_evm_metrics (con y sin presupuesto, con y sin tareas)
- BudgetManagementService: set_project_budget, approve_budget, check_budget_alerts
- ExpenseService: create_expense, list_expenses, approve_expense, update_expense,
  delete_expense
- ResourceCostRateService: get_active_rate, create_rate, update_rate, delete_rate
- BudgetSnapshotService: create_snapshot (idempotente), list_snapshots
- InvoiceService: generate_invoice_data
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Project, Phase, Task, TimesheetEntry,
    ResourceCostRate, ProjectBudget, ProjectExpense, BudgetSnapshot,
)
from apps.proyectos.budget_services import (
    CostCalculationService,
    EVMService,
    BudgetManagementService,
    ExpenseService,
    ResourceCostRateService,
    BudgetSnapshotService,
    InvoiceService,
)

# ── Counters ──────────────────────────────────────────────────────────────────

_NIT   = [700_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'budget_test_{_EMAIL[0]}@test.com'


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def company():
    c = Company.objects.create(name='Budget Test Co', nit=_nit())
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
def user2(company):
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
def project(company, user):
    return Project.all_objects.create(
        company=company,
        gerente=user,
        codigo=f'BG-{_nit()}',
        nombre='Budget Project',
        tipo='civil_works',
        estado='in_progress',
        cliente_id='C-001',
        cliente_nombre='Test Client',
        fecha_inicio_planificada=date.today() - timedelta(days=30),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_total=Decimal('1000000.00'),
    )


@pytest.fixture
def phase(project):
    return Phase.all_objects.create(
        company=project.company,
        proyecto=project,
        nombre='General Phase',
        orden=1,
        fecha_inicio_planificada=date.today() - timedelta(days=30),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('500000'),
    )


@pytest.fixture
def task(project, phase, user):
    return Task.objects.create(
        company=project.company,
        proyecto=project,
        fase=phase,
        nombre='Task A',
        responsable=user,
        estado='in_progress',
        porcentaje_completado=50,
        horas_estimadas=Decimal('40.00'),
    )


@pytest.fixture
def budget(project, company):
    return ProjectBudget.objects.create(
        company=company,
        project=project,
        planned_labor_cost=Decimal('500000.00'),
        planned_expense_cost=Decimal('200000.00'),
        planned_total_budget=Decimal('700000.00'),
        alert_threshold_percentage=Decimal('80.00'),
        currency='COP',
    )


@pytest.fixture
def cost_rate(user, company):
    return ResourceCostRate.objects.create(
        company=company,
        user=user,
        start_date=date.today() - timedelta(days=365),
        end_date=None,
        hourly_rate=Decimal('50000.00'),
        currency='COP',
    )


@pytest.fixture
def timesheet_entry(task, user, company):
    return TimesheetEntry.objects.create(
        company=company,
        tarea=task,
        usuario=user,
        fecha=date.today() - timedelta(days=5),
        horas=Decimal('8.00'),
        descripcion='Test work',
    )


@pytest.fixture
def expense(project, company, user):
    return ProjectExpense.objects.create(
        company=company,
        project=project,
        category='materials',
        description='Test materials',
        amount=Decimal('50000.00'),
        currency='COP',
        expense_date=date.today() - timedelta(days=2),
        paid_by=user,
        billable=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CostCalculationService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCostCalculationService:

    def test_build_rate_index_empty(self, company):
        """Sin tarifas: retorna dict vacío."""
        result = CostCalculationService._build_rate_index([], str(company.id))
        assert result == {}

    def test_build_rate_index_one_user(self, user, cost_rate, company):
        """Con una tarifa activa: indexa correctamente por user_id."""
        index = CostCalculationService._build_rate_index(
            [str(user.id)], str(company.id)
        )
        assert str(user.id) in index
        assert len(index[str(user.id)]) == 1
        start, end, rate = index[str(user.id)][0]
        assert rate == Decimal('50000.00')

    def test_resolve_rate_found(self, user, cost_rate, company):
        """Tarifa encontrada para fecha válida."""
        index = CostCalculationService._build_rate_index(
            [str(user.id)], str(company.id)
        )
        rate = CostCalculationService._resolve_rate(
            str(user.id), date.today(), index
        )
        assert rate == Decimal('50000.00')

    def test_resolve_rate_not_found(self, user, company):
        """Sin tarifa registrada → retorna 0.00."""
        rate = CostCalculationService._resolve_rate(str(user.id), date.today(), {})
        assert rate == Decimal('0.00')

    def test_get_labor_cost_no_entries(self, project):
        """Sin timesheets: labor_cost = 0, entries_count = 0."""
        result = CostCalculationService.get_labor_cost(str(project.id))
        assert result['labor_cost'] == Decimal('0.00')
        assert result['entries_count'] == 0

    def test_get_labor_cost_with_entries_and_rate(
        self, project, task, user, company, cost_rate, timesheet_entry
    ):
        """Con timesheet y tarifa: costo = horas × tarifa."""
        result = CostCalculationService.get_labor_cost(str(project.id))
        expected = Decimal('8.00') * Decimal('50000.00')
        assert result['labor_cost'] == expected
        assert result['entries_count'] == 1
        assert result['entries_without_rate'] == 0
        assert result['total_hours'] == Decimal('8.00')

    def test_get_labor_cost_without_rate_logs_warning(
        self, project, task, user, company, timesheet_entry
    ):
        """Con timesheet pero sin tarifa: entries_without_rate incrementa."""
        result = CostCalculationService.get_labor_cost(str(project.id))
        assert result['labor_cost'] == Decimal('0.00')
        assert result['entries_without_rate'] == 1

    def test_get_labor_cost_date_filter(
        self, project, task, user, company, cost_rate, timesheet_entry
    ):
        """Filtro por fecha excluye entradas fuera del rango."""
        future_start = date.today() + timedelta(days=1)
        result = CostCalculationService.get_labor_cost(
            str(project.id), start_date=future_start
        )
        assert result['entries_count'] == 0

    def test_get_expense_cost_no_expenses(self, project):
        """Sin gastos: expense_cost = 0."""
        result = CostCalculationService.get_expense_cost(str(project.id))
        assert result['expense_cost'] == Decimal('0.00')
        assert result['expenses_count'] == 0

    def test_get_expense_cost_with_expense(self, project, expense):
        """Con gastos: suma correctamente."""
        result = CostCalculationService.get_expense_cost(str(project.id))
        assert result['expense_cost'] == Decimal('50000.00')
        assert result['expenses_count'] == 1

    def test_get_expense_cost_billable_only(self, project, expense, company):
        """billable_only=True filtra correctamente."""
        # Crear un gasto no facturable
        ProjectExpense.objects.create(
            company=company,
            project=project,
            category='travel',
            description='Non-billable trip',
            amount=Decimal('10000.00'),
            currency='COP',
            expense_date=date.today(),
            billable=False,
        )
        result = CostCalculationService.get_expense_cost(
            str(project.id), billable_only=True
        )
        assert result['expense_cost'] == Decimal('50000.00')

    def test_get_total_cost_combines(
        self, project, task, user, company, cost_rate, timesheet_entry, expense
    ):
        """Total = labor + expense."""
        result = CostCalculationService.get_total_cost(str(project.id))
        expected_labor = Decimal('8.00') * Decimal('50000.00')
        expected_total = expected_labor + Decimal('50000.00')
        assert result['total_cost'] == expected_total
        assert result['labor_cost'] == expected_labor
        assert result['expense_cost'] == Decimal('50000.00')

    def test_get_budget_variance_no_budget(self, project):
        """Sin presupuesto: status = 'no_budget'."""
        result = CostCalculationService.get_budget_variance(str(project.id))
        assert result['status'] == 'no_budget'

    def test_get_budget_variance_under_budget(self, project, budget):
        """Sin gastos ni timesheets: status = 'under'."""
        result = CostCalculationService.get_budget_variance(str(project.id))
        assert result['status'] == 'under'
        assert result['variance'] == budget.planned_total_budget

    def test_get_budget_variance_over_budget(
        self, project, budget, company
    ):
        """Gastos > presupuesto: status = 'over'."""
        ProjectExpense.objects.create(
            company=company,
            project=project,
            category='materials',
            description='Overrun',
            amount=Decimal('800000.00'),
            currency='COP',
            expense_date=date.today(),
            billable=True,
        )
        result = CostCalculationService.get_budget_variance(str(project.id))
        assert result['status'] == 'over'

    def test_get_cost_by_resource_no_entries(self, project):
        """Sin timesheets: lista vacía."""
        result = CostCalculationService.get_cost_by_resource(str(project.id))
        assert result == []

    def test_get_cost_by_resource_with_entries(
        self, project, task, user, company, cost_rate, timesheet_entry
    ):
        """Con timesheets: retorna desglose por usuario."""
        result = CostCalculationService.get_cost_by_resource(str(project.id))
        assert len(result) == 1
        assert result[0]['user_id'] == str(user.id)
        assert result[0]['hours'] == Decimal('8.00')
        assert result[0]['total_cost'] == Decimal('8.00') * Decimal('50000.00')
        assert result[0]['pct'] == Decimal('100.00')

    def test_get_cost_by_task_no_entries(self, project):
        """Sin timesheets: lista vacía."""
        result = CostCalculationService.get_cost_by_task(str(project.id))
        assert result == []

    def test_get_cost_by_task_with_entries(
        self, project, task, user, company, cost_rate, timesheet_entry
    ):
        """Con timesheets: retorna desglose por tarea."""
        result = CostCalculationService.get_cost_by_task(str(project.id))
        assert len(result) == 1
        assert result[0]['task_id'] == str(task.id)
        assert result[0]['hours'] == Decimal('8.00')
        assert result[0]['labor_cost'] == Decimal('8.00') * Decimal('50000.00')


# ─────────────────────────────────────────────────────────────────────────────
# EVMService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestEVMService:

    def test_evm_no_budget_returns_warning(self, project):
        """Sin presupuesto: warning y BAC = 0."""
        result = EVMService.get_evm_metrics(str(project.id))
        assert result['BAC'] == Decimal('0.00')
        assert result['warning'] is not None
        assert 'presupuesto' in result['warning']

    def test_evm_with_budget_no_tasks(self, project, budget):
        """Con presupuesto pero sin tareas: completion = 0, EV = 0."""
        result = EVMService.get_evm_metrics(str(project.id))
        assert result['EV'] == Decimal('0.00')
        assert result['completion_percentage'] == Decimal('0.00')
        assert result['BAC'] == Decimal('700000.00')

    def test_evm_with_tasks_and_budget(
        self, project, budget, task, user, company, cost_rate, timesheet_entry
    ):
        """Con presupuesto y tarea 50% completada: EV > 0, AC > 0."""
        result = EVMService.get_evm_metrics(str(project.id))
        # BAC correcto
        assert result['BAC'] == Decimal('700000.00')
        # EV = BAC × (50/100) = 350000
        assert result['EV'] == Decimal('350000.00')
        # AC > 0 (tiene timesheets con tarifa)
        assert result['AC'] > Decimal('0.00')
        # CPI y SPI calculados
        assert result['CPI'] is not None
        assert result['SPI'] is not None
        # Health states válidos
        assert result['schedule_health'] in ('on_track', 'at_risk', 'behind')
        assert result['cost_health'] in ('on_track', 'at_risk', 'over_budget')

    def test_evm_project_not_found(self):
        """Proyecto inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            EVMService.get_evm_metrics('00000000-0000-0000-0000-000000000000')

    def test_evm_with_approved_budget(self, project, budget, user):
        """Budget aprobado: BAC usa approved_budget."""
        budget.approved_budget = Decimal('900000.00')
        budget.approved_by = user
        budget.approved_date = timezone.now()
        budget.save()

        result = EVMService.get_evm_metrics(str(project.id))
        assert result['BAC'] == Decimal('900000.00')

    def test_evm_custom_as_of_date(self, project, budget):
        """as_of_date personalizado: PV calculado desde esa fecha."""
        past_date = project.fecha_inicio_planificada
        result = EVMService.get_evm_metrics(str(project.id), as_of_date=past_date)
        # PV en fecha inicio = 0 (elapsed_days = 0)
        assert result['PV'] == Decimal('0.00')
        assert result['as_of_date'] == past_date.isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# BudgetManagementService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBudgetManagementService:

    def test_set_budget_creates_new(self, project, company):
        """Primer set_project_budget crea el registro."""
        budget = BudgetManagementService.set_project_budget(
            project_id=str(project.id),
            data={
                'planned_labor_cost':    Decimal('400000.00'),
                'planned_expense_cost':  Decimal('100000.00'),
                'planned_total_budget':  Decimal('500000.00'),
                'currency':              'COP',
            },
            company_id=str(company.id),
        )
        assert budget.pk is not None
        assert budget.planned_total_budget == Decimal('500000.00')

    def test_set_budget_updates_existing(self, project, budget, company):
        """Segundo set_project_budget actualiza el registro existente."""
        updated = BudgetManagementService.set_project_budget(
            project_id=str(project.id),
            data={'notes': 'Updated notes'},
            company_id=str(company.id),
        )
        assert updated.pk == budget.pk
        assert updated.notes == 'Updated notes'

    def test_set_budget_approved_blocks_amount_fields(
        self, project, budget, user, company
    ):
        """Presupuesto aprobado: intento de modificar monto lanza ValidationError."""
        budget.approved_by   = user
        budget.approved_date = timezone.now()
        budget.save()

        with pytest.raises(ValidationError) as exc_info:
            BudgetManagementService.set_project_budget(
                project_id=str(project.id),
                data={'planned_total_budget': Decimal('999000.00')},
                company_id=str(company.id),
            )
        assert 'aprobado' in str(exc_info.value).lower()

    def test_set_budget_approved_allows_notes(self, project, budget, user, company):
        """Presupuesto aprobado: notas sí se pueden modificar."""
        budget.approved_by   = user
        budget.approved_date = timezone.now()
        budget.save()

        updated = BudgetManagementService.set_project_budget(
            project_id=str(project.id),
            data={'notes': 'Post-approval note'},
            company_id=str(company.id),
        )
        assert updated.notes == 'Post-approval note'

    def test_set_budget_project_not_found(self, company):
        """Proyecto inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            BudgetManagementService.set_project_budget(
                project_id='00000000-0000-0000-0000-000000000000',
                data={'planned_total_budget': Decimal('1000.00')},
                company_id=str(company.id),
            )

    def test_approve_budget_ok(self, project, budget, user):
        """Aprobación exitosa: sets approved_budget + approved_by + approved_date."""
        result = BudgetManagementService.approve_budget(
            project_id=str(project.id),
            approved_budget=Decimal('700000.00'),
            approved_by_user_id=str(user.id),
        )
        assert result.approved_budget == Decimal('700000.00')
        assert result.approved_by == user
        assert result.approved_date is not None
        assert result.is_approved is True

    def test_approve_budget_no_budget_raises(self, project):
        """Sin presupuesto previo: ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            BudgetManagementService.approve_budget(
                project_id=str(project.id),
                approved_budget=Decimal('500000.00'),
                approved_by_user_id='00000000-0000-0000-0000-000000000000',
            )
        assert 'presupuesto' in str(exc_info.value).lower()

    def test_approve_budget_already_approved_raises(self, project, budget, user):
        """Presupuesto ya aprobado: ValidationError."""
        budget.approved_by   = user
        budget.approved_date = timezone.now()
        budget.approved_budget = Decimal('700000.00')
        budget.save()

        with pytest.raises(ValidationError) as exc_info:
            BudgetManagementService.approve_budget(
                project_id=str(project.id),
                approved_budget=Decimal('800000.00'),
                approved_by_user_id=str(user.id),
            )
        assert 'aprobado' in str(exc_info.value).lower()

    def test_approve_budget_zero_raises(self, project, budget, user):
        """Monto aprobado <= 0: ValidationError."""
        with pytest.raises(ValidationError):
            BudgetManagementService.approve_budget(
                project_id=str(project.id),
                approved_budget=Decimal('0.00'),
                approved_by_user_id=str(user.id),
            )

    def test_check_alerts_no_budget(self, project):
        """Sin presupuesto: lista vacía."""
        result = BudgetManagementService.check_budget_alerts(str(project.id))
        assert result == []

    def test_check_alerts_under_budget(self, project, budget):
        """Bajo presupuesto y lejos del umbral: sin alertas."""
        result = BudgetManagementService.check_budget_alerts(str(project.id))
        assert result == []

    def test_check_alerts_warning_triggered(self, project, budget, company):
        """Costo cerca del umbral (80%): alerta tipo warning."""
        # Crear gasto al 85% del presupuesto
        ProjectExpense.objects.create(
            company=company,
            project=project,
            category='materials',
            description='Big spend',
            amount=Decimal('595000.00'),  # 85% de 700000
            currency='COP',
            expense_date=date.today(),
        )
        result = BudgetManagementService.check_budget_alerts(str(project.id))
        types = [a['type'] for a in result]
        assert 'warning' in types or 'danger' in types

    def test_check_alerts_danger_over_budget(self, project, budget, company):
        """Sobre presupuesto: alerta tipo danger."""
        ProjectExpense.objects.create(
            company=company,
            project=project,
            category='materials',
            description='Overrun',
            amount=Decimal('800000.00'),
            currency='COP',
            expense_date=date.today(),
        )
        result = BudgetManagementService.check_budget_alerts(str(project.id))
        types = [a['type'] for a in result]
        assert 'danger' in types


# ─────────────────────────────────────────────────────────────────────────────
# ExpenseService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestExpenseService:

    def test_create_expense_ok(self, project, user, company):
        """Crea gasto exitosamente."""
        exp = ExpenseService.create_expense(
            project_id=str(project.id),
            data={
                'category':     'materials',
                'description':  'Test material',
                'amount':       Decimal('25000.00'),
                'currency':     'COP',
                'expense_date': date.today(),
                'billable':     True,
            },
            company_id=str(company.id),
            paid_by_user_id=str(user.id),
        )
        assert exp.pk is not None
        assert exp.amount == Decimal('25000.00')
        assert exp.paid_by == user

    def test_create_expense_zero_amount_raises(self, project, company):
        """Amount <= 0: ValidationError."""
        with pytest.raises(ValidationError):
            ExpenseService.create_expense(
                project_id=str(project.id),
                data={
                    'category':     'materials',
                    'description':  'X',
                    'amount':       Decimal('0.00'),
                    'currency':     'COP',
                    'expense_date': date.today(),
                },
                company_id=str(company.id),
                paid_by_user_id=None,
            )

    def test_create_expense_future_date_raises(self, project, company):
        """Fecha futura: ValidationError."""
        with pytest.raises(ValidationError):
            ExpenseService.create_expense(
                project_id=str(project.id),
                data={
                    'category':     'travel',
                    'description':  'Future trip',
                    'amount':       Decimal('5000.00'),
                    'currency':     'COP',
                    'expense_date': date.today() + timedelta(days=30),
                },
                company_id=str(company.id),
                paid_by_user_id=None,
            )

    def test_create_expense_project_not_found_raises(self, company):
        """Proyecto inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            ExpenseService.create_expense(
                project_id='00000000-0000-0000-0000-000000000000',
                data={
                    'category':     'materials',
                    'description':  'X',
                    'amount':       Decimal('1000.00'),
                    'currency':     'COP',
                    'expense_date': date.today(),
                },
                company_id=str(company.id),
                paid_by_user_id=None,
            )

    def test_list_expenses_no_filters(self, project, expense):
        """Sin filtros: retorna todos los gastos."""
        result = ExpenseService.list_expenses(str(project.id))
        assert result.count() == 1

    def test_list_expenses_filter_by_category(self, project, expense, company):
        """Filtro por categoría: retorna solo coincidencias."""
        ProjectExpense.objects.create(
            company=company,
            project=project,
            category='travel',
            description='Trip',
            amount=Decimal('20000.00'),
            currency='COP',
            expense_date=date.today(),
        )
        result = ExpenseService.list_expenses(
            str(project.id), filters={'category': 'materials'}
        )
        assert all(e.category == 'materials' for e in result)

    def test_list_expenses_filter_billable(self, project, expense, company):
        """Filtro billable=True/False funciona."""
        ProjectExpense.objects.create(
            company=company,
            project=project,
            category='travel',
            description='Non-billable',
            amount=Decimal('5000.00'),
            currency='COP',
            expense_date=date.today(),
            billable=False,
        )
        billable = ExpenseService.list_expenses(
            str(project.id), filters={'billable': True}
        )
        assert all(e.billable for e in billable)

    def test_approve_expense_ok(self, expense, user2, company):
        """Aprobación exitosa: sets approved_by + approved_date."""
        result = ExpenseService.approve_expense(
            expense_id=str(expense.id),
            approved_by_user_id=str(user2.id),
            company_id=str(company.id),
        )
        assert result.is_approved is True
        assert result.approved_by == user2

    def test_approve_expense_self_approval_raises(self, expense, user, company):
        """El pagador no puede aprobar su propio gasto."""
        from django.core.exceptions import PermissionDenied
        with pytest.raises(PermissionDenied) as exc_info:
            ExpenseService.approve_expense(
                expense_id=str(expense.id),
                approved_by_user_id=str(user.id),
                company_id=str(company.id),
            )
        assert 'aprobador' in str(exc_info.value).lower()

    def test_approve_expense_already_approved_raises(
        self, expense, user2, company
    ):
        """Gasto ya aprobado: ValidationError."""
        expense.approved_by   = user2
        expense.approved_date = timezone.now()
        expense.save()

        with pytest.raises(ValidationError):
            ExpenseService.approve_expense(
                expense_id=str(expense.id),
                approved_by_user_id=str(user2.id),
                company_id=str(company.id),
            )

    def test_update_expense_ok(self, expense, company):
        """Actualización exitosa de campos."""
        updated = ExpenseService.update_expense(
            expense_id=str(expense.id),
            data={'description': 'Updated description', 'amount': Decimal('60000.00')},
            company_id=str(company.id),
        )
        assert updated.description == 'Updated description'
        assert updated.amount == Decimal('60000.00')

    def test_update_approved_expense_raises(self, expense, user2, company):
        """Gasto aprobado no se puede editar."""
        expense.approved_by   = user2
        expense.approved_date = timezone.now()
        expense.save()

        with pytest.raises(ValidationError):
            ExpenseService.update_expense(
                expense_id=str(expense.id),
                data={'description': 'Try to edit'},
                company_id=str(company.id),
            )

    def test_delete_expense_ok(self, project, company):
        """Eliminación exitosa de gasto no aprobado."""
        exp = ProjectExpense.objects.create(
            company=company,
            project=project,
            category='travel',
            description='Delete me',
            amount=Decimal('5000.00'),
            currency='COP',
            expense_date=date.today(),
        )
        ExpenseService.delete_expense(str(exp.id), str(company.id))
        assert not ProjectExpense.objects.filter(id=exp.id).exists()

    def test_delete_approved_expense_raises(self, expense, user2, company):
        """Gasto aprobado no se puede eliminar."""
        expense.approved_by   = user2
        expense.approved_date = timezone.now()
        expense.save()

        with pytest.raises(ValidationError):
            ExpenseService.delete_expense(str(expense.id), str(company.id))


# ─────────────────────────────────────────────────────────────────────────────
# ResourceCostRateService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestResourceCostRateService:

    def test_get_active_rate_found(self, user, company, cost_rate):
        """Tarifa activa encontrada para hoy."""
        result = ResourceCostRateService.get_active_rate(
            str(user.id), str(company.id), date.today()
        )
        assert result is not None
        assert result.hourly_rate == Decimal('50000.00')

    def test_get_active_rate_not_found(self, user, company):
        """Sin tarifa registrada: retorna None."""
        result = ResourceCostRateService.get_active_rate(
            str(user.id), str(company.id), date.today()
        )
        assert result is None

    def test_get_active_rate_closed_rate_expired(self, user, company):
        """Tarifa cerrada cuyo end_date ya pasó: no se retorna."""
        ResourceCostRate.objects.create(
            company=company,
            user=user,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
            hourly_rate=Decimal('40000.00'),
            currency='COP',
        )
        result = ResourceCostRateService.get_active_rate(
            str(user.id), str(company.id), date.today()
        )
        assert result is None

    def test_create_rate_ok(self, user, company):
        """Crea tarifa nueva sin solapamiento."""
        rate = ResourceCostRateService.create_rate(
            user_id=str(user.id),
            data={
                'user':        user,
                'start_date':  date.today(),
                'end_date':    None,
                'hourly_rate': Decimal('75000.00'),
                'currency':    'COP',
            },
            company_id=str(company.id),
        )
        assert rate.pk is not None
        assert rate.hourly_rate == Decimal('75000.00')

    def test_create_rate_zero_rate_raises(self, user, company):
        """Tarifa <= 0: ValidationError."""
        with pytest.raises(ValidationError):
            ResourceCostRateService.create_rate(
                user_id=str(user.id),
                data={
                    'user':        user,
                    'start_date':  date.today(),
                    'end_date':    None,
                    'hourly_rate': Decimal('0.00'),
                    'currency':    'COP',
                },
                company_id=str(company.id),
            )

    def test_create_rate_end_before_start_raises(self, user, company):
        """end_date <= start_date: ValidationError."""
        with pytest.raises(ValidationError):
            ResourceCostRateService.create_rate(
                user_id=str(user.id),
                data={
                    'user':        user,
                    'start_date':  date.today(),
                    'end_date':    date.today() - timedelta(days=1),
                    'hourly_rate': Decimal('50000.00'),
                    'currency':    'COP',
                },
                company_id=str(company.id),
            )

    def test_create_rate_overlap_raises(self, user, company, cost_rate):
        """Solapamiento con tarifa existente: ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ResourceCostRateService.create_rate(
                user_id=str(user.id),
                data={
                    'user':        user,
                    'start_date':  date.today(),
                    'end_date':    None,
                    'hourly_rate': Decimal('60000.00'),
                    'currency':    'COP',
                },
                company_id=str(company.id),
            )
        assert 'solapa' in str(exc_info.value).lower()

    def test_update_rate_ok(self, user, company, cost_rate):
        """Actualiza hourly_rate correctamente."""
        updated = ResourceCostRateService.update_rate(
            rate_id=str(cost_rate.id),
            data={'hourly_rate': Decimal('65000.00')},
            company_id=str(company.id),
        )
        assert updated.hourly_rate == Decimal('65000.00')

    def test_update_rate_not_found_raises(self, company):
        """Tarifa inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            ResourceCostRateService.update_rate(
                rate_id='00000000-0000-0000-0000-000000000000',
                data={'hourly_rate': Decimal('50000.00')},
                company_id=str(company.id),
            )

    def test_delete_rate_ok(self, user, company):
        """Eliminación exitosa."""
        rate = ResourceCostRate.objects.create(
            company=company,
            user=user,
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            hourly_rate=Decimal('30000.00'),
            currency='COP',
        )
        ResourceCostRateService.delete_rate(str(rate.id), str(company.id))
        assert not ResourceCostRate.objects.filter(id=rate.id).exists()

    def test_delete_rate_not_found_raises(self, company):
        """Tarifa inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            ResourceCostRateService.delete_rate(
                '00000000-0000-0000-0000-000000000000', str(company.id)
            )


# ─────────────────────────────────────────────────────────────────────────────
# BudgetSnapshotService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBudgetSnapshotService:

    def test_create_snapshot_ok(self, project, budget, company):
        """Crea snapshot del día actual."""
        snapshot = BudgetSnapshotService.create_snapshot(
            str(project.id), str(company.id)
        )
        assert snapshot.pk is not None
        assert snapshot.snapshot_date == date.today()
        assert snapshot.planned_budget == Decimal('700000.00')

    def test_create_snapshot_idempotent(self, project, budget, company):
        """Llamar dos veces el mismo día actualiza en lugar de crear duplicado."""
        s1 = BudgetSnapshotService.create_snapshot(str(project.id), str(company.id))
        s2 = BudgetSnapshotService.create_snapshot(str(project.id), str(company.id))
        assert s1.pk == s2.pk
        count = BudgetSnapshot.objects.filter(project=project).count()
        assert count == 1

    def test_create_snapshot_project_not_found(self, company):
        """Proyecto inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            BudgetSnapshotService.create_snapshot(
                '00000000-0000-0000-0000-000000000000', str(company.id)
            )

    def test_list_snapshots_empty(self, project):
        """Sin snapshots: lista vacía."""
        result = BudgetSnapshotService.list_snapshots(str(project.id))
        assert result == []

    def test_list_snapshots_returns_all(self, project, budget, company):
        """Retorna todos los snapshots en orden cronológico."""
        BudgetSnapshotService.create_snapshot(str(project.id), str(company.id))
        result = BudgetSnapshotService.list_snapshots(str(project.id))
        assert len(result) == 1
        assert 'snapshot_date' in result[0]
        assert 'total_cost' in result[0]


# ─────────────────────────────────────────────────────────────────────────────
# InvoiceService
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestInvoiceService:

    def test_generate_invoice_empty_project(self, project, company):
        """Proyecto sin timesheets ni gastos: grand_total = 0."""
        data = InvoiceService.generate_invoice_data(str(project.id), str(company.id))
        assert data['grand_total'] == Decimal('0.00')
        assert data['line_items'] == []
        assert data['project_name'] == project.nombre
        assert data['client_name'] == project.cliente_nombre

    def test_generate_invoice_with_labor(
        self, project, budget, task, user, company, cost_rate, timesheet_entry
    ):
        """Con timesheets: incluye líneas de mano de obra."""
        data = InvoiceService.generate_invoice_data(str(project.id), str(company.id))
        labor_lines = [li for li in data['line_items'] if li['type'] == 'labor']
        assert len(labor_lines) == 1
        assert labor_lines[0]['quantity'] == Decimal('8.00')
        assert data['subtotal_labor'] == Decimal('8.00') * Decimal('50000.00')

    def test_generate_invoice_excludes_unapproved_expenses(
        self, project, budget, company, expense
    ):
        """Gastos no aprobados no aparecen en el invoice."""
        data = InvoiceService.generate_invoice_data(str(project.id), str(company.id))
        expense_lines = [li for li in data['line_items'] if li['type'] == 'expense']
        assert len(expense_lines) == 0

    def test_generate_invoice_includes_approved_billable_expenses(
        self, project, budget, company, expense, user2
    ):
        """Gastos aprobados y facturables aparecen en el invoice."""
        expense.approved_by   = user2
        expense.approved_date = timezone.now()
        expense.save()

        data = InvoiceService.generate_invoice_data(str(project.id), str(company.id))
        expense_lines = [li for li in data['line_items'] if li['type'] == 'expense']
        assert len(expense_lines) == 1
        assert data['subtotal_expenses'] == Decimal('50000.00')

    def test_generate_invoice_project_not_found(self, company):
        """Proyecto inexistente: ValidationError."""
        with pytest.raises(ValidationError):
            InvoiceService.generate_invoice_data(
                '00000000-0000-0000-0000-000000000000', str(company.id)
            )
