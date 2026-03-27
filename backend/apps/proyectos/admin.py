"""
SaiSuite — Proyectos: Admin
"""
from django.contrib import admin
from apps.proyectos.models import (
    Project, Phase, ProjectStakeholder, AccountingDocument, Milestone,
    Activity, ProjectActivity, Task, TaskTag, WorkSession,
    ResourceAssignment, ResourceCapacity, ResourceAvailability,
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
