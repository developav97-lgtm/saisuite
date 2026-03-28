"""
SaiSuite — Feature #7: Budget & Cost Tracking — Views
25 endpoints REST bajo /api/v1/projects/

Regla: las views solo orquestan (request → service → response).
Sin lógica de negocio aquí.

Routes:
  Budget
    GET/POST/PATCH  <project_pk>/budget/
    POST            <project_pk>/budget/approve/
    GET             <project_pk>/budget/variance/
    GET             <project_pk>/budget/alerts/
    GET/POST        <project_pk>/budget/snapshots/

  Costs
    GET             <project_pk>/costs/total/
    GET             <project_pk>/costs/by-resource/
    GET             <project_pk>/costs/by-task/
    GET             <project_pk>/costs/evm/
    GET             <project_pk>/invoice-data/

  Expenses
    GET/POST        <project_pk>/expenses/
    GET/PATCH/DEL   expenses/<pk>/
    POST            expenses/<pk>/approve/

  Cost Rates
    GET/POST        resources/cost-rates/
    GET/PATCH/DEL   resources/cost-rates/<pk>/
"""
import logging
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.proyectos.budget_serializers import (
    BudgetAlertSerializer,
    BudgetSnapshotSerializer,
    BudgetVarianceSerializer,
    CostBreakdownResourceSerializer,
    CostBreakdownTaskSerializer,
    CostSummarySerializer,
    EvmMetricsSerializer,
    InvoiceDataSerializer,
    ProjectBudgetSerializer,
    ProjectBudgetWriteSerializer,
    ProjectExpenseDetailSerializer,
    ProjectExpenseListSerializer,
    ProjectExpenseWriteSerializer,
    ResourceCostRateDetailSerializer,
    ResourceCostRateListSerializer,
    ResourceCostRateWriteSerializer,
)
from apps.proyectos.budget_services import (
    BudgetManagementService,
    BudgetSnapshotService,
    CostCalculationService,
    EVMService,
    ExpenseService,
    InvoiceService,
    ResourceCostRateService,
)
from apps.proyectos.models import ProjectBudget, ProjectExpense, ResourceCostRate
from apps.proyectos.permissions import CanAccessProyectos

logger = logging.getLogger(__name__)


def _company_id(request) -> str:
    return str(request.user.company_id)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _bad_request(exc: Exception) -> Response:
    """Convierte ValidationError → 400 con {detail}."""
    msg = exc.message if hasattr(exc, 'message') else str(exc)
    return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)


def _not_found(resource: str) -> Response:
    return Response({'detail': f'{resource} no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# Budget endpoints
# ─────────────────────────────────────────────────────────────────────────────

class ProjectBudgetView(APIView):
    """
    BG-15 — CRUD de presupuesto del proyecto.

    GET    <project_pk>/budget/   → retorna presupuesto con campos computados
    POST   <project_pk>/budget/   → crea o reemplaza presupuesto
    PATCH  <project_pk>/budget/   → actualiza campos parcialmente
    """
    permission_classes = [CanAccessProyectos]

    def _build_computed_context(self, project_id: str) -> dict:
        """Inyecta campos computados en el contexto del serializer."""
        try:
            totals = CostCalculationService.get_total_cost(project_id)
            variance = CostCalculationService.get_budget_variance(project_id)
        except Exception:
            return {}

        alert_level = 'none'
        alerts = BudgetManagementService.check_budget_alerts(project_id)
        if alerts:
            severities = [a['type'] for a in alerts]
            if 'danger' in severities:
                alert_level = 'critical'
            elif 'warning' in severities:
                alert_level = 'warning'

        return {
            'actual_labor_cost':   str(totals.get('labor_cost', '0.00')),
            'actual_expense_cost': str(totals.get('expense_cost', '0.00')),
            'actual_total_cost':   str(totals.get('total_cost', '0.00')),
            'variance':            str(variance.get('variance', '0.00')),
            'variance_percentage': str(variance.get('variance_percentage', '0.00')),
            'alert':               alert_level,
        }

    def get(self, request, project_pk=None):
        try:
            budget = ProjectBudget.objects.select_related('project', 'approved_by').get(
                project_id=str(project_pk),
                company_id=_company_id(request),
            )
        except ProjectBudget.DoesNotExist:
            return _not_found('Presupuesto')

        computed = self._build_computed_context(str(project_pk))
        serializer = ProjectBudgetSerializer(
            budget,
            context={'computed_fields': computed, 'request': request},
        )
        return Response(serializer.data)

    def post(self, request, project_pk=None):
        serializer = ProjectBudgetWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            budget = BudgetManagementService.set_project_budget(
                project_id=str(project_pk),
                data=serializer.validated_data,
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        computed = self._build_computed_context(str(project_pk))
        out = ProjectBudgetSerializer(
            budget,
            context={'computed_fields': computed, 'request': request},
        )
        return Response(out.data, status=status.HTTP_201_CREATED)

    def patch(self, request, project_pk=None):
        try:
            budget = ProjectBudget.objects.get(
                project_id=str(project_pk),
                company_id=_company_id(request),
            )
        except ProjectBudget.DoesNotExist:
            return _not_found('Presupuesto')

        serializer = ProjectBudgetWriteSerializer(budget, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated = BudgetManagementService.set_project_budget(
                project_id=str(project_pk),
                data=serializer.validated_data,
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        computed = self._build_computed_context(str(project_pk))
        out = ProjectBudgetSerializer(
            updated,
            context={'computed_fields': computed, 'request': request},
        )
        return Response(out.data)


class BudgetApproveView(APIView):
    """
    BG-15 — Aprobar presupuesto del proyecto.

    POST <project_pk>/budget/approve/
    Body: {"approved_budget": "1500000.00"}
    """
    permission_classes = [CanAccessProyectos]

    def post(self, request, project_pk=None):
        raw = request.data.get('approved_budget')
        if raw is None:
            return Response(
                {'detail': 'El campo approved_budget es requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            approved_budget = Decimal(str(raw))
        except InvalidOperation:
            return Response(
                {'detail': 'approved_budget debe ser un número decimal válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            budget = BudgetManagementService.approve_budget(
                project_id=str(project_pk),
                approved_budget=approved_budget,
                approved_by_user_id=str(request.user.id),
            )
        except ValidationError as exc:
            return _bad_request(exc)
        except ProjectBudget.DoesNotExist:
            return _not_found('Presupuesto')

        out = ProjectBudgetSerializer(budget, context={'request': request})
        return Response(out.data)


class BudgetVarianceView(APIView):
    """
    BG-16 — Varianza entre presupuesto aprobado y costo real.

    GET <project_pk>/budget/variance/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        result = CostCalculationService.get_budget_variance(str(project_pk))
        serializer = BudgetVarianceSerializer(data=result)
        serializer.is_valid()
        return Response(serializer.data)


class BudgetAlertsView(APIView):
    """
    BG-17 — Alertas de presupuesto del proyecto.

    GET <project_pk>/budget/alerts/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        alerts = BudgetManagementService.check_budget_alerts(str(project_pk))
        return Response(alerts)


class BudgetSnapshotListView(APIView):
    """
    BG-18 — Snapshots históricos del presupuesto.

    GET  <project_pk>/budget/snapshots/   → lista cronológica
    POST <project_pk>/budget/snapshots/   → crea snapshot de hoy (idempotente)
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        snapshots = BudgetSnapshotService.list_snapshots(str(project_pk))
        serializer = BudgetSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)

    def post(self, request, project_pk=None):
        try:
            snapshot = BudgetSnapshotService.create_snapshot(
                project_id=str(project_pk),
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        serializer = BudgetSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# Cost endpoints
# ─────────────────────────────────────────────────────────────────────────────

class CostTotalView(APIView):
    """
    BG-15 — Resumen de costos totales del proyecto.

    GET <project_pk>/costs/total/
    Query params: start_date, end_date (YYYY-MM-DD, optional)
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        result = CostCalculationService.get_total_cost(str(project_pk))
        serializer = CostSummarySerializer(data=result)
        serializer.is_valid()
        return Response(serializer.data)


class CostByResourceView(APIView):
    """
    BG-15 — Desglose de costos por recurso.

    GET <project_pk>/costs/by-resource/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        items = CostCalculationService.get_cost_by_resource(str(project_pk))
        serializer = CostBreakdownResourceSerializer(items, many=True)
        return Response(serializer.data)


class CostByTaskView(APIView):
    """
    BG-15 — Desglose de costos por tarea.

    GET <project_pk>/costs/by-task/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        items = CostCalculationService.get_cost_by_task(str(project_pk))
        serializer = CostBreakdownTaskSerializer(items, many=True)
        return Response(serializer.data)


class EVMMetricsView(APIView):
    """
    BG-29 — Métricas de Earned Value Management (EVM).

    GET <project_pk>/costs/evm/
    Query params: as_of_date (YYYY-MM-DD, optional — default hoy)
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        from datetime import date as date_type
        as_of_str = request.query_params.get('as_of_date')
        as_of = None
        if as_of_str:
            try:
                as_of = date_type.fromisoformat(as_of_str)
            except ValueError:
                return Response(
                    {'detail': 'as_of_date debe tener formato YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        result = EVMService.get_evm_metrics(
            project_id=str(project_pk),
            as_of_date=as_of,
        )
        serializer = EvmMetricsSerializer(data=result)
        serializer.is_valid()
        return Response(serializer.data)


class InvoiceDataView(APIView):
    """
    BG-48 — Datos para generación de factura del proyecto.

    GET <project_pk>/invoice-data/
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        try:
            data = InvoiceService.generate_invoice_data(str(project_pk), _company_id(request))
        except ValidationError as exc:
            return _bad_request(exc)

        serializer = InvoiceDataSerializer(data=data)
        serializer.is_valid()
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# Expense endpoints
# ─────────────────────────────────────────────────────────────────────────────

class ProjectExpenseListView(APIView):
    """
    BG-20 — Listado y creación de gastos del proyecto.

    GET  <project_pk>/expenses/
    POST <project_pk>/expenses/
    Query params (GET): category, billable (true|false), start_date, end_date
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request, project_pk=None):
        filters: dict = {}
        if category := request.query_params.get('category'):
            filters['category'] = category
        if billable := request.query_params.get('billable'):
            filters['billable'] = billable.lower() == 'true'
        if start := request.query_params.get('start_date'):
            filters['start_date'] = start
        if end := request.query_params.get('end_date'):
            filters['end_date'] = end

        expenses = ExpenseService.list_expenses(
            project_id=str(project_pk),
            filters=filters,
        )
        serializer = ProjectExpenseListSerializer(expenses, many=True)
        return Response(serializer.data)

    def post(self, request, project_pk=None):
        serializer = ProjectExpenseWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # paid_by is a User instance from the FK field; extract its ID
        paid_by_obj = serializer.validated_data.get('paid_by')
        paid_by_id  = str(paid_by_obj.id) if paid_by_obj else None

        try:
            expense = ExpenseService.create_expense(
                project_id=str(project_pk),
                data=serializer.validated_data,
                company_id=_company_id(request),
                paid_by_user_id=paid_by_id,
            )
        except ValidationError as exc:
            return _bad_request(exc)

        out = ProjectExpenseDetailSerializer(expense)
        return Response(out.data, status=status.HTTP_201_CREATED)


class ProjectExpenseDetailView(APIView):
    """
    BG-21 — Detalle, actualización y eliminación de un gasto.

    GET    expenses/<pk>/
    PATCH  expenses/<pk>/
    DELETE expenses/<pk>/
    """
    permission_classes = [CanAccessProyectos]

    def _get_expense(self, pk: str, company_id: str):
        try:
            return ProjectExpense.objects.select_related('paid_by', 'approved_by').get(
                id=pk,
                company_id=company_id,
            )
        except ProjectExpense.DoesNotExist:
            return None

    def get(self, request, pk=None):
        expense = self._get_expense(str(pk), _company_id(request))
        if expense is None:
            return _not_found('Gasto')
        return Response(ProjectExpenseDetailSerializer(expense).data)

    def patch(self, request, pk=None):
        expense = self._get_expense(str(pk), _company_id(request))
        if expense is None:
            return _not_found('Gasto')

        serializer = ProjectExpenseWriteSerializer(expense, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated = ExpenseService.update_expense(
                expense_id=str(pk),
                data=serializer.validated_data,
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        return Response(ProjectExpenseDetailSerializer(updated).data)

    def delete(self, request, pk=None):
        expense = self._get_expense(str(pk), _company_id(request))
        if expense is None:
            return _not_found('Gasto')

        try:
            ExpenseService.delete_expense(
                expense_id=str(pk),
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseApproveView(APIView):
    """
    BG-22 — Aprobar un gasto.

    POST expenses/<pk>/approve/
    """
    permission_classes = [CanAccessProyectos]

    def post(self, request, pk=None):
        try:
            expense = ExpenseService.approve_expense(
                expense_id=str(pk),
                approved_by_user_id=str(request.user.id),
                company_id=_company_id(request),
            )
        except PermissionDenied as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as exc:
            return _bad_request(exc)
        except ProjectExpense.DoesNotExist:
            return _not_found('Gasto')

        return Response(ProjectExpenseDetailSerializer(expense).data)


# ─────────────────────────────────────────────────────────────────────────────
# Cost Rate endpoints
# ─────────────────────────────────────────────────────────────────────────────

class CostRateListView(APIView):
    """
    BG-23 — Listado y creación de tarifas de costo por recurso.

    GET  resources/cost-rates/
    POST resources/cost-rates/
    Query params (GET): user_id (UUID, optional)
    """
    permission_classes = [CanAccessProyectos]

    def get(self, request):
        qs = ResourceCostRate.objects.select_related('user').filter(
            company_id=_company_id(request),
        ).order_by('user__email', '-start_date')

        if user_id := request.query_params.get('user_id'):
            qs = qs.filter(user_id=user_id)

        serializer = ResourceCostRateListSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ResourceCostRateWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # user is a User instance from the FK field; extract its ID
        user_obj = serializer.validated_data.get('user')
        user_id  = str(user_obj.id) if user_obj else ''

        try:
            rate = ResourceCostRateService.create_rate(
                user_id=user_id,
                data=serializer.validated_data,
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        out = ResourceCostRateDetailSerializer(rate)
        return Response(out.data, status=status.HTTP_201_CREATED)


class CostRateDetailView(APIView):
    """
    BG-24 — Detalle, actualización y desactivación de tarifa.

    GET    resources/cost-rates/<pk>/
    PATCH  resources/cost-rates/<pk>/
    DELETE resources/cost-rates/<pk>/
    """
    permission_classes = [CanAccessProyectos]

    def _get_rate(self, pk: str, company_id: str):
        try:
            return ResourceCostRate.objects.select_related('user').get(
                id=pk,
                company_id=company_id,
            )
        except ResourceCostRate.DoesNotExist:
            return None

    def get(self, request, pk=None):
        rate = self._get_rate(str(pk), _company_id(request))
        if rate is None:
            return _not_found('Tarifa')
        return Response(ResourceCostRateDetailSerializer(rate).data)

    def patch(self, request, pk=None):
        rate = self._get_rate(str(pk), _company_id(request))
        if rate is None:
            return _not_found('Tarifa')

        serializer = ResourceCostRateWriteSerializer(rate, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated = ResourceCostRateService.update_rate(
                rate_id=str(pk),
                data=serializer.validated_data,
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        return Response(ResourceCostRateDetailSerializer(updated).data)

    def delete(self, request, pk=None):
        rate = self._get_rate(str(pk), _company_id(request))
        if rate is None:
            return _not_found('Tarifa')

        try:
            ResourceCostRateService.delete_rate(
                rate_id=str(pk),
                company_id=_company_id(request),
            )
        except ValidationError as exc:
            return _bad_request(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)
