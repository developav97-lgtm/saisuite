"""
SaiSuite — Terceros Serializers
Transformación de datos para la API de terceros. Sin lógica de negocio.
"""
from rest_framework import serializers
from .models import Tercero, TerceroDireccion


class TerceroDireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TerceroDireccion
        fields = [
            'id', 'tipo', 'nombre_sucursal',
            'pais', 'departamento', 'ciudad',
            'direccion_linea1', 'direccion_linea2', 'codigo_postal',
            'nombre_contacto', 'telefono_contacto', 'email_contacto',
            'saiopen_linea_id', 'activa', 'es_principal',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TerceroListSerializer(serializers.ModelSerializer):
    """Campos mínimos para listados y autocomplete."""
    class Meta:
        model = Tercero
        fields = [
            'id', 'codigo', 'tipo_identificacion', 'numero_identificacion',
            'nombre_completo', 'tipo_persona', 'tipo_tercero',
            'email', 'telefono', 'celular',
            'saiopen_synced', 'activo',
        ]
        read_only_fields = ['id', 'codigo', 'nombre_completo', 'saiopen_synced']


class TerceroDetailSerializer(serializers.ModelSerializer):
    """Detalle completo con direcciones."""
    direcciones = TerceroDireccionSerializer(many=True, read_only=True)

    class Meta:
        model = Tercero
        fields = [
            'id', 'codigo',
            'tipo_identificacion', 'numero_identificacion',
            'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido',
            'razon_social', 'nombre_completo',
            'tipo_persona', 'tipo_tercero',
            'email', 'telefono', 'celular',
            'saiopen_id', 'sai_key', 'saiopen_synced',
            'activo', 'direcciones',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'codigo', 'nombre_completo', 'saiopen_synced', 'created_at', 'updated_at']


class TerceroCreateUpdateSerializer(serializers.ModelSerializer):
    # allow_null=True en campos opcionales: el form Angular envía null cuando están vacíos
    primer_nombre    = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    segundo_nombre   = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    primer_apellido  = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    segundo_apellido = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    razon_social     = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    tipo_tercero     = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    email            = serializers.EmailField(required=False, allow_blank=True, allow_null=True, default='')
    telefono         = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    celular          = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')

    class Meta:
        model = Tercero
        fields = [
            'tipo_identificacion', 'numero_identificacion',
            'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido',
            'razon_social', 'tipo_persona', 'tipo_tercero',
            'email', 'telefono', 'celular',
        ]

    def to_internal_value(self, data):
        # Normalizar null → '' en todos los CharField opcionales antes de validar
        nullable_fields = [
            'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido',
            'razon_social', 'tipo_tercero', 'email', 'telefono', 'celular',
        ]
        mutable = data.copy() if hasattr(data, 'copy') else dict(data)
        for field in nullable_fields:
            if field in mutable and mutable[field] is None:
                mutable[field] = ''
        return super().to_internal_value(mutable)

    def validate(self, attrs):
        tipo_persona = attrs.get('tipo_persona') or (self.instance.tipo_persona if self.instance else None)
        razon_social = attrs.get('razon_social', getattr(self.instance, 'razon_social', ''))
        primer_apellido = attrs.get('primer_apellido', getattr(self.instance, 'primer_apellido', ''))

        if tipo_persona == 'juridica' and not razon_social:
            raise serializers.ValidationError({'razon_social': 'Obligatorio para persona jurídica.'})
        if tipo_persona == 'natural' and not primer_apellido:
            raise serializers.ValidationError({'primer_apellido': 'Obligatorio para persona natural.'})
        return attrs
