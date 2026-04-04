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
    """Serializer de lectura para DashboardCard."""
    class Meta:
        model = DashboardCard
        fields = [
            'id', 'card_type_code', 'chart_type',
            'pos_x', 'pos_y', 'width', 'height',
            'filtros_config', 'titulo_personalizado', 'orden',
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


class DashboardCardUpdateSerializer(serializers.Serializer):
    """Serializer de escritura para actualizar una tarjeta."""
    chart_type = serializers.CharField(max_length=20, required=False)
    pos_x = serializers.IntegerField(required=False)
    pos_y = serializers.IntegerField(required=False)
    width = serializers.IntegerField(required=False)
    height = serializers.IntegerField(required=False)
    filtros_config = serializers.DictField(required=False)
    titulo_personalizado = serializers.CharField(max_length=100, required=False)
    orden = serializers.IntegerField(required=False)


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
    descripcion = serializers.CharField(required=False, default='')
    es_privado = serializers.BooleanField(default=True)
    orientacion = serializers.ChoiceField(
        choices=Dashboard.Orientacion.choices,
        default='portrait',
    )


class DashboardUpdateSerializer(serializers.Serializer):
    """Serializer de escritura para actualizar un dashboard."""
    titulo = serializers.CharField(max_length=120, required=False)
    descripcion = serializers.CharField(required=False)
    es_privado = serializers.BooleanField(required=False)
    orientacion = serializers.ChoiceField(
        choices=Dashboard.Orientacion.choices,
        required=False,
    )


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
