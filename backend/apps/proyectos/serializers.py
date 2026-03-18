"""
SaiSuite — Proyectos: Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
import logging
from decimal import Decimal
from rest_framework import serializers
from apps.proyectos.models import Proyecto, Fase, TipoProyecto, EstadoProyecto

logger = logging.getLogger(__name__)


class UserSummarySerializer(serializers.Serializer):
    """Representación mínima del usuario para lectura en proyectos."""
    id         = serializers.UUIDField()
    email      = serializers.EmailField()
    full_name  = serializers.CharField()


class FaseListSerializer(serializers.ModelSerializer):
    """Serializer de listado de fases — campos mínimos."""
    presupuesto_total = serializers.SerializerMethodField()

    class Meta:
        model  = Fase
        fields = [
            'id', 'nombre', 'orden', 'porcentaje_avance',
            'presupuesto_total', 'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_presupuesto_total(self, obj: Fase) -> str:
        total = (
            obj.presupuesto_mano_obra
            + obj.presupuesto_materiales
            + obj.presupuesto_subcontratos
            + obj.presupuesto_equipos
            + obj.presupuesto_otros
        )
        return str(total)


class FaseDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de fase — todos los campos."""
    presupuesto_total = serializers.SerializerMethodField()

    class Meta:
        model  = Fase
        fields = [
            'id', 'proyecto', 'nombre', 'descripcion', 'orden',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_mano_obra', 'presupuesto_materiales',
            'presupuesto_subcontratos', 'presupuesto_equipos',
            'presupuesto_otros', 'presupuesto_total',
            'porcentaje_avance', 'activo',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at', 'updated_at']

    def get_presupuesto_total(self, obj: Fase) -> str:
        total = (
            obj.presupuesto_mano_obra
            + obj.presupuesto_materiales
            + obj.presupuesto_subcontratos
            + obj.presupuesto_equipos
            + obj.presupuesto_otros
        )
        return str(total)


class FaseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para fases."""

    class Meta:
        model  = Fase
        fields = [
            'nombre', 'descripcion', 'orden',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_mano_obra', 'presupuesto_materiales',
            'presupuesto_subcontratos', 'presupuesto_equipos',
            'presupuesto_otros', 'porcentaje_avance',
        ]

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio_planificada')
        fin    = attrs.get('fecha_fin_planificada')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {'fecha_fin_planificada': 'La fecha de fin no puede ser anterior a la fecha de inicio.'}
            )
        avance = attrs.get('porcentaje_avance')
        if avance is not None and not (Decimal('0') <= avance <= Decimal('100')):
            raise serializers.ValidationError(
                {'porcentaje_avance': 'El porcentaje de avance debe estar entre 0 y 100.'}
            )
        return attrs


class ProyectoListSerializer(serializers.ModelSerializer):
    """Serializer de listado de proyectos — campos mínimos para tabla."""
    gerente = UserSummarySerializer(read_only=True)

    class Meta:
        model  = Proyecto
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'estado',
            'cliente_nombre', 'gerente',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'presupuesto_total', 'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProyectoDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de proyecto — todos los campos."""
    gerente             = UserSummarySerializer(read_only=True)
    coordinador         = UserSummarySerializer(read_only=True)
    fases_count         = serializers.SerializerMethodField()
    presupuesto_fases_total = serializers.SerializerMethodField()

    class Meta:
        model  = Proyecto
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'estado',
            'cliente_id', 'cliente_nombre',
            'gerente', 'coordinador',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_total',
            'porcentaje_administracion', 'porcentaje_imprevistos', 'porcentaje_utilidad',
            'saiopen_proyecto_id', 'sincronizado_con_saiopen', 'ultima_sincronizacion',
            'activo', 'fases_count', 'presupuesto_fases_total',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_fases_count(self, obj: Proyecto) -> int:
        return obj.fases.filter(activo=True).count()

    def get_presupuesto_fases_total(self, obj: Proyecto) -> str:
        from django.db.models import Sum
        result = obj.fases.filter(activo=True).aggregate(
            total=Sum('presupuesto_mano_obra')
                + Sum('presupuesto_materiales')
                + Sum('presupuesto_subcontratos')
                + Sum('presupuesto_equipos')
                + Sum('presupuesto_otros')
        )
        total = result.get('total') or Decimal('0')
        return str(total)


class ProyectoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para proyectos."""
    # codigo es opcional — el service lo genera automáticamente si no se provee
    codigo      = serializers.CharField(max_length=50, required=False, allow_blank=True)
    gerente     = serializers.UUIDField()
    coordinador = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model  = Proyecto
        fields = [
            'codigo', 'nombre', 'tipo',
            'cliente_id', 'cliente_nombre',
            'gerente', 'coordinador',
            'fecha_inicio_planificada', 'fecha_fin_planificada',
            'fecha_inicio_real', 'fecha_fin_real',
            'presupuesto_total',
            'porcentaje_administracion', 'porcentaje_imprevistos', 'porcentaje_utilidad',
        ]

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio_planificada')
        fin    = attrs.get('fecha_fin_planificada')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {'fecha_fin_planificada': 'La fecha de fin no puede ser anterior a la fecha de inicio.'}
            )
        presupuesto = attrs.get('presupuesto_total', Decimal('0'))
        if presupuesto < Decimal('0'):
            raise serializers.ValidationError(
                {'presupuesto_total': 'El presupuesto total no puede ser negativo.'}
            )
        return attrs


class CambiarEstadoSerializer(serializers.Serializer):
    """Serializer para la acción de cambio de estado del proyecto."""
    nuevo_estado = serializers.ChoiceField(choices=EstadoProyecto.choices)
    forzar       = serializers.BooleanField(
        default=False,
        required=False,
        help_text='Permite cerrar proyecto con fases incompletas (requiere company_admin)',
    )
