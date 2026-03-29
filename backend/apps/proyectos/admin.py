"""
SaiSuite — Proyectos: Admin
"""
from django.contrib import admin
from django.utils import timezone
from apps.proyectos.models import (
    Project, Phase, ProjectStakeholder, AccountingDocument, Milestone,
    Activity, ProjectActivity, SaiopenActivity, Task, TaskTag, WorkSession,
    TimesheetEntry, TaskDependency,
    ResourceAssignment, ResourceCapacity, ResourceAvailability,
    ProjectBaseline, TaskConstraint, WhatIfScenario,
    ResourceCostRate, ProjectBudget, ProjectExpense, BudgetSnapshot,
)


class PhaseInline(admin.TabularInline):
    model       = Phase
    extra       = 0
    fields      = ['nombre', 'orden', 'porcentaje_avance', 'activo']
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display   = ['codigo', 'nombre', 'company', 'tipo', 'estado', 'gerente', 'presupuesto_total', 'activo']
    list_filter    = ['estado', 'tipo', 'activo', 'sincronizado_con_saiopen']
    search_fields  = ['codigo', 'nombre', 'cliente_nombre']
    raw_id_fields  = ['gerente', 'coordinador']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines        = [PhaseInline]

    fieldsets = (
        ('Información general', {
            'fields': ('id', 'company', 'codigo', 'nombre', 'tipo', 'estado', 'activo'),
        }),
        ('Cliente', {
            'fields': ('cliente_id', 'cliente_nombre'),
        }),
        ('Responsables', {
            'fields': ('gerente', 'coordinador'),
        }),
        ('Fechas', {
            'fields': (
                'fecha_inicio_planificada', 'fecha_fin_planificada',
                'fecha_inicio_real', 'fecha_fin_real',
            ),
        }),
        ('Presupuesto y AIU', {
            'fields': (
                'presupuesto_total',
                'porcentaje_administracion', 'porcentaje_imprevistos', 'porcentaje_utilidad',
            ),
        }),
        ('Sincronización Saiopen', {
            'fields': ('saiopen_proyecto_id', 'sincronizado_con_saiopen', 'ultima_sincronizacion'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'proyecto', 'orden', 'porcentaje_avance', 'activo']
    list_filter   = ['activo']
    search_fields = ['nombre', 'proyecto__codigo']
    raw_id_fields = ['proyecto']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ProjectStakeholder)
class ProjectStakeholderAdmin(admin.ModelAdmin):
    list_display  = ['tercero_nombre', 'rol', 'proyecto', 'activo']
    list_filter   = ['rol', 'activo']
    search_fields = ['tercero_nombre', 'tercero_id', 'proyecto__codigo']


@admin.register(AccountingDocument)
class AccountingDocumentAdmin(admin.ModelAdmin):
    list_display  = ['numero_documento', 'tipo_documento', 'fecha_documento', 'proyecto', 'valor_neto']
    list_filter   = ['tipo_documento']
    search_fields = ['numero_documento', 'saiopen_doc_id', 'tercero_nombre']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sincronizado_desde_saiopen']


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'proyecto', 'porcentaje_proyecto', 'valor_facturar', 'facturado']
    list_filter   = ['facturable', 'facturado']
    search_fields = ['nombre', 'proyecto__codigo']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display  = ['codigo', 'nombre', 'company', 'tipo', 'unidad_medida', 'costo_unitario_base', 'activo']
    list_filter   = ['tipo', 'activo', 'sincronizado_con_saiopen']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ProjectActivity)
class ProjectActivityAdmin(admin.ModelAdmin):
    list_display  = ['actividad', 'proyecto', 'fase', 'cantidad_planificada', 'cantidad_ejecutada', 'costo_unitario', 'porcentaje_avance']
    list_filter   = ['actividad__tipo']
    search_fields = ['actividad__codigo', 'actividad__nombre', 'proyecto__codigo']
    raw_id_fields = ['proyecto', 'actividad', 'fase']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nombre', 'proyecto', 'responsable',
        'estado', 'prioridad', 'porcentaje_completado', 'fecha_limite'
    ]
    list_filter = ['estado', 'prioridad', 'proyecto', 'fase']
    search_fields = ['nombre', 'codigo', 'descripcion']
    raw_id_fields = ['proyecto', 'fase', 'tarea_padre', 'responsable']
    filter_horizontal = ['followers', 'tags']
    readonly_fields = ['codigo', 'actividad_proyecto_id', 'nivel_jerarquia', 'id', 'created_at', 'updated_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'codigo', 'nombre', 'descripcion', 'proyecto', 'fase')
        }),
        ('Jerarquía', {
            'fields': ('tarea_padre', 'nivel_jerarquia')
        }),
        ('Asignación', {
            'fields': ('responsable', 'followers')
        }),
        ('Clasificación', {
            'fields': ('estado', 'prioridad', 'tags', 'porcentaje_completado')
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin', 'fecha_limite')
        }),
        ('Timesheet', {
            'fields': ('horas_estimadas', 'horas_registradas')
        }),
        ('Recurrencia', {
            'fields': ('es_recurrente', 'frecuencia_recurrencia', 'proxima_generacion'),
            'classes': ('collapse',)
        }),
        ('Legacy', {
            'fields': ('actividad_proyecto_id',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'color', 'company']
    list_filter = ['color', 'company']
    search_fields = ['nombre']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display  = ['tarea', 'usuario', 'inicio', 'fin', 'duracion_horas', 'estado']
    list_filter   = ['estado', 'inicio']
    search_fields = ['tarea__codigo', 'tarea__nombre', 'usuario__email']
    raw_id_fields = ['tarea', 'usuario']
    readonly_fields = ['id', 'duracion_horas', 'created_at', 'updated_at']
    date_hierarchy = 'inicio'


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #4 — RESOURCE MANAGEMENT
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(ResourceAssignment)
class ResourceAssignmentAdmin(admin.ModelAdmin):
    list_display   = ['usuario', 'tarea', 'porcentaje_asignacion', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter    = ['activo', 'fecha_inicio']
    search_fields  = ['usuario__email', 'usuario__first_name', 'tarea__codigo', 'tarea__nombre']
    raw_id_fields  = ['tarea', 'usuario']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'fecha_inicio'

    fieldsets = (
        ('Asignación', {
            'fields': ('id', 'company', 'tarea', 'usuario', 'porcentaje_asignacion', 'activo'),
        }),
        ('Período', {
            'fields': ('fecha_inicio', 'fecha_fin', 'notas'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ResourceCapacity)
class ResourceCapacityAdmin(admin.ModelAdmin):
    list_display   = ['usuario', 'horas_por_semana', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter    = ['activo']
    search_fields  = ['usuario__email', 'usuario__first_name']
    raw_id_fields  = ['usuario']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Capacidad', {
            'fields': ('id', 'company', 'usuario', 'horas_por_semana', 'activo'),
        }),
        ('Período', {
            'fields': ('fecha_inicio', 'fecha_fin'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ResourceAvailability)
class ResourceAvailabilityAdmin(admin.ModelAdmin):
    list_display   = ['usuario', 'tipo', 'fecha_inicio', 'fecha_fin', 'aprobado', 'aprobado_por']
    list_filter    = ['tipo', 'aprobado', 'activo']
    search_fields  = ['usuario__email', 'usuario__first_name', 'descripcion']
    raw_id_fields  = ['usuario', 'aprobado_por']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'fecha_inicio'

    fieldsets = (
        ('Ausencia', {
            'fields': ('id', 'company', 'usuario', 'tipo', 'descripcion', 'activo'),
        }),
        ('Período', {
            'fields': ('fecha_inicio', 'fecha_fin'),
        }),
        ('Aprobación', {
            'fields': ('aprobado', 'aprobado_por', 'fecha_aprobacion'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #5 / Sprint 2 — SAIOPEN ACTIVITIES
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(SaiopenActivity)
class SaiopenActivityAdmin(admin.ModelAdmin):
    list_display    = ['codigo', 'nombre', 'unidad_medida', 'costo_unitario_base', 'activo', 'sincronizado_con_saiopen']
    list_filter     = ['unidad_medida', 'activo', 'sincronizado_con_saiopen']
    search_fields   = ['codigo', 'nombre', 'saiopen_actividad_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering        = ['codigo']

    @admin.action(description='Marcar como sincronizadas con Saiopen')
    def marcar_sincronizadas(self, request, queryset):
        count = queryset.update(sincronizado_con_saiopen=True)
        self.message_user(request, f'{count} actividades marcadas como sincronizadas.')

    actions = ['marcar_sincronizadas']


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #5 / Sprint 2 — TIMESHEETS
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(admin.ModelAdmin):
    list_display    = ['tarea', 'usuario', 'fecha', 'horas', 'validado', 'validado_por', 'descripcion_corta']
    list_filter     = ['validado', 'fecha', 'tarea__proyecto']
    search_fields   = ['tarea__codigo', 'tarea__nombre', 'usuario__email', 'descripcion']
    raw_id_fields   = ['tarea', 'usuario', 'validado_por']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy  = 'fecha'

    @admin.display(description='Descripción')
    def descripcion_corta(self, obj):
        return obj.descripcion[:60] + '…' if len(obj.descripcion) > 60 else obj.descripcion or '—'

    @admin.action(description='Validar registros seleccionados')
    def validar_timesheets(self, request, queryset):
        count = queryset.filter(validado=False).update(
            validado=True,
            validado_por=request.user,
            fecha_validacion=timezone.now(),
        )
        self.message_user(request, f'{count} registros de horas validados.')

    actions = ['validar_timesheets']

    fieldsets = (
        ('Registro', {
            'fields': ('id', 'company', 'tarea', 'usuario', 'fecha', 'horas', 'descripcion'),
        }),
        ('Validación', {
            'fields': ('validado', 'validado_por', 'fecha_validacion'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #6 — SCHEDULING (TaskDependency)
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    list_display    = ['tarea_predecesora', 'tarea_sucesora', 'tipo_dependencia', 'retraso_dias']
    list_filter     = ['tipo_dependencia', 'tarea_predecesora__proyecto']
    search_fields   = ['tarea_predecesora__nombre', 'tarea_predecesora__codigo',
                       'tarea_sucesora__nombre', 'tarea_sucesora__codigo']
    raw_id_fields   = ['tarea_predecesora', 'tarea_sucesora']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering        = ['tarea_predecesora']


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #6 — SCHEDULING (Baselines, Constraints, What-If)
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(ProjectBaseline)
class ProjectBaselineAdmin(admin.ModelAdmin):
    list_display    = ['project', 'name', 'is_active_baseline', 'total_tasks_snapshot',
                       'project_end_date_snapshot', 'created_at']
    list_filter     = ['is_active_baseline', 'project']
    search_fields   = ['name', 'description', 'project__codigo', 'project__nombre']
    raw_id_fields   = ['project']
    readonly_fields = ['id', 'tasks_snapshot', 'resources_snapshot', 'critical_path_snapshot', 'created_at', 'updated_at']
    ordering        = ['-created_at']

    @admin.display(description='Descripción')
    def descripcion_corta(self, obj):
        if not obj.description:
            return '—'
        return obj.description[:60] + '…' if len(obj.description) > 60 else obj.description

    fieldsets = (
        ('Información', {
            'fields': ('id', 'company', 'project', 'name', 'description', 'is_active_baseline'),
        }),
        ('Métricas del snapshot', {
            'fields': ('project_end_date_snapshot', 'total_tasks_snapshot'),
        }),
        ('Datos del snapshot', {
            'fields': ('tasks_snapshot', 'resources_snapshot', 'critical_path_snapshot'),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TaskConstraint)
class TaskConstraintAdmin(admin.ModelAdmin):
    list_display    = ['task', 'constraint_type', 'constraint_date']
    list_filter     = ['constraint_type', 'task__proyecto']
    search_fields   = ['task__nombre', 'task__codigo']
    raw_id_fields   = ['task']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering        = ['task', 'constraint_type']


@admin.register(WhatIfScenario)
class WhatIfScenarioAdmin(admin.ModelAdmin):
    list_display    = ['project', 'name', 'days_delta', 'tasks_affected_count',
                       'simulated_end_date', 'simulation_ran_at', 'created_by']
    list_filter     = ['project']
    search_fields   = ['name', 'description', 'project__codigo']
    raw_id_fields   = ['project', 'created_by']
    readonly_fields = ['id', 'task_changes', 'resource_changes', 'dependency_changes',
                       'simulated_end_date', 'simulated_critical_path', 'days_delta',
                       'tasks_affected_count', 'simulation_ran_at', 'created_at', 'updated_at']
    ordering        = ['-created_at']

    fieldsets = (
        ('Escenario', {
            'fields': ('id', 'company', 'project', 'name', 'description', 'created_by'),
        }),
        ('Cambios propuestos', {
            'fields': ('task_changes', 'resource_changes', 'dependency_changes'),
            'classes': ('collapse',),
        }),
        ('Resultados de simulación', {
            'fields': ('simulated_end_date', 'days_delta', 'tasks_affected_count',
                       'simulated_critical_path', 'simulation_ran_at'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE #7 — BUDGET & COST TRACKING
# ──────────────────────────────────────────────────────────────────────────────

@admin.register(ResourceCostRate)
class ResourceCostRateAdmin(admin.ModelAdmin):
    list_display    = ['user', 'hourly_rate', 'currency', 'start_date', 'end_date']
    list_filter     = ['currency', 'start_date']
    search_fields   = ['user__email', 'user__first_name', 'notes']
    raw_id_fields   = ['user']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering        = ['user', '-start_date']

    fieldsets = (
        ('Tarifa', {
            'fields': ('id', 'company', 'user', 'hourly_rate', 'currency'),
        }),
        ('Vigencia', {
            'fields': ('start_date', 'end_date', 'notes'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ProjectBudget)
class ProjectBudgetAdmin(admin.ModelAdmin):
    list_display    = ['project', 'planned_total_budget', 'approved_budget', 'currency',
                       'alert_threshold_percentage', 'es_aprobado', 'approved_date']
    list_filter     = ['currency', 'approved_date']
    search_fields   = ['project__codigo', 'project__nombre', 'notes']
    raw_id_fields   = ['project', 'approved_by']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering        = ['-created_at']

    @admin.display(description='Aprobado', boolean=True)
    def es_aprobado(self, obj):
        return obj.is_approved

    @admin.action(description='Aprobar presupuestos seleccionados')
    def aprobar_presupuestos(self, request, queryset):
        count = 0
        for budget in queryset.filter(approved_date__isnull=True):
            budget.approved_budget = budget.planned_total_budget
            budget.approved_by = request.user
            budget.approved_date = timezone.now()
            budget.save(update_fields=['approved_budget', 'approved_by', 'approved_date'])
            count += 1
        self.message_user(request, f'{count} presupuestos aprobados.')

    actions = ['aprobar_presupuestos']

    fieldsets = (
        ('Proyecto', {
            'fields': ('id', 'company', 'project', 'currency'),
        }),
        ('Presupuesto planificado', {
            'fields': ('planned_labor_cost', 'planned_expense_cost', 'planned_total_budget'),
        }),
        ('Aprobación', {
            'fields': ('approved_budget', 'approved_by', 'approved_date'),
        }),
        ('Alertas', {
            'fields': ('alert_threshold_percentage', 'notes'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    list_display    = ['project', 'category', 'description', 'amount', 'currency',
                       'expense_date', 'billable', 'es_aprobado', 'paid_by']
    list_filter     = ['category', 'billable', 'currency', 'expense_date']
    search_fields   = ['project__codigo', 'description', 'notes', 'paid_by__email']
    raw_id_fields   = ['project', 'paid_by', 'approved_by']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy  = 'expense_date'
    ordering        = ['-expense_date']

    @admin.display(description='Aprobado', boolean=True)
    def es_aprobado(self, obj):
        return obj.is_approved

    @admin.action(description='Aprobar gastos seleccionados')
    def aprobar_gastos(self, request, queryset):
        count = queryset.filter(approved_date__isnull=True).update(
            approved_by=request.user,
            approved_date=timezone.now(),
        )
        self.message_user(request, f'{count} gastos aprobados.')

    actions = ['aprobar_gastos']

    fieldsets = (
        ('Gasto', {
            'fields': ('id', 'company', 'project', 'category', 'description', 'amount', 'currency'),
        }),
        ('Detalles', {
            'fields': ('expense_date', 'paid_by', 'billable', 'receipt_url', 'notes'),
        }),
        ('Aprobación', {
            'fields': ('approved_by', 'approved_date'),
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(BudgetSnapshot)
class BudgetSnapshotAdmin(admin.ModelAdmin):
    list_display    = ['project', 'snapshot_date', 'labor_cost', 'expense_cost',
                       'total_cost', 'planned_budget', 'variance', 'variance_percentage']
    list_filter     = ['snapshot_date', 'project']
    search_fields   = ['project__codigo', 'project__nombre']
    raw_id_fields   = ['project']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy  = 'snapshot_date'
    ordering        = ['-snapshot_date']
