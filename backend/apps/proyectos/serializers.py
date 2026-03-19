"""
SaiSuite — Proyectos: Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
import logging
from decimal import Decimal
from rest_framework import serializers
from apps.proyectos.models import (
    Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito,
    TipoProyecto, EstadoProyecto, RolTercero, TipoDocumento,
    Actividad, ActividadProyecto, TipoActividad,
)

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
    codigo          = serializers.CharField(max_length=50, required=False, allow_blank=True)
    gerente         = serializers.UUIDField()
    coordinador     = serializers.UUIDField(required=False, allow_null=True)
    # consecutivo_id: UUID del ConfiguracionConsecutivo a usar para generar el código
    consecutivo_id  = serializers.UUIDField(required=False, allow_null=True, write_only=True)

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
            'consecutivo_id',
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


# ──────────────────────────────────────────────
# Fase B: TerceroProyecto
# ──────────────────────────────────────────────

class TerceroProyectoSerializer(serializers.ModelSerializer):
    """Serializer de lectura y escritura para terceros vinculados al proyecto."""
    rol_display  = serializers.CharField(source='get_rol_display', read_only=True)
    fase_nombre  = serializers.CharField(source='fase.nombre', read_only=True, default=None)

    class Meta:
        model  = TerceroProyecto
        fields = [
            'id', 'proyecto', 'tercero_id', 'tercero_nombre',
            'rol', 'rol_display', 'fase', 'fase_nombre', 'activo',
            'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at']


class TerceroProyectoCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para vincular un tercero al proyecto."""

    class Meta:
        model  = TerceroProyecto
        fields = ['tercero_id', 'tercero_nombre', 'rol', 'fase']

    def validate_fase(self, fase):
        """La fase debe pertenecer al mismo proyecto."""
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase


# ──────────────────────────────────────────────
# Fase B: DocumentoContable
# ──────────────────────────────────────────────

class DocumentoContableListSerializer(serializers.ModelSerializer):
    """Serializer de listado de documentos contables — campos mínimos."""
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', read_only=True
    )

    class Meta:
        model  = DocumentoContable
        fields = [
            'id', 'tipo_documento', 'tipo_documento_display',
            'numero_documento', 'fecha_documento',
            'tercero_nombre', 'valor_neto',
            'sincronizado_desde_saiopen',
        ]
        read_only_fields = fields


class DocumentoContableDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de documento contable — todos los campos."""
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', read_only=True
    )

    class Meta:
        model  = DocumentoContable
        fields = [
            'id', 'proyecto', 'fase',
            'saiopen_doc_id', 'tipo_documento', 'tipo_documento_display',
            'numero_documento', 'fecha_documento',
            'tercero_id', 'tercero_nombre',
            'valor_bruto', 'valor_descuento', 'valor_neto',
            'observaciones', 'sincronizado_desde_saiopen',
        ]
        read_only_fields = fields


# ──────────────────────────────────────────────
# Fase B: Hito
# ──────────────────────────────────────────────

class HitoSerializer(serializers.ModelSerializer):
    """Serializer de lectura para hitos del proyecto."""
    fase_nombre = serializers.CharField(source='fase.nombre', read_only=True, default=None)

    class Meta:
        model  = Hito
        fields = [
            'id', 'proyecto', 'fase', 'fase_nombre',
            'nombre', 'descripcion',
            'porcentaje_proyecto', 'valor_facturar',
            'facturable', 'facturado',
            'documento_factura', 'fecha_facturacion',
            'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'facturado', 'documento_factura', 'fecha_facturacion', 'created_at']


class HitoCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para crear un hito."""

    class Meta:
        model  = Hito
        fields = ['nombre', 'descripcion', 'fase', 'porcentaje_proyecto', 'valor_facturar', 'facturable']

    def validate_porcentaje_proyecto(self, value):
        if not (Decimal('0') < value <= Decimal('100')):
            raise serializers.ValidationError(
                'El porcentaje debe ser mayor a 0 y máximo 100.'
            )
        return value

    def validate_valor_facturar(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError(
                'El valor a facturar debe ser mayor a cero.'
            )
        return value

    def validate_fase(self, fase):
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase


class GenerarFacturaSerializer(serializers.Serializer):
    """Serializer para la acción de generar factura desde un hito."""
    confirmar = serializers.BooleanField(
        help_text='Debe ser true para confirmar la solicitud de facturación.'
    )

    def validate_confirmar(self, value):
        if not value:
            raise serializers.ValidationError(
                'Debe confirmar la solicitud de facturación.'
            )
        return value


# ──────────────────────────────────────────────
# Actividades — catálogo global
# ──────────────────────────────────────────────

class ActividadListSerializer(serializers.ModelSerializer):
    """Serializer de listado de actividades — campos mínimos para tabla."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Actividad
        fields = [
            'id', 'codigo', 'nombre', 'tipo', 'tipo_display',
            'unidad_medida', 'costo_unitario_base', 'activo', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ActividadDetailSerializer(serializers.ModelSerializer):
    """Serializer de detalle de actividad — todos los campos."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Actividad
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'tipo', 'tipo_display', 'unidad_medida', 'costo_unitario_base',
            'saiopen_actividad_id', 'sincronizado_con_saiopen',
            'activo', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ActividadCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para el catálogo de actividades."""
    codigo         = serializers.CharField(max_length=50, required=False, allow_blank=True)
    # consecutivo_id: UUID del ConfiguracionConsecutivo a usar para generar el código
    consecutivo_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Actividad
        fields = [
            'codigo', 'nombre', 'descripcion',
            'tipo', 'unidad_medida', 'costo_unitario_base',
            'consecutivo_id',
        ]

    def validate_costo_unitario_base(self, value):
        from decimal import Decimal
        if value < Decimal('0'):
            raise serializers.ValidationError('El costo unitario no puede ser negativo.')
        return value


# ──────────────────────────────────────────────
# Actividades — asignación a proyecto
# ──────────────────────────────────────────────

class ActividadProyectoSerializer(serializers.ModelSerializer):
    """Serializer de lectura para actividades asignadas a un proyecto."""
    actividad_codigo       = serializers.CharField(source='actividad.codigo', read_only=True)
    actividad_nombre       = serializers.CharField(source='actividad.nombre', read_only=True)
    actividad_unidad_medida = serializers.CharField(source='actividad.unidad_medida', read_only=True)
    actividad_tipo         = serializers.CharField(source='actividad.tipo', read_only=True)
    fase_nombre            = serializers.CharField(source='fase.nombre', read_only=True, default=None)
    presupuesto_total      = serializers.SerializerMethodField()

    class Meta:
        model  = ActividadProyecto
        fields = [
            'id', 'proyecto', 'actividad',
            'actividad_codigo', 'actividad_nombre',
            'actividad_unidad_medida', 'actividad_tipo',
            'fase', 'fase_nombre',
            'cantidad_planificada', 'cantidad_ejecutada',
            'costo_unitario', 'presupuesto_total',
            'porcentaje_avance', 'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at']

    def get_presupuesto_total(self, obj: ActividadProyecto) -> str:
        return str(obj.presupuesto_total)


class ActividadProyectoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para asignar/actualizar actividades en un proyecto."""

    class Meta:
        model  = ActividadProyecto
        fields = [
            'actividad', 'fase',
            'cantidad_planificada', 'cantidad_ejecutada',
            'costo_unitario', 'porcentaje_avance',
        ]

    def validate_fase(self, fase):
        """La fase debe pertenecer al mismo proyecto."""
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase

    def validate_porcentaje_avance(self, value):
        from decimal import Decimal
        if not (Decimal('0') <= value <= Decimal('100')):
            raise serializers.ValidationError(
                'El porcentaje de avance debe estar entre 0 y 100.'
            )
        return value

    def validate_cantidad_planificada(self, value):
        from decimal import Decimal
        if value < Decimal('0'):
            raise serializers.ValidationError('La cantidad no puede ser negativa.')
        return value
