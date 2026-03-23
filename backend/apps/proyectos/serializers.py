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
    Actividad, ActividadProyecto, TipoActividad, ConfiguracionModulo,
    Tarea, TareaTag, SesionTrabajo,
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

    def validate_porcentaje_avance(self, value):
        if not (Decimal('0') <= value <= Decimal('100')):
            raise serializers.ValidationError(
                'El porcentaje de avance debe estar entre 0 y 100.'
            )
        return value

    def validate(self, attrs):
        inicio = attrs.get('fecha_inicio_planificada')
        fin    = attrs.get('fecha_fin_planificada')
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {'fecha_fin_planificada': 'La fecha de fin no puede ser anterior a la fecha de inicio.'}
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
            'presupuesto_total', 'porcentaje_avance', 'activo', 'created_at',
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
            'presupuesto_total', 'porcentaje_avance',
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
    """Serializer de lectura para terceros vinculados al proyecto."""
    rol_display  = serializers.CharField(source='get_rol_display', read_only=True)
    fase_nombre  = serializers.CharField(source='fase.nombre', read_only=True, default=None)
    tercero_fk_nombre = serializers.CharField(
        source='tercero_fk.nombre_completo', read_only=True, default=None,
    )

    class Meta:
        model  = TerceroProyecto
        fields = [
            'id', 'proyecto', 'tercero_id', 'tercero_nombre',
            'rol', 'rol_display', 'fase', 'fase_nombre',
            'tercero_fk', 'tercero_fk_nombre',
            'activo', 'created_at',
        ]
        read_only_fields = ['id', 'proyecto', 'created_at', 'tercero_fk_nombre']


class TerceroProyectoCreateSerializer(serializers.ModelSerializer):
    """Serializer de escritura para vincular un tercero al proyecto."""

    class Meta:
        model  = TerceroProyecto
        fields = ['tercero_id', 'tercero_nombre', 'rol', 'fase', 'tercero_fk']

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
            'saiopen_doc_id', 'numero_documento', 'fecha_documento',
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
    """Serializer de escritura para asignar/actualizar actividades en un proyecto.
    porcentaje_avance es auto-calculado por señales — no se acepta en escritura.
    """

    class Meta:
        model  = ActividadProyecto
        fields = [
            'actividad', 'fase',
            'cantidad_planificada', 'cantidad_ejecutada',
            'costo_unitario',
        ]

    def validate_fase(self, fase):
        """La fase debe pertenecer al mismo proyecto."""
        proyecto = self.context.get('proyecto')
        if fase and proyecto and fase.proyecto_id != proyecto.id:
            raise serializers.ValidationError(
                'La fase debe pertenecer al mismo proyecto.'
            )
        return fase

    def validate_cantidad_planificada(self, value):
        from decimal import Decimal
        if value < Decimal('0'):
            raise serializers.ValidationError('La cantidad no puede ser negativa.')
        return value

    def validate(self, attrs):
        cantidad_ejecutada = attrs.get('cantidad_ejecutada')
        proyecto = self.context.get('proyecto')
        if (
            cantidad_ejecutada is not None
            and Decimal(str(cantidad_ejecutada)) > Decimal('0')
            and proyecto
            and proyecto.estado not in ('en_ejecucion', 'suspendido')
        ):
            raise serializers.ValidationError({
                'cantidad_ejecutada': (
                    'Solo se puede registrar cantidad ejecutada cuando el proyecto '
                    'está en ejecución o suspendido.'
                )
            })
        return attrs


# ──────────────────────────────────────────────
# Configuración del módulo
# ──────────────────────────────────────────────

class ConfiguracionModuloSerializer(serializers.ModelSerializer):
    """Serializer para la configuración del módulo de proyectos."""

    class Meta:
        model  = ConfiguracionModulo
        fields = [
            'requiere_sync_saiopen_para_ejecucion',
            'dias_alerta_vencimiento',
            'modo_timesheet',
        ]


# ──────────────────────────────────────────────
# Sistema de Tareas
# ──────────────────────────────────────────────

class TareaTagSerializer(serializers.ModelSerializer):
    """Serializer para tags de tareas."""

    class Meta:
        model = TareaTag
        fields = ['id', 'nombre', 'color', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TareaSerializer(serializers.ModelSerializer):
    """
    Serializer para Tarea con nested subtareas y followers.
    """

    # Campos calculados (read-only)
    es_vencida      = serializers.BooleanField(read_only=True)
    tiene_subtareas = serializers.BooleanField(read_only=True)
    nivel_jerarquia = serializers.IntegerField(read_only=True)

    # Nested serializers para lectura
    responsable_detail  = serializers.SerializerMethodField()
    proyecto_detail     = serializers.SerializerMethodField()
    fase_detail         = serializers.SerializerMethodField()
    cliente_detail      = serializers.SerializerMethodField()
    tags_detail         = TareaTagSerializer(source='tags', many=True, read_only=True)
    subtareas_detail    = serializers.SerializerMethodField()
    followers_detail    = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            'id', 'codigo', 'nombre', 'descripcion',
            'proyecto', 'proyecto_detail',
            'fase', 'fase_detail',
            'tarea_padre',
            'cliente', 'cliente_detail',
            'responsable', 'responsable_detail',
            'followers', 'followers_detail',
            'prioridad', 'tags', 'tags_detail',
            'fecha_inicio', 'fecha_fin', 'fecha_limite',
            'estado', 'porcentaje_completado',
            'horas_estimadas', 'horas_registradas',
            'es_recurrente', 'frecuencia_recurrencia', 'proxima_generacion',
            'es_vencida', 'tiene_subtareas', 'nivel_jerarquia',
            'subtareas_detail',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'codigo', 'es_vencida', 'tiene_subtareas',
            'nivel_jerarquia', 'created_at', 'updated_at',
        ]

    def get_cliente_detail(self, obj):
        if obj.cliente:
            return {
                'id': str(obj.cliente.id),
                'nombre': obj.cliente.nombre_completo,
                'numero_identificacion': obj.cliente.numero_identificacion,
            }
        return None

    def get_responsable_detail(self, obj):
        if obj.responsable:
            return {
                'id': str(obj.responsable.id),
                'nombre': obj.responsable.full_name,
                'email': obj.responsable.email,
            }
        return None

    def get_proyecto_detail(self, obj):
        return {
            'id': str(obj.proyecto.id),
            'nombre': obj.proyecto.nombre,
            'codigo': obj.proyecto.codigo,
        }

    def get_fase_detail(self, obj):
        if obj.fase:
            return {
                'id': str(obj.fase.id),
                'nombre': obj.fase.nombre,
                'orden': obj.fase.orden,
            }
        return None

    def get_followers_detail(self, obj):
        return [
            {
                'id': str(f.id),
                'nombre': f.full_name,
                'email': f.email,
            }
            for f in obj.followers.all()
        ]

    def get_subtareas_detail(self, obj):
        """Nested subtareas (máximo 2 niveles para performance)."""
        if obj.nivel_jerarquia >= 2:
            return []
        subtareas = obj.subtareas.all()
        return TareaSerializer(subtareas, many=True, context=self.context).data

    def validate(self, data):
        """Validaciones de negocio."""
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin    = data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_inicio >= fecha_fin:
            raise serializers.ValidationError({
                'fecha_fin': 'Fecha fin debe ser posterior a fecha inicio'
            })

        tarea_padre = data.get('tarea_padre')
        proyecto    = data.get('proyecto')
        if tarea_padre and proyecto and tarea_padre.proyecto_id != proyecto.id:
            raise serializers.ValidationError({
                'tarea_padre': 'Tarea padre debe pertenecer al mismo proyecto'
            })

        horas_estimadas   = data.get('horas_estimadas', 0)
        horas_registradas = data.get('horas_registradas', 0)
        if horas_estimadas and horas_registradas > horas_estimadas * 2:
            raise serializers.ValidationError({
                'horas_registradas': 'Horas registradas exceden significativamente las estimadas'
            })

        return data

    def create(self, validated_data):
        """Crear tarea y auto-agregar creador y responsable como followers."""
        followers = validated_data.pop('followers', [])
        tags      = validated_data.pop('tags', [])

        tarea = Tarea.all_objects.create(**validated_data)

        # Auto-agregar creador como follower
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            tarea.followers.add(request.user)

        # Auto-agregar responsable como follower
        if tarea.responsable:
            tarea.followers.add(tarea.responsable)

        # Agregar followers y tags adicionales
        if followers:
            tarea.followers.add(*followers)
        if tags:
            tarea.tags.set(tags)

        return tarea

    def update(self, instance, validated_data):
        followers = validated_data.pop('followers', None)
        tags      = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if followers is not None:
            instance.followers.set(followers)
        if tags is not None:
            instance.tags.set(tags)

        return instance


# ──────────────────────────────────────────────
# Timesheet — SesionTrabajo
# ──────────────────────────────────────────────

class SesionTrabajoSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de trabajo (cronómetro)."""
    duracion_horas = serializers.SerializerMethodField()
    usuario_detail = UserSummarySerializer(source='usuario', read_only=True)
    tarea_detail   = serializers.SerializerMethodField()

    class Meta:
        model = SesionTrabajo
        fields = [
            'id',
            'tarea', 'tarea_detail',
            'usuario', 'usuario_detail',
            'inicio', 'fin',
            'pausas',
            'duracion_segundos', 'duracion_horas',
            'estado', 'notas',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'duracion_segundos', 'duracion_horas',
            'created_at', 'updated_at',
        ]

    def get_duracion_horas(self, obj: SesionTrabajo) -> str:
        return str(obj.duracion_horas.quantize(Decimal('0.01')))

    def get_tarea_detail(self, obj: SesionTrabajo) -> dict:
        return {
            'id':     str(obj.tarea.id),
            'codigo': obj.tarea.codigo,
            'nombre': obj.tarea.nombre,
        }
