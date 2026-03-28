"""
SaiSuite — Proyectos: Budget & Cost Serializers (Feature #7)

Reglas estrictas:
- Serializers solo transforman datos. Sin lógica de negocio.
- Campos computados (actuals, variance) se pasan desde la view vía SerializerMethodField
  o se inyectan en el contexto. El serializer NO llama a services.
- Todos los campos de dinero se retornan como string para preservar precisión
  decimal en el frontend (evitar pérdida de precisión con JSON float).
"""
from rest_framework import serializers

from apps.proyectos.models import (
    ResourceCostRate,
    ProjectBudget,
    ProjectExpense,
    BudgetSnapshot,
    ExpenseCategory,
)


# ─── ResourceCostRate ────────────────────────────────────────────────────────

class ResourceCostRateListSerializer(serializers.ModelSerializer):
    """Listado compacto de tarifas — usado en tablas y selects."""
    user_email     = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    is_active      = serializers.SerializerMethodField()

    class Meta:
        model  = ResourceCostRate
        fields = [
            'id', 'user', 'user_email', 'user_full_name',
            'start_date', 'end_date', 'hourly_rate', 'currency',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'user_email', 'user_full_name', 'is_active', 'created_at']

    def get_is_active(self, obj: ResourceCostRate) -> bool:
        return obj.end_date is None


class ResourceCostRateDetailSerializer(ResourceCostRateListSerializer):
    """Detalle completo, incluye notas."""
    class Meta(ResourceCostRateListSerializer.Meta):
        fields = ResourceCostRateListSerializer.Meta.fields + ['notes', 'updated_at']
        read_only_fields = ResourceCostRateListSerializer.Meta.read_only_fields + ['updated_at']


class ResourceCostRateWriteSerializer(serializers.ModelSerializer):
    """Para crear/actualizar tarifas — validación básica de campos."""
    class Meta:
        model  = ResourceCostRate
        fields = ['user', 'start_date', 'end_date', 'hourly_rate', 'currency', 'notes']

    def validate_hourly_rate(self, value):
        from decimal import Decimal
        if value <= Decimal('0.00'):
            raise serializers.ValidationError('La tarifa por hora debe ser mayor a 0.')
        return value

    def validate(self, attrs):
        start = attrs.get('start_date')
        end   = attrs.get('end_date')
        if start and end and end <= start:
            raise serializers.ValidationError(
                {'end_date': 'La fecha de fin debe ser posterior a la fecha de inicio.'}
            )
        return attrs


# ─── ProjectBudget ───────────────────────────────────────────────────────────

class ProjectBudgetSerializer(serializers.ModelSerializer):
    """
    Serializer de presupuesto.
    Los campos de costo real (actual_*) y variance se inyectan desde la view
    después de llamar a CostCalculationService — no se calculan aquí.
    """
    is_approved = serializers.SerializerMethodField()

    # Campos computados: la view los añade al diccionario de representación
    # si los pasa en el contexto con key 'computed_fields'.
    actual_labor_cost   = serializers.SerializerMethodField()
    actual_expense_cost = serializers.SerializerMethodField()
    actual_total_cost   = serializers.SerializerMethodField()
    variance            = serializers.SerializerMethodField()
    variance_percentage = serializers.SerializerMethodField()
    alert               = serializers.SerializerMethodField()

    class Meta:
        model  = ProjectBudget
        fields = [
            'id', 'project',
            'planned_labor_cost', 'planned_expense_cost', 'planned_total_budget',
            'approved_budget', 'approved_by', 'approved_date', 'is_approved',
            'alert_threshold_percentage', 'currency', 'notes',
            # Campos computados — se inyectan desde la view
            'actual_labor_cost', 'actual_expense_cost', 'actual_total_cost',
            'variance', 'variance_percentage', 'alert',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'approved_by', 'approved_date', 'is_approved',
            'actual_labor_cost', 'actual_expense_cost', 'actual_total_cost',
            'variance', 'variance_percentage', 'alert',
            'created_at', 'updated_at',
        ]

    def _get_computed(self, obj: ProjectBudget, key: str):
        """Recupera un campo computado inyectado por la view en el contexto."""
        computed = self.context.get('computed_fields', {})
        return computed.get(key)

    def get_is_approved(self, obj: ProjectBudget) -> bool:
        return obj.is_approved

    def get_actual_labor_cost(self, obj):
        return self._get_computed(obj, 'actual_labor_cost')

    def get_actual_expense_cost(self, obj):
        return self._get_computed(obj, 'actual_expense_cost')

    def get_actual_total_cost(self, obj):
        return self._get_computed(obj, 'actual_total_cost')

    def get_variance(self, obj):
        return self._get_computed(obj, 'variance')

    def get_variance_percentage(self, obj):
        return self._get_computed(obj, 'variance_percentage')

    def get_alert(self, obj):
        return self._get_computed(obj, 'alert')


class ProjectBudgetWriteSerializer(serializers.ModelSerializer):
    """Para crear/actualizar el presupuesto planificado."""
    class Meta:
        model  = ProjectBudget
        fields = [
            'planned_labor_cost', 'planned_expense_cost', 'planned_total_budget',
            'alert_threshold_percentage', 'currency', 'notes',
        ]

    def validate_planned_total_budget(self, value):
        from decimal import Decimal
        if value < Decimal('0.00'):
            raise serializers.ValidationError('El presupuesto total no puede ser negativo.')
        return value

    def validate_alert_threshold_percentage(self, value):
        from decimal import Decimal
        if not (Decimal('1.00') <= value <= Decimal('100.00')):
            raise serializers.ValidationError(
                'El umbral de alerta debe estar entre 1% y 100%.'
            )
        return value


# ─── ProjectExpense ──────────────────────────────────────────────────────────

class ProjectExpenseListSerializer(serializers.ModelSerializer):
    """Listado compacto de gastos — usado en tablas."""
    paid_by_name = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_approved  = serializers.SerializerMethodField()

    class Meta:
        model  = ProjectExpense
        fields = [
            'id', 'project',
            'category', 'category_display', 'description',
            'amount', 'currency', 'expense_date',
            'paid_by', 'paid_by_name',
            'billable', 'is_approved',
            'created_at',
        ]
        read_only_fields = ['id', 'paid_by_name', 'category_display', 'is_approved', 'created_at']

    def get_paid_by_name(self, obj: ProjectExpense) -> str:
        if obj.paid_by:
            return obj.paid_by.full_name or obj.paid_by.email
        return ''

    def get_is_approved(self, obj: ProjectExpense) -> bool:
        return obj.is_approved


class ProjectExpenseDetailSerializer(ProjectExpenseListSerializer):
    """Detalle completo, incluye aprobación y recibo."""
    approved_by_name = serializers.SerializerMethodField()

    class Meta(ProjectExpenseListSerializer.Meta):
        fields = ProjectExpenseListSerializer.Meta.fields + [
            'receipt_url', 'notes',
            'approved_by', 'approved_by_name', 'approved_date',
            'updated_at',
        ]
        read_only_fields = ProjectExpenseListSerializer.Meta.read_only_fields + [
            'approved_by', 'approved_by_name', 'approved_date', 'updated_at',
        ]

    def get_approved_by_name(self, obj: ProjectExpense) -> str:
        if obj.approved_by:
            return obj.approved_by.full_name or obj.approved_by.email
        return ''


class ProjectExpenseWriteSerializer(serializers.ModelSerializer):
    """Para crear/actualizar gastos."""
    class Meta:
        model  = ProjectExpense
        fields = [
            'category', 'description', 'amount', 'currency',
            'expense_date', 'paid_by', 'receipt_url', 'billable', 'notes',
        ]

    def validate_amount(self, value):
        from decimal import Decimal
        if value <= Decimal('0.00'):
            raise serializers.ValidationError('El monto del gasto debe ser mayor a 0.')
        return value

    def validate_category(self, value):
        valid = [c[0] for c in ExpenseCategory.choices]
        if value not in valid:
            raise serializers.ValidationError(f'Categoría inválida. Opciones: {valid}')
        return value


# ─── BudgetSnapshot ──────────────────────────────────────────────────────────

class BudgetSnapshotSerializer(serializers.ModelSerializer):
    """Solo lectura — los snapshots no se editan manualmente."""

    class Meta:
        model  = BudgetSnapshot
        fields = [
            'id', 'project', 'snapshot_date',
            'labor_cost', 'expense_cost', 'total_cost',
            'planned_budget', 'variance', 'variance_percentage',
            'created_at',
        ]
        read_only_fields = fields


# ─── Respuestas calculadas (sin modelo) ──────────────────────────────────────

class CostSummarySerializer(serializers.Serializer):
    """Respuesta de /costs/total/"""
    labor_cost   = serializers.DecimalField(max_digits=15, decimal_places=2)
    expense_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_cost   = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency     = serializers.CharField(max_length=3)


class CostBreakdownResourceSerializer(serializers.Serializer):
    """Un ítem de /costs/by-resource/"""
    user_id             = serializers.UUIDField()
    user_full_name      = serializers.CharField()
    hours_worked        = serializers.DecimalField(max_digits=10, decimal_places=2)
    cost                = serializers.DecimalField(max_digits=15, decimal_places=2)
    percentage_of_total = serializers.DecimalField(max_digits=5, decimal_places=2)


class CostBreakdownTaskSerializer(serializers.Serializer):
    """Un ítem de /costs/by-task/"""
    task_id         = serializers.UUIDField()
    task_name       = serializers.CharField()
    estimated_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    actual_hours    = serializers.DecimalField(max_digits=10, decimal_places=2)
    actual_cost     = serializers.DecimalField(max_digits=15, decimal_places=2)
    hours_variance  = serializers.DecimalField(max_digits=10, decimal_places=2)


class BudgetVarianceSerializer(serializers.Serializer):
    """Respuesta de /budget/variance/"""
    planned_budget      = serializers.DecimalField(max_digits=15, decimal_places=2)
    actual_cost         = serializers.DecimalField(max_digits=15, decimal_places=2)
    variance            = serializers.DecimalField(max_digits=15, decimal_places=2)
    variance_percentage = serializers.DecimalField(max_digits=7, decimal_places=2)
    is_over_budget      = serializers.BooleanField()
    alert_triggered     = serializers.BooleanField()
    currency            = serializers.CharField(max_length=3)


class BudgetAlertSerializer(serializers.Serializer):
    """Respuesta de /budget/alerts/"""
    alert_level          = serializers.ChoiceField(choices=['none', 'warning', 'critical'])
    message              = serializers.CharField()
    current_percentage   = serializers.DecimalField(max_digits=7, decimal_places=2)
    threshold_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)


class EvmMetricsSerializer(serializers.Serializer):
    """Respuesta de /costs/evm/"""
    planned_value              = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    earned_value               = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    actual_cost                = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    cost_variance              = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    schedule_variance          = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    cost_performance_index     = serializers.DecimalField(max_digits=7, decimal_places=4, allow_null=True)
    schedule_performance_index = serializers.DecimalField(max_digits=7, decimal_places=4, allow_null=True)
    estimate_at_completion     = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    completion_percentage      = serializers.DecimalField(max_digits=5, decimal_places=2)
    as_of_date                 = serializers.DateField()
    currency                   = serializers.CharField(max_length=3)


class InvoiceLineItemSerializer(serializers.Serializer):
    """Un ítem de línea en /invoice-data/"""
    type        = serializers.ChoiceField(choices=['labor', 'expense'])
    description = serializers.CharField()
    quantity    = serializers.DecimalField(max_digits=10, decimal_places=2)
    unit_rate   = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal    = serializers.DecimalField(max_digits=15, decimal_places=2)


class InvoiceDataSerializer(serializers.Serializer):
    """Respuesta de /invoice-data/"""
    project_id         = serializers.UUIDField()
    project_name       = serializers.CharField()
    client_name        = serializers.CharField()
    line_items         = InvoiceLineItemSerializer(many=True)
    subtotal_labor     = serializers.DecimalField(max_digits=15, decimal_places=2)
    subtotal_expenses  = serializers.DecimalField(max_digits=15, decimal_places=2)
    grand_total        = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency           = serializers.CharField(max_length=3)
    generated_at       = serializers.DateTimeField()
