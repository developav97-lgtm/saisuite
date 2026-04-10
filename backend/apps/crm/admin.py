"""
SaiSuite — CRM Admin Panel
"""
from django.contrib import admin
from .models import (
    CrmPipeline, CrmEtapa, CrmLead, CrmLeadScoringRule,
    CrmOportunidad, CrmActividad, CrmTimelineEvent,
    CrmImpuesto, CrmProducto, CrmCotizacion, CrmLineaCotizacion,
)


class CrmEtapaInline(admin.TabularInline):
    model  = CrmEtapa
    extra  = 0
    fields = ['nombre', 'orden', 'probabilidad', 'es_ganado', 'es_perdido', 'color']


@admin.register(CrmPipeline)
class CrmPipelineAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'company', 'es_default', 'created_at']
    list_filter   = ['company', 'es_default']
    search_fields = ['nombre']
    inlines       = [CrmEtapaInline]


@admin.register(CrmLead)
class CrmLeadAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'empresa', 'email', 'fuente', 'score', 'convertido', 'asignado_a', 'company', 'created_at']
    list_filter   = ['company', 'fuente', 'convertido']
    search_fields = ['nombre', 'empresa', 'email']
    readonly_fields = ['score', 'convertido', 'convertido_en']


@admin.register(CrmLeadScoringRule)
class CrmLeadScoringRuleAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'campo', 'operador', 'valor', 'puntos', 'orden', 'company']
    list_filter  = ['company']
    ordering     = ['company', 'orden']


class CrmActividadInline(admin.TabularInline):
    model  = CrmActividad
    extra  = 0
    fields = ['tipo', 'titulo', 'fecha_programada', 'completada', 'asignado_a']


@admin.register(CrmOportunidad)
class CrmOportunidadAdmin(admin.ModelAdmin):
    list_display  = ['titulo', 'contacto', 'etapa', 'valor_esperado', 'asignado_a', 'company', 'ganada_en', 'created_at']
    list_filter   = ['company', 'pipeline', 'etapa']
    search_fields = ['titulo', 'contacto__nombre_completo']
    inlines       = [CrmActividadInline]
    readonly_fields = ['ganada_en', 'perdida_en', 'proxima_actividad_fecha']


@admin.register(CrmActividad)
class CrmActividadAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'oportunidad', 'fecha_programada', 'completada', 'asignado_a']
    list_filter  = ['tipo', 'completada', 'company']
    search_fields = ['titulo']


@admin.register(CrmImpuesto)
class CrmImpuestoAdmin(admin.ModelAdmin):
    list_display  = ['nombre', 'porcentaje', 'es_default', 'sai_key', 'saiopen_synced', 'company']
    list_filter   = ['company', 'es_default', 'saiopen_synced']
    search_fields = ['nombre']


@admin.register(CrmProducto)
class CrmProductoAdmin(admin.ModelAdmin):
    list_display  = ['codigo', 'nombre', 'precio_base', 'unidad_venta', 'impuesto', 'sai_key', 'saiopen_synced', 'company']
    list_filter   = ['company', 'clase', 'grupo', 'saiopen_synced']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['sai_key', 'saiopen_synced', 'ultima_sync']


class CrmLineaCotizacionInline(admin.TabularInline):
    model   = CrmLineaCotizacion
    extra   = 0
    fields  = ['conteo', 'descripcion', 'cantidad', 'vlr_unitario', 'descuento_p', 'impuesto', 'total_parcial']
    readonly_fields = ['conteo', 'total_parcial']


@admin.register(CrmCotizacion)
class CrmCotizacionAdmin(admin.ModelAdmin):
    list_display  = ['numero_interno', 'titulo', 'oportunidad', 'estado', 'total', 'saiopen_synced', 'created_at']
    list_filter   = ['company', 'estado', 'saiopen_synced']
    search_fields = ['numero_interno', 'titulo']
    readonly_fields = ['numero_interno', 'subtotal', 'total_iva', 'total', 'sai_key', 'saiopen_synced']
    inlines       = [CrmLineaCotizacionInline]
