"""
SaiSuite — Core Serializers
"""
from rest_framework import serializers
from apps.core.models import ConfiguracionConsecutivo


class ConfiguracionConsecutivoSerializer(serializers.ModelSerializer):
    proximo_codigo = serializers.SerializerMethodField()

    class Meta:
        model  = ConfiguracionConsecutivo
        fields = [
            'id', 'nombre', 'tipo', 'subtipo', 'prefijo',
            'ultimo_numero', 'formato', 'activo',
            'proximo_codigo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'proximo_codigo', 'created_at', 'updated_at']

    def get_proximo_codigo(self, obj: ConfiguracionConsecutivo) -> str:
        return obj.generar_preview()


class ConfiguracionConsecutivoCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ConfiguracionConsecutivo
        fields = ['nombre', 'tipo', 'subtipo', 'prefijo', 'ultimo_numero', 'formato', 'activo']

    def validate_formato(self, value: str) -> str:
        """Verifica que el formato tenga las variables obligatorias y sea válido."""
        try:
            result = value.format(prefijo='TST', numero=1)
            if not result:
                raise serializers.ValidationError('El formato generó una cadena vacía.')
        except (KeyError, ValueError) as exc:
            raise serializers.ValidationError(
                f'Formato inválido: {exc}. Use {{prefijo}} y {{numero}}.'
            ) from exc
        return value
