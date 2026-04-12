"""
SaiSuite -- Contabilidad: Serializers
Los serializers SOLO transforman datos. Sin logica de negocio.
"""
import logging
from rest_framework import serializers

from apps.contabilidad.models import (
    MovimientoContable,
    ConfiguracionContable,
    CuentaContable,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Sync Input Serializers (write)
# ──────────────────────────────────────────────

class GLRecordSerializer(serializers.Serializer):
    """Serializer para un registro individual de GL que llega del agente de sync."""
    conteo = serializers.IntegerField()
    auxiliar = serializers.DecimalField(max_digits=18, decimal_places=4)
    auxiliar_nombre = serializers.CharField(max_length=120, default='')
    titulo_codigo = serializers.IntegerField(required=False, allow_null=True, default=None)
    titulo_nombre = serializers.CharField(max_length=120, required=False, default='')
    grupo_codigo = serializers.IntegerField(required=False, allow_null=True, default=None)
    grupo_nombre = serializers.CharField(max_length=120, required=False, default='')
    cuenta_codigo = serializers.IntegerField(required=False, allow_null=True, default=None)
    cuenta_nombre = serializers.CharField(max_length=120, required=False, default='')
    subcuenta_codigo = serializers.IntegerField(required=False, allow_null=True, default=None)
    subcuenta_nombre = serializers.CharField(max_length=120, required=False, default='')
    tercero_id = serializers.CharField(max_length=30)
    tercero_nombre = serializers.CharField(max_length=35, required=False, default='')
    debito = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    tipo = serializers.CharField(max_length=3, required=False, default='')
    batch = serializers.IntegerField(required=False, allow_null=True, default=None)
    invc = serializers.CharField(max_length=15, required=False, default='')
    descripcion = serializers.CharField(max_length=120, required=False, default='')
    fecha = serializers.DateField()
    duedate = serializers.DateField(required=False, allow_null=True, default=None)
    periodo = serializers.CharField(max_length=7)
    departamento_codigo = serializers.IntegerField(required=False, allow_null=True, default=None)
    departamento_nombre = serializers.CharField(max_length=40, required=False, default='')
    centro_costo_codigo = serializers.IntegerField(required=False, allow_null=True, default=None)
    centro_costo_nombre = serializers.CharField(max_length=40, required=False, default='')
    proyecto_codigo = serializers.CharField(max_length=10, required=False, allow_null=True, default=None)
    proyecto_nombre = serializers.CharField(max_length=60, required=False, default='')
    actividad_codigo = serializers.CharField(max_length=3, required=False, allow_null=True, default=None)
    actividad_nombre = serializers.CharField(max_length=60, required=False, default='')


class GLBatchSerializer(serializers.Serializer):
    """Serializer para el batch de registros GL."""
    records = GLRecordSerializer(many=True)


class ACCTRecordSerializer(serializers.Serializer):
    """Serializer para un registro del plan de cuentas (ACCT)."""
    codigo = serializers.DecimalField(max_digits=18, decimal_places=4)
    descripcion = serializers.CharField(max_length=120)
    nivel = serializers.IntegerField(default=0)
    clase = serializers.CharField(max_length=1, required=False, default='')
    tipo = serializers.CharField(max_length=3, required=False, default='')
    titulo_codigo = serializers.IntegerField(default=0)
    grupo_codigo = serializers.IntegerField(default=0)
    cuenta_codigo = serializers.IntegerField(default=0)
    subcuenta_codigo = serializers.IntegerField(default=0)
    posicion_financiera = serializers.IntegerField(default=0)


class ACCTBatchSerializer(serializers.Serializer):
    """Serializer para el batch de registros ACCT."""
    records = ACCTRecordSerializer(many=True)


class OERecordSerializer(serializers.Serializer):
    """Serializer para un registro de encabezado de factura (OE)."""
    number = serializers.IntegerField()
    tipo = serializers.CharField(max_length=3, default='')
    id_sucursal = serializers.IntegerField(default=1)
    tercero_id = serializers.CharField(max_length=30, default='')
    tercero_nombre = serializers.CharField(max_length=120, required=False, default='')
    salesman = serializers.IntegerField(required=False, allow_null=True, default=None)
    salesman_nombre = serializers.CharField(max_length=60, required=False, default='')
    fecha = serializers.DateField()
    duedate = serializers.DateField(required=False, allow_null=True, default=None)
    periodo = serializers.CharField(max_length=7, default='')
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento_global = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    posted = serializers.BooleanField(default=False)
    closed = serializers.BooleanField(default=False)
    cod_moneda = serializers.CharField(max_length=5, required=False, default='COP')
    comentarios = serializers.CharField(required=False, default='')


class OEBatchSerializer(serializers.Serializer):
    """Serializer para el batch de encabezados OE."""
    records = OERecordSerializer(many=True)


class OEDetRecordSerializer(serializers.Serializer):
    """Serializer para una línea de factura (OEDET)."""
    conteo = serializers.IntegerField()
    # Referencia al encabezado para resolver FK
    factura_number = serializers.IntegerField()
    factura_tipo = serializers.CharField(max_length=3, default='')
    factura_id_sucursal = serializers.IntegerField(default=1)
    # Campos del detalle
    item_codigo = serializers.CharField(max_length=30, default='')
    item_descripcion = serializers.CharField(max_length=120, required=False, default='')
    location = serializers.CharField(max_length=3, required=False, default='')
    qty_order = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    qty_ship = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    precio_unitario = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    precio_extendido = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo_unitario = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    valor_iva = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    porc_iva = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    margen_valor = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    margen_porcentaje = serializers.DecimalField(max_digits=7, decimal_places=2, default=0)
    proyecto_codigo = serializers.CharField(max_length=10, required=False, default='')


class OEDetBatchSerializer(serializers.Serializer):
    """Serializer para el batch de líneas OEDET."""
    records = OEDetRecordSerializer(many=True)


class CARPRORecordSerializer(serializers.Serializer):
    """Serializer para un movimiento de cartera (CARPRO)."""
    conteo = serializers.IntegerField()
    tercero_id = serializers.CharField(max_length=30, default='')
    tercero_nombre = serializers.CharField(max_length=120, required=False, default='')
    cuenta_contable = serializers.DecimalField(max_digits=18, decimal_places=4)
    tipo = serializers.CharField(max_length=3, required=False, default='')
    batch = serializers.IntegerField(required=False, allow_null=True, default=None)
    invc = serializers.CharField(max_length=15, required=False, default='')
    descripcion = serializers.CharField(max_length=120, required=False, default='')
    fecha = serializers.DateField()
    duedate = serializers.DateField(required=False, allow_null=True, default=None)
    periodo = serializers.CharField(max_length=7, default='')
    debito = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    departamento = serializers.IntegerField(required=False, allow_null=True, default=None)
    centro_costo = serializers.IntegerField(required=False, allow_null=True, default=None)
    proyecto_codigo = serializers.CharField(max_length=10, required=False, default='')
    tipo_cartera = serializers.ChoiceField(choices=['CXC', 'CXP'], default='CXC')


class CARPROBatchSerializer(serializers.Serializer):
    """Serializer para el batch de movimientos CARPRO."""
    records = CARPRORecordSerializer(many=True)


class ITEMACTRecordSerializer(serializers.Serializer):
    """Serializer para un movimiento de inventario (ITEMACT)."""
    conteo = serializers.IntegerField()
    item_codigo = serializers.CharField(max_length=30, default='')
    item_descripcion = serializers.CharField(max_length=120, required=False, default='')
    location = serializers.CharField(max_length=3, required=False, default='')
    tercero_id = serializers.CharField(max_length=30, required=False, default='')
    tipo = serializers.CharField(max_length=3, required=False, default='')
    batch = serializers.IntegerField(required=False, allow_null=True, default=None)
    fecha = serializers.DateField()
    periodo = serializers.CharField(max_length=7, default='')
    cantidad = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    valor_unitario = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    costo_peps = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_unidades = serializers.DecimalField(max_digits=15, decimal_places=4, default=0)
    saldo_pesos = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    lote = serializers.CharField(max_length=30, required=False, default='')
    serie = serializers.CharField(max_length=50, required=False, default='')
    lote_vencimiento = serializers.DateField(required=False, allow_null=True, default=None)


class ITEMACTBatchSerializer(serializers.Serializer):
    """Serializer para el batch de movimientos ITEMACT."""
    records = ITEMACTRecordSerializer(many=True)


# ──────────────────────────────────────────────
# Read Serializers (output)
# ──────────────────────────────────────────────

class SyncStatusSerializer(serializers.Serializer):
    """Serializer de respuesta para el estado de sincronizacion."""
    sync_activo = serializers.BooleanField()
    usa_departamentos_cc = serializers.BooleanField()
    usa_proyectos_actividades = serializers.BooleanField()
    ultimo_conteo_gl = serializers.IntegerField()
    ultima_sync_gl = serializers.DateTimeField(allow_null=True)
    ultima_sync_acct = serializers.DateTimeField(allow_null=True)
    sync_error = serializers.CharField()
    total_movimientos = serializers.IntegerField()
    total_cuentas = serializers.IntegerField()


class SyncResultSerializer(serializers.Serializer):
    """Serializer de respuesta para el resultado de una operacion de sync."""
    inserted = serializers.IntegerField()
    updated = serializers.IntegerField()
    errors = serializers.ListField(child=serializers.CharField())


class CuentaContableSerializer(serializers.ModelSerializer):
    """Serializer de lectura para CuentaContable."""
    class Meta:
        model = CuentaContable
        fields = [
            'codigo', 'descripcion', 'nivel', 'clase', 'tipo',
            'titulo_codigo', 'grupo_codigo', 'cuenta_codigo',
            'subcuenta_codigo', 'posicion_financiera',
        ]


class MovimientoContableSerializer(serializers.ModelSerializer):
    """Serializer de lectura para MovimientoContable (admin/debug)."""
    class Meta:
        model = MovimientoContable
        fields = [
            'conteo', 'auxiliar', 'auxiliar_nombre',
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
