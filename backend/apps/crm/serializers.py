"""
SaiSuite — CRM Serializers
Solo transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers
from .models import (
    CrmPipeline, CrmEtapa, CrmLead, CrmLeadScoringRule,
    CrmOportunidad, CrmActividad, CrmTimelineEvent,
)


class UserMinSerializer(serializers.Serializer):
    id        = serializers.UUIDField()
    email     = serializers.EmailField()
    full_name = serializers.CharField()


class CrmEtapaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CrmEtapa
        fields = ['id', 'nombre', 'orden', 'probabilidad', 'es_ganado', 'es_perdido', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']


class CrmEtapaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CrmEtapa
        fields = ['nombre', 'orden', 'probabilidad', 'es_ganado', 'es_perdido', 'color']


class CrmPipelineListSerializer(serializers.ModelSerializer):
    etapas = CrmEtapaSerializer(many=True, read_only=True)

    class Meta:
        model  = CrmPipeline
        fields = ['id', 'nombre', 'descripcion', 'es_default', 'etapas', 'created_at']
        read_only_fields = ['id', 'created_at']


class CrmPipelineDetailSerializer(serializers.ModelSerializer):
    etapas = CrmEtapaSerializer(many=True, read_only=True)

    class Meta:
        model  = CrmPipeline
        fields = ['id', 'nombre', 'descripcion', 'es_default', 'etapas', 'created_at']
        read_only_fields = ['id', 'created_at']


class CrmPipelineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CrmPipeline
        fields = ['nombre', 'descripcion', 'es_default']


# ── LEADS ─────────────────────────────────────

class CrmLeadListSerializer(serializers.ModelSerializer):
    asignado_a       = UserMinSerializer(read_only=True)
    asignado_a_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = CrmLead
        fields = [
            'id', 'nombre', 'empresa', 'email', 'telefono', 'cargo',
            'fuente', 'score', 'convertido', 'asignado_a', 'asignado_a_nombre', 'created_at',
        ]
        read_only_fields = ['id', 'score', 'convertido', 'created_at']

    def get_asignado_a_nombre(self, obj):
        if obj.asignado_a_id:
            return getattr(obj.asignado_a, 'full_name', None) or obj.asignado_a.email
        return None


class CrmLeadDetailSerializer(serializers.ModelSerializer):
    asignado_a        = UserMinSerializer(read_only=True)
    asignado_a_nombre = serializers.SerializerMethodField()
    pipeline          = CrmPipelineListSerializer(read_only=True)

    class Meta:
        model  = CrmLead
        fields = [
            'id', 'nombre', 'empresa', 'email', 'telefono', 'cargo',
            'fuente', 'notas', 'score', 'pipeline', 'asignado_a', 'asignado_a_nombre',
            'convertido', 'convertido_en', 'oportunidad', 'tercero',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'score', 'convertido', 'convertido_en', 'oportunidad', 'created_at', 'updated_at']

    def get_asignado_a_nombre(self, obj):
        if obj.asignado_a_id:
            return getattr(obj.asignado_a, 'full_name', None) or obj.asignado_a.email
        return None


class CrmLeadCreateSerializer(serializers.ModelSerializer):
    pipeline_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model  = CrmLead
        fields = ['nombre', 'empresa', 'email', 'telefono', 'cargo', 'fuente', 'notas', 'pipeline_id']


class CrmLeadConvertirSerializer(serializers.Serializer):
    etapa_id               = serializers.UUIDField()
    valor_esperado         = serializers.DecimalField(max_digits=15, decimal_places=2, default=0)
    fecha_cierre_estimada  = serializers.DateField(required=False, allow_null=True)
    tercero_id             = serializers.UUIDField(required=False, allow_null=True)
    crear_tercero          = serializers.BooleanField(default=False)
    asignado_a_id          = serializers.UUIDField(required=False, allow_null=True)


class CrmLeadScoringRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CrmLeadScoringRule
        fields = ['id', 'nombre', 'campo', 'operador', 'valor', 'puntos', 'orden', 'created_at']
        read_only_fields = ['id', 'created_at']


# ── OPORTUNIDADES ─────────────────────────────

class CrmOportunidadCardSerializer(serializers.ModelSerializer):
    """Serializer compacto para tarjetas Kanban."""
    contacto_nombre         = serializers.CharField(source='contacto.nombre_completo', read_only=True, default='')
    etapa_nombre            = serializers.CharField(source='etapa.nombre', read_only=True)
    asignado_nombre         = serializers.SerializerMethodField()
    valor_ponderado         = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model  = CrmOportunidad
        fields = [
            'id', 'titulo', 'contacto_nombre', 'etapa_nombre', 'etapa',
            'valor_esperado', 'valor_ponderado', 'probabilidad',
            'fecha_cierre_estimada', 'asignado_nombre',
            'proxima_actividad_fecha', 'proxima_actividad_tipo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_asignado_nombre(self, obj):
        if obj.asignado_a:
            return getattr(obj.asignado_a, 'full_name', obj.asignado_a.email)
        return None


class CrmOportunidadListSerializer(serializers.ModelSerializer):
    contacto_nombre = serializers.CharField(source='contacto.nombre_completo', read_only=True, default='')
    etapa_nombre    = serializers.CharField(source='etapa.nombre', read_only=True)
    pipeline_nombre = serializers.CharField(source='pipeline.nombre', read_only=True)
    asignado_a      = UserMinSerializer(read_only=True)

    class Meta:
        model  = CrmOportunidad
        fields = [
            'id', 'titulo', 'contacto', 'contacto_nombre', 'pipeline', 'pipeline_nombre',
            'etapa', 'etapa_nombre', 'valor_esperado', 'probabilidad',
            'fecha_cierre_estimada', 'asignado_a', 'ganada_en', 'perdida_en',
            'proxima_actividad_fecha', 'proxima_actividad_tipo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CrmOportunidadDetailSerializer(serializers.ModelSerializer):
    asignado_a      = UserMinSerializer(read_only=True)
    etapa_detalle   = CrmEtapaSerializer(source='etapa', read_only=True)
    pipeline_detalle = CrmPipelineListSerializer(source='pipeline', read_only=True)

    class Meta:
        model  = CrmOportunidad
        fields = [
            'id', 'titulo', 'contacto', 'pipeline', 'pipeline_detalle',
            'etapa', 'etapa_detalle', 'valor_esperado', 'probabilidad',
            'fecha_cierre_estimada', 'asignado_a', 'descripcion',
            'ganada_en', 'perdida_en', 'motivo_perdida',
            'proxima_actividad_fecha', 'proxima_actividad_tipo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'ganada_en', 'perdida_en', 'created_at', 'updated_at']


class CrmOportunidadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CrmOportunidad
        fields = [
            'titulo', 'contacto', 'pipeline', 'etapa',
            'valor_esperado', 'probabilidad', 'fecha_cierre_estimada',
            'asignado_a', 'descripcion',
        ]


class CrmMoverEtapaSerializer(serializers.Serializer):
    etapa_id = serializers.UUIDField()


class CrmPerderSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=200)


class CrmEnviarEmailSerializer(serializers.Serializer):
    asunto = serializers.CharField(max_length=200)
    cuerpo = serializers.CharField()


# ── ACTIVIDADES ───────────────────────────────

class CrmActividadSerializer(serializers.ModelSerializer):
    asignado_a       = serializers.UUIDField(source='asignado_a.id', read_only=True, default=None)
    asignado_a_nombre = serializers.SerializerMethodField()
    tipo_display     = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = CrmActividad
        fields = [
            'id', 'oportunidad', 'lead', 'tipo', 'tipo_display', 'titulo', 'descripcion',
            'fecha_programada', 'completada', 'completada_en',
            'asignado_a', 'asignado_a_nombre', 'resultado', 'created_at',
        ]
        read_only_fields = ['id', 'oportunidad', 'lead', 'completada', 'completada_en', 'created_at']

    def get_asignado_a_nombre(self, obj):
        if obj.asignado_a_id:
            user = obj.asignado_a
            return getattr(user, 'full_name', None) or user.email
        return None


class CrmActividadCreateSerializer(serializers.ModelSerializer):
    asignado_a_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model  = CrmActividad
        fields = ['tipo', 'titulo', 'descripcion', 'fecha_programada', 'asignado_a_id']


class CrmCompletarActividadSerializer(serializers.Serializer):
    resultado = serializers.CharField(required=False, allow_blank=True, default='')


# ── TIMELINE ──────────────────────────────────

class CrmTimelineEventSerializer(serializers.ModelSerializer):
    usuario     = UserMinSerializer(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = CrmTimelineEvent
        fields = ['id', 'tipo', 'tipo_display', 'descripcion', 'usuario', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']


class CrmNotaSerializer(serializers.Serializer):
    nota = serializers.CharField()


# ── KANBAN ────────────────────────────────────

class CrmKanbanEtapaSerializer(serializers.Serializer):
    etapa_id       = serializers.UUIDField(source='etapa.id')
    etapa_nombre   = serializers.CharField(source='etapa.nombre')
    color          = serializers.CharField(source='etapa.color', allow_null=True, default=None)
    probabilidad   = serializers.DecimalField(source='etapa.probabilidad', max_digits=5, decimal_places=2)
    es_ganado      = serializers.BooleanField(source='etapa.es_ganado')
    es_perdido     = serializers.BooleanField(source='etapa.es_perdido')
    oportunidades  = CrmOportunidadCardSerializer(many=True)
    total_valor    = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_count    = serializers.IntegerField()


class CrmActividadAgendaSerializer(CrmActividadSerializer):
    """Extiende CrmActividadSerializer con contexto del recurso relacionado."""
    contexto_nombre = serializers.SerializerMethodField()
    contexto_tipo   = serializers.SerializerMethodField()

    class Meta(CrmActividadSerializer.Meta):
        fields = CrmActividadSerializer.Meta.fields + ['contexto_nombre', 'contexto_tipo']

    def get_contexto_nombre(self, obj):
        if obj.oportunidad_id:
            return obj.oportunidad.titulo
        if obj.lead_id:
            return obj.lead.nombre
        return None

    def get_contexto_tipo(self, obj):
        if obj.oportunidad_id:
            return 'oportunidad'
        if obj.lead_id:
            return 'lead'
        return None


class CrmReordenarEtapasSerializer(serializers.Serializer):
    orden = serializers.ListField(child=serializers.UUIDField(), min_length=1)
