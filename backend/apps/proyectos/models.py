"""
SaiSuite — Módulo de Proyectos
Gestión de ejecución de proyectos complementando la imputación contable de Saiopen.
"""
import logging
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class TipoProyecto(models.TextChoices):
    OBRA_CIVIL        = 'obra_civil',        'Obra civil'
    CONSULTORIA       = 'consultoria',       'Consultoría'
    MANUFACTURA       = 'manufactura',       'Manufactura'
    SERVICIOS         = 'servicios',         'Servicios'
    LICITACION_PUBLICA = 'licitacion_publica', 'Licitación pública'
    OTRO              = 'otro',              'Otro'


class EstadoProyecto(models.TextChoices):
    BORRADOR     = 'borrador',     'Borrador'
    PLANIFICADO  = 'planificado',  'Planificado'
    EN_EJECUCION = 'en_ejecucion', 'En ejecución'
    SUSPENDIDO   = 'suspendido',   'Suspendido'
    CERRADO      = 'cerrado',      'Cerrado'
    CANCELADO    = 'cancelado',    'Cancelado'


class RolTercero(models.TextChoices):
    CLIENTE        = 'cliente',        'Cliente'
    SUBCONTRATISTA = 'subcontratista', 'Subcontratista'
    PROVEEDOR      = 'proveedor',      'Proveedor'
    CONSULTOR      = 'consultor',      'Consultor'
    INTERVENTOR    = 'interventor',    'Interventor'
    SUPERVISOR     = 'supervisor',     'Supervisor'


class TipoDocumento(models.TextChoices):
    FACTURA_VENTA      = 'factura_venta',      'Factura de venta'
    FACTURA_COMPRA     = 'factura_compra',      'Factura de compra'
    ORDEN_COMPRA       = 'orden_compra',        'Orden de compra'
    RECIBO_CAJA        = 'recibo_caja',         'Recibo de caja'
    COMPROBANTE_EGRESO = 'comprobante_egreso',  'Comprobante de egreso'
    NOMINA             = 'nomina',              'Nómina'
    ANTICIPO           = 'anticipo',            'Anticipo'
    ACTA_OBRA          = 'acta_obra',           'Acta de obra'


class Proyecto(BaseModel):
    """
    Proyecto de ejecución en Saicloud.
    Complementa la imputación contable de Saiopen con gestión de fases,
    presupuestos, terceros vinculados y análisis de rentabilidad.
    """
    codigo  = models.CharField(max_length=50, db_index=True)
    nombre  = models.CharField(max_length=255)
    tipo    = models.CharField(max_length=30, choices=TipoProyecto.choices)
    estado  = models.CharField(
        max_length=20,
        choices=EstadoProyecto.choices,
        default=EstadoProyecto.BORRADOR,
    )

    # Cliente principal (referencia a Saiopen — no FK para evitar acoplamiento)
    cliente_id     = models.CharField(max_length=50)
    cliente_nombre = models.CharField(max_length=255)

    # Responsables internos
    gerente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='proyectos_como_gerente',
    )
    coordinador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos_como_coordinador',
    )

    # Fechas planificadas
    fecha_inicio_planificada = models.DateField()
    fecha_fin_planificada    = models.DateField()

    # Fechas reales (se completan durante ejecución)
    fecha_inicio_real = models.DateField(null=True, blank=True)
    fecha_fin_real    = models.DateField(null=True, blank=True)

    # Presupuesto
    presupuesto_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0
    )

    # AIU — Administración, Imprevistos, Utilidad
    porcentaje_administracion = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('10.00')
    )
    porcentaje_imprevistos = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('5.00')
    )
    porcentaje_utilidad = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('10.00')
    )

    # Sincronización con Saiopen (gestionada por el agente Go)
    saiopen_proyecto_id      = models.CharField(max_length=50, null=True, blank=True)
    sincronizado_con_saiopen = models.BooleanField(default=False)
    ultima_sincronizacion    = models.DateTimeField(null=True, blank=True)

    # Avance físico promedio calculado automáticamente desde las fases
    porcentaje_avance = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Porcentaje de avance físico (0-100). Calculado automáticamente desde fases.',
        editable=False,
    )

    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        ordering            = ['-created_at']
        unique_together     = [('company', 'codigo')]

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'


class ConfiguracionModulo(models.Model):
    """
    Configuración del módulo de proyectos por empresa.
    Se crea automáticamente con valores por defecto al primer acceso.
    """
    MODOS_TIMESHEET = [
        ('manual',      'Manual — registro de horas'),
        ('cronometro',  'Cronómetro — tiempo real'),
        ('ambos',       'Ambos modos disponibles'),
        ('desactivado', 'Desactivado'),
    ]

    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='configuracion_proyectos',
    )
    requiere_sync_saiopen_para_ejecucion = models.BooleanField(
        default=False,
        help_text='Si True, el proyecto debe estar sincronizado con Saiopen antes de iniciar ejecución.',
    )
    dias_alerta_vencimiento = models.PositiveIntegerField(
        default=15,
        help_text='Días antes del vencimiento de fase para mostrar alerta.',
    )
    modo_timesheet = models.CharField(
        max_length=20,
        choices=MODOS_TIMESHEET,
        default='ambos',
        verbose_name='Modo de timesheet',
    )

    class Meta:
        verbose_name        = 'Configuración de proyectos'
        verbose_name_plural = 'Configuraciones de proyectos'

    def __str__(self):
        return f'Config proyectos — {self.company}'


class Fase(BaseModel):
    """
    Fase o etapa de un proyecto.
    Presupuesto desglosado por categoría (mano de obra, materiales, etc.)
    """
    proyecto    = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='fases')
    nombre      = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    orden       = models.PositiveIntegerField(default=0)

    # Fechas planificadas
    fecha_inicio_planificada = models.DateField()
    fecha_fin_planificada    = models.DateField()

    # Fechas reales
    fecha_inicio_real = models.DateField(null=True, blank=True)
    fecha_fin_real    = models.DateField(null=True, blank=True)

    # Presupuesto por categoría — NUMERIC(15,2) como exige el estándar
    presupuesto_mano_obra    = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_materiales   = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_subcontratos = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_equipos      = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_otros        = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    porcentaje_avance = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Porcentaje de avance físico (0-100)'
    )

    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Fase'
        verbose_name_plural = 'Fases'
        ordering            = ['orden']
        unique_together     = [('proyecto', 'orden')]

    def __str__(self):
        return f'{self.proyecto.codigo} / Fase {self.orden}: {self.nombre}'


class TerceroProyecto(BaseModel):
    """
    Tercero vinculado a un proyecto con un rol específico.
    Un tercero puede tener múltiples roles en el mismo proyecto.

    tercero_fk es la referencia normalizada (apps.terceros.Tercero).
    Los campos tercero_id/tercero_nombre se mantienen para loose coupling con Saiopen
    y compatibilidad con registros previos.
    """
    proyecto      = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='terceros')
    tercero_id    = models.CharField(max_length=50, help_text='NIT/ID del tercero en Saiopen')
    tercero_nombre = models.CharField(max_length=255)
    rol           = models.CharField(max_length=20, choices=RolTercero.choices)
    fase          = models.ForeignKey(
        Fase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='terceros',
    )
    # FK normalizada al catálogo de terceros (opcional — se llena cuando el tercero existe en Saisuite)
    tercero_fk = models.ForeignKey(
        'terceros.Tercero',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='proyectos_vinculados',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Tercero del proyecto'
        verbose_name_plural = 'Terceros del proyecto'
        unique_together     = [('proyecto', 'tercero_id', 'rol', 'fase')]

    def __str__(self):
        return f'{self.tercero_nombre} ({self.get_rol_display()}) — {self.proyecto.codigo}'


class DocumentoContable(BaseModel):
    """
    Documento contable generado en Saiopen e importado al proyecto vía agente Go.
    Solo lectura desde Saicloud — la escritura es exclusiva del agente de sincronización.
    """
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='documentos')
    fase     = models.ForeignKey(
        Fase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='documentos',
    )

    # Datos del documento en Saiopen
    saiopen_doc_id    = models.CharField(max_length=100)
    tipo_documento    = models.CharField(max_length=30, choices=TipoDocumento.choices)
    numero_documento  = models.CharField(max_length=100)
    fecha_documento   = models.DateField()

    # Tercero
    tercero_id     = models.CharField(max_length=50)
    tercero_nombre = models.CharField(max_length=255)

    # Montos — NUMERIC(15,2)
    valor_bruto    = models.DecimalField(max_digits=15, decimal_places=2)
    valor_descuento = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_neto     = models.DecimalField(max_digits=15, decimal_places=2)

    observaciones             = models.TextField(blank=True)
    sincronizado_desde_saiopen = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Documento contable'
        verbose_name_plural = 'Documentos contables'
        ordering            = ['-fecha_documento']
        unique_together     = [('company', 'saiopen_doc_id')]

    def __str__(self):
        return f'{self.get_tipo_documento_display()} {self.numero_documento} ({self.fecha_documento})'


class TipoActividad(models.TextChoices):
    MANO_OBRA   = 'mano_obra',   'Mano de obra'
    MATERIAL    = 'material',    'Material'
    EQUIPO      = 'equipo',      'Equipo'
    SUBCONTRATO = 'subcontrato', 'Subcontrato'


class Actividad(BaseModel):
    """
    Actividad reutilizable — catálogo global por empresa.
    Una misma actividad puede asignarse a múltiples proyectos.
    Ejemplo: "Excavación", "Instalación eléctrica", "Pintura".
    """
    codigo              = models.CharField(max_length=50, db_index=True)
    nombre              = models.CharField(max_length=255)
    descripcion         = models.TextField(blank=True)
    unidad_medida       = models.CharField(max_length=50, help_text='m2, m3, unidad, hora, etc.')
    costo_unitario_base = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Costo de referencia. Puede diferir por proyecto.',
    )
    tipo   = models.CharField(max_length=20, choices=TipoActividad.choices)
    activo = models.BooleanField(default=True, db_index=True)

    # Sincronización con Saiopen (opcional)
    saiopen_actividad_id     = models.CharField(max_length=50, null=True, blank=True)
    sincronizado_con_saiopen = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering            = ['codigo']
        unique_together     = [('company', 'codigo')]

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'


class ActividadProyecto(BaseModel):
    """
    Asignación de una Actividad a un Proyecto.
    El costo_unitario puede diferir del costo_unitario_base del catálogo.
    presupuesto_total se calcula como cantidad_planificada × costo_unitario.
    """
    proyecto  = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='actividades')
    actividad = models.ForeignKey(Actividad, on_delete=models.PROTECT, related_name='asignaciones')
    fase      = models.ForeignKey(
        Fase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='actividades',
    )

    cantidad_planificada = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cantidad_ejecutada   = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo_unitario       = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    porcentaje_avance    = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Porcentaje de avance de esta actividad (0-100)',
    )

    @property
    def presupuesto_total(self) -> Decimal:
        return self.cantidad_planificada * self.costo_unitario

    class Meta:
        verbose_name        = 'Actividad del proyecto'
        verbose_name_plural = 'Actividades del proyecto'
        ordering            = ['actividad__codigo']
        unique_together     = [('proyecto', 'actividad', 'fase')]

    def __str__(self):
        return f'{self.proyecto.codigo} / {self.actividad.codigo}'


class Hito(BaseModel):
    """
    Hito facturable del proyecto.
    Representa un porcentaje del avance que genera una factura en Saiopen.
    """
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='hitos')
    fase     = models.ForeignKey(
        Fase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hitos',
    )

    nombre      = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)

    # Porcentaje del proyecto total que representa este hito
    porcentaje_proyecto = models.DecimalField(max_digits=5, decimal_places=2)
    valor_facturar      = models.DecimalField(max_digits=15, decimal_places=2)

    # Estado de facturación
    facturable         = models.BooleanField(default=True)
    facturado          = models.BooleanField(default=False)
    documento_factura  = models.ForeignKey(
        DocumentoContable, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hitos_facturados',
    )
    fecha_facturacion = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Hito'
        verbose_name_plural = 'Hitos'
        ordering            = ['created_at']

    def __str__(self):
        estado = 'Facturado' if self.facturado else 'Pendiente'
        return f'{self.proyecto.codigo} — {self.nombre} ({estado})'


class TareaTag(BaseModel):
    """
    Etiquetas para categorizar y filtrar tareas.
    Hereda company de BaseModel — no duplicar FK.
    """
    nombre = models.CharField(max_length=50)
    color = models.CharField(
        max_length=20,
        default='blue',
        choices=[
            ('red', 'Rojo'),
            ('orange', 'Naranja'),
            ('yellow', 'Amarillo'),
            ('green', 'Verde'),
            ('blue', 'Azul'),
            ('purple', 'Morado'),
            ('pink', 'Rosa'),
            ('gray', 'Gris'),
        ]
    )

    class Meta:
        unique_together = [('company', 'nombre')]
        ordering = ['nombre']
        verbose_name = 'Etiqueta de Tarea'
        verbose_name_plural = 'Etiquetas de Tareas'

    def __str__(self):
        return self.nombre


class Tarea(BaseModel):
    """
    Tarea de proyecto con capacidades avanzadas.
    Reemplaza ActividadProyecto con funcionalidad completa tipo Odoo.
    """

    # ===== RELACIONES PRINCIPALES =====
    proyecto = models.ForeignKey(
        'Proyecto',
        on_delete=models.CASCADE,
        related_name='tareas'
    )
    fase = models.ForeignKey(
        'Fase',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tareas'
    )

    # ===== JERARQUÍA (SUBTAREAS MULTI-NIVEL) =====
    tarea_padre = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subtareas'
    )

    # ===== BÁSICO =====
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=50, blank=True)  # auto: TASK-00001

    # ===== CLIENTE OPCIONAL (DEC-019) =====
    cliente = models.ForeignKey(
        'terceros.Tercero',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tareas',
        verbose_name='Cliente',
        help_text='Tercero (cliente) asociado a esta tarea (opcional)',
    )

    # ===== ASIGNACIÓN Y COLABORACIÓN =====
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tareas_asignadas'
    )
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='tareas_siguiendo',
        blank=True
    )

    # ===== CLASIFICACIÓN =====
    prioridad = models.IntegerField(
        default=2,
        choices=[
            (1, 'Baja'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ]
    )
    tags = models.ManyToManyField('TareaTag', related_name='tareas', blank=True)

    # ===== FECHAS =====
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)  # deadline

    # ===== ESTADO Y PROGRESO =====
    estado = models.CharField(
        max_length=20,
        default='por_hacer',
        choices=[
            ('por_hacer', 'Por Hacer'),
            ('en_progreso', 'En Progreso'),
            ('en_revision', 'En Revisión'),
            ('bloqueada', 'Bloqueada'),
            ('completada', 'Completada'),
            ('cancelada', 'Cancelada'),
        ]
    )
    porcentaje_completado = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # ===== TIMESHEET (HORAS) =====
    horas_estimadas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    horas_registradas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # ===== RECURRENCIA =====
    es_recurrente = models.BooleanField(default=False)
    frecuencia_recurrencia = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('diaria', 'Diaria'),
            ('semanal', 'Semanal'),
            ('mensual', 'Mensual'),
        ]
    )
    proxima_generacion = models.DateField(null=True, blank=True)

    # ===== LEGACY (MIGRACIÓN) =====
    actividad_proyecto_id = models.UUIDField(
        null=True,
        blank=True,
        editable=False,
        help_text='ID de ActividadProyecto original (solo para migración)'
    )

    class Meta:
        ordering = ['-prioridad', 'fecha_limite', 'nombre']
        indexes = [
            models.Index(fields=['proyecto', 'estado']),
            models.Index(fields=['responsable']),
            models.Index(fields=['fecha_limite']),
        ]
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}" if self.codigo else self.nombre

    def clean(self):
        """Validaciones de negocio"""
        from django.core.exceptions import ValidationError

        # Validar fechas
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_inicio >= self.fecha_fin:
                raise ValidationError({
                    'fecha_fin': 'Fecha fin debe ser posterior a fecha inicio'
                })

        # Validar que no sea su propia subtarea
        if self.tarea_padre_id and self.id and self.tarea_padre_id == self.id:
            raise ValidationError({
                'tarea_padre': 'Una tarea no puede ser subtarea de sí misma'
            })

        # Validar que tarea_padre pertenece al mismo proyecto
        if self.tarea_padre and self.tarea_padre.proyecto_id != self.proyecto_id:
            raise ValidationError({
                'tarea_padre': 'Tarea padre debe pertenecer al mismo proyecto'
            })

        # Validar nivel máximo de jerarquía (5 niveles)
        if self.tarea_padre and self.nivel_jerarquia >= 5:
            raise ValidationError({
                'tarea_padre': 'Máximo 5 niveles de subtareas permitidos'
            })

    def save(self, *args, **kwargs):
        # Generar código automáticamente
        if not self.codigo:
            from django.db.models import Max
            from django.db.models.functions import Cast, Substr

            ultimo_numero = Tarea.all_objects.filter(
                proyecto=self.proyecto
            ).aggregate(
                max_num=Max(
                    Cast(
                        Substr('codigo', 6),  # Después de "TASK-"
                        output_field=models.IntegerField()
                    )
                )
            )['max_num'] or 0

            self.codigo = f"TASK-{ultimo_numero + 1:05d}"

        super().save(*args, **kwargs)

    @property
    def es_vencida(self):
        """Retorna True si la tarea está vencida"""
        from django.utils import timezone
        if not self.fecha_limite:
            return False
        return (
            self.fecha_limite < timezone.now().date()
            and self.estado not in ['completada', 'cancelada']
        )

    @property
    def tiene_subtareas(self):
        """Retorna True si la tarea tiene subtareas"""
        return self.subtareas.exists()

    @property
    def nivel_jerarquia(self):
        """Retorna el nivel de jerarquía (0=raíz, 1=sub, 2=sub-sub, etc.)"""
        nivel = 0
        padre = self.tarea_padre
        while padre:
            nivel += 1
            if nivel > 10:  # Prevenir loops infinitos
                break
            padre = padre.tarea_padre
        return nivel


class SesionTrabajo(BaseModel):
    """
    Sesión de trabajo cronometrada sobre una tarea.
    Soporta pausas; la duración neta se calcula al detener la sesión.
    """
    ESTADOS = [
        ('activa',     'Activa'),
        ('pausada',    'Pausada'),
        ('finalizada', 'Finalizada'),
    ]

    tarea = models.ForeignKey(
        'Tarea',
        on_delete=models.CASCADE,
        related_name='sesiones_trabajo',
        verbose_name='Tarea',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sesiones_trabajo',
        verbose_name='Usuario',
    )

    inicio             = models.DateTimeField(verbose_name='Inicio')
    fin                = models.DateTimeField(null=True, blank=True, verbose_name='Fin')
    # [{"inicio": "2026-03-22T10:15:00+00:00", "fin": "2026-03-22T10:30:00+00:00"}]
    pausas             = models.JSONField(default=list, verbose_name='Pausas')
    duracion_segundos  = models.IntegerField(default=0, verbose_name='Duración (segundos)')
    estado             = models.CharField(
        max_length=20, choices=ESTADOS, default='activa', verbose_name='Estado',
    )
    notas              = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table            = 'sesiones_trabajo'
        verbose_name        = 'Sesión de Trabajo'
        verbose_name_plural = 'Sesiones de Trabajo'
        ordering            = ['-inicio']
        indexes             = [
            models.Index(fields=['tarea', 'usuario']),
            models.Index(fields=['estado', 'usuario']),
        ]

    def __str__(self):
        return f'{self.usuario.get_full_name()} — {self.tarea.codigo} ({self.estado})'

    @property
    def duracion_horas(self) -> Decimal:
        """Duración neta en horas decimales (solo lectura)."""
        return Decimal(self.duracion_segundos) / Decimal(3600)
