"""
SaiSuite — CRM: Cotización Serializers
"""
from rest_framework import serializers
from .models import CrmCotizacion, CrmLineaCotizacion, CrmImpuesto, CrmProducto


class CrmImpuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CrmImpuesto
        fields = ['id', 'nombre', 'porcentaje', 'es_default', 'sai_key']
        read_only_fields = ['id', 'sai_key']


class CrmProductoListSerializer(serializers.ModelSerializer):
    impuesto = CrmImpuestoSerializer(read_only=True)

    class Meta:
        model  = CrmProducto
        fields = ['id', 'codigo', 'nombre', 'precio_base', 'unidad_venta', 'impuesto', 'clase', 'grupo']
        read_only_fields = ['id', 'codigo', 'sai_key']


class CrmLineaCotizacionSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True, default='')
    impuesto_nombre = serializers.CharField(source='impuesto.nombre', read_only=True, default='')
    impuesto_pct    = serializers.DecimalField(source='impuesto.porcentaje', max_digits=6,
                                               decimal_places=4, read_only=True, default=0)

    class Meta:
        model  = CrmLineaCotizacion
        fields = [
            'id', 'conteo', 'producto', 'producto_nombre',
            'descripcion', 'descripcion_adic',
            'cantidad', 'vlr_unitario', 'descuento_p',
            'impuesto', 'impuesto_nombre', 'impuesto_pct',
            'iva_valor', 'total_parcial',
            'proyecto', 'actividad',
        ]
        read_only_fields = ['id', 'conteo', 'iva_valor', 'total_parcial']


class CrmLineaCotizacionCreateSerializer(serializers.Serializer):
    producto_id      = serializers.UUIDField(required=False, allow_null=True)
    descripcion      = serializers.CharField(max_length=200)
    descripcion_adic = serializers.CharField(required=False, allow_blank=True, default='')
    cantidad         = serializers.DecimalField(max_digits=15, decimal_places=4, default=1)
    vlr_unitario     = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento_p      = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    impuesto_id      = serializers.UUIDField(required=False, allow_null=True)
    proyecto         = serializers.CharField(max_length=10, required=False, allow_blank=True, default='')
    actividad        = serializers.CharField(max_length=3, required=False, allow_blank=True, default='')


class CrmCotizacionListSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model  = CrmCotizacion
        fields = [
            'id', 'numero_interno', 'titulo', 'estado', 'estado_display',
            'total', 'fecha_vencimiento', 'saiopen_synced', 'created_at',
        ]
        read_only_fields = ['id', 'numero_interno', 'created_at']


class CrmCotizacionDetailSerializer(serializers.ModelSerializer):
    lineas         = CrmLineaCotizacionSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model  = CrmCotizacion
        fields = [
            'id', 'oportunidad', 'numero_interno', 'titulo', 'contacto',
            'validez_dias', 'fecha_vencimiento', 'estado', 'estado_display',
            'subtotal', 'descuento_adicional_p', 'descuento_adicional_val',
            'total_iva', 'total',
            'observaciones', 'condiciones', 'lineas',
            'sai_numero', 'sai_key', 'saiopen_synced',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero_interno', 'subtotal', 'descuento_adicional_val',
            'total_iva', 'total', 'sai_numero', 'sai_key', 'saiopen_synced',
            'created_at', 'updated_at',
        ]


class CrmCotizacionCreateSerializer(serializers.Serializer):
    titulo           = serializers.CharField(max_length=200, required=False, allow_blank=True)
    contacto_id      = serializers.UUIDField(required=False, allow_null=True)
    validez_dias     = serializers.IntegerField(default=30)
    observaciones    = serializers.CharField(required=False, allow_blank=True, default='')
    condiciones      = serializers.CharField(required=False, allow_blank=True, default='')


class CrmCotizacionUpdateSerializer(serializers.Serializer):
    titulo                = serializers.CharField(max_length=200, required=False)
    validez_dias          = serializers.IntegerField(required=False)
    fecha_vencimiento     = serializers.DateField(required=False, allow_null=True)
    observaciones         = serializers.CharField(required=False, allow_blank=True)
    condiciones           = serializers.CharField(required=False, allow_blank=True)
    descuento_adicional_p = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)


class CrmCotizacionEnviarSerializer(serializers.Serializer):
    email_destino = serializers.EmailField(required=False, allow_blank=True)


class CrmSyncConfirmSerializer(serializers.Serializer):
    """Para el callback del agente tras crear COTIZACI en Saiopen."""
    cotizacion_id = serializers.UUIDField()
    sai_numero    = serializers.IntegerField()
    sai_tipo      = serializers.CharField(max_length=3)
    sai_empresa   = serializers.IntegerField()
    sai_sucursal  = serializers.IntegerField()
