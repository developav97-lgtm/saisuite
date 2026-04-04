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
