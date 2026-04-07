"""
SaiSuite -- Contabilidad: Admin
Registro en Django Admin para modelos contables.
"""
from django.contrib import admin

from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
    CuentaContable,
    TerceroSaiopen,
    ShipToSaiopen,
    TributariaSaiopen,
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


@admin.register(TerceroSaiopen)
class TerceroSaiopenAdmin(admin.ModelAdmin):
    """Admin readonly para terceros sincronizados desde CUST."""
    list_display = [
        'id_n', 'nit', 'nombre', 'company', 'ciudad',
        'es_cliente', 'es_proveedor', 'es_empleado', 'activo', 'sincronizado_en',
    ]
    list_filter = ['company', 'es_cliente', 'es_proveedor', 'es_empleado', 'activo']
    search_fields = ['id_n', 'nit', 'nombre', 'email']
    readonly_fields = [
        'company', 'id_n', 'nit', 'nombre', 'direccion', 'ciudad', 'departamento',
        'telefono', 'telefono2', 'email', 'es_cliente', 'es_proveedor', 'es_empleado',
        'activo', 'acct', 'acctp', 'regimen', 'fecha_creacion', 'descuento',
        'creditlmt', 'version_saiopen', 'sincronizado_en',
    ]
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ShipToSaiopen)
class ShipToSaiopenAdmin(admin.ModelAdmin):
    """Admin readonly para direcciones de envío sincronizadas desde SHIPTO."""
    list_display = [
        'id_n', 'succliente', 'descripcion', 'company',
        'ciudad', 'departamento', 'es_principal', 'estado', 'sincronizado_en',
    ]
    list_filter = ['company', 'es_principal', 'estado']
    search_fields = ['id_n', 'nombre', 'descripcion', 'addr1']
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TributariaSaiopen)
class TributariaSaiopenAdmin(admin.ModelAdmin):
    """Admin readonly para información tributaria sincronizada desde TRIBUTARIA."""
    list_display = [
        'id_n', 'company', 'tdoc', 'tipo_contribuyente',
        'primer_nombre', 'primer_apellido', 'sincronizado_en',
    ]
    list_filter = ['company', 'tdoc', 'tipo_contribuyente']
    search_fields = ['id_n', 'primer_nombre', 'primer_apellido']
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
