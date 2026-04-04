# FEATURE-7: Budget & Cost Tracking — Backend Architecture

**Feature:** Budget & Cost Tracking
**App:** `backend/apps/proyectos/`
**New files:** `budget_services.py`, `budget_serializers.py`, `budget_views.py`
**New migrations:** `0018_feature_7_budget_models.py`, `0019_feature_7_budget_indexes.py`
**Date:** 2026-03-27
**Stack:** Django 5 + DRF + PostgreSQL 16

---

## Table of Contents

1. [Model Definitions](#1-model-definitions)
2. [Service Function Signatures](#2-service-function-signatures)
3. [EVM Algorithm — Detailed Pseudocode](#3-evm-algorithm--detailed-pseudocode)
4. [Endpoint Table](#4-endpoint-table)
5. [Performance Strategy](#5-performance-strategy)
6. [Testing Strategy](#6-testing-strategy)
7. [Migration Notes](#7-migration-notes)

---

## 1. Model Definitions

All models inherit from `BaseModel` (UUID pk, `company` FK, `created_at`, `updated_at`, soft-delete via `activo`). Money fields use `NUMERIC(15,2)` — never float. All models are multi-tenant via `company`.

### 1.1 ResourceCostRate

```python
# backend/apps/proyectos/models.py — append after existing ResourceCapacity class

class ResourceCostRate(BaseModel):
    """
    Tarifa horaria facturable de un recurso (usuario) para un período dado.

    Regla de negocio: los rangos de fechas [start_date, end_date] no pueden
    solaparse para el mismo par (user, company). end_date=NULL significa
    "actualmente vigente". Solo puede existir un registro con end_date=NULL
    por (user, company).

    La validación de solapamiento se aplica en ResourceCostRateService.create_rate()
    antes de persistir, usando la constraint de base de datos como red de seguridad.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cost_rates',
        verbose_name='Usuario',
    )
    # company viene de BaseModel — no duplicar FK

    start_date = models.DateField(verbose_name='Fecha inicio vigencia')
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha fin vigencia',
        help_text='NULL indica que la tarifa está actualmente vigente.',
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Tarifa por hora',
    )
    currency = models.CharField(
        max_length=3,
        default='COP',
        verbose_name='Moneda (ISO 4217)',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table = 'resource_cost_rates'
        verbose_name = 'Tarifa de Costo de Recurso'
        verbose_name_plural = 'Tarifas de Costo de Recursos'
        ordering = ['-start_date']
        indexes = [
            # Lookup principal: tarifa activa de un usuario en una empresa
            models.Index(fields=['user', 'company', 'start_date']),
            # Filtrar por fecha en consultas de costo histórico
            models.Index(fields=['company', 'start_date', 'end_date']),
        ]
        constraints = [
            # Solo puede existir una tarifa abierta (end_date IS NULL) por (user, company)
            # NOTA: PostgreSQL partial unique index — no expresable en Meta.constraints
            # estándar de Django. Se crea manualmente en la migración 0019.
            models.CheckConstraint(
                check=models.Q(start_date__lte=models.F('end_date'))
                    | models.Q(end_date__isnull=True),
                name='resource_cost_rate_start_before_end',
            ),
            models.CheckConstraint(
                check=models.Q(hourly_rate__gte=Decimal('0.00')),
                name='resource_cost_rate_non_negative',
            ),
        ]

    def __str__(self):
        end = self.end_date.isoformat() if self.end_date else 'presente'
        return (
            f'{self.user_id} — {self.hourly_rate} {self.currency}/h '
            f'({self.start_date} → {end})'
        )
```

**Partial unique index (must be added in migration 0019 — see section 7):**

```sql
-- Garantiza solo una tarifa abierta por (user, company)
CREATE UNIQUE INDEX resource_cost_rates_open_rate_unique
    ON resource_cost_rates (user_id, company_id)
    WHERE end_date IS NULL;
```

---

### 1.2 ProjectBudget

```python
class ProjectBudget(BaseModel):
    """
    Presupuesto planificado y aprobado de un proyecto.

    Relación OneToOne con Project: un proyecto tiene exactamente un presupuesto.
    Se crea explícitamente mediante la API — no se auto-crea en Project.save().

    Flujo de aprobación:
        DRAFT → PENDING_APPROVAL → APPROVED
        APPROVED → REVISION (si se modifica planned_total_budget)
    """
    project = models.OneToOneField(
        'Project',
        on_delete=models.CASCADE,
        related_name='budget',
        verbose_name='Proyecto',
    )

    # Componentes del presupuesto planificado
    planned_labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo mano de obra planificado',
    )
    planned_expense_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo gastos planificado',
    )
    planned_total_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Presupuesto total planificado',
        help_text=(
            'Puede incluir AIU y contingencia además de labor + expense. '
            'No se auto-calcula: el gestor lo define explícitamente.'
        ),
    )

    # Aprobación
    approved_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Presupuesto aprobado',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budgets',
        verbose_name='Aprobado por',
    )
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación',
    )

    # Alertas
    alert_threshold_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        validators=[
            MinValueValidator(Decimal('1.00')),
            MaxValueValidator(Decimal('100.00')),
        ],
        verbose_name='Umbral de alerta (%)',
        help_text='Porcentaje de ejecución del presupuesto que activa una alerta.',
    )

    currency = models.CharField(
        max_length=3,
        default='COP',
        verbose_name='Moneda (ISO 4217)',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table = 'project_budgets'
        verbose_name = 'Presupuesto de Proyecto'
        verbose_name_plural = 'Presupuestos de Proyectos'
        indexes = [
            # Consultas de alerta por empresa (job periódico futuro)
            models.Index(fields=['company', 'approved_budget']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(planned_labor_cost__gte=Decimal('0.00')),
                name='project_budget_labor_non_negative',
            ),
            models.CheckConstraint(
                check=models.Q(planned_expense_cost__gte=Decimal('0.00')),
                name='project_budget_expense_non_negative',
            ),
            models.CheckConstraint(
                check=models.Q(planned_total_budget__gte=Decimal('0.00')),
                name='project_budget_total_non_negative',
            ),
        ]

    def __str__(self):
        return f'Budget {self.project.codigo} — {self.planned_total_budget} {self.currency}'
```

---

### 1.3 ProjectExpense

```python
class ExpenseCategory(models.TextChoices):
    MATERIALS      = 'materials',     'Materiales'
    EQUIPMENT      = 'equipment',     'Equipos'
    TRAVEL         = 'travel',        'Viáticos y transporte'
    SUBCONTRACTOR  = 'subcontractor', 'Subcontratista'
    SOFTWARE       = 'software',      'Software / licencias'
    TRAINING       = 'training',      'Capacitación'
    OTHER          = 'other',         'Otro'


class ProjectExpense(BaseModel):
    """
    Gasto real incurrido en un proyecto.

    Los gastos pueden ser facturables (se incluyen en invoice_data)
    o no facturables (costos internos).

    El campo amount siempre es positivo. Para anular un gasto
    se usa soft-delete (activo=False de BaseModel) — nunca se
    registran importes negativos.
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Proyecto',
    )
    category = models.CharField(
        max_length=20,
        choices=ExpenseCategory.choices,
        verbose_name='Categoría',
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Descripción',
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto',
    )
    currency = models.CharField(
        max_length=3,
        default='COP',
        verbose_name='Moneda (ISO 4217)',
    )
    expense_date = models.DateField(verbose_name='Fecha del gasto')
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses_paid',
        verbose_name='Pagado por',
    )
    receipt_url = models.URLField(
        blank=True,
        verbose_name='URL comprobante',
        help_text='URL del recibo en S3 o servicio de almacenamiento.',
    )
    billable = models.BooleanField(
        default=True,
        verbose_name='Facturable',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table = 'project_expenses'
        verbose_name = 'Gasto de Proyecto'
        verbose_name_plural = 'Gastos de Proyecto'
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['project', 'expense_date']),
            models.Index(fields=['project', 'billable']),
            models.Index(fields=['company', 'category']),
            # Soporte para listados filtrados por fecha en empresa
            models.Index(fields=['company', 'expense_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=Decimal('0.00')),
                name='project_expense_amount_positive',
            ),
        ]

    def __str__(self):
        return f'{self.project.codigo} — {self.get_category_display()} {self.amount} {self.currency}'
```

---

### 1.4 BudgetSnapshot

```python
class BudgetSnapshot(BaseModel):
    """
    Foto diaria del estado financiero del proyecto.

    Se genera automáticamente (via tarea periódica Celery o llamada explícita)
    y sirve como serie temporal para gráficos de burn-rate y tendencias.

    unique_together garantiza una sola foto por proyecto por día.
    Si se necesita re-generar, se debe eliminar la existente primero.
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='budget_snapshots',
        verbose_name='Proyecto',
    )
    snapshot_date = models.DateField(verbose_name='Fecha del snapshot')

    # Costos reales al momento del snapshot
    labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo mano de obra real',
    )
    expense_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo gastos reales',
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo total real',
    )

    # Referencia presupuestal en el momento del snapshot
    planned_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Presupuesto planificado (en fecha)',
        help_text='Copia del planned_total_budget o approved_budget vigente al tomar el snapshot.',
    )

    # Variación
    variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Variación (planned - actual)',
        help_text='Positivo = bajo presupuesto. Negativo = sobre presupuesto.',
    )
    variance_percentage = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Variación (%)',
    )

    class Meta:
        db_table = 'budget_snapshots'
        verbose_name = 'Snapshot de Presupuesto'
        verbose_name_plural = 'Snapshots de Presupuesto'
        ordering = ['-snapshot_date']
        unique_together = [['project', 'snapshot_date']]
        indexes = [
            # Series temporales por empresa (reportes cruzados)
            models.Index(fields=['company', 'snapshot_date']),
            # Historial de un proyecto
            models.Index(fields=['project', 'snapshot_date']),
        ]

    def __str__(self):
        return f'Snapshot {self.project.codigo} @ {self.snapshot_date} — {self.total_cost}'
```

---

## 2. Service Function Signatures

All service functions live in `backend/apps/proyectos/budget_services.py`. Pattern follows `tarea_services.py`: static methods grouped by responsibility class, `@transaction.atomic` on writes, structured logging via `logger.info/warning/error`.

```python
"""
SaiSuite — Proyectos: BudgetService
TODA la lógica de presupuesto y costos va aquí. Las views solo orquestan.

Dependencias de modelos:
    Project, Task, Phase, TimesheetEntry  (apps.proyectos.models)
    ResourceCostRate, ProjectBudget,
    ProjectExpense, BudgetSnapshot        (apps.proyectos.models — Feature 7)
    settings.AUTH_USER_MODEL

Convención de moneda:
    Todos los cálculos usan Decimal, nunca float.
    La moneda retornada en cada respuesta es la del presupuesto del proyecto
    (ProjectBudget.currency). Si no hay presupuesto, se usa 'COP'.
    No se hace conversión de moneda entre registros de distinta moneda —
    se asume que todas las entradas de un proyecto usan la misma moneda.
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, F, Q, Avg
from django.utils import timezone

from apps.proyectos.models import (
    Project, Task, TimesheetEntry,
    ResourceCostRate, ProjectBudget, ProjectExpense, BudgetSnapshot,
)

logger = logging.getLogger(__name__)
```

---

### 2.1 Class: CostCalculationService

```python
class CostCalculationService:
    """
    Cálculo de costos reales: mano de obra (timesheets × tarifas) y gastos directos.
    """

    @staticmethod
    def get_labor_cost(
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Calcula el costo de mano de obra real del proyecto.

        Algoritmo:
            1. Obtener todos los TimesheetEntry del proyecto en el rango dado.
               JOIN: TimesheetEntry → tarea → proyecto (usar select_related).
            2. Para cada entrada (usuario, fecha, horas):
               a. Buscar la ResourceCostRate vigente en entry.fecha para
                  (entry.usuario_id, project.company_id).
               b. Si no hay tarifa → se registra warning y se contabiliza a 0.
               c. costo_entrada = entry.horas × rate.hourly_rate
            3. Sumar todos los costos_entrada.

        Nota de performance: la consulta principal usa
        TimesheetEntry.objects.filter(tarea__proyecto_id=project_id)
        con select_related('usuario', 'tarea__proyecto').
        La búsqueda de tarifas se hace en Python (no N+1) precargando todas
        las tarifas de la empresa una sola vez en un dict indexado por
        (user_id, start_date, end_date).

        Args:
            project_id: UUID del proyecto.
            start_date: Filtro inicio (inclusivo). None = desde el inicio.
            end_date: Filtro fin (inclusivo). None = hasta hoy.

        Returns:
            {
                "labor_cost": Decimal,
                "total_hours": Decimal,
                "currency": str,
                "entries_count": int,
                "entries_without_rate": int,  # advertencia si > 0
            }

        Raises:
            ValidationError: si project_id no existe o no pertenece a la company.
        """

    @staticmethod
    def get_expense_cost(
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        billable_only: bool = False,
    ) -> dict:
        """
        Suma los gastos directos registrados del proyecto.

        Algoritmo:
            1. Filtrar ProjectExpense: project_id, activo=True.
            2. Aplicar filtros opcionales: expense_date range, billable_only.
            3. Agregar con Sum('amount').

        Args:
            project_id: UUID del proyecto.
            start_date: Filtro fecha inicio (inclusivo).
            end_date: Filtro fecha fin (inclusivo).
            billable_only: Si True, solo gastos con billable=True.

        Returns:
            {
                "expense_cost": Decimal,
                "expenses_count": int,
                "currency": str,
            }
        """

    @staticmethod
    def get_total_cost(project_id: str) -> dict:
        """
        Costo total real = labor_cost + expense_cost (sin filtros de fecha).

        Llama internamente a get_labor_cost() y get_expense_cost().

        Returns:
            {
                "labor_cost": Decimal,
                "expense_cost": Decimal,
                "total_cost": Decimal,
                "currency": str,
                "total_hours": Decimal,
            }
        """

    @staticmethod
    def get_budget_variance(project_id: str) -> dict:
        """
        Calcula la variación respecto al presupuesto aprobado (o planificado si
        no hay aprobado).

        Algoritmo:
            1. Obtener ProjectBudget del proyecto. Si no existe →
               variance = None, status = 'no_budget'.
            2. reference_budget = approved_budget si no es None,
               si no planned_total_budget.
            3. actual_cost = get_total_cost(project_id)['total_cost']
            4. variance = reference_budget − actual_cost
            5. variance_pct = (actual_cost / reference_budget × 100) si reference > 0
            6. status:
               - 'under'   si actual_cost < reference_budget × alert_threshold (%)
               - 'warning' si actual_cost >= reference_budget × alert_threshold (%)
                           y actual_cost < reference_budget
               - 'on'      si actual_cost == reference_budget (tolerancia ±0.01)
               - 'over'    si actual_cost > reference_budget

        Returns:
            {
                "planned_budget": Decimal,
                "approved_budget": Decimal | None,
                "reference_budget": Decimal,
                "actual_cost": Decimal,
                "variance": Decimal,         # positivo = bajo presupuesto
                "variance_percentage": Decimal,
                "execution_percentage": Decimal,
                "status": "under" | "warning" | "on" | "over" | "no_budget",
                "currency": str,
            }
        """

    @staticmethod
    def get_cost_by_resource(project_id: str) -> list[dict]:
        """
        Desglosa el costo de mano de obra por recurso (usuario).

        Algoritmo:
            1. Obtener todos los TimesheetEntry del proyecto agrupados por usuario.
            2. Para cada usuario:
               a. Calcular horas totales (Sum).
               b. Calcular costo total usando la misma lógica de tarifa por fecha
                  que get_labor_cost (se procesa por entrada en Python).
               c. hourly_rate_avg = total_cost / total_hours si hours > 0.
               d. pct = user_cost / total_project_labor_cost × 100.
            3. Ordenar por total_cost DESC.

        Returns:
            [
                {
                    "user_id": str,
                    "user_name": str,
                    "user_email": str,
                    "hours": Decimal,
                    "hourly_rate_avg": Decimal,
                    "total_cost": Decimal,
                    "pct": Decimal,   # porcentaje del costo total de MO
                }
            ]
        """

    @staticmethod
    def get_cost_by_task(project_id: str) -> list[dict]:
        """
        Desglosa costos (MO + gastos) por tarea.

        Algoritmo:
            1. Obtener todas las Task del proyecto con prefetch de timesheets.
            2. Para cada tarea:
               a. hours = Sum de TimesheetEntry.horas para esa tarea.
               b. labor_cost = calcular con tarifas (mismo algoritmo que get_labor_cost).
               c. expense_cost = Sum de ProjectExpense donde… no aplica directamente
                  (los gastos son a nivel proyecto). expense_cost = 0 por tarea a menos
                  que se añada FK en ProjectExpense a Task en el futuro.
                  NOTA: en esta versión, expense_cost por tarea = 0.
                  Los gastos solo se desglosan a nivel proyecto.
               d. total_cost = labor_cost + expense_cost.
            3. Incluir solo tareas con hours > 0 o total_cost > 0.
            4. Ordenar por total_cost DESC.

        Returns:
            [
                {
                    "task_id": str,
                    "task_code": str,
                    "task_name": str,
                    "hours": Decimal,
                    "labor_cost": Decimal,
                    "expense_cost": Decimal,
                    "total_cost": Decimal,
                }
            ]
        """
```

---

### 2.2 Class: EVMService

```python
class EVMService:
    """
    Earned Value Management (EVM) según estándares PMI PMBOK.

    Glosario de métricas:
        BAC  — Budget at Completion: presupuesto total aprobado (o planificado).
        PV   — Planned Value: trabajo planificado × BAC.
        EV   — Earned Value: trabajo completado × BAC.
        AC   — Actual Cost: costo real incurrido.
        CV   — Cost Variance: EV − AC (negativo = sobre costo).
        SV   — Schedule Variance: EV − PV (negativo = retrasado).
        CPI  — Cost Performance Index: EV / AC.
        SPI  — Schedule Performance Index: EV / PV.
        EAC  — Estimate at Completion: BAC / CPI.
        ETC  — Estimate to Complete: EAC − AC.
        TCPI — To-Complete Performance Index: (BAC − EV) / (BAC − AC).
        VAC  — Variance at Completion: BAC − EAC.
    """

    @staticmethod
    def get_evm_metrics(project_id: str) -> dict:
        """
        Calcula todas las métricas EVM del proyecto.
        Ver sección 3 para el pseudocódigo detallado.

        Returns:
            {
                "BAC": Decimal,
                "PV": Decimal,
                "EV": Decimal,
                "AC": Decimal,
                "CV": Decimal,
                "SV": Decimal,
                "CPI": Decimal | None,
                "SPI": Decimal | None,
                "EAC": Decimal | None,
                "ETC": Decimal | None,
                "TCPI": Decimal | None,
                "VAC": Decimal | None,
                "schedule_health": "on_track" | "at_risk" | "behind",
                "cost_health": "on_track" | "at_risk" | "over_budget",
                "currency": str,
                "as_of_date": str,  # ISO date
                "warning": str | None,  # ej. "No budget defined"
            }
        """
```

---

### 2.3 Class: BudgetManagementService

```python
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

        Algoritmo:
            1. Verificar que el proyecto existe y pertenece a company_id.
            2. Intentar obtener ProjectBudget existente (get_or_create).
            3. Si existe y está aprobado (approved_budget is not None):
               - Permitir actualización solo de: alert_threshold_percentage, notes.
               - Cualquier cambio en montos requiere pasar approved_budget=None
                 (reset a borrador) — esto es una decisión de diseño explícita.
            4. Aplicar data al objeto y llamar full_clean() antes de save().
            5. Log de la operación.

        Args:
            project_id: UUID del proyecto.
            data: dict con campos del ProjectBudget a crear/actualizar.
            company_id: UUID de la empresa (validación multi-tenant).

        Returns:
            ProjectBudget

        Raises:
            ValidationError: proyecto no encontrado, no pertenece a la empresa,
                             o intento de modificar presupuesto aprobado.
        """

    @staticmethod
    @transaction.atomic
    def approve_budget(
        project_id: str,
        approved_budget: Decimal,
        approved_by_user_id: str,
    ) -> ProjectBudget:
        """
        Aprueba formalmente el presupuesto de un proyecto.

        Reglas:
            - El proyecto debe tener un ProjectBudget previo.
            - approved_budget debe ser > 0.
            - Se registran approved_by y approved_date (timezone.now()).
            - Solo roles company_admin pueden llamar este endpoint
              (validación en la view, no en el service).

        Args:
            project_id: UUID del proyecto.
            approved_budget: Monto aprobado (Decimal).
            approved_by_user_id: UUID del usuario aprobador.

        Returns:
            ProjectBudget actualizado.

        Raises:
            ValidationError: sin presupuesto previo o monto inválido.
        """

    @staticmethod
    def check_budget_alerts(project_id: str) -> list[dict]:
        """
        Evalúa si el proyecto ha superado umbrales de alerta de presupuesto.

        Algoritmo:
            1. Obtener varianza mediante get_budget_variance(project_id).
            2. Si status == 'no_budget' → retornar lista vacía.
            3. execution_pct = varianza['execution_percentage']
            4. Generar alertas:
               a. Si execution_pct >= 100 →
                  {type: 'danger', message: '...', current_pct, threshold: 100}
               b. Si execution_pct >= alert_threshold (de ProjectBudget) →
                  {type: 'warning', message: '...', current_pct, threshold}
               c. Si execution_pct >= alert_threshold − 10 (pre-alerta) →
                  {type: 'info', message: '...', current_pct, threshold}
            5. Cada alerta incluye breakdown de labor vs expense.

        Returns:
            [
                {
                    "type": "info" | "warning" | "danger",
                    "message": str,
                    "current_pct": Decimal,
                    "threshold": Decimal,
                    "labor_cost": Decimal,
                    "expense_cost": Decimal,
                    "total_cost": Decimal,
                    "reference_budget": Decimal,
                }
            ]
        """
```

---

### 2.4 Class: ExpenseService

```python
class ExpenseService:
    """
    CRUD de gastos directos del proyecto.
    """

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

        Validaciones:
            1. Proyecto existe y pertenece a company_id.
            2. amount > 0 (validado por modelo, pero reconfirmar aquí para
               dar mensaje de error amigable).
            3. expense_date <= date.today() (no se permiten gastos futuros).
            4. Si paid_by_user_id no es None, el usuario debe pertenecer
               a la misma empresa.

        Args:
            project_id: UUID del proyecto.
            data: dict con campos del gasto (category, description, amount,
                  currency, expense_date, receipt_url, billable, notes).
            paid_by_user_id: UUID del usuario que pagó (puede ser None).
            company_id: UUID de la empresa.

        Returns:
            ProjectExpense creado.
        """

    @staticmethod
    def list_expenses(
        project_id: str,
        filters: Optional[dict] = None,
    ) -> models.QuerySet:
        """
        Lista gastos de un proyecto con filtros opcionales.

        Filtros soportados (via `filters` dict):
            - category: str (ExpenseCategory value)
            - billable: bool
            - start_date / end_date: date (rango de expense_date)
            - paid_by_user_id: str (UUID del usuario)

        Returns:
            QuerySet de ProjectExpense con select_related('paid_by', 'project').
        """

    @staticmethod
    @transaction.atomic
    def update_expense(
        expense_id: str,
        data: dict,
        company_id: str,
    ) -> ProjectExpense:
        """
        Actualiza campos de un gasto existente.

        Restricciones:
            - No se puede editar un gasto de un proyecto cerrado.
            - Campos inmutables: project, company.

        Raises:
            ValidationError: gasto no encontrado, no pertenece a la empresa,
                             o proyecto cerrado.
        """

    @staticmethod
    @transaction.atomic
    def delete_expense(
        expense_id: str,
        company_id: str,
    ) -> None:
        """
        Soft-delete de un gasto (activo=False).

        No se puede eliminar gasto de proyecto cerrado.

        Raises:
            ValidationError: gasto no encontrado, no pertenece a la empresa,
                             o proyecto cerrado.
        """
```

---

### 2.5 Class: ResourceCostRateService

```python
class ResourceCostRateService:
    """
    Gestión de tarifas horarias de recursos.
    """

    @staticmethod
    def get_active_rate(
        user_id: str,
        company_id: str,
        on_date: date,
    ) -> Optional[ResourceCostRate]:
        """
        Obtiene la tarifa vigente para un usuario en una fecha dada.

        Algoritmo:
            SELECT * FROM resource_cost_rates
            WHERE user_id = user_id
              AND company_id = company_id
              AND start_date <= on_date
              AND (end_date >= on_date OR end_date IS NULL)
              AND activo = TRUE
            ORDER BY start_date DESC
            LIMIT 1

        Returns:
            ResourceCostRate o None si no hay tarifa registrada.
        """

    @staticmethod
    @transaction.atomic
    def create_rate(
        user_id: str,
        data: dict,
        company_id: str,
    ) -> ResourceCostRate:
        """
        Crea una nueva tarifa horaria para un recurso.

        Validaciones de solapamiento (antes de persistir):
            1. Si data['end_date'] is None:
               - No debe existir otro registro con end_date=NULL para
                 (user_id, company_id).
               - No debe existir registro con start_date >= data['start_date']
                 y end_date IS NULL o end_date >= data['start_date'].
            2. Si data['end_date'] is not None:
               - No debe existir registro con rango que se solape:
                 NOT (end_date < data['start_date'] OR start_date > data['end_date'])
                 — esto equivale a la condición de solapamiento estándar.
            3. data['start_date'] <= data['end_date'] si ambos están definidos.

        Args:
            user_id: UUID del usuario al que aplica la tarifa.
            data: dict con start_date, end_date, hourly_rate, currency, notes.
            company_id: UUID de la empresa.

        Returns:
            ResourceCostRate creada.

        Raises:
            ValidationError: solapamiento de fechas, usuario no encontrado,
                             o datos inválidos.
        """

    @staticmethod
    def list_rates(
        company_id: str,
        user_id: Optional[str] = None,
        active_only: bool = False,
    ) -> models.QuerySet:
        """
        Lista tarifas de la empresa con filtros opcionales.

        Args:
            company_id: UUID de la empresa (obligatorio, multi-tenant).
            user_id: Filtrar por usuario específico.
            active_only: Si True, solo tarifas con end_date=NULL.

        Returns:
            QuerySet con select_related('user').
        """
```

---

### 2.6 Class: InvoicingService

```python
class InvoicingService:
    """
    Recopila datos para facturación al cliente.
    """

    @staticmethod
    def get_invoice_data(project_id: str) -> dict:
        """
        Consolida las horas y gastos facturables para generar una factura.

        Algoritmo:
            1. labor = get_labor_cost(project_id) — todas las horas sin filtro.
            2. expenses = get_expense_cost(project_id, billable_only=True).
            3. billable_expenses = list_expenses(project_id, {'billable': True}).
            4. total_billable = labor['labor_cost'] + expenses['expense_cost'].

        Returns:
            {
                "labor_hours": Decimal,
                "labor_cost": Decimal,
                "billable_expenses": list[dict],  # categoría, descripción, monto
                "expense_cost": Decimal,
                "total_billable": Decimal,
                "currency": str,
                "as_of_date": str,  # ISO date de hoy
            }
        """
```

---

### 2.7 Class: SnapshotService

```python
class SnapshotService:
    """
    Generación y consulta de snapshots financieros del proyecto.
    """

    @staticmethod
    @transaction.atomic
    def create_budget_snapshot(project_id: str) -> BudgetSnapshot:
        """
        Genera o actualiza el snapshot financiero del día de hoy.

        Algoritmo:
            1. today = date.today()
            2. total = get_total_cost(project_id)
            3. budget = ProjectBudget para el proyecto (puede no existir).
            4. planned_budget = approved_budget o planned_total_budget o 0.
            5. variance = planned_budget − total['total_cost']
            6. variance_pct:
               - Si planned_budget > 0: (total_cost / planned_budget × 100)
               - Si not: 0
            7. BudgetSnapshot.objects.update_or_create(
                   project_id=project_id, snapshot_date=today,
                   defaults={labor_cost, expense_cost, total_cost,
                             planned_budget, variance, variance_pct}
               )
            8. Log de creación.

        Returns:
            BudgetSnapshot (creado o actualizado).

        Raises:
            ValidationError: proyecto no encontrado.
        """
```

---

## 3. EVM Algorithm — Detailed Pseudocode

### 3.1 Conceptual Mapping to Existing Data

| EVM Concept | Source in SaiSuite |
|---|---|
| BAC (Budget at Completion) | `ProjectBudget.approved_budget` or `planned_total_budget` |
| % Complete (physical) | Weighted avg of `Task.porcentaje_completado` × `Task.horas_estimadas` |
| PV (Planned Value) | BAC × % work scheduled to be done by today |
| EV (Earned Value) | BAC × % work actually completed today |
| AC (Actual Cost) | `get_total_cost(project_id)['total_cost']` |

### 3.2 Full Pseudocode for `EVMService.get_evm_metrics`

```
FUNCTION get_evm_metrics(project_id) -> dict:

    # --- Step 1: Load project and budget ---
    project = Project.objects.select_related('budget').get(id=project_id)

    IF project has no budget:
        RETURN {all metrics: None, warning: "No budget defined for this project"}

    BAC = project.budget.approved_budget
          IF NOT NULL
          ELSE project.budget.planned_total_budget

    IF BAC <= 0:
        RETURN {all metrics: None, warning: "Budget is zero, EVM cannot be calculated"}

    currency = project.budget.currency
    today = date.today()
    project_start = project.fecha_inicio_planificada
    project_end   = project.fecha_fin_planificada

    # --- Step 2: Calculate PV (Planned Value) ---
    # PV = BAC × (elapsed planned duration / total planned duration)
    # This is the "time-phased" budget: how much work was SUPPOSED to be done by today.

    total_planned_days = (project_end - project_start).days
    IF total_planned_days <= 0:
        time_pct = Decimal('1.00')   # degenerate case: single-day project
    ELSE:
        elapsed_days = (today - project_start).days
        elapsed_days = CLAMP(elapsed_days, 0, total_planned_days)
        time_pct = Decimal(elapsed_days) / Decimal(total_planned_days)

    PV = (BAC × time_pct).quantize(Decimal('0.01'))

    # NOTE: A more accurate PV would use task-level baseline schedules.
    # The time-linear approximation is used here because Feature 7 does not
    # yet have task-level cost budgets. When Feature 6 baselines are available,
    # PV should be recalculated as:
    #   SUM over all tasks of (task_planned_cost × min(1, elapsed/task_duration))

    # --- Step 3: Calculate EV (Earned Value) ---
    # EV = BAC × weighted_completion_percentage
    # Weighted by horas_estimadas — tasks with more estimated hours contribute more.

    tasks = Task.objects.filter(
        proyecto_id=project_id,
        activo=True,
    ).exclude(estado='cancelled')

    total_estimated_hours = SUM(task.horas_estimadas for task in tasks)
                            or 0

    IF total_estimated_hours <= 0:
        # Fallback: simple average of porcentaje_completado
        IF tasks.count() > 0:
            avg_completion = SUM(task.porcentaje_completado for task in tasks)
                             / tasks.count()
        ELSE:
            avg_completion = Decimal('0')
        weighted_completion_pct = avg_completion / Decimal('100')
    ELSE:
        weighted_sum = SUM(
            task.horas_estimadas × task.porcentaje_completado
            FOR task IN tasks
        )
        weighted_completion_pct = (weighted_sum / total_estimated_hours) / Decimal('100')

    EV = (BAC × weighted_completion_pct).quantize(Decimal('0.01'))

    # --- Step 4: Calculate AC (Actual Cost) ---
    AC = CostCalculationService.get_total_cost(project_id)['total_cost']

    # --- Step 5: Calculate derived metrics ---
    CV = EV - AC                    # Cost Variance     (negative = over cost)
    SV = EV - PV                    # Schedule Variance (negative = behind schedule)

    CPI  = (EV / AC).quantize('0.0001')  IF AC > 0  ELSE None
    SPI  = (EV / PV).quantize('0.0001')  IF PV > 0  ELSE None

    # Estimate at Completion (assuming current efficiency continues)
    EAC  = (BAC / CPI).quantize('0.01')  IF CPI and CPI > 0  ELSE None

    # Estimate to Complete
    ETC  = (EAC - AC).quantize('0.01')   IF EAC is not None  ELSE None

    # To-Complete Performance Index (efficiency needed on remaining work to meet BAC)
    remaining_budget = BAC - EV
    budget_spent     = BAC - AC
    TCPI = (remaining_budget / budget_spent).quantize('0.0001')
           IF budget_spent > 0
           ELSE None

    # Variance at Completion
    VAC = (BAC - EAC).quantize('0.01')   IF EAC is not None  ELSE None

    # --- Step 6: Health indicators ---
    IF CPI is None:
        cost_health = 'unknown'
    ELIF CPI >= Decimal('0.95'):
        cost_health = 'on_track'
    ELIF CPI >= Decimal('0.80'):
        cost_health = 'at_risk'
    ELSE:
        cost_health = 'over_budget'

    IF SPI is None:
        schedule_health = 'unknown'
    ELIF SPI >= Decimal('0.95'):
        schedule_health = 'on_track'
    ELIF SPI >= Decimal('0.80'):
        schedule_health = 'at_risk'
    ELSE:
        schedule_health = 'behind'

    # --- Step 7: Log and return ---
    logger.info('EVM metrics calculated', extra={
        'project_id': project_id,
        'BAC': str(BAC), 'PV': str(PV), 'EV': str(EV), 'AC': str(AC),
        'CPI': str(CPI), 'SPI': str(SPI),
    })

    RETURN {
        "BAC": BAC, "PV": PV, "EV": EV, "AC": AC,
        "CV": CV, "SV": SV,
        "CPI": CPI, "SPI": SPI,
        "EAC": EAC, "ETC": ETC, "TCPI": TCPI, "VAC": VAC,
        "schedule_health": schedule_health,
        "cost_health": cost_health,
        "weighted_completion_pct": (weighted_completion_pct * 100).quantize('0.01'),
        "currency": currency,
        "as_of_date": today.isoformat(),
        "warning": None,
    }
```

### 3.3 Edge Cases Handled in EVM

| Condition | Behavior |
|---|---|
| No `ProjectBudget` | All metrics = None, warning message returned |
| `BAC = 0` | All metrics = None, warning returned |
| `AC = 0` (no timesheets yet) | CPI = None (division by zero avoided), EAC = None |
| `PV = 0` (project not started) | SPI = None |
| All tasks cancelled | `weighted_completion_pct = 0`, EV = 0 |
| Project past end date | `time_pct` clamped to 1.0, PV = BAC |
| Tasks with no `horas_estimadas` | Fallback to simple average of `porcentaje_completado` |
| `CPI < 0` (EV=0 but AC>0) | EAC = None (mathematically valid but misleading early-stage) |

---

## 4. Endpoint Table

All endpoints are prefixed with `/api/v1/projects/` (mounted in `urls.py` alongside existing routes). Authentication: JWT required on all endpoints. Permissions follow existing pattern: `IsAuthenticated` + company scoping in the service layer.

### 4.1 Budget Endpoints

| Method | URL | Permission | Description |
|---|---|---|---|
| GET | `{id}/budget/` | Authenticated, company member | Retrieve project budget |
| POST | `{id}/budget/` | `company_admin` | Create or update budget |
| POST | `{id}/budget/approve/` | `company_admin` | Approve budget with formal amount |

**GET `{id}/budget/` — Response 200:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "planned_labor_cost": "5000000.00",
  "planned_expense_cost": "1200000.00",
  "planned_total_budget": "7000000.00",
  "approved_budget": "6800000.00",
  "approved_by": {"id": "uuid", "full_name": "...", "email": "..."},
  "approved_date": "2026-03-01T10:00:00Z",
  "alert_threshold_percentage": "80.00",
  "currency": "COP",
  "notes": "",
  "created_at": "...",
  "updated_at": "..."
}
```

**POST `{id}/budget/` — Request body:**
```json
{
  "planned_labor_cost": "5000000.00",
  "planned_expense_cost": "1200000.00",
  "planned_total_budget": "7000000.00",
  "alert_threshold_percentage": "80.00",
  "currency": "COP",
  "notes": ""
}
```

**POST `{id}/budget/approve/` — Request body:**
```json
{
  "approved_budget": "6800000.00"
}
```

---

### 4.2 Cost Calculation Endpoints

All are `GET`, read-only, no request body. Query params where noted.

| Method | URL | Query Params | Description |
|---|---|---|---|
| GET | `{id}/labor-cost/` | `start_date`, `end_date` (ISO date) | Labor cost in range |
| GET | `{id}/expense-cost/` | `start_date`, `end_date`, `billable_only` (bool) | Expense cost |
| GET | `{id}/total-cost/` | — | Total labor + expenses |
| GET | `{id}/variance/` | — | Budget vs actual variance |
| GET | `{id}/cost-by-resource/` | — | Cost breakdown per user |
| GET | `{id}/cost-by-task/` | — | Cost breakdown per task |
| GET | `{id}/evm-metrics/` | — | Full EVM metrics |
| GET | `{id}/alerts/` | — | Active budget alerts |
| GET | `{id}/invoice-data/` | — | Billable summary for invoicing |

**GET `{id}/evm-metrics/` — Response 200:**
```json
{
  "BAC": "6800000.00",
  "PV":  "3400000.00",
  "EV":  "3100000.00",
  "AC":  "3250000.00",
  "CV":  "-150000.00",
  "SV":  "-300000.00",
  "CPI": "0.9538",
  "SPI": "0.9118",
  "EAC": "7128000.00",
  "ETC": "3878000.00",
  "TCPI": "1.0845",
  "VAC": "-328000.00",
  "schedule_health": "at_risk",
  "cost_health": "at_risk",
  "weighted_completion_pct": "45.59",
  "currency": "COP",
  "as_of_date": "2026-03-27",
  "warning": null
}
```

**GET `{id}/alerts/` — Response 200:**
```json
[
  {
    "type": "warning",
    "message": "El proyecto ha ejecutado el 85% del presupuesto aprobado.",
    "current_pct": "85.00",
    "threshold": "80.00",
    "labor_cost": "4500000.00",
    "expense_cost": "800000.00",
    "total_cost": "5300000.00",
    "reference_budget": "6800000.00"
  }
]
```

---

### 4.3 Snapshot Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `{id}/snapshots/` | List historical snapshots (paginated) |
| POST | `{id}/create-snapshot/` | Force create today's snapshot |

---

### 4.4 Expense Endpoints

| Method | URL | Query Params | Description |
|---|---|---|---|
| GET | `expenses/` | `project`, `category`, `start_date`, `end_date`, `billable` | List expenses |
| POST | `expenses/` | — | Create expense |
| GET | `expenses/{id}/` | — | Retrieve expense |
| PATCH | `expenses/{id}/` | — | Update expense |
| DELETE | `expenses/{id}/` | — | Soft-delete expense |

**POST `expenses/` — Request body:**
```json
{
  "project": "uuid",
  "category": "travel",
  "description": "Viáticos visita cliente Medellín",
  "amount": "450000.00",
  "currency": "COP",
  "expense_date": "2026-03-20",
  "paid_by": "uuid",
  "receipt_url": "https://s3.amazonaws.com/...",
  "billable": true,
  "notes": ""
}
```

---

### 4.5 Cost Rate Endpoints

| Method | URL | Query Params | Description |
|---|---|---|---|
| GET | `cost-rates/` | `user`, `active` (bool) | List cost rates |
| POST | `cost-rates/` | — | Create cost rate |
| GET | `cost-rates/{id}/` | — | Retrieve rate |
| PATCH | `cost-rates/{id}/` | — | Update rate |
| DELETE | `cost-rates/{id}/` | — | Soft-delete rate |

**POST `cost-rates/` — Request body:**
```json
{
  "user": "uuid",
  "start_date": "2026-01-01",
  "end_date": null,
  "hourly_rate": "85000.00",
  "currency": "COP",
  "notes": "Tarifa vigente 2026"
}
```

---

### 4.6 URL Registration in `urls.py`

The following paths must be added to the existing `urlpatterns` list in `apps/proyectos/urls.py`, importing views from `budget_views.py`:

```python
from apps.proyectos.budget_views import (
    ProjectBudgetView,
    ApproveBudgetView,
    LaborCostView,
    ExpenseCostView,
    TotalCostView,
    BudgetVarianceView,
    CostByResourceView,
    CostByTaskView,
    EVMMetricsView,
    BudgetAlertsView,
    InvoiceDataView,
    BudgetSnapshotListView,
    CreateBudgetSnapshotView,
    ProjectExpenseViewSet,
    ResourceCostRateViewSet,
)

# Budget router
budget_router = SimpleRouter()
budget_router.register(r'expenses', ProjectExpenseViewSet, basename='expense')
budget_router.register(r'cost-rates', ResourceCostRateViewSet, basename='cost-rate')

# Add to urlpatterns:
path('', include(budget_router.urls)),
path('<uuid:project_pk>/budget/', ProjectBudgetView.as_view(), name='project-budget'),
path('<uuid:project_pk>/budget/approve/', ApproveBudgetView.as_view(), name='project-budget-approve'),
path('<uuid:project_pk>/labor-cost/', LaborCostView.as_view(), name='project-labor-cost'),
path('<uuid:project_pk>/expense-cost/', ExpenseCostView.as_view(), name='project-expense-cost'),
path('<uuid:project_pk>/total-cost/', TotalCostView.as_view(), name='project-total-cost'),
path('<uuid:project_pk>/variance/', BudgetVarianceView.as_view(), name='project-budget-variance'),
path('<uuid:project_pk>/cost-by-resource/', CostByResourceView.as_view(), name='project-cost-by-resource'),
path('<uuid:project_pk>/cost-by-task/', CostByTaskView.as_view(), name='project-cost-by-task'),
path('<uuid:project_pk>/evm-metrics/', EVMMetricsView.as_view(), name='project-evm-metrics'),
path('<uuid:project_pk>/alerts/', BudgetAlertsView.as_view(), name='project-budget-alerts'),
path('<uuid:project_pk>/invoice-data/', InvoiceDataView.as_view(), name='project-invoice-data'),
path('<uuid:project_pk>/snapshots/', BudgetSnapshotListView.as_view(), name='project-budget-snapshots'),
path('<uuid:project_pk>/create-snapshot/', CreateBudgetSnapshotView.as_view(), name='project-create-snapshot'),
```

---

## 5. Performance Strategy

### 5.1 Critical Queries and ORM Optimization

#### get_labor_cost — Main Bottleneck

This is the most expensive operation. The naive approach (one query per timesheet entry to find the matching rate) produces N+1 queries.

**Optimized approach:**

```python
# Step 1: One query — all timesheets for the project
timesheets = (
    TimesheetEntry.objects
    .filter(tarea__proyecto_id=project_id, activo=True)
    .select_related('usuario', 'tarea')
    .values('usuario_id', 'fecha', 'horas')
)

# Step 2: One query — all cost rates for the company (preload into memory dict)
# Only needed for users who appear in timesheets
user_ids = {t['usuario_id'] for t in timesheets}
rates = (
    ResourceCostRate.objects
    .filter(company_id=company_id, user_id__in=user_ids, activo=True)
    .order_by('user_id', 'start_date')
    .values('user_id', 'start_date', 'end_date', 'hourly_rate')
)

# Build in-memory index: {user_id: [(start, end, rate), ...]}
rate_index = defaultdict(list)
for r in rates:
    rate_index[r['user_id']].append((r['start_date'], r['end_date'], r['hourly_rate']))

# Step 3: Calculate in Python — O(n × k) where k = avg rates per user (usually 1-3)
```

This pattern reduces database roundtrips from O(n) to O(2) regardless of timesheet volume.

#### get_cost_by_task

Use `prefetch_related` on timesheets when loading tasks:

```python
tasks = (
    Task.objects
    .filter(proyecto_id=project_id, activo=True)
    .exclude(estado='cancelled')
    .prefetch_related(
        models.Prefetch(
            'timesheets',
            queryset=TimesheetEntry.objects.filter(activo=True)
                .values('usuario_id', 'fecha', 'horas'),
        )
    )
)
```

#### BudgetSnapshot List

Since snapshots are queried as a time series, they must be fetched with:
```python
BudgetSnapshot.objects.filter(project_id=project_id).order_by('snapshot_date')
```
The composite index on `(project, snapshot_date)` covers this query.

---

### 5.2 Caching Strategy

| Endpoint | Cache TTL | Cache Key | Invalidation |
|---|---|---|---|
| `evm-metrics/` | 5 minutes | `evm:{project_id}` | On new timesheet, new expense, budget change |
| `total-cost/` | 5 minutes | `total_cost:{project_id}` | On new timesheet, new expense |
| `cost-by-resource/` | 5 minutes | `cost_by_resource:{project_id}` | On new timesheet |
| `snapshots/` | 1 hour | `snapshots:{project_id}` | On `create-snapshot` |
| `alerts/` | 10 minutes | `alerts:{project_id}` | On cost change or budget change |

Use Django's cache framework (`django.core.cache.cache`). Cache invalidation is done in the service layer using `cache.delete(key)` at the end of write operations.

**Implementation pattern (in budget_services.py):**
```python
from django.core.cache import cache

CACHE_TTL_SHORT = 300   # 5 min
CACHE_TTL_LONG  = 3600  # 1 hour

def _invalidate_cost_caches(project_id: str) -> None:
    """Call this after any write that affects costs."""
    for key in ['evm', 'total_cost', 'cost_by_resource', 'alerts']:
        cache.delete(f'{key}:{project_id}')
```

---

### 5.3 Database Indexes Beyond Django Defaults

The following indexes are NOT created automatically by Django and must be added in migration `0019`:

```sql
-- 1. Tarifa activa (end_date IS NULL) — unique partial index (see section 1.1)
CREATE UNIQUE INDEX resource_cost_rates_open_rate_unique
    ON resource_cost_rates (user_id, company_id)
    WHERE end_date IS NULL;

-- 2. Lookup tarifa vigente en fecha (usado en get_labor_cost)
CREATE INDEX resource_cost_rates_active_lookup
    ON resource_cost_rates (user_id, company_id, start_date)
    WHERE activo = TRUE;

-- 3. Gastos facturables por proyecto (usado en get_expense_cost con billable_only=True)
CREATE INDEX project_expenses_billable
    ON project_expenses (project_id, billable)
    WHERE activo = TRUE;

-- 4. Snapshots ordenados por fecha (series temporales)
CREATE INDEX budget_snapshots_project_date
    ON budget_snapshots (project_id, snapshot_date DESC);

-- 5. Timesheets por proyecto (JOIN en get_labor_cost — complementa índice existente)
-- NOTA: ya existe idx en (tarea, validado) y (usuario, fecha).
-- Agregar índice en (tarea.proyecto_id via task) no es directo — se cubre
-- con select_related y el índice de FK en tarea.proyecto_id (creado por Django).
-- No se necesita índice adicional.
```

---

### 5.4 Query Count Targets

| Endpoint | Target DB queries | Strategy |
|---|---|---|
| `total-cost/` | 3 (project, timesheets, rates) | Preload rates dict |
| `evm-metrics/` | 4 (project+budget, timesheets, rates, tasks) | select_related + preload |
| `cost-by-resource/` | 3 | Same as total-cost + user names |
| `cost-by-task/` | 3 (project, tasks+timesheets, rates) | prefetch_related |
| `snapshots/` | 1 | Direct filter + index |
| `invoice-data/` | 4 | Reuse get_labor_cost + get_expense_cost |

---

## 6. Testing Strategy

All tests go in `backend/apps/proyectos/tests/test_budget_services.py`. Pattern follows existing test files in the app. Coverage target: 85% for `budget_services.py`.

### 6.1 Test Fixtures

```python
# Fixtures needed for all budget tests
@pytest.fixture
def company(db):
    return Company.objects.create(name='Test Co')

@pytest.fixture
def project(company):
    return Project.objects.create(
        codigo='PRY-001', nombre='Test Project',
        tipo='services', estado='in_progress',
        gerente=user, company=company,
        fecha_inicio_planificada=date(2026, 1, 1),
        fecha_fin_planificada=date(2026, 12, 31),
    )

@pytest.fixture
def user_with_rate(company, project):
    """User with an active cost rate of 100,000 COP/h."""
    user = get_user_model().objects.create(email='dev@test.co', company=company)
    ResourceCostRate.objects.create(
        user=user, company=company,
        start_date=date(2026, 1, 1), end_date=None,
        hourly_rate=Decimal('100000.00'), currency='COP',
    )
    return user
```

---

### 6.2 CostCalculationService Tests

| Test | Scenario | Expected |
|---|---|---|
| `test_labor_cost_no_timesheets` | Project with no TimesheetEntry | `labor_cost=0`, `entries_count=0` |
| `test_labor_cost_no_rate` | Timesheets exist but no ResourceCostRate | `labor_cost=0`, `entries_without_rate=N`, warning logged |
| `test_labor_cost_rate_expired` | TimesheetEntry date after `end_date` of only rate | Rate not applied, `entries_without_rate=1` |
| `test_labor_cost_multiple_rates` | User had rate change mid-project | Correct rate applied per entry date |
| `test_labor_cost_date_filter` | Entries outside `start_date/end_date` filter | Only entries in range counted |
| `test_expense_cost_billable_only` | Mix of billable and non-billable expenses | Only billable counted when `billable_only=True` |
| `test_expense_cost_no_expenses` | No expenses registered | `expense_cost=0` |
| `test_total_cost_sum` | Both labor and expenses | `total_cost = labor + expense` |

---

### 6.3 BudgetManagementService Tests

| Test | Scenario | Expected |
|---|---|---|
| `test_set_budget_creates_new` | No prior budget | Budget created with correct fields |
| `test_set_budget_updates_existing` | Budget already exists | Updated, not duplicated |
| `test_approve_budget_no_prior_budget` | No ProjectBudget | `ValidationError` |
| `test_approve_budget_zero_amount` | `approved_budget=0` | `ValidationError` |
| `test_approve_budget_success` | Valid budget, valid approver | `approved_budget` set, `approved_date` set |
| `test_check_alerts_no_budget` | No budget | Empty list returned |
| `test_check_alerts_under_threshold` | Execution at 50%, threshold at 80% | Empty list |
| `test_check_alerts_warning` | Execution at 85%, threshold at 80% | One warning alert |
| `test_check_alerts_danger` | Execution at 102% | One danger alert (over budget) |
| `test_variance_no_budget` | No budget | `status='no_budget'` |
| `test_variance_under` | Actual < planned | `status='under'`, `variance > 0` |
| `test_variance_over` | Actual > planned | `status='over'`, `variance < 0` |

---

### 6.4 EVMService Tests

| Test | Scenario | Expected |
|---|---|---|
| `test_evm_no_budget` | No ProjectBudget | All metrics None, warning message |
| `test_evm_zero_budget` | Budget = 0 | All metrics None, warning message |
| `test_evm_no_timesheets_no_progress` | BAC set, no AC, no EV | AC=0, EV=0, CPI=None, SPI=Some |
| `test_evm_on_track` | EV ≈ PV, AC ≈ EV | CPI ≈ 1.0, SPI ≈ 1.0, `cost_health='on_track'` |
| `test_evm_over_budget` | AC > EV significantly | `CPI < 0.80`, `cost_health='over_budget'` |
| `test_evm_behind_schedule` | SPI < 0.80 | `schedule_health='behind'` |
| `test_evm_all_tasks_cancelled` | All tasks cancelled | `EV=0`, `weighted_completion_pct=0` |
| `test_evm_project_past_end_date` | `fecha_fin_planificada` in past | `PV = BAC`, `time_pct = 1.0` |
| `test_evm_no_estimated_hours` | Tasks with `horas_estimadas=0` | Fallback to simple avg, no ZeroDivisionError |
| `test_evm_cpi_eac_consistency` | EAC = BAC / CPI | Numeric consistency within 0.01 tolerance |

---

### 6.5 ResourceCostRateService Tests

| Test | Scenario | Expected |
|---|---|---|
| `test_get_active_rate_found` | Rate covering the date | Correct rate returned |
| `test_get_active_rate_not_found` | No rate for the date | `None` returned |
| `test_get_active_rate_between_ranges` | Date between two rates | No rate returned (gap) |
| `test_create_rate_overlap_open` | Two open rates (end_date=None) | `ValidationError` |
| `test_create_rate_overlap_date_range` | Ranges overlap | `ValidationError` |
| `test_create_rate_adjacent_no_overlap` | Rate ends 2026-03-31, new starts 2026-04-01 | Created successfully |
| `test_create_rate_start_after_end` | `start_date > end_date` | `ValidationError` |

---

### 6.6 ExpenseService Tests

| Test | Scenario | Expected |
|---|---|---|
| `test_create_expense_future_date` | `expense_date` = tomorrow | `ValidationError` |
| `test_create_expense_negative_amount` | `amount = -100` | `ValidationError` (model constraint) |
| `test_delete_expense_closed_project` | Project `estado='closed'` | `ValidationError` |
| `test_update_expense_closed_project` | Same | `ValidationError` |
| `test_create_expense_wrong_company` | `paid_by` from different company | `ValidationError` |

---

### 6.7 SnapshotService Tests

| Test | Scenario | Expected |
|---|---|---|
| `test_create_snapshot_no_budget` | No budget → `planned_budget=0` | Snapshot created with `variance=0` |
| `test_create_snapshot_idempotent` | Called twice in same day | Second call updates existing (no duplicate) |
| `test_snapshot_variance_calculation` | Budget=1M, cost=800K | `variance=200000`, `variance_pct=80.00` |
| `test_snapshot_over_budget` | cost > budget | `variance < 0`, `variance_pct > 100` |

---

## 7. Migration Notes

### 7.1 Migration Order

Feature 7 requires two migrations. They must be applied in order:

```
0018_feature_7_budget_models.py   — model tables
0019_feature_7_budget_indexes.py  — partial and custom indexes
```

Migration `0018` depends on `0017_feature_6_scheduling_indexes`.

### 7.2 Migration 0018 — Model Tables

Creates 4 new tables:
- `resource_cost_rates`
- `project_budgets`
- `project_expenses`
- `budget_snapshots`

Includes all FKs, check constraints, and standard Django-generated indexes.

**No data migrations are required** — these are new tables with no pre-existing data.

```python
# backend/apps/proyectos/migrations/0018_feature_7_budget_models.py
# Generated by: python manage.py makemigrations proyectos --name feature_7_budget_models
# Dependencies: [('proyectos', '0017_feature_6_scheduling_indexes')]
#
# Operations: CreateModel × 4 (ResourceCostRate, ProjectBudget, ProjectExpense, BudgetSnapshot)
# All with their CheckConstraints as defined in models above.
```

### 7.3 Migration 0019 — Custom Indexes

This migration adds database-level objects that cannot be expressed via `Meta.constraints` or `Meta.indexes` in Django:

```python
# backend/apps/proyectos/migrations/0019_feature_7_budget_indexes.py

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0018_feature_7_budget_models'),
    ]

    operations = [
        # Partial unique index: only one open rate per (user, company)
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX resource_cost_rates_open_rate_unique
                    ON resource_cost_rates (user_id, company_id)
                    WHERE end_date IS NULL AND activo = TRUE;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS resource_cost_rates_open_rate_unique;
            """,
        ),

        # Partial index for active rate lookup by date
        migrations.RunSQL(
            sql="""
                CREATE INDEX resource_cost_rates_active_lookup
                    ON resource_cost_rates (user_id, company_id, start_date)
                    WHERE activo = TRUE;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS resource_cost_rates_active_lookup;
            """,
        ),

        # Partial index for billable expense lookups
        migrations.RunSQL(
            sql="""
                CREATE INDEX project_expenses_billable
                    ON project_expenses (project_id, billable)
                    WHERE activo = TRUE;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS project_expenses_billable;
            """,
        ),

        # Descending snapshot index for time-series queries
        migrations.RunSQL(
            sql="""
                CREATE INDEX budget_snapshots_project_date_desc
                    ON budget_snapshots (project_id, snapshot_date DESC);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS budget_snapshots_project_date_desc;
            """,
        ),
    ]
```

### 7.4 Rollback Plan

Both migrations are fully reversible:
- `0019` uses `RunSQL` with `reverse_sql` that drops all custom indexes.
- `0018` uses standard `CreateModel` operations — Django auto-generates reverse `DeleteModel`.

To rollback: `python manage.py migrate proyectos 0017`

### 7.5 Production Deployment Checklist

- [ ] Run `python manage.py migrate` — no downtime required (new tables, no ALTER on existing tables).
- [ ] Verify `resource_cost_rates_open_rate_unique` index created: `\d resource_cost_rates` in psql.
- [ ] No seed data required — rates and budgets are created by users via the API.
- [ ] After deploy: smoke test `GET /api/v1/projects/{id}/total-cost/` on a project with existing timesheets.
- [ ] Confirm `entries_without_rate` counter in response — if > 0, inform users to register cost rates.

---

## Appendix: File Creation Order (per CLAUDE.md Section 5)

```
1. models.py       — Add 4 new model classes (ResourceCostRate, ProjectBudget,
                     ProjectExpense, BudgetSnapshot) + ExpenseCategory TextChoices
2. Migration 0018  — python manage.py makemigrations proyectos --name feature_7_budget_models
3. Migration 0019  — Create manually with RunSQL for partial indexes
4. budget_serializers.py  — One serializer pair per model (list + detail)
5. budget_services.py     — All service classes defined in section 2
6. budget_views.py        — Views orchestrating service calls, no business logic
7. urls.py update  — Register budget_router + individual paths
8. tests/test_budget_services.py  — All tests from section 6
```
