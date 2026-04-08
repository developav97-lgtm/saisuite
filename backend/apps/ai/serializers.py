"""
SaiSuite — AI: Serializers
Serializers para Knowledge Base y feedback de IA.
Regla: los serializers solo transforman datos, no tienen lógica de negocio.
"""
from rest_framework import serializers

from apps.ai.models import AIFeedback, KnowledgeSource


class KnowledgeSourceListSerializer(serializers.ModelSerializer):
    """Serializer de lista para fuentes de conocimiento."""

    class Meta:
        model = KnowledgeSource
        fields = [
            'id',
            'file_name',
            'source_channel',
            'original_format',
            'module',
            'category',
            'chunk_count',
            'total_tokens',
            'last_indexed_at',
            'created_at',
        ]


class KnowledgeUploadSerializer(serializers.Serializer):
    """Serializer para subir un archivo al knowledge base via panel admin."""
    file = serializers.FileField()
    module = serializers.CharField(max_length=50, required=False, default='')
    category = serializers.CharField(max_length=30, required=False, default='')


class KnowledgeIngestSerializer(serializers.Serializer):
    """Serializer para ingesta via n8n (webhook)."""
    file = serializers.FileField()
    file_name = serializers.CharField(max_length=255)
    module = serializers.CharField(max_length=50, required=False, default='')
    category = serializers.CharField(max_length=30, required=False, default='')
    drive_file_id = serializers.CharField(max_length=255, required=False, default='')


class KnowledgeIngestResultSerializer(serializers.Serializer):
    """Serializer de respuesta para operaciones de ingesta."""
    chunks_created = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    file_name = serializers.CharField()
    status = serializers.CharField()
    is_update = serializers.BooleanField()


class AIFeedbackCreateSerializer(serializers.Serializer):
    """Serializer para crear feedback sobre respuestas de IA."""
    mensaje_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=-1, max_value=1)

    def validate_rating(self, value):
        if value == 0:
            raise serializers.ValidationError('El rating debe ser 1 (positivo) o -1 (negativo).')
        return value


class AIFeedbackSerializer(serializers.ModelSerializer):
    """Serializer de lectura para feedback de IA."""

    class Meta:
        model = AIFeedback
        fields = [
            'id',
            'rating',
            'module_context',
            'question',
            'answer',
            'created_at',
        ]
