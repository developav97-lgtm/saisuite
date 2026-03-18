"""
SaiSuite — Proyectos: Admin
"""
from django.contrib import admin
from apps.proyectos.models import Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito


class FaseInline(admin.TabularInline):
    model       = Fase
    extra       = 0
    fields      = ['nombre', 'orden', 'porcentaje_avance', 'activo']
    show_change_link = True


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display   = ['codigo', 'nombre', 'company', 'tipo', 'estado', 'gerente', 'presupuesto_total', 'activo']
    list_filter    = ['estado', 'tipo', 'activo', 'sincronizado_con_saiopen']
    search_fields  = ['codigo', 'nombre', 'cliente_nombre']
    raw_id_fields  = ['gerente', 'coordinador']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines        = [FaseInline]

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


@admin.register(Fase)
class FaseAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'proyecto', 'orden', 'porcentaje_avance', 'activo']
    list_filter   = ['activo']
    search_fields = ['nombre', 'proyecto__codigo']
    raw_id_fields = ['proyecto']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(TerceroProyecto)
class TerceroProyectoAdmin(admin.ModelAdmin):
    list_display  = ['tercero_nombre', 'rol', 'proyecto', 'activo']
    list_filter   = ['rol', 'activo']
    search_fields = ['tercero_nombre', 'tercero_id', 'proyecto__codigo']


@admin.register(DocumentoContable)
class DocumentoContableAdmin(admin.ModelAdmin):
    list_display  = ['numero_documento', 'tipo_documento', 'fecha_documento', 'proyecto', 'valor_neto']
    list_filter   = ['tipo_documento']
    search_fields = ['numero_documento', 'saiopen_doc_id', 'tercero_nombre']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sincronizado_desde_saiopen']


@admin.register(Hito)
class HitoAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'proyecto', 'porcentaje_proyecto', 'valor_facturar', 'facturado']
    list_filter   = ['facturable', 'facturado']
    search_fields = ['nombre', 'proyecto__codigo']
