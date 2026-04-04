"""
SaiSuite -- Contabilidad: Admin
Registro en Django Admin para modelos contables.
"""
from django.contrib import admin

from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
    CuentaContable,
)


@admin.register(MovimientoContable)
class MovimientoContableAdmin(admin.ModelAdmin):
    """Admin readonly para movimientos contables sincronizados."""
    list_display = [
        'conteo', 'company', 'periodo', 'fecha',
        'auxiliar', 'auxiliar_nombre',
        'debito', 'credito', 'tercero_id',
    ]
    list_filter = ['company', 'periodo', 'titulo_codigo', 'tipo']
    search_fields = ['auxiliar_nombre', 'tercero_nombre', 'descripcion', 'invc']
    readonly_fields = [
        'company', 'conteo', 'auxiliar', 'auxiliar_nombre',
        'titulo_codigo', 'titulo_nombre',
        'grupo_codigo', 'grupo_nombre',
        'cuenta_codigo', 'cuenta_nombre',
        'subcuenta_codigo', 'subcuenta_nombre',
        'tercero_id', 'tercero_nombre',
        'debito', 'credito',
        'tipo', 'batch', 'invc', 'descripcion',
        'fecha', 'duedate', 'periodo',
        'departamento_codigo', 'departamento_nombre',
        'centro_costo_codigo', 'centro_costo_nombre',
        'proyecto_codigo', 'proyecto_nombre',
        'actividad_codigo', 'actividad_nombre',
        'sincronizado_en',
    ]
    list_per_page = 50
    ordering = ['-fecha', '-conteo']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracionContable)
class ConfiguracionContableAdmin(admin.ModelAdmin):
    """Admin editable para configuracion contable por empresa."""
    list_display = [
        'company', 'sync_activo', 'usa_departamentos_cc',
        'usa_proyectos_actividades', 'ultimo_conteo_gl',
        'ultima_sync_gl',
    ]
    list_filter = ['sync_activo', 'usa_departamentos_cc', 'usa_proyectos_actividades']


@admin.register(CuentaContable)
class CuentaContableAdmin(admin.ModelAdmin):
    """Admin readonly para plan de cuentas sincronizado."""
    list_display = [
        'codigo', 'descripcion', 'company', 'nivel', 'clase', 'tipo',
    ]
    list_filter = ['company', 'nivel', 'clase']
    search_fields = ['descripcion']
    readonly_fields = [
        'company', 'codigo', 'descripcion', 'nivel', 'clase', 'tipo',
        'titulo_codigo', 'grupo_codigo', 'cuenta_codigo',
        'subcuenta_codigo', 'posicion_financiera',
    ]
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
