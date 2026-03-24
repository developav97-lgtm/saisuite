"""
SaiSuite — Notifications: Serializers
Solo transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from .models import Notificacion, Comentario, PreferenciaNotificacion


class NotificacionSerializer(serializers.ModelSerializer):
    tipo_display        = serializers.CharField(source='get_tipo_display', read_only=True)
    objeto_model        = serializers.SerializerMethodField()
    objeto_id_str       = serializers.UUIDField(source='object_id', read_only=True)

    class Meta:
        model  = Notificacion
        fields = [
            'id', 'tipo', 'tipo_display',
            'titulo', 'mensaje',
            'objeto_model', 'objeto_id_str',
            'url_accion', 'ancla',
            'leida', 'leida_en',
            'snoozed_until', 'recordatorio_en',
            'metadata',
            'created_at',
        ]
        read_only_fields = fields

    def get_objeto_model(self, obj: Notificacion) -> str:
        try:
            return obj.content_type.model
        except Exception:
            return ''


class ComentarioAutorSerializer(serializers.Serializer):
    """Representación mínima del autor de un comentario."""
    id        = serializers.UUIDField()
    full_name = serializers.CharField()
    email     = serializers.EmailField()


class RespuestaSerializer(serializers.ModelSerializer):
    """Serializer plano para respuestas (nivel 2). Sin anidación adicional."""
    autor    = ComentarioAutorSerializer(read_only=True)
    editado  = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Comentario
        fields = [
            'id', 'autor', 'texto', 'editado', 'editado_en', 'created_at',
        ]
        read_only_fields = fields


class ComentarioSerializer(serializers.ModelSerializer):
    """Serializer de lectura para comentarios raíz con respuestas anidadas."""
    autor      = ComentarioAutorSerializer(read_only=True)
    respuestas = RespuestaSerializer(many=True, read_only=True)
    menciones  = ComentarioAutorSerializer(many=True, read_only=True)

    class Meta:
        model  = Comentario
        fields = [
            'id', 'autor',
            'texto', 'editado', 'editado_en',
            'padre',
            'respuestas', 'menciones',
            'created_at',
        ]
        read_only_fields = [
            'id', 'autor', 'editado', 'editado_en',
            'respuestas', 'menciones', 'created_at',
        ]


class ComentarioCreateSerializer(serializers.Serializer):
    """Serializer de escritura para crear un comentario."""
    content_type_model = serializers.CharField(
        help_text='Nombre del modelo al que pertenece el comentario. Ej: tarea',
    )
    object_id  = serializers.UUIDField()
    texto      = serializers.CharField(min_length=1, max_length=5000)
    padre      = serializers.UUIDField(required=False, allow_null=True, default=None)

    def validate_content_type_model(self, value: str) -> str:
        if not ContentType.objects.filter(model=value.lower()).exists():
            raise serializers.ValidationError(f'Modelo "{value}" no encontrado.')
        return value.lower()

    def validate(self, data):
        # Verificar que el padre pertenece al mismo objeto
        if data.get('padre'):
            try:
                padre = Comentario.objects.get(id=data['padre'])
            except Comentario.DoesNotExist:
                raise serializers.ValidationError({'padre': 'Comentario padre no encontrado.'})
            ct = ContentType.objects.get(model=data['content_type_model'])
            if padre.content_type_id != ct.id or str(padre.object_id) != str(data['object_id']):
                raise serializers.ValidationError(
                    {'padre': 'El comentario padre no pertenece al mismo objeto.'}
                )
            data['padre_obj'] = padre
        return data


class ComentarioEditSerializer(serializers.Serializer):
    """Serializer de escritura para editar el texto de un comentario."""
    texto = serializers.CharField(min_length=1, max_length=5000)


class PreferenciaNotificacionSerializer(serializers.ModelSerializer):
    tipo_display      = serializers.CharField(source='get_tipo_display', read_only=True)
    frecuencia_display = serializers.CharField(source='get_frecuencia_display', read_only=True)

    class Meta:
        model  = PreferenciaNotificacion
        fields = [
            'id', 'tipo', 'tipo_display',
            'habilitado_app', 'habilitado_email', 'habilitado_push',
            'frecuencia', 'frecuencia_display',
            'agrupar', 'sonido_habilitado',
            'updated_at',
        ]
        read_only_fields = ['id', 'tipo', 'tipo_display', 'frecuencia_display', 'updated_at']


class NoLeidasCountSerializer(serializers.Serializer):
    """Respuesta del endpoint de conteo de no leídas."""
    count = serializers.IntegerField()
