"""
SaiSuite — Chat: Serializers
Solo transforman datos. No calculan, no llaman APIs, no tienen efectos secundarios.
"""
from rest_framework import serializers

from .models import Conversacion, Mensaje


class MensajeSerializer(serializers.ModelSerializer):
    """Serializer de lectura para mensajes."""
    remitente_nombre = serializers.CharField(source='remitente.full_name', read_only=True)
    remitente_email = serializers.EmailField(source='remitente.email', read_only=True)
    responde_a_contenido = serializers.CharField(
        source='responde_a.contenido',
        read_only=True,
        default=None,
    )

    class Meta:
        model = Mensaje
        fields = [
            'id', 'conversacion', 'remitente', 'remitente_nombre', 'remitente_email',
            'contenido', 'contenido_html', 'imagen_url',
            'responde_a', 'responde_a_contenido',
            'leido_por_destinatario', 'leido_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'contenido_html', 'leido_por_destinatario', 'leido_at',
            'created_at', 'updated_at',
        ]


class MensajeCreateSerializer(serializers.Serializer):
    """Serializer de escritura para enviar un mensaje."""
    contenido = serializers.CharField(required=False, allow_blank=True, default='')
    imagen_url = serializers.CharField(required=False, allow_blank=True, default='')
    responde_a_id = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate(self, data):
        if not data.get('contenido') and not data.get('imagen_url'):
            raise serializers.ValidationError('Se requiere contenido o imagen')
        return data


class ConversacionListSerializer(serializers.ModelSerializer):
    """Serializer de lectura para listado de conversaciones."""
    participante_1_nombre = serializers.CharField(
        source='participante_1.full_name', read_only=True,
    )
    participante_1_email = serializers.EmailField(
        source='participante_1.email', read_only=True,
    )
    participante_2_nombre = serializers.CharField(
        source='participante_2.full_name', read_only=True,
    )
    participante_2_email = serializers.EmailField(
        source='participante_2.email', read_only=True,
    )
    ultimo_mensaje_contenido = serializers.CharField(
        source='ultimo_mensaje.contenido',
        read_only=True,
        default=None,
    )
    mensajes_sin_leer = serializers.SerializerMethodField()

    class Meta:
        model = Conversacion
        fields = [
            'id',
            'participante_1', 'participante_1_nombre', 'participante_1_email',
            'participante_2', 'participante_2_nombre', 'participante_2_email',
            'ultimo_mensaje', 'ultimo_mensaje_contenido', 'ultimo_mensaje_at',
            'mensajes_sin_leer',
            'created_at', 'updated_at',
        ]

    def get_mensajes_sin_leer(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        user = request.user
        # Contar mensajes no leidos donde el usuario NO es el remitente
        return obj.mensajes.filter(
            leido_por_destinatario=False,
        ).exclude(remitente=user).count()


class ConversacionCreateSerializer(serializers.Serializer):
    """Serializer de escritura para crear/obtener una conversacion."""
    destinatario_id = serializers.UUIDField()


class AutocompleteEntidadSerializer(serializers.Serializer):
    """Serializer para resultados de autocomplete de entidades [PRY-001]."""
    id = serializers.UUIDField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    tipo = serializers.CharField()


class AutocompleteUsuarioSerializer(serializers.Serializer):
    """Serializer para resultados de autocomplete de @menciones."""
    id = serializers.UUIDField()
    nombre = serializers.CharField()
    email = serializers.EmailField()
