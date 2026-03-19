"""
SaiSuite — Módulo de Proyectos
Gestión de ejecución de proyectos complementando la imputación contable de Saiopen.
"""
import logging
from decimal import Decimal
from django.db import models
from django.conf import settings
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

    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        ordering            = ['-created_at']
        unique_together     = [('company', 'codigo')]

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'


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
