"""
SaiSuite -- Dashboard: Serializers
Los serializers SOLO transforman datos. Sin logica de negocio.
"""
import logging
from rest_framework import serializers

from apps.dashboard.models import (
    Dashboard,
    DashboardCard,
    DashboardShare,
    ModuleTrial,
    ReportBI,
    ReportBIShare,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# User Summary (reusable)
# ──────────────────────────────────────────────

class UserSummarySerializer(serializers.Serializer):
    """Representacion minima del usuario para lectura."""
    id = serializers.UUIDField()
    email = serializers.EmailField()
    full_name = serializers.CharField()


# ──────────────────────────────────────────────
# Dashboard Card
# ──────────────────────────────────────────────

class DashboardCardSerializer(serializers.ModelSerializer):
    """Serializer de lectura para DashboardCard. Incluye campos bi_report para tarjetas BI."""
    bi_report_id = serializers.UUIDField(
        source='bi_report.id', read_only=True, allow_null=True,
    )
    bi_report_titulo = serializers.CharField(
        source='bi_report.titulo', read_only=True, allow_null=True,
    )
    bi_report_tipo_visualizacion = serializers.CharField(
        source='bi_report.tipo_visualizacion', read_only=True, allow_null=True,
    )
    bi_report_campos_config = serializers.JSONField(
        source='bi_report.campos_config', read_only=True, allow_null=True,
    )

    class Meta:
        model = DashboardCard
        fields = [
            'id', 'card_type_code', 'chart_type',
            'pos_x', 'pos_y', 'width', 'height',
            'filtros_config', 'titulo_personalizado', 'orden',
            'bi_report_id', 'bi_report_titulo',
            'bi_report_tipo_visualizacion', 'bi_report_campos_config',
        ]
        read_only_fields = ['id']


class DashboardCardCreateSerializer(serializers.Serializer):
    """Serializer de escritura para agregar una tarjeta al dashboard."""
    card_type_code = serializers.CharField(max_length=50)
    chart_type = serializers.CharField(max_length=20, default='bar')
    pos_x = serializers.IntegerField(default=0)
    pos_y = serializers.IntegerField(default=0)
    width = serializers.IntegerField(default=2)
    height = serializers.IntegerField(default=2)
    filtros_config = serializers.DictField(required=False, default=dict)
    titulo_personalizado = serializers.CharField(max_length=100, required=False, default='')
    orden = serializers.IntegerField(default=0)
    # Solo para card_type_code='bi_report'
    bi_report_id = serializers.UUIDField(required=False, allow_null=True)


class DashboardCardUpdateSerializer(serializers.Serializer):
    """Serializer de escritura para actualizar una tarjeta."""
    chart_type = serializers.CharField(max_length=20, required=False, allow_blank=True)
    pos_x = serializers.IntegerField(required=False)
    pos_y = serializers.IntegerField(required=False)
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    filtros_config = serializers.DictField(required=False)
    titulo_personalizado = serializers.CharField(max_length=100, required=False, allow_blank=True)
    orden = serializers.IntegerField(required=False)
    bi_report_id = serializers.UUIDField(required=False, allow_null=True)


class CardLayoutItemSerializer(serializers.Serializer):
    """Un item del layout para save_layout masivo."""
    id = serializers.IntegerField()
    pos_x = serializers.IntegerField()
    pos_y = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    orden = serializers.IntegerField(default=0)


class CardLayoutSerializer(serializers.Serializer):
    """Serializer para guardar el layout completo de tarjetas."""
    layout = CardLayoutItemSerializer(many=True)


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

class DashboardListSerializer(serializers.ModelSerializer):
    """Serializer de listado de dashboards -- campos minimos."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            'id', 'titulo', 'descripcion', 'es_privado',
            'es_favorito', 'es_default', 'orientacion',
            'filtros_default',
            'user_email', 'card_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_card_count(self, obj) -> int:
        return obj.cards.count()


class DashboardDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de dashboard -- incluye tarjetas."""
    user = UserSummarySerializer(read_only=True)
    cards = DashboardCardSerializer(many=True, read_only=True)
    shares = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            'id', 'titulo', 'descripcion', 'es_privado',
            'es_favorito', 'es_default', 'orientacion',
            'filtros_default',
            'user', 'cards', 'shares',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_shares(self, obj) -> list:
        return [
            {
                'user_id': str(share.compartido_con_id),
                'email': share.compartido_con.email,
                'full_name': share.compartido_con.full_name,
                'puede_editar': share.puede_editar,
                'creado_en': share.creado_en.isoformat(),
            }
            for share in obj.shares.select_related('compartido_con').all()
        ]


class DashboardCreateSerializer(serializers.Serializer):
    """Serializer de escritura para crear un dashboard."""
    titulo = serializers.CharField(max_length=120)
    descripcion = serializers.CharField(required=False, default='', allow_blank=True)
    es_privado = serializers.BooleanField(default=True)
    orientacion = serializers.ChoiceField(
        choices=Dashboard.Orientacion.choices,
        default='portrait',
    )
    filtros_default = serializers.DictField(required=False, default=dict)


class DashboardUpdateSerializer(serializers.Serializer):
    """Serializer de escritura para actualizar un dashboard."""
    titulo = serializers.CharField(max_length=120, required=False)
    descripcion = serializers.CharField(required=False)
    es_privado = serializers.BooleanField(required=False)
    orientacion = serializers.ChoiceField(
        choices=Dashboard.Orientacion.choices,
        required=False,
    )
    filtros_default = serializers.DictField(required=False)


class DashboardSaveFiltersSerializer(serializers.Serializer):
    """Serializer para guardar filtros predeterminados de un dashboard."""
    filtros_default = serializers.DictField()


# ──────────────────────────────────────────────
# Share
# ──────────────────────────────────────────────

class DashboardShareSerializer(serializers.Serializer):
    """Serializer de lectura para DashboardShare."""
    user_id = serializers.UUIDField(source='compartido_con_id')
    email = serializers.CharField(source='compartido_con.email')
    full_name = serializers.CharField(source='compartido_con.full_name')
    puede_editar = serializers.BooleanField()
    creado_en = serializers.DateTimeField()


class DashboardShareCreateSerializer(serializers.Serializer):
    """Serializer de escritura para compartir un dashboard."""
    user_id = serializers.UUIDField()
    puede_editar = serializers.BooleanField(default=False)


# ──────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────

class CardDataRequestSerializer(serializers.Serializer):
    """Serializer para solicitar datos de una tarjeta."""
    card_type_code = serializers.CharField(max_length=50)
    filtros = serializers.DictField(required=False, default=dict)
    card_config = serializers.DictField(required=False, default=dict)


class CardDataResponseSerializer(serializers.Serializer):
    """Serializer de respuesta con datos para graficar."""
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())
    summary = serializers.DictField()


# ──────────────────────────────────────────────
# Trial
# ──────────────────────────────────────────────

class TrialStatusSerializer(serializers.Serializer):
    """Serializer de estado del trial."""
    tiene_acceso = serializers.BooleanField()
    tipo_acceso = serializers.CharField()
    dias_restantes = serializers.IntegerField(allow_null=True)
    expira_en = serializers.DateTimeField(allow_null=True)


class ModuleTrialSerializer(serializers.ModelSerializer):
    """Serializer de lectura para ModuleTrial."""
    esta_activo = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = ModuleTrial
        fields = [
            'module_code', 'iniciado_en', 'expira_en',
            'esta_activo', 'dias_restantes',
        ]

    def get_esta_activo(self, obj) -> bool:
        return obj.esta_activo()

    def get_dias_restantes(self, obj) -> int:
        return obj.dias_restantes()


# ──────────────────────────────────────────────
# Report BI
# ──────────────────────────────────────────────

class ReportBIListSerializer(serializers.ModelSerializer):
    """Serializer de listado de reportes BI -- campos mínimos."""
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ReportBI
        fields = [
            'id', 'titulo', 'es_privado',
            'es_favorito', 'es_template', 'fuentes',
            'tipo_visualizacion', 'categoria_galeria', 'user_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportBIDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de reporte BI -- incluye config completa."""
    user = UserSummarySerializer(read_only=True)
    shares = serializers.SerializerMethodField()

    class Meta:
        model = ReportBI
        fields = [
            'id', 'titulo', 'es_privado',
            'es_favorito', 'es_template', 'fuentes',
            'campos_config', 'tipo_visualizacion', 'viz_config',
            'filtros', 'orden_config', 'limite_registros',
            'template_origen', 'categoria_galeria', 'user', 'shares',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_shares(self, obj) -> list:
        return [
            {
                'user_id': str(share.compartido_con_id),
                'email': share.compartido_con.email,
                'full_name': share.compartido_con.full_name,
                'puede_editar': share.puede_editar,
                'creado_en': share.creado_en.isoformat(),
            }
            for share in obj.shares.select_related('compartido_con').all()
        ]


class ReportBICreateSerializer(serializers.Serializer):
    """Serializer de escritura para crear un reporte BI."""
    titulo = serializers.CharField(max_length=200)
    es_privado = serializers.BooleanField(default=True)
    es_template = serializers.BooleanField(required=False, default=False)
    fuentes = serializers.ListField(
        child=serializers.CharField(max_length=30),
        min_length=1,
    )
    campos_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )
    tipo_visualizacion = serializers.ChoiceField(
        choices=ReportBI.TipoVisualizacion.choices,
        default='table',
    )
    viz_config = serializers.DictField(required=False, default=dict)
    filtros = serializers.ListField(
        child=serializers.DictField(), required=False, default=list,
    )
    orden_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )
    limite_registros = serializers.IntegerField(required=False, allow_null=True)
    template_origen = serializers.UUIDField(required=False, allow_null=True)
    categoria_galeria = serializers.ChoiceField(
        choices=ReportBI.CategoriaGaleria.choices,
        required=False,
        allow_null=True,
    )


class ReportBIUpdateSerializer(serializers.Serializer):
    """Serializer de escritura para actualizar un reporte BI."""
    titulo = serializers.CharField(max_length=200, required=False)
    es_privado = serializers.BooleanField(required=False)
    es_favorito = serializers.BooleanField(required=False)
    es_template = serializers.BooleanField(required=False)
    fuentes = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=False,
    )
    campos_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
    tipo_visualizacion = serializers.ChoiceField(
        choices=ReportBI.TipoVisualizacion.choices,
        required=False,
    )
    viz_config = serializers.DictField(required=False)
    filtros = serializers.ListField(
        child=serializers.DictField(), required=False,
    )
    orden_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )
    limite_registros = serializers.IntegerField(required=False, allow_null=True)
    categoria_galeria = serializers.ChoiceField(
        choices=ReportBI.CategoriaGaleria.choices,
        required=False,
        allow_null=True,
    )


class ReportBIExecuteSerializer(serializers.Serializer):
    """Serializer para ejecutar un reporte (preview o guardado)."""
    fuentes = serializers.ListField(
        child=serializers.CharField(max_length=30),
        min_length=1,
    )
    campos_config = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )
    tipo_visualizacion = serializers.ChoiceField(
        choices=ReportBI.TipoVisualizacion.choices,
        default='table',
    )
    viz_config = serializers.DictField(required=False, default=dict)
    filtros = serializers.ListField(
        child=serializers.DictField(), required=False, default=list,
    )
    orden_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )
    limite_registros = serializers.IntegerField(required=False, allow_null=True)


class ReportBIShareCreateSerializer(serializers.Serializer):
    """Serializer para compartir un reporte BI."""
    user_id = serializers.UUIDField()
    puede_editar = serializers.BooleanField(default=False)


# ── Sprint 4: bi_report cards ─────────────────────────────────────────────────


class BiCardExecuteRequestSerializer(serializers.Serializer):
    """Serializer para ejecutar una tarjeta de tipo bi_report con filtros de dashboard."""
    dashboard_filters = serializers.DictField(required=False, default=dict)


class BiSelectableReportSerializer(serializers.ModelSerializer):
    """Serializer para reportes BI seleccionables como tarjetas de dashboard."""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = ReportBI
        fields = [
            'id', 'titulo',
            'tipo_visualizacion', 'fuentes',
            'es_favorito', 'user_email',
        ]
