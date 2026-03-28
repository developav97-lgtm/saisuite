"""
SaiSuite — Proyectos: Budget & Cost Tracking Services (Feature #7)

TODA la lógica de presupuesto y costos va aquí.
Las views solo orquestan: reciben request → llaman service → retornan response.

Dependencias de modelos:
    Project, Task, TimesheetEntry           (apps.proyectos.models)
    ResourceCostRate, ProjectBudget,
    ProjectExpense, BudgetSnapshot          (apps.proyectos.models — Feature #7)
    settings.AUTH_USER_MODEL

Convención de moneda:
    Todos los cálculos usan Decimal, nunca float.
    La moneda retornada es la del presupuesto del proyecto (ProjectBudget.currency).
    Si no hay presupuesto, se usa 'COP'.
    No se realiza conversión entre monedas distintas — se asume que todas las
    entradas de un proyecto comparten la misma moneda.

Performance — get_labor_cost():
    En lugar de una consulta SQL por entrada de timesheet (N+1 queries),
    se pre-cargan TODAS las tarifas de los usuarios involucrados en UNA consulta
    y se resuelven en Python usando un dict indexado por user_id.
    Resultado: O(2-4) queries DB independientemente del volumen de timesheets.
"""
import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from apps.proyectos.models import (
    Project,
    Task,
    TimesheetEntry,
    ResourceCostRate,
    ProjectBudget,
    ProjectExpense,
    BudgetSnapshot,
)

logger = logging.getLogger(__name__)

# ─── Constantes ──────────────────────────────────────────────────────────────

_ZERO = Decimal('0.00')
_TWO  = Decimal('0.01')     # cuantización a 2 decimales


def _q2(value: Decimal) -> Decimal:
    """Redondea a 2 decimales usando ROUND_HALF_UP."""
    return value.quantize(_TWO, rounding=ROUND_HALF_UP)


# ─────────────────────────────────────────────────────────────────────────────
# CostCalculationService
# ─────────────────────────────────────────────────────────────────────────────

class CostCalculationService:
    """
    Cálculo de costos reales: mano de obra (timesheets × tarifas) y gastos directos.
    """

    # ── Helpers privados ─────────────────────────────────────────────────────

    @staticmethod
    def _build_rate_index(user_ids: list, company_id: str) -> dict:
        """
        Pre-carga todas las tarifas activas de los usuarios dados y las
        organiza en un dict: {user_id: [(start_date, end_date, hourly_rate), ...]}
        ordenado por start_date DESC para que el primer match sea el más reciente.

        Se usa para evitar N+1 queries en el cálculo de labor cost.
        """
        rates = (
            ResourceCostRate.objects
            .filter(user_id__in=user_ids, company_id=company_id)
            .values('user_id', 'start_date', 'end_date', 'hourly_rate')
            .order_by('user_id', '-start_date')
        )
        index: dict = defaultdict(list)
        for r in rates:
            index[str(r['user_id'])].append(
                (r['start_date'], r['end_date'], r['hourly_rate'])
            )
        return dict(index)

    @staticmethod
    def _resolve_rate(
        user_id: str,
        entry_date: date,
        rate_index: dict,
    ) -> Decimal:
        """
        Devuelve la tarifa horaria del usuario en entry_date usando el índice
        pre-cargado. Retorna Decimal('0') si no hay tarifa registrada.
        """
        periods = rate_index.get(str(user_id), [])
        for start, end, hourly in periods:
            if start <= entry_date and (end is None or end >= entry_date):
                return Decimal(str(hourly))
        return _ZERO

    @staticmethod
    def _get_project(project_id: str) -> Project:
        """Obtiene el proyecto o lanza ValidationError si no existe."""
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise ValidationError(f'Proyecto {project_id} no encontrado.')

    # ── Métodos públicos ──────────────────────────────────────────────────────

    @staticmethod
    def get_labor_cost(
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Calcula el costo de mano de obra real del proyecto.

        Algoritmo:
            1. Obtener todos los TimesheetEntry del proyecto en el rango dado,
               con select_related para evitar N+1.
            2. Pre-cargar tarifas de todos los usuarios involucrados en UNA query.
            3. Por cada entrada: cost = horas × tarifa_en_esa_fecha.
            4. Sumar costos.

        Retorna:
            {
                "labor_cost": Decimal,
                "total_hours": Decimal,
                "currency": str,
                "entries_count": int,
                "entries_without_rate": int,
            }
        """
        qs = (
            TimesheetEntry.objects
            .filter(tarea__proyecto_id=project_id)
            .select_related('usuario', 'tarea__proyecto')
        )
        if start_date:
            qs = qs.filter(fecha__gte=start_date)
        if end_date:
            qs = qs.filter(fecha__lte=end_date)

        entries = list(qs)
        if not entries:
            project = CostCalculationService._get_project(project_id)
            currency = getattr(getattr(project, 'budget', None), 'currency', 'COP')
            return {
                'labor_cost': _ZERO,
                'total_hours': _ZERO,
                'currency': currency,
                'entries_count': 0,
                'entries_without_rate': 0,
            }

        # Obtener company_id desde la primera entrada
        company_id = str(entries[0].tarea.proyecto.company_id)
        currency   = getattr(
            getattr(entries[0].tarea.proyecto, 'budget', None), 'currency', 'COP'
        )

        # Pre-cargar tarifas de todos los usuarios en UNA query
        user_ids   = list({str(e.usuario_id) for e in entries})
        rate_index = CostCalculationService._build_rate_index(user_ids, company_id)

        total_cost  = _ZERO
        total_hours = _ZERO
        without_rate = 0

        for entry in entries:
            rate = CostCalculationService._resolve_rate(
                str(entry.usuario_id), entry.fecha, rate_index
            )
            if rate == _ZERO:
                without_rate += 1
                logger.warning(
                    'timesheet_entry_no_rate',
                    extra={
                        'user_id':    str(entry.usuario_id),
                        'entry_date': str(entry.fecha),
                        'project_id': project_id,
                    },
                )
            total_cost  += entry.horas * rate
            total_hours += entry.horas

        return {
            'labor_cost':           _q2(total_cost),
            'total_hours':          _q2(total_hours),
            'currency':             currency,
            'entries_count':        len(entries),
            'entries_without_rate': without_rate,
        }

    @staticmethod
    def get_expense_cost(
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        billable_only: bool = False,
    ) -> dict:
        """
        Suma los gastos directos registrados del proyecto.

        Retorna:
            {
                "expense_cost": Decimal,
                "expenses_count": int,
                "currency": str,
            }
        """
        qs = ProjectExpense.objects.filter(project_id=project_id)
        if start_date:
            qs = qs.filter(expense_date__gte=start_date)
        if end_date:
            qs = qs.filter(expense_date__lte=end_date)
        if billable_only:
            qs = qs.filter(billable=True)

        result = qs.aggregate(total=Sum('amount'), count=Sum('amount') * 0 + Sum('amount', filter=Q(amount__gt=0)))
        # Forma correcta: Count separado
        count       = qs.count()
        total       = qs.aggregate(total=Sum('amount'))['total'] or _ZERO
        expense_cost = _q2(Decimal(str(total)))

        # Moneda desde el presupuesto del proyecto
        try:
            budget   = ProjectBudget.objects.get(project_id=project_id)
            currency = budget.currency
        except ProjectBudget.DoesNotExist:
            currency = 'COP'

        return {
            'expense_cost':   expense_cost,
            'expenses_count': count,
            'currency':       currency,
        }

    @staticmethod
    def get_total_cost(project_id: str) -> dict:
        """
        Costo total real = labor_cost + expense_cost.

        Retorna:
            {
                "labor_cost": Decimal,
                "expense_cost": Decimal,
                "total_cost": Decimal,
                "total_hours": Decimal,
                "currency": str,
                "entries_without_rate": int,
            }
        """
        labor   = CostCalculationService.get_labor_cost(project_id)
        expense = CostCalculationService.get_expense_cost(project_id)

        return {
            'labor_cost':           labor['labor_cost'],
            'expense_cost':         expense['expense_cost'],
            'total_cost':           _q2(labor['labor_cost'] + expense['expense_cost']),
            'total_hours':          labor['total_hours'],
            'currency':             labor['currency'],
            'entries_without_rate': labor['entries_without_rate'],
        }

    @staticmethod
    def get_budget_variance(project_id: str) -> dict:
        """
        Calcula la variación respecto al presupuesto aprobado (o planificado).

        Retorna:
            {
                "planned_budget": Decimal,
                "approved_budget": Decimal | None,
                "reference_budget": Decimal,
                "actual_cost": Decimal,
                "variance": Decimal,            # positivo = bajo presupuesto
                "variance_percentage": Decimal,
                "execution_percentage": Decimal,
                "status": "under"|"warning"|"on"|"over"|"no_budget",
                "currency": str,
            }
        """
        try:
            budget = ProjectBudget.objects.get(project_id=project_id)
        except ProjectBudget.DoesNotExist:
            return {
                'planned_budget':     _ZERO,
                'approved_budget':    None,
                'reference_budget':   _ZERO,
                'actual_cost':        _ZERO,
                'variance':           _ZERO,
                'variance_percentage':_ZERO,
                'execution_percentage':_ZERO,
                'status':             'no_budget',
                'currency':           'COP',
            }

        reference = budget.approved_budget if budget.approved_budget else budget.planned_total_budget
        costs     = CostCalculationService.get_total_cost(project_id)
        actual    = costs['total_cost']

        variance = reference - actual
        exec_pct = (_q2(actual / reference * 100) if reference > _ZERO else _ZERO)
        var_pct  = (_q2(variance / reference * 100) if reference > _ZERO else _ZERO)

        threshold = budget.alert_threshold_percentage
        if reference == _ZERO:
            status = 'no_budget'
        elif actual > reference:
            status = 'over'
        elif abs(actual - reference) <= Decimal('0.01'):
            status = 'on'
        elif exec_pct >= threshold:
            status = 'warning'
        else:
            status = 'under'

        return {
            'planned_budget':      budget.planned_total_budget,
            'approved_budget':     budget.approved_budget,
            'reference_budget':    reference,
            'actual_cost':         actual,
            'variance':            _q2(variance),
            'variance_percentage': var_pct,
            'execution_percentage':exec_pct,
            'status':              status,
            'currency':            budget.currency,
        }

    @staticmethod
    def get_cost_by_resource(project_id: str) -> list:
        """
        Desglosa el costo de mano de obra por recurso (usuario).

        Retorna lista de dicts ordenada por total_cost DESC.
        Retorna [] si no hay timesheets o si ocurre cualquier error inesperado.
        """
        try:
            entries = (
                TimesheetEntry.objects
                .filter(tarea__proyecto_id=project_id)
                .select_related('usuario', 'tarea', 'tarea__proyecto')
            )
            if not entries.exists():
                return []

            entries_list = list(entries)
            first = entries_list[0]
            if not hasattr(first.tarea, 'proyecto') or first.tarea.proyecto is None:
                logger.error(
                    "get_cost_by_resource: tarea sin proyecto cargado",
                    extra={"project_id": project_id},
                )
                return []

            company_id = str(first.tarea.proyecto.company_id)

            # Pre-cargar tarifas una sola vez
            user_ids   = list({str(e.usuario_id) for e in entries_list})
            rate_index = CostCalculationService._build_rate_index(user_ids, company_id)

            # Acumular por usuario
            user_data: dict = {}
            for entry in entries_list:
                uid  = str(entry.usuario_id)
                rate = CostCalculationService._resolve_rate(uid, entry.fecha, rate_index)
                cost = entry.horas * rate
                if uid not in user_data:
                    user_data[uid] = {
                        'user_id':    uid,
                        'user_name':  entry.usuario.full_name or entry.usuario.email,
                        'user_email': entry.usuario.email,
                        'hours':      _ZERO,
                        'total_cost': _ZERO,
                    }
                user_data[uid]['hours']      += entry.horas
                user_data[uid]['total_cost'] += cost

            total_labor = sum(u['total_cost'] for u in user_data.values()) or _ZERO

            result = []
            for u in user_data.values():
                hours      = _q2(u['hours'])
                total_cost = _q2(u['total_cost'])
                avg_rate   = _q2(total_cost / hours) if hours > _ZERO else _ZERO
                pct        = _q2(total_cost / total_labor * 100) if total_labor > _ZERO else _ZERO
                result.append({
                    'user_id':         u['user_id'],
                    'user_name':       u['user_name'],
                    'user_email':      u['user_email'],
                    'hours':           hours,
                    'hourly_rate_avg': avg_rate,
                    'total_cost':      total_cost,
                    'pct':             pct,
                })

            result.sort(key=lambda x: x['total_cost'], reverse=True)
            return result

        except Exception as exc:
            logger.error(
                "get_cost_by_resource: error inesperado calculando costos por recurso",
                extra={"project_id": project_id, "error": str(exc)},
            )
            return []

    @staticmethod
    def get_cost_by_task(project_id: str) -> list:
        """
        Desglosa costos de mano de obra por tarea.
        (Gastos directos son a nivel proyecto — expense_cost por tarea = 0 en v1)

        Retorna lista de dicts ordenada por total_cost DESC,
        incluyendo solo tareas con hours > 0.
        Retorna [] si no hay timesheets o si ocurre cualquier error inesperado.
        """
        try:
            entries = (
                TimesheetEntry.objects
                .filter(tarea__proyecto_id=project_id)
                .select_related('usuario', 'tarea', 'tarea__proyecto')
            )
            if not entries.exists():
                return []

            entries_list = list(entries)
            first = entries_list[0]
            if not hasattr(first.tarea, 'proyecto') or first.tarea.proyecto is None:
                logger.error(
                    "get_cost_by_task: tarea sin proyecto cargado",
                    extra={"project_id": project_id},
                )
                return []

            company_id = str(first.tarea.proyecto.company_id)

            user_ids   = list({str(e.usuario_id) for e in entries_list})
            rate_index = CostCalculationService._build_rate_index(user_ids, company_id)

            # Acumular por tarea
            task_data: dict = {}
            for entry in entries_list:
                tid  = str(entry.tarea_id)
                rate = CostCalculationService._resolve_rate(
                    str(entry.usuario_id), entry.fecha, rate_index
                )
                cost = entry.horas * rate
                if tid not in task_data:
                    task_data[tid] = {
                        'task_id':       tid,
                        'task_code':     entry.tarea.codigo or '',
                        'task_name':     entry.tarea.nombre,
                        'hours':         _ZERO,
                        'labor_cost':    _ZERO,
                        'expense_cost':  _ZERO,
                        'total_cost':    _ZERO,
                    }
                task_data[tid]['hours']      += entry.horas
                task_data[tid]['labor_cost'] += cost

            result = []
            for t in task_data.values():
                hours       = _q2(t['hours'])
                labor_cost  = _q2(t['labor_cost'])
                total_cost  = labor_cost  # expense_cost por tarea = 0 en v1
                result.append({
                    'task_id':      t['task_id'],
                    'task_code':    t['task_code'],
                    'task_name':    t['task_name'],
                    'hours':        hours,
                    'labor_cost':   labor_cost,
                    'expense_cost': _ZERO,
                    'total_cost':   total_cost,
                })

            result.sort(key=lambda x: x['total_cost'], reverse=True)
            return result

        except Exception as exc:
            logger.error(
                "get_cost_by_task: error inesperado calculando costos por tarea",
                extra={"project_id": project_id, "error": str(exc)},
            )
            return []


# ─────────────────────────────────────────────────────────────────────────────
# EVMService
# ─────────────────────────────────────────────────────────────────────────────

class EVMService:
    """
    Earned Value Management (EVM) según estándares PMI PMBOK.

    Glosario:
        BAC  — Budget at Completion (presupuesto total aprobado o planificado)
        PV   — Planned Value: BAC × (días_transcurridos / días_totales)
        EV   — Earned Value: BAC × (% completado del proyecto)
        AC   — Actual Cost: costo real incurrido
        CV   — Cost Variance: EV − AC  (negativo = sobre costo)
        SV   — Schedule Variance: EV − PV  (negativo = retrasado)
        CPI  — Cost Performance Index: EV / AC
        SPI  — Schedule Performance Index: EV / PV
        EAC  — Estimate at Completion: BAC / CPI
        ETC  — Estimate to Complete: EAC − AC
        TCPI — To-Complete Performance Index: (BAC − EV) / (BAC − AC)
        VAC  — Variance at Completion: BAC − EAC

    Simplificación documentada (DEC-028):
        PV usa distribución temporal lineal del presupuesto.
        EV usa el promedio del porcentaje_completado de las tareas.
        Un EVM task-level requeriría presupuestos por tarea (fuera del alcance de Feature #7).
    """

    @staticmethod
    def get_evm_metrics(project_id: str, as_of_date: Optional[date] = None) -> dict:
        """
        Calcula todas las métricas EVM del proyecto.

        Args:
            project_id:  UUID del proyecto.
            as_of_date:  Fecha de referencia para PV. Por defecto: hoy.

        Retorna:
            {
                "BAC": Decimal, "PV": Decimal, "EV": Decimal, "AC": Decimal,
                "CV": Decimal, "SV": Decimal,
                "CPI": Decimal|None, "SPI": Decimal|None,
                "EAC": Decimal|None, "ETC": Decimal|None,
                "TCPI": Decimal|None, "VAC": Decimal|None,
                "completion_percentage": Decimal,
                "schedule_health": "on_track"|"at_risk"|"behind",
                "cost_health": "on_track"|"at_risk"|"over_budget",
                "currency": str,
                "as_of_date": str,   # ISO date
                "warning": str|None,
            }
        """
        ref_date = as_of_date or date.today()
        warning  = None

        # ── 1. Obtener proyecto y presupuesto ─────────────────────────────
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise ValidationError(f'Proyecto {project_id} no encontrado.')

        try:
            budget   = ProjectBudget.objects.get(project_id=project_id)
            BAC      = budget.approved_budget if budget.approved_budget else budget.planned_total_budget
            currency = budget.currency
        except ProjectBudget.DoesNotExist:
            warning  = 'No se ha definido presupuesto para este proyecto.'
            BAC      = _ZERO
            currency = 'COP'

        # ── 2. Planned Value (PV) — distribución lineal ───────────────────
        start = project.fecha_inicio_planificada
        end   = project.fecha_fin_planificada

        if start and end and BAC > _ZERO:
            total_days   = (end - start).days or 1  # evitar división por cero
            elapsed_days = max(0, (ref_date - start).days)
            elapsed_days = min(elapsed_days, total_days)  # cap al máximo
            PV = _q2(BAC * Decimal(str(elapsed_days)) / Decimal(str(total_days)))
        else:
            PV = _ZERO
            if BAC > _ZERO:
                warning = (warning or '') + ' Fechas del proyecto no definidas — PV = 0.'

        # ── 3. Earned Value (EV) — avg completion_percentage × BAC ───────
        task_completion = (
            Task.objects
            .filter(proyecto_id=project_id)
            .aggregate(avg_pct=Sum('porcentaje_completado'))
        )
        task_count = Task.objects.filter(proyecto_id=project_id).count()

        if task_count > 0 and task_completion['avg_pct'] is not None:
            completion_pct = Decimal(str(task_completion['avg_pct'])) / Decimal(str(task_count))
        else:
            completion_pct = _ZERO

        EV = _q2(BAC * completion_pct / Decimal('100')) if BAC > _ZERO else _ZERO

        # ── 4. Actual Cost (AC) ───────────────────────────────────────────
        costs = CostCalculationService.get_total_cost(project_id)
        AC    = costs['total_cost']

        # ── 5. Métricas derivadas ─────────────────────────────────────────
        CV  = _q2(EV - AC)
        SV  = _q2(EV - PV)
        CPI = _q2(EV / AC) if AC > _ZERO else None
        SPI = _q2(EV / PV) if PV > _ZERO else None

        EAC  = _q2(BAC / CPI) if CPI and CPI > _ZERO else None
        ETC  = _q2(EAC - AC)  if EAC is not None else None
        VAC  = _q2(BAC - EAC) if EAC is not None else None

        BAC_minus_EV = BAC - EV
        BAC_minus_AC = BAC - AC
        TCPI = (
            _q2(BAC_minus_EV / BAC_minus_AC)
            if BAC_minus_AC > _ZERO else None
        )

        # ── 6. Indicadores de salud ───────────────────────────────────────
        def _schedule_health(spi) -> str:
            if spi is None: return 'at_risk'
            if spi >= Decimal('0.9'): return 'on_track'
            if spi >= Decimal('0.7'): return 'at_risk'
            return 'behind'

        def _cost_health(cpi) -> str:
            if cpi is None: return 'at_risk'
            if cpi >= Decimal('0.9'): return 'on_track'
            if cpi >= Decimal('0.7'): return 'at_risk'
            return 'over_budget'

        logger.info(
            'evm_calculated',
            extra={
                'project_id':        project_id,
                'BAC':               str(BAC),
                'EV':                str(EV),
                'AC':                str(AC),
                'CPI':               str(CPI),
                'SPI':               str(SPI),
                'completion_pct':    str(completion_pct),
            },
        )

        return {
            'BAC':                  BAC,
            'PV':                   PV,
            'EV':                   EV,
            'AC':                   AC,
            'CV':                   CV,
            'SV':                   SV,
            'CPI':                  CPI,
            'SPI':                  SPI,
            'EAC':                  EAC,
            'ETC':                  ETC,
            'TCPI':                 TCPI,
            'VAC':                  VAC,
            'completion_percentage':_q2(completion_pct),
            'schedule_health':      _schedule_health(SPI),
            'cost_health':          _cost_health(CPI),
            'currency':             currency,
            'as_of_date':           ref_date.isoformat(),
            'warning':              warning,
        }


# ─────────────────────────────────────────────────────────────────────────────
# BudgetManagementService
# ─────────────────────────────────────────────────────────────────────────────

class BudgetManagementService:
    """
    CRUD del presupuesto del proyecto y flujo de aprobación.
    """

    @staticmethod
    @transaction.atomic
    def set_project_budget(
        project_id: str,
        data: dict,
        company_id: str,
    ) -> ProjectBudget:
        """
        Crea o actualiza el presupuesto de un proyecto.

        Si el presupuesto ya está aprobado (approved_date IS NOT NULL),
        solo se pueden editar: alert_threshold_percentage, notes.
        Para modificar montos, primero se debe resetear la aprobación.

        Retorna ProjectBudget.

        Raises:
            ValidationError: proyecto no encontrado o intento de modificar
                             campos bloqueados en presupuesto aprobado.
        """
        try:
            project = Project.objects.get(id=project_id, company_id=company_id)
        except Project.DoesNotExist:
            raise ValidationError(
                f'Proyecto {project_id} no encontrado en la empresa.'
            )

        budget, created = ProjectBudget.objects.get_or_create(
            project=project,
            defaults={'company_id': company_id},
        )

        # Si está aprobado, solo permitir editar umbral y notas
        amount_fields = {
            'planned_labor_cost', 'planned_expense_cost',
            'planned_total_budget', 'currency',
        }
        if budget.is_approved:
            blocked = amount_fields.intersection(set(data.keys()))
            if blocked:
                raise ValidationError(
                    f'El presupuesto está aprobado. No se pueden modificar: '
                    f'{", ".join(sorted(blocked))}. '
                    f'Contacte al administrador para revertir la aprobación.'
                )

        for field, value in data.items():
            setattr(budget, field, value)

        budget.full_clean()
        budget.save()

        logger.info(
            'budget_set',
            extra={
                'project_id': project_id,
                'company_id': company_id,
                'total':      str(budget.planned_total_budget),
                'is_new':     created,
            },
        )
        return budget

    @staticmethod
    @transaction.atomic
    def approve_budget(
        project_id: str,
        approved_budget: Decimal,
        approved_by_user_id: str,
    ) -> ProjectBudget:
        """
        Aprueba formalmente el presupuesto del proyecto.

        Raises:
            ValidationError: sin presupuesto previo, monto inválido, o ya aprobado.
        """
        try:
            budget = ProjectBudget.objects.select_for_update().get(
                project_id=project_id
            )
        except ProjectBudget.DoesNotExist:
            raise ValidationError(
                'Debe definir un presupuesto antes de aprobarlo.'
            )

        if budget.is_approved:
            raise ValidationError('El presupuesto ya fue aprobado.')

        if approved_budget <= _ZERO:
            raise ValidationError('El presupuesto aprobado debe ser mayor a 0.')

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            approver = User.objects.get(id=approved_by_user_id)
        except User.DoesNotExist:
            raise ValidationError('Usuario aprobador no encontrado.')

        budget.approved_budget = approved_budget
        budget.approved_by     = approver
        budget.approved_date   = timezone.now()
        budget.save(update_fields=['approved_budget', 'approved_by', 'approved_date', 'updated_at'])

        logger.info(
            'budget_approved',
            extra={
                'project_id':   project_id,
                'approved_by':  approved_by_user_id,
                'amount':       str(approved_budget),
            },
        )
        return budget

    @staticmethod
    def check_budget_alerts(project_id: str) -> list:
        """
        Evalúa si el proyecto ha superado umbrales de alerta de presupuesto.

        Retorna lista de dicts de alerta (puede estar vacía si no hay budget
        o si el proyecto está bajo presupuesto con margen holgado).
        """
        variance = CostCalculationService.get_budget_variance(project_id)

        if variance['status'] == 'no_budget':
            return []

        try:
            budget = ProjectBudget.objects.get(project_id=project_id)
        except ProjectBudget.DoesNotExist:
            return []

        costs     = CostCalculationService.get_total_cost(project_id)
        exec_pct  = variance['execution_percentage']
        threshold = budget.alert_threshold_percentage
        reference = variance['reference_budget']
        alerts    = []

        base_payload = {
            'current_pct':      exec_pct,
            'threshold':        threshold,
            'labor_cost':       costs['labor_cost'],
            'expense_cost':     costs['expense_cost'],
            'total_cost':       costs['total_cost'],
            'reference_budget': reference,
        }

        if exec_pct >= Decimal('100'):
            alerts.append({
                **base_payload,
                'type':    'danger',
                'message': (
                    f'Presupuesto superado: {exec_pct}% ejecutado '
                    f'(sobre {reference} {budget.currency}). '
                    'Se requiere aprobación de presupuesto adicional.'
                ),
            })
        elif exec_pct >= threshold:
            alerts.append({
                **base_payload,
                'type':    'warning',
                'message': (
                    f'Alerta de presupuesto: {exec_pct}% ejecutado '
                    f'(umbral configurado: {threshold}%).'
                ),
            })
        elif exec_pct >= threshold - Decimal('10'):
            alerts.append({
                **base_payload,
                'type':    'info',
                'message': (
                    f'Pre-alerta: {exec_pct}% del presupuesto ejecutado. '
                    f'El umbral de alerta es {threshold}%.'
                ),
            })

        return alerts


# ─────────────────────────────────────────────────────────────────────────────
# ExpenseService
# ─────────────────────────────────────────────────────────────────────────────

class ExpenseService:
    """CRUD de gastos directos del proyecto."""

    @staticmethod
    @transaction.atomic
    def create_expense(
        project_id: str,
        data: dict,
        paid_by_user_id: Optional[str],
        company_id: str,
    ) -> ProjectExpense:
        """
        Registra un gasto directo en el proyecto.

        Raises:
            ValidationError: proyecto no encontrado, amount <= 0,
                             o fecha futura.
        """
        try:
            project = Project.objects.get(id=project_id, company_id=company_id)
        except Project.DoesNotExist:
            raise ValidationError(
                f'Proyecto {project_id} no encontrado en la empresa.'
            )

        amount = Decimal(str(data.get('amount', 0)))
        if amount <= _ZERO:
            raise ValidationError('El monto del gasto debe ser mayor a 0.')

        expense_date = data.get('expense_date')
        if expense_date and isinstance(expense_date, date):
            if expense_date > date.today() + timedelta(days=1):
                raise ValidationError(
                    'No se pueden registrar gastos con fecha futura.'
                )

        paid_by = None
        if paid_by_user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                paid_by = User.objects.get(id=paid_by_user_id, company_id=company_id)
            except User.DoesNotExist:
                raise ValidationError('Usuario "pagado por" no encontrado en la empresa.')

        expense = ProjectExpense(
            project    = project,
            company_id = company_id,
            paid_by    = paid_by,
            **{k: v for k, v in data.items() if k != 'paid_by'},
        )
        expense.full_clean()
        expense.save()

        logger.info(
            'expense_created',
            extra={
                'project_id':  project_id,
                'expense_id':  str(expense.id),
                'amount':      str(expense.amount),
                'category':    expense.category,
                'company_id':  company_id,
            },
        )
        return expense

    @staticmethod
    def list_expenses(
        project_id: str,
        filters: Optional[dict] = None,
    ):
        """
        Lista gastos de un proyecto con filtros opcionales.

        Filtros soportados (via `filters` dict):
            - category: str
            - billable: bool
            - start_date / end_date: date
            - paid_by_user_id: str
        """
        qs = (
            ProjectExpense.objects
            .filter(project_id=project_id)
            .select_related('paid_by', 'approved_by', 'project')
            .order_by('-expense_date', '-created_at')
        )
        if not filters:
            return qs

        if 'category' in filters and filters['category']:
            qs = qs.filter(category=filters['category'])
        if 'billable' in filters and filters['billable'] is not None:
            qs = qs.filter(billable=filters['billable'])
        if 'start_date' in filters and filters['start_date']:
            qs = qs.filter(expense_date__gte=filters['start_date'])
        if 'end_date' in filters and filters['end_date']:
            qs = qs.filter(expense_date__lte=filters['end_date'])
        if 'paid_by_user_id' in filters and filters['paid_by_user_id']:
            qs = qs.filter(paid_by_id=filters['paid_by_user_id'])

        return qs

    @staticmethod
    @transaction.atomic
    def approve_expense(
        expense_id: str,
        approved_by_user_id: str,
        company_id: str,
    ) -> ProjectExpense:
        """
        Aprueba un gasto. El aprobador no puede ser el mismo usuario que registró
        el gasto (segregación de funciones).

        Raises:
            ValidationError: gasto no encontrado, ya aprobado, o aprobador = pagador.
        """
        try:
            expense = ProjectExpense.objects.select_for_update().get(
                id=expense_id, company_id=company_id
            )
        except ProjectExpense.DoesNotExist:
            raise ProjectExpense.DoesNotExist(f'Gasto {expense_id} no encontrado.')

        if expense.is_approved:
            raise ValidationError('Este gasto ya fue aprobado.')

        if expense.paid_by_id and str(expense.paid_by_id) == str(approved_by_user_id):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied(
                'El aprobador no puede ser el mismo usuario que registró el gasto.'
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            approver = User.objects.get(id=approved_by_user_id)
        except User.DoesNotExist:
            raise ValidationError('Usuario aprobador no encontrado.')

        expense.approved_by   = approver
        expense.approved_date = timezone.now()
        expense.save(update_fields=['approved_by', 'approved_date', 'updated_at'])

        logger.info(
            'expense_approved',
            extra={
                'expense_id':  expense_id,
                'approved_by': approved_by_user_id,
                'amount':      str(expense.amount),
            },
        )
        return expense

    @staticmethod
    @transaction.atomic
    def update_expense(
        expense_id: str,
        data: dict,
        company_id: str,
    ) -> ProjectExpense:
        """
        Actualiza campos de un gasto existente.
        No se puede editar si ya está aprobado.

        Raises:
            ValidationError: gasto no encontrado, ya aprobado, o datos inválidos.
        """
        try:
            expense = ProjectExpense.objects.select_for_update().get(
                id=expense_id, company_id=company_id
            )
        except ProjectExpense.DoesNotExist:
            raise ValidationError(f'Gasto {expense_id} no encontrado.')

        if expense.is_approved:
            raise ValidationError(
                'No se puede editar un gasto ya aprobado. '
                'Contacte al administrador para revertir la aprobación.'
            )

        immutable = {'project', 'company', 'company_id', 'project_id'}
        for field, value in data.items():
            if field not in immutable:
                setattr(expense, field, value)

        expense.full_clean()
        expense.save()

        logger.info(
            'expense_updated',
            extra={'expense_id': expense_id, 'company_id': company_id},
        )
        return expense

    @staticmethod
    @transaction.atomic
    def delete_expense(
        expense_id: str,
        company_id: str,
    ) -> None:
        """
        Elimina un gasto (hard delete). No se puede eliminar si está aprobado.

        Raises:
            ValidationError: gasto no encontrado o ya aprobado.
        """
        try:
            expense = ProjectExpense.objects.get(
                id=expense_id, company_id=company_id
            )
        except ProjectExpense.DoesNotExist:
            raise ValidationError(f'Gasto {expense_id} no encontrado.')

        if expense.is_approved:
            raise ValidationError(
                'No se puede eliminar un gasto aprobado. '
                'Contacte al administrador para revertir la aprobación.'
            )

        expense_id_log = expense_id
        expense.delete()

        logger.info(
            'expense_deleted',
            extra={'expense_id': expense_id_log, 'company_id': company_id},
        )


# ─────────────────────────────────────────────────────────────────────────────
# ResourceCostRateService
# ─────────────────────────────────────────────────────────────────────────────

class ResourceCostRateService:
    """Gestión de tarifas horarias de recursos (usuarios)."""

    @staticmethod
    def get_active_rate(
        user_id: str,
        company_id: str,
        on_date: date,
    ) -> Optional[ResourceCostRate]:
        """
        Obtiene la tarifa vigente para un usuario en una fecha dada.

        Retorna None si no hay tarifa registrada.
        """
        return (
            ResourceCostRate.objects
            .filter(
                user_id=user_id,
                company_id=company_id,
                start_date__lte=on_date,
            )
            .filter(Q(end_date__gte=on_date) | Q(end_date__isnull=True))
            .order_by('-start_date')
            .first()
        )

    @staticmethod
    def _validate_overlap(
        user_id: str,
        company_id: str,
        start_date: date,
        end_date: Optional[date],
        exclude_id: Optional[str] = None,
    ) -> None:
        """
        Valida que el nuevo rango no solape con tarifas existentes del mismo
        (user, company).

        Raises:
            ValidationError con mensaje descriptivo si hay solapamiento.
        """
        qs = ResourceCostRate.objects.filter(
            user_id=user_id,
            company_id=company_id,
        )
        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        # Posibles solapamientos (álgebra de intervalos):
        # [new_start, new_end] solapa con [ex_start, ex_end] si:
        #   new_start <= ex_end (o ex_end IS NULL)
        #   AND new_end (o +∞) >= ex_start
        if end_date is None:
            # Nueva tarifa abierta: solapa con cualquiera que inicie
            # después o al mismo tiempo que new_start y con cualquier
            # tarifa abierta existente
            overlapping = qs.filter(
                Q(start_date__gte=start_date) |
                Q(end_date__isnull=True, start_date__lte=start_date)
            )
        else:
            # Nueva tarifa cerrada: solapa con cualquiera cuyo rango
            # intersecta [start_date, end_date]
            overlapping = qs.filter(
                start_date__lte=end_date
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=start_date)
            )

        conflict = overlapping.first()
        if conflict:
            conflict_end = conflict.end_date.isoformat() if conflict.end_date else 'presente'
            raise ValidationError(
                f'La tarifa se solapa con una tarifa existente del período '
                f'{conflict.start_date} → {conflict_end}. '
                f'Ajuste las fechas para evitar el solapamiento.'
            )

    @staticmethod
    @transaction.atomic
    def create_rate(
        user_id: str,
        data: dict,
        company_id: str,
    ) -> ResourceCostRate:
        """
        Crea una nueva tarifa horaria para un recurso.

        Raises:
            ValidationError: solapamiento con tarifa existente, hourly_rate <= 0,
                             o end_date <= start_date.
        """
        start_date = data.get('start_date')
        end_date   = data.get('end_date')
        hourly     = Decimal(str(data.get('hourly_rate', 0)))

        if hourly <= _ZERO:
            raise ValidationError('La tarifa por hora debe ser mayor a 0.')
        if end_date and end_date <= start_date:
            raise ValidationError(
                'La fecha de fin debe ser posterior a la fecha de inicio.'
            )

        ResourceCostRateService._validate_overlap(
            user_id, company_id, start_date, end_date
        )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValidationError(f'Usuario {user_id} no encontrado.')

        rate = ResourceCostRate(
            user_id    = user_id,
            company_id = company_id,
            **data,
        )
        rate.full_clean()
        rate.save()

        logger.info(
            'cost_rate_created',
            extra={
                'user_id':     user_id,
                'company_id':  company_id,
                'start_date':  str(start_date),
                'end_date':    str(end_date) if end_date else 'open',
                'hourly_rate': str(hourly),
            },
        )
        return rate

    @staticmethod
    @transaction.atomic
    def update_rate(
        rate_id: str,
        data: dict,
        company_id: str,
    ) -> ResourceCostRate:
        """
        Actualiza una tarifa existente.

        Raises:
            ValidationError: tarifa no encontrada, solapamiento, o datos inválidos.
        """
        try:
            rate = ResourceCostRate.objects.select_for_update().get(
                id=rate_id, company_id=company_id
            )
        except ResourceCostRate.DoesNotExist:
            raise ValidationError(f'Tarifa {rate_id} no encontrada.')

        start_date = data.get('start_date', rate.start_date)
        end_date   = data.get('end_date', rate.end_date)
        hourly     = Decimal(str(data.get('hourly_rate', rate.hourly_rate)))

        if hourly <= _ZERO:
            raise ValidationError('La tarifa por hora debe ser mayor a 0.')
        if end_date and end_date <= start_date:
            raise ValidationError(
                'La fecha de fin debe ser posterior a la fecha de inicio.'
            )

        ResourceCostRateService._validate_overlap(
            str(rate.user_id), company_id, start_date, end_date, exclude_id=rate_id
        )

        for field, value in data.items():
            setattr(rate, field, value)
        rate.full_clean()
        rate.save()

        logger.info(
            'cost_rate_updated',
            extra={'rate_id': rate_id, 'company_id': company_id},
        )
        return rate

    @staticmethod
    @transaction.atomic
    def delete_rate(
        rate_id: str,
        company_id: str,
    ) -> None:
        """
        Elimina una tarifa horaria (hard delete).

        Raises:
            ValidationError: tarifa no encontrada.
        """
        try:
            rate = ResourceCostRate.objects.get(id=rate_id, company_id=company_id)
        except ResourceCostRate.DoesNotExist:
            raise ValidationError(f'Tarifa {rate_id} no encontrada.')

        rate.delete()
        logger.info(
            'cost_rate_deleted',
            extra={'rate_id': rate_id, 'company_id': company_id},
        )


# ─────────────────────────────────────────────────────────────────────────────
# BudgetSnapshotService
# ─────────────────────────────────────────────────────────────────────────────

class BudgetSnapshotService:
    """Creación y consulta de snapshots periódicos del presupuesto."""

    @staticmethod
    @transaction.atomic
    def create_snapshot(project_id: str, company_id: str) -> BudgetSnapshot:
        """
        Crea o actualiza el snapshot del día actual para un proyecto.

        Idempotente: si ya existe un snapshot hoy, lo actualiza con los
        valores más recientes en lugar de fallar.

        Retorna BudgetSnapshot.
        """
        try:
            project = Project.objects.get(id=project_id, company_id=company_id)
        except Project.DoesNotExist:
            raise ValidationError(f'Proyecto {project_id} no encontrado.')

        costs    = CostCalculationService.get_total_cost(project_id)
        variance = CostCalculationService.get_budget_variance(project_id)

        snapshot, created = BudgetSnapshot.objects.update_or_create(
            project_id    = project_id,
            snapshot_date = date.today(),
            defaults={
                'company_id':         company_id,
                'labor_cost':         costs['labor_cost'],
                'expense_cost':       costs['expense_cost'],
                'total_cost':         costs['total_cost'],
                'planned_budget':     variance['reference_budget'],
                'variance':           variance['variance'],
                'variance_percentage':variance['variance_percentage'],
            },
        )

        logger.info(
            'budget_snapshot_created',
            extra={
                'project_id':   project_id,
                'snapshot_date':str(date.today()),
                'total_cost':   str(costs['total_cost']),
                'is_new':       created,
            },
        )
        return snapshot

    @staticmethod
    def list_snapshots(project_id: str) -> list:
        """
        Lista todos los snapshots de un proyecto ordenados por fecha asc.
        Retorna lista de dicts listos para serializar.
        """
        qs = (
            BudgetSnapshot.objects
            .filter(project_id=project_id)
            .order_by('snapshot_date')
            .values(
                'id', 'snapshot_date',
                'labor_cost', 'expense_cost', 'total_cost',
                'planned_budget', 'variance', 'variance_percentage',
            )
        )
        return list(qs)


# ─────────────────────────────────────────────────────────────────────────────
# InvoiceService
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceService:
    """Generación de datos para facturación al cliente."""

    @staticmethod
    def generate_invoice_data(project_id: str, company_id: str) -> dict:
        """
        Prepara la información de facturación del proyecto.

        Incluye:
        - Líneas de mano de obra: una por usuario (horas, tarifa promedio, subtotal)
        - Líneas de gastos: solo los gastos aprobados y facturables

        Nota: Los gastos NO aprobados y los NO facturables se excluyen
              explícitamente del invoice.

        Retorna:
            {
                "project_id": str,
                "project_name": str,
                "client_name": str,
                "line_items": [{"type", "description", "quantity", "unit_rate", "subtotal"}],
                "subtotal_labor": Decimal,
                "subtotal_expenses": Decimal,
                "grand_total": Decimal,
                "currency": str,
                "generated_at": str (ISO datetime),
            }
        """
        try:
            project = Project.objects.get(id=project_id, company_id=company_id)
        except Project.DoesNotExist:
            raise ValidationError(f'Proyecto {project_id} no encontrado.')

        try:
            budget   = ProjectBudget.objects.get(project_id=project_id)
            currency = budget.currency
        except ProjectBudget.DoesNotExist:
            currency = 'COP'

        # ── Líneas de mano de obra (por recurso) ──────────────────────────
        breakdown = CostCalculationService.get_cost_by_resource(project_id)
        labor_items = []
        subtotal_labor = _ZERO

        for item in breakdown:
            if item['total_cost'] == _ZERO:
                continue
            labor_items.append({
                'type':        'labor',
                'description': f"Mano de obra — {item['user_name']}",
                'quantity':    item['hours'],
                'unit_rate':   item['hourly_rate_avg'],
                'subtotal':    item['total_cost'],
            })
            subtotal_labor += item['total_cost']

        # ── Líneas de gastos facturables aprobados ─────────────────────────
        billable_expenses = (
            ProjectExpense.objects
            .filter(
                project_id  = project_id,
                billable    = True,
                approved_date__isnull = False,
            )
            .order_by('expense_date')
        )
        expense_items   = []
        subtotal_expenses = _ZERO

        for exp in billable_expenses:
            expense_items.append({
                'type':        'expense',
                'description': f"{exp.get_category_display()} — {exp.description}",
                'quantity':    Decimal('1.00'),
                'unit_rate':   exp.amount,
                'subtotal':    exp.amount,
            })
            subtotal_expenses += exp.amount

        line_items    = labor_items + expense_items
        grand_total   = _q2(subtotal_labor + subtotal_expenses)
        subtotal_labor    = _q2(subtotal_labor)
        subtotal_expenses = _q2(subtotal_expenses)

        return {
            'project_id':         str(project.id),
            'project_name':       project.nombre,
            'client_name':        project.cliente_nombre,
            'line_items':         line_items,
            'subtotal_labor':     subtotal_labor,
            'subtotal_expenses':  subtotal_expenses,
            'grand_total':        grand_total,
            'currency':           currency,
            'generated_at':       timezone.now().isoformat(),
        }
