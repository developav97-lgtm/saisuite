"""
SaiSuite — Módulo de Proyectos
Gestión de ejecución de proyectos complementando la imputación contable de Saiopen.
"""
import logging
from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class ProjectType(models.TextChoices):
    CIVIL_WORKS    = 'civil_works',    'Obra civil'
    CONSULTING     = 'consulting',     'Consultoría'
    MANUFACTURING  = 'manufacturing',  'Manufactura'
    SERVICES       = 'services',       'Servicios'
    PUBLIC_TENDER  = 'public_tender',  'Licitación pública'
    OTHER          = 'other',          'Otro'


class ProjectStatus(models.TextChoices):
    DRAFT       = 'draft',       'Borrador'
    PLANNED     = 'planned',     'Planificado'
    IN_PROGRESS = 'in_progress', 'En ejecución'
    SUSPENDED   = 'suspended',   'Suspendido'
    CLOSED      = 'closed',      'Cerrado'
    CANCELLED   = 'cancelled',   'Cancelado'


class StakeholderRole(models.TextChoices):
    CLIENT        = 'client',        'Cliente'
    SUBCONTRACTOR = 'subcontractor', 'Subcontratista'
    VENDOR        = 'vendor',        'Proveedor'
    CONSULTANT    = 'consultant',    'Consultor'
    INSPECTOR     = 'inspector',     'Interventor'
    SUPERVISOR    = 'supervisor',    'Supervisor'


class DocumentType(models.TextChoices):
    SALES_INVOICE    = 'sales_invoice',    'Factura de venta'
    PURCHASE_INVOICE = 'purchase_invoice', 'Factura de compra'
    PURCHASE_ORDER   = 'purchase_order',   'Orden de compra'
    CASH_RECEIPT     = 'cash_receipt',     'Recibo de caja'
    EXPENSE_VOUCHER  = 'expense_voucher',  'Comprobante de egreso'
    PAYROLL          = 'payroll',          'Nómina'
    ADVANCE          = 'advance',          'Anticipo'
    WORK_CERTIFICATE = 'work_certificate', 'Acta de obra'


class PhaseStatus(models.TextChoices):
    PLANNED   = 'planned',   'Planificada'
    ACTIVE    = 'active',    'Activa'
    COMPLETED = 'completed', 'Completada'
    CANCELLED = 'cancelled', 'Cancelada'


class MeasurementMode(models.TextChoices):
    STATUS_ONLY = 'status_only', 'Solo estados'
    TIMESHEET   = 'timesheet',   'Timesheet (horas)'
    QUANTITY    = 'quantity',    'Cantidad ejecutada'


class Project(BaseModel):
    """
    Proyecto de ejecución en Saicloud.
    Complementa la imputación contable de Saiopen con gestión de fases,
    presupuestos, terceros vinculados y análisis de rentabilidad.
    """
    codigo  = models.CharField(max_length=50, db_index=True)
    nombre  = models.CharField(max_length=255)
    tipo    = models.CharField(max_length=30, choices=ProjectType.choices)
    estado  = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
    )

    # Cliente principal (referencia a Saiopen — no FK para evitar acoplamiento)
    cliente_id     = models.CharField(max_length=50, blank=True)
    cliente_nombre = models.CharField(max_length=255, blank=True)

    # Responsables internos
    gerente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='projects_as_manager',
    )
    coordinador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_as_coordinator',
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


class ModuleSettings(models.Model):
    """
    Configuración del módulo de proyectos por empresa.
    Se crea automáticamente con valores por defecto al primer acceso.
    """
    TIMESHEET_MODES = [
        ('manual',   'Manual — hour recording'),
        ('timer',    'Timer — real time'),
        ('both',     'Both modes available'),
        ('disabled', 'Disabled'),
    ]

    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='project_settings',
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
        choices=TIMESHEET_MODES,
        default='both',
        verbose_name='Modo de timesheet',
    )

    class Meta:
        verbose_name        = 'Configuración de proyectos'
        verbose_name_plural = 'Configuraciones de proyectos'

    def __str__(self):
        return f'Config proyectos — {self.company}'


class Phase(BaseModel):
    """
    Fase o etapa de un proyecto.
    Presupuesto desglosado por categoría (mano de obra, materiales, etc.)
    """
    proyecto    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
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

    estado = models.CharField(
        max_length=20,
        choices=PhaseStatus.choices,
        default=PhaseStatus.PLANNED,
        help_text='Estado operativo de la fase.',
    )

    porcentaje_avance = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Porcentaje de avance físico (0-100). Calculado automáticamente desde tareas.'
    )

    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Fase'
        verbose_name_plural = 'Fases'
        ordering            = ['orden']
        unique_together     = [('proyecto', 'orden')]

    def __str__(self):
        return f'{self.proyecto.codigo} / Fase {self.orden}: {self.nombre}'


class ProjectStakeholder(BaseModel):
    """
    Tercero vinculado a un proyecto con un rol específico.
    Un tercero puede tener múltiples roles en el mismo proyecto.

    tercero_fk es la referencia normalizada (apps.terceros.Tercero).
    Los campos tercero_id/tercero_nombre se mantienen para loose coupling con Saiopen
    y compatibilidad con registros previos.
    """
    proyecto      = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stakeholders')
    tercero_id    = models.CharField(max_length=50, help_text='NIT/ID del tercero en Saiopen')
    tercero_nombre = models.CharField(max_length=255)
    rol           = models.CharField(max_length=20, choices=StakeholderRole.choices)
    fase          = models.ForeignKey(
        Phase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stakeholders',
    )
    # FK normalizada al catálogo de terceros (opcional — se llena cuando el tercero existe en Saisuite)
    tercero_fk = models.ForeignKey(
        'terceros.Tercero',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='linked_projects',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Tercero del proyecto'
        verbose_name_plural = 'Terceros del proyecto'
        unique_together     = [('proyecto', 'tercero_id', 'rol', 'fase')]

    def __str__(self):
        return f'{self.tercero_nombre} ({self.get_rol_display()}) — {self.proyecto.codigo}'


class AccountingDocument(BaseModel):
    """
    Documento contable generado en Saiopen e importado al proyecto vía agente Go.
    Solo lectura desde Saicloud — la escritura es exclusiva del agente de sincronización.
    """
    proyecto = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    fase     = models.ForeignKey(
        Phase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='documents',
    )

    # Datos del documento en Saiopen
    saiopen_doc_id    = models.CharField(max_length=100)
    tipo_documento    = models.CharField(max_length=30, choices=DocumentType.choices)
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


class ActivityType(models.TextChoices):
    LABOR       = 'labor',       'Mano de obra'
    MATERIAL    = 'material',    'Material'
    EQUIPMENT   = 'equipment',   'Equipo'
    SUBCONTRACT = 'subcontract', 'Subcontrato'
    MILESTONE   = 'milestone',   'Hito'


class Activity(BaseModel):
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
    tipo   = models.CharField(max_length=20, choices=ActivityType.choices)
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


class ProjectActivity(BaseModel):
    """
    Asignación de una Activity a un Project.
    El costo_unitario puede diferir del costo_unitario_base del catálogo.
    presupuesto_total se calcula como cantidad_planificada × costo_unitario.
    """
    proyecto  = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities')
    actividad = models.ForeignKey(Activity, on_delete=models.PROTECT, related_name='assignments')
    fase      = models.ForeignKey(
        Phase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activities',
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


class SaiopenActivity(BaseModel):
    """
    Catálogo de actividades sincronizadas desde Saiopen.
    Una misma actividad puede vincularse a múltiples tareas y fases.
    unidad_medida determina el modo de medición en la UI (DEC-020).
    """
    codigo          = models.CharField(max_length=50, db_index=True)
    nombre          = models.CharField(max_length=255)
    descripcion     = models.TextField(blank=True)
    unidad_medida   = models.CharField(
        max_length=20,
        choices=MeasurementMode.choices,
        default=MeasurementMode.STATUS_ONLY,
        help_text='Determina el modo de medición: status_only, timesheet o quantity.',
    )
    costo_unitario_base = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Costo de referencia. Puede diferir por tarea.',
    )
    activo = models.BooleanField(default=True, db_index=True)

    # Sincronización Saiopen (gestionada por el agente)
    saiopen_actividad_id     = models.CharField(max_length=50, null=True, blank=True)
    sincronizado_con_saiopen = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Actividad Saiopen'
        verbose_name_plural = 'Actividades Saiopen'
        ordering            = ['codigo']
        unique_together     = [('company', 'codigo')]

    def __str__(self):
        return f'{self.codigo} — {self.nombre}'


class Milestone(BaseModel):
    """
    Hito facturable del proyecto.
    Representa un porcentaje del avance que genera una factura en Saiopen.
    """
    proyecto = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    fase     = models.ForeignKey(
        Phase, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='milestones',
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
        AccountingDocument, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invoiced_milestones',
    )
    fecha_facturacion = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Hito'
        verbose_name_plural = 'Hitos'
        ordering            = ['created_at']

    def __str__(self):
        estado = 'Facturado' if self.facturado else 'Pendiente'
        return f'{self.proyecto.codigo} — {self.nombre} ({estado})'


class TaskTag(BaseModel):
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


class Task(BaseModel):
    """
    Tarea de proyecto con capacidades avanzadas.
    Reemplaza ActividadProyecto con funcionalidad completa tipo Odoo.
    """

    # ===== RELACIONES PRINCIPALES =====
    # fase es obligatoria (DEC-021): la jerarquía es Proyecto → Fase → Tarea.
    # proyecto se auto-sincroniza desde fase.proyecto en save() para facilitar
    # consultas de performance sin romper la API existente.
    fase = models.ForeignKey(
        'Phase',
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='Fase a la que pertenece esta tarea (obligatoria).',
    )
    proyecto = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        editable=False,
        help_text='Auto-derivado de fase.proyecto. No editar directamente.',
    )

    # ===== ACTIVIDAD SAIOPEN (DEC-022) =====
    actividad_saiopen = models.ForeignKey(
        'SaiopenActivity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text='Actividad de Saiopen que determina el modo de medición.',
    )

    # ===== JERARQUÍA (SUBTAREAS MULTI-NIVEL) =====
    tarea_padre = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subtasks'
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
        related_name='assigned_tasks'
    )
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='following_tasks',
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
    tags = models.ManyToManyField('TaskTag', related_name='tasks', blank=True)

    # ===== FECHAS =====
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    fecha_limite = models.DateField(null=True, blank=True)  # deadline

    # ===== ESTADO Y PROGRESO =====
    estado = models.CharField(
        max_length=20,
        default='todo',
        choices=[
            ('todo',        'To Do'),
            ('in_progress', 'In Progress'),
            ('in_review',   'In Review'),
            ('blocked',     'Blocked'),
            ('completed',   'Completed'),
            ('cancelled',   'Cancelled'),
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

    # ===== MEDICIÓN POR CANTIDAD (DEC-022) =====
    cantidad_objetivo   = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Cantidad objetivo (aplica cuando actividad_saiopen.unidad_medida = quantity).',
    )
    cantidad_registrada = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text='Cantidad ejecutada registrada.',
    )

    # ===== RECURRENCIA =====
    es_recurrente = models.BooleanField(default=False)
    frecuencia_recurrencia = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('daily',   'Daily'),
            ('weekly',  'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    proxima_generacion = models.DateField(null=True, blank=True)

    # ===== ACTIVIDAD DEL PROYECTO (DEC-022) =====
    actividad_proyecto = models.ForeignKey(
        'ProjectActivity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks',
        help_text='Actividad del proyecto a la que pertenece esta tarea.',
    )

    class Meta:
        ordering = ['-prioridad', 'fecha_limite', 'nombre']
        indexes = [
            models.Index(fields=['fase', 'estado']),
            models.Index(fields=['proyecto', 'estado']),
            models.Index(fields=['responsable']),
            models.Index(fields=['fecha_limite']),
            # Feature #6 — scheduling performance indexes (SK-25, SK-26)
            models.Index(
                fields=['proyecto', 'fecha_inicio', 'fecha_fin'],
                name='idx_task_proj_dates',
            ),
            models.Index(
                fields=['fecha_fin'],
                name='idx_task_fecha_fin',
            ),
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
        if self.tarea_padre:
            proyecto_id = self.proyecto_id or (self.fase.proyecto_id if self.fase_id and self.fase else None)
            if proyecto_id and self.tarea_padre.proyecto_id != proyecto_id:
                raise ValidationError({
                    'tarea_padre': 'Tarea padre debe pertenecer al mismo proyecto'
                })

        # Validar nivel máximo de jerarquía (5 niveles)
        if self.tarea_padre and self.nivel_jerarquia >= 5:
            raise ValidationError({
                'tarea_padre': 'Máximo 5 niveles de subtareas permitidos'
            })

    def save(self, *args, **kwargs):
        # Mantener proyecto sincronizado con fase.proyecto (DEC-021)
        if self.fase_id and not self.proyecto_id:
            self.proyecto_id = self.fase.proyecto_id

        # Generar código automáticamente
        if not self.codigo:
            from django.db.models import Max
            from django.db.models.functions import Cast, Substr

            ultimo_numero = Task.all_objects.filter(
                proyecto_id=self.proyecto_id
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
    def modo_medicion(self) -> str:
        """Modo de medición determinado por la actividad asociada."""
        if self.actividad_saiopen_id and self.actividad_saiopen:
            return self.actividad_saiopen.unidad_medida
        if self.actividad_proyecto_id and self.actividad_proyecto_id:
            try:
                um = (self.actividad_proyecto.actividad.unidad_medida or '').lower().strip()
                _DIA_UNITS = {'dia', 'día', 'dias', 'días', 'day', 'days'}
                if um == 'hora' or um in _DIA_UNITS:
                    return MeasurementMode.TIMESHEET
                if um:
                    return MeasurementMode.QUANTITY
            except Exception:
                pass
        return MeasurementMode.STATUS_ONLY

    @property
    def progreso_porcentaje(self) -> float:
        """Progreso calculado según el modo de medición de la actividad."""
        modo = self.modo_medicion
        if modo == MeasurementMode.TIMESHEET:
            if self.horas_estimadas and self.horas_estimadas > 0:
                return min(float(self.horas_registradas) / float(self.horas_estimadas) * 100, 100.0)
        elif modo == MeasurementMode.QUANTITY:
            if self.cantidad_objetivo and self.cantidad_objetivo > 0:
                return min(float(self.cantidad_registrada) / float(self.cantidad_objetivo) * 100, 100.0)
        return float(self.porcentaje_completado)

    @property
    def es_vencida(self):
        """Retorna True si la tarea está vencida"""
        from django.utils import timezone
        if not self.fecha_limite:
            return False
        return (
            self.fecha_limite < timezone.now().date()
            and self.estado not in ['completed', 'cancelled']
        )

    @property
    def tiene_subtareas(self):
        """Retorna True si la tarea tiene subtareas"""
        return self.subtasks.exists()

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


class WorkSession(BaseModel):
    """
    Sesión de trabajo cronometrada sobre una tarea.
    Soporta pausas; la duración neta se calcula al detener la sesión.
    """
    ESTADOS = [
        ('active',   'Active'),
        ('paused',   'Paused'),
        ('finished', 'Finished'),
    ]

    tarea = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='work_sessions',
        verbose_name='Tarea',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='work_sessions',
        verbose_name='Usuario',
    )

    inicio             = models.DateTimeField(verbose_name='Inicio')
    fin                = models.DateTimeField(null=True, blank=True, verbose_name='Fin')
    # [{"inicio": "2026-03-22T10:15:00+00:00", "fin": "2026-03-22T10:30:00+00:00"}]
    pausas             = models.JSONField(default=list, verbose_name='Pausas')
    duracion_segundos  = models.IntegerField(default=0, verbose_name='Duración (segundos)')
    estado             = models.CharField(
        max_length=20, choices=ESTADOS, default='active', verbose_name='Estado',
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
        return f'{self.usuario.full_name} — {self.tarea.codigo} ({self.estado})'

    @property
    def duracion_horas(self) -> Decimal:
        """Duración neta en horas decimales (solo lectura)."""
        return Decimal(self.duracion_segundos) / Decimal(3600)


class TimesheetEntry(BaseModel):
    """
    Registro diario de horas trabajadas en una tarea.
    Un usuario puede tener un solo registro por tarea por día.
    Una vez validado, el registro no se puede editar ni eliminar.
    """
    tarea = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='timesheets',
        verbose_name='Tarea',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='timesheets',
        verbose_name='Usuario',
    )
    fecha       = models.DateField(verbose_name='Fecha')
    horas       = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name='Horas',
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('24'))],
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    # Validación
    validado          = models.BooleanField(default=False, verbose_name='Validado')
    validado_por      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='validated_timesheets',
        verbose_name='Validado por',
    )
    fecha_validacion  = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de validación')

    class Meta:
        db_table            = 'timesheet_entries'
        verbose_name        = 'Registro de Horas'
        verbose_name_plural = 'Registros de Horas'
        ordering            = ['-fecha', '-created_at']
        unique_together     = [['tarea', 'usuario', 'fecha']]
        indexes             = [
            models.Index(fields=['usuario', 'fecha']),
            models.Index(fields=['tarea', 'validado']),
        ]

    def __str__(self):
        return f'{self.usuario.full_name or self.usuario.email} — {self.tarea.codigo} ({self.fecha}) {self.horas}h'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.horas is not None:
            if self.horas <= 0:
                raise ValidationError({'horas': 'El valor debe ser mayor a 0.'})
            if self.horas > 365:
                raise ValidationError({'horas': 'El valor no puede superar 365 por registro.'})


class DependencyType(models.TextChoices):
    FINISH_TO_START  = 'FS', 'Finish to Start (FS)'
    START_TO_START   = 'SS', 'Start to Start (SS)'
    FINISH_TO_FINISH = 'FF', 'Finish to Finish (FF)'


class TaskDependency(BaseModel):
    """
    Relación predecesora-sucesora entre dos tareas del mismo proyecto.
    Soporta los tipos clásicos de dependencia CPM: FS, SS, FF.
    """
    tarea_predecesora = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='successors',
        verbose_name='Tarea predecesora',
    )
    tarea_sucesora = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='predecessors',
        verbose_name='Tarea sucesora',
    )
    tipo_dependencia = models.CharField(
        max_length=2,
        choices=DependencyType.choices,
        default=DependencyType.FINISH_TO_START,
    )
    retraso_dias = models.IntegerField(
        default=0,
        help_text='Lag time en días (puede ser negativo para adelantar).',
    )

    class Meta:
        verbose_name        = 'Dependencia de tarea'
        verbose_name_plural = 'Dependencias de tareas'
        unique_together     = [['company', 'tarea_predecesora', 'tarea_sucesora']]
        indexes = [
            # Feature #6 — scheduling performance index (SK-27)
            models.Index(
                fields=['tarea_predecesora'],
                name='idx_tdep_predecessor',
            ),
        ]

    def __str__(self):
        return (
            f'{self.tarea_predecesora.codigo} → {self.tarea_sucesora.codigo} '
            f'({self.tipo_dependencia})'
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.tarea_predecesora_id and self.tarea_sucesora_id:
            if self.tarea_predecesora_id == self.tarea_sucesora_id:
                raise ValidationError(
                    'Una tarea no puede ser predecesora de sí misma.'
                )


# ===========================================================================
# FEATURE #4 — RESOURCE MANAGEMENT
# ===========================================================================

class AvailabilityType(models.TextChoices):
    VACATION   = 'vacation',   'Vacaciones'
    SICK_LEAVE = 'sick_leave', 'Incapacidad'
    HOLIDAY    = 'holiday',    'Festivo'
    TRAINING   = 'training',   'Capacitación'
    OTHER      = 'other',      'Otro'


class ResourceAssignment(BaseModel):
    """
    Asignación formal de un usuario a una tarea con porcentaje de dedicación.

    Un usuario solo puede tener una asignación activa por tarea (unique_together).
    El porcentaje representa la fracción de su capacidad semanal dedicada a esta tarea.
    Si la suma de porcentajes en cualquier día supera 100%, ResourceService detecta
    el conflicto (DEC-025).

    FK usuario → PROTECT: nunca eliminar usuario con asignaciones (preservar histórico).
    Desactivar el usuario primero vía UserService.deactivate_user().
    """
    tarea = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='resource_assignments',
        verbose_name='Tarea',
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='resource_assignments',
        verbose_name='Usuario',
    )
    porcentaje_asignacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Porcentaje de asignación',
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('100.00')),
        ],
        help_text='Fracción de la capacidad semanal del usuario dedicada a esta tarea (0.01–100).',
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    fecha_fin    = models.DateField(verbose_name='Fecha de fin')
    notas        = models.TextField(blank=True, verbose_name='Notas')
    activo       = models.BooleanField(default=True, db_index=True, verbose_name='Activo')

    class Meta:
        verbose_name        = 'Asignación de recurso'
        verbose_name_plural = 'Asignaciones de recursos'
        ordering            = ['fecha_inicio', 'usuario']
        unique_together     = [('company', 'tarea', 'usuario')]
        indexes = [
            models.Index(
                fields=['company', 'usuario', 'fecha_inicio', 'fecha_fin'],
                name='idx_rassign_co_us_dates',
            ),
            models.Index(
                fields=['tarea', 'fecha_inicio', 'fecha_fin'],
                name='idx_rassign_tarea_dates',
            ),
            models.Index(
                fields=['usuario', 'activo'],
                name='idx_rassign_us_activo',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='ck_rassign_fecha_fin_gte_inicio',
            ),
        ]

    def __str__(self):
        return (
            f'{self.usuario.full_name} → {self.tarea.codigo} '
            f'({self.porcentaje_asignacion}% | {self.fecha_inicio}–{self.fecha_fin})'
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser igual o posterior a la fecha de inicio.',
                })


class ResourceCapacity(BaseModel):
    """
    Capacidad laboral semanal de un usuario para un período dado.

    Los períodos del mismo usuario no deben solaparse: validar en
    ResourceCapacityService.crear_capacidad() y actualizar_capacidad().
    fecha_fin=None significa capacidad indefinida (sin fecha de expiración).
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_capacities',
        verbose_name='Usuario',
    )
    horas_por_semana = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Horas por semana',
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('168.00')),
        ],
        help_text='Horas laborables por semana (máx. 168 = 7 días × 24h).',
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    fecha_fin    = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de fin',
        help_text='Dejar en blanco para capacidad indefinida.',
    )
    activo = models.BooleanField(default=True, db_index=True, verbose_name='Activo')

    class Meta:
        verbose_name        = 'Capacidad de recurso'
        verbose_name_plural = 'Capacidades de recursos'
        ordering            = ['usuario', 'fecha_inicio']
        indexes = [
            models.Index(
                fields=['company', 'usuario', 'activo', 'fecha_inicio'],
                name='idx_rcap_co_us_active_start',
            ),
            models.Index(
                fields=['company', 'usuario'],
                name='idx_rcap_open_ended',
                condition=Q(fecha_fin__isnull=True),
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=models.F('fecha_inicio')),
                name='ck_rcap_fecha_fin_gt_inicio',
            ),
            models.CheckConstraint(
                condition=Q(horas_por_semana__gt=0),
                name='ck_rcap_horas_positivas',
            ),
        ]

    def __str__(self):
        fin = str(self.fecha_fin) if self.fecha_fin else 'indefinido'
        return (
            f'{self.usuario.full_name} — {self.horas_por_semana}h/semana '
            f'({self.fecha_inicio} → {fin})'
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.',
                })


class ResourceAvailability(BaseModel):
    """
    Ausencia o indisponibilidad de un usuario para un período.

    Solo ausencias con aprobado=True se descuentan de la capacidad efectiva.
    Ausencias del mismo tipo no pueden solaparse para el mismo usuario:
    validar en ResourceAvailabilityService.registrar_ausencia().
    Ausencias de distintos tipos sí pueden coexistir el mismo día
    (ej: festivo + capacitación).
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_availabilities',
        verbose_name='Usuario',
    )
    tipo = models.CharField(
        max_length=20,
        choices=AvailabilityType.choices,
        verbose_name='Tipo de ausencia',
    )
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    fecha_fin    = models.DateField(verbose_name='Fecha de fin')
    descripcion  = models.TextField(blank=True, verbose_name='Descripción')

    aprobado         = models.BooleanField(default=False, db_index=True, verbose_name='Aprobado')
    aprobado_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_absences',
        verbose_name='Aprobado por',
    )
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación',
    )
    activo = models.BooleanField(default=True, db_index=True, verbose_name='Activo')

    class Meta:
        verbose_name        = 'Disponibilidad de recurso'
        verbose_name_plural = 'Disponibilidades de recursos'
        ordering            = ['fecha_inicio', 'usuario']
        indexes = [
            models.Index(
                fields=['company', 'usuario', 'aprobado', 'fecha_inicio', 'fecha_fin'],
                name='idx_ravail_co_us_ap_dates',
            ),
            models.Index(
                fields=['company', 'aprobado'],
                name='idx_ravail_co_aprobado',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='ck_ravail_fecha_fin_gte_inicio',
            ),
        ]

    def __str__(self):
        return (
            f'{self.usuario.full_name} — {self.get_tipo_display()} '
            f'({self.fecha_inicio} → {self.fecha_fin})'
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser igual o posterior a la fecha de inicio.',
                })
        if self.aprobado and not self.aprobado_por_id:
            raise ValidationError({
                'aprobado_por': 'Debe especificar quién aprobó la ausencia.',
            })


# ──────────────────────────────────────────────────────────────────────────────
# Feature #6 — Advanced Scheduling
# ──────────────────────────────────────────────────────────────────────────────

class ProjectBaseline(BaseModel):
    """
    Snapshot del plan del proyecto en un momento dado.
    Permite comparar plan original vs plan actual (Earned-Value / schedule variance).

    Solo un baseline puede estar activo por proyecto+company al mismo tiempo
    (UniqueConstraint parcial con condition=is_active_baseline=True).
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='baselines',
        verbose_name='Proyecto',
    )
    name = models.CharField(max_length=255, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_active_baseline = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Baseline activo',
        help_text='Solo un baseline activo por proyecto.',
    )

    # Snapshot de tareas al momento de crear el baseline
    # [{task_id, nombre, fecha_inicio, fecha_fin, horas_estimadas}]
    tasks_snapshot = models.JSONField(default=list, verbose_name='Snapshot de tareas')

    # Snapshot de asignaciones de recursos
    # [{assignment_id, task_id, user_id, porcentaje, fecha_inicio, fecha_fin}]
    resources_snapshot = models.JSONField(
        default=list,
        verbose_name='Snapshot de recursos',
    )

    # Métricas del momento del snapshot
    project_end_date_snapshot = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha fin proyecto (snapshot)',
    )
    total_tasks_snapshot = models.IntegerField(
        default=0,
        verbose_name='Total tareas (snapshot)',
    )
    critical_path_snapshot = models.JSONField(
        default=list,
        verbose_name='Ruta crítica (snapshot)',
        help_text='Lista de task_ids que formaban la ruta crítica.',
    )

    class Meta:
        verbose_name        = 'Baseline de proyecto'
        verbose_name_plural = 'Baselines de proyectos'
        ordering            = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'project'],
                condition=models.Q(is_active_baseline=True),
                name='uq_one_active_baseline_per_project',
            )
        ]

    def __str__(self):
        active_label = ' [ACTIVO]' if self.is_active_baseline else ''
        return f'{self.project.nombre} — {self.name}{active_label}'


class ConstraintType(models.TextChoices):
    ASAP                  = 'asap',                   'As Soon As Possible'
    ALAP                  = 'alap',                   'As Late As Possible'
    MUST_START_ON         = 'must_start_on',          'Must Start On'
    MUST_FINISH_ON        = 'must_finish_on',         'Must Finish On'
    START_NO_EARLIER_THAN = 'start_no_earlier_than',  'Start No Earlier Than'
    START_NO_LATER_THAN   = 'start_no_later_than',    'Start No Later Than'
    FINISH_NO_EARLIER_THAN = 'finish_no_earlier_than', 'Finish No Earlier Than'
    FINISH_NO_LATER_THAN  = 'finish_no_later_than',   'Finish No Later Than'


class TaskConstraint(BaseModel):
    """
    Restricción de scheduling aplicada a una tarea.
    Las restricciones se respetan durante auto-schedule.

    Una tarea puede tener múltiples constraints de tipos distintos, pero no
    dos constraints del mismo tipo para la misma tarea+company.
    """
    task = models.ForeignKey(
        'Task',
        on_delete=models.CASCADE,
        related_name='scheduling_constraints',
        verbose_name='Tarea',
    )
    constraint_type = models.CharField(
        max_length=30,
        choices=ConstraintType.choices,
        default=ConstraintType.ASAP,
        verbose_name='Tipo de restricción',
    )
    constraint_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de restricción',
        help_text='Requerido para tipos con fecha (must_start_on, start_no_earlier_than, etc.).',
    )

    class Meta:
        verbose_name        = 'Restricción de tarea'
        verbose_name_plural = 'Restricciones de tareas'
        unique_together     = [('company', 'task', 'constraint_type')]

    def __str__(self):
        date_suffix = f' ({self.constraint_date})' if self.constraint_date else ''
        return f'{self.task.nombre} — {self.get_constraint_type_display()}{date_suffix}'

    def clean(self):
        from django.core.exceptions import ValidationError
        date_required = {
            ConstraintType.MUST_START_ON,
            ConstraintType.MUST_FINISH_ON,
            ConstraintType.START_NO_EARLIER_THAN,
            ConstraintType.START_NO_LATER_THAN,
            ConstraintType.FINISH_NO_EARLIER_THAN,
            ConstraintType.FINISH_NO_LATER_THAN,
        }
        if self.constraint_type in date_required and not self.constraint_date:
            raise ValidationError({
                'constraint_date': (
                    f'constraint_date es obligatorio para el tipo "{self.constraint_type}".'
                )
            })


class WhatIfScenario(BaseModel):
    """
    Escenario de simulación hipotética ("what if").

    Los cambios se aplican sobre un clon en memoria — nunca modifican datos reales.
    Los resultados (simulated_end_date, days_delta, etc.) se guardan en el mismo
    registro después de ejecutar run_simulation().
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='what_if_scenarios',
        verbose_name='Proyecto',
    )
    name = models.CharField(max_length=255, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_what_if_scenarios',
        verbose_name='Creado por',
    )

    # Cambios propuestos (estructura JSON):
    # task_changes:       {str(task_id): {field: new_value, ...}}
    # resource_changes:   {str(assignment_id): {field: new_value, ...}}
    # dependency_changes: {str(dep_id): {'retraso_dias': N}}
    task_changes       = models.JSONField(default=dict, verbose_name='Cambios en tareas')
    resource_changes   = models.JSONField(default=dict, verbose_name='Cambios en recursos')
    dependency_changes = models.JSONField(default=dict, verbose_name='Cambios en dependencias')

    # Resultados — null hasta que se ejecute run_simulation()
    simulated_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha fin simulada',
    )
    simulated_critical_path = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Ruta crítica simulada',
        help_text='Lista de task_ids en la ruta crítica del escenario.',
    )
    days_delta = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Delta días',
        help_text='Días de diferencia vs plan actual. Positivo = retraso, negativo = adelanto.',
    )
    tasks_affected_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Tareas afectadas',
    )
    simulation_ran_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Simulación ejecutada en',
    )

    class Meta:
        verbose_name        = 'Escenario What-If'
        verbose_name_plural = 'Escenarios What-If'
        ordering            = ['-created_at']

    def __str__(self):
        ran = ' [simulado]' if self.simulation_ran_at else ' [pendiente]'
        return f'{self.project.nombre} — {self.name}{ran}'


# ─────────────────────────────────────────────────────────────────────────────
# Feature #7 — Budget & Cost Tracking
# ─────────────────────────────────────────────────────────────────────────────

class ResourceCostRate(BaseModel):
    """
    Tarifa horaria facturable de un recurso (usuario) para un período dado.

    Regla de negocio: los rangos de fechas [start_date, end_date] no pueden
    solaparse para el mismo par (user, company). end_date=NULL significa
    "actualmente vigente". Solo puede existir un registro con end_date=NULL
    por (user, company).

    La validación de solapamiento se aplica en budget_services antes de
    persistir. El partial unique index (WHERE end_date IS NULL) creado en la
    migración 0019 actúa como red de seguridad en la base de datos.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cost_rates',
        verbose_name='Usuario',
    )
    # company viene de BaseModel — no duplicar FK

    start_date = models.DateField(verbose_name='Fecha inicio vigencia')
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha fin vigencia',
        help_text='NULL indica que la tarifa está actualmente vigente.',
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Tarifa por hora',
    )
    currency = models.CharField(
        max_length=3,
        default='COP',
        verbose_name='Moneda (ISO 4217)',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table             = 'resource_cost_rates'
        verbose_name         = 'Tarifa de Costo de Recurso'
        verbose_name_plural  = 'Tarifas de Costo de Recursos'
        ordering             = ['-start_date']
        indexes = [
            models.Index(fields=['user', 'company', 'start_date']),
            models.Index(fields=['company', 'start_date', 'end_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_date__lte=models.F('end_date'))
                    | Q(end_date__isnull=True),
                name='resource_cost_rate_start_before_end',
            ),
            models.CheckConstraint(
                condition=Q(hourly_rate__gte=Decimal('0.00')),
                name='resource_cost_rate_non_negative',
            ),
        ]

    def __str__(self):
        end = self.end_date.isoformat() if self.end_date else 'presente'
        return (
            f'{self.user_id} — {self.hourly_rate} {self.currency}/h '
            f'({self.start_date} → {end})'
        )


class ProjectBudget(BaseModel):
    """
    Presupuesto planificado y aprobado de un proyecto.

    Relación OneToOne con Project: un proyecto tiene exactamente un presupuesto.
    Se crea explícitamente mediante la API — no se auto-crea en Project.save().

    El campo `approved_date` indica si el presupuesto fue aprobado
    (approved_date IS NOT NULL ↔ aprobado). No se usa un campo BooleanField
    separado para evitar inconsistencias.
    """
    project = models.OneToOneField(
        'Project',
        on_delete=models.CASCADE,
        related_name='budget',
        verbose_name='Proyecto',
    )

    # Componentes del presupuesto planificado
    planned_labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo mano de obra planificado',
    )
    planned_expense_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo gastos planificado',
    )
    planned_total_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Presupuesto total planificado',
        help_text=(
            'Puede incluir AIU y contingencia además de labor + expense. '
            'No se auto-calcula: el gestor lo define explícitamente.'
        ),
    )

    # Aprobación
    approved_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Presupuesto aprobado',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budgets',
        verbose_name='Aprobado por',
    )
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación',
    )

    # Alertas
    alert_threshold_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        validators=[
            MinValueValidator(Decimal('1.00')),
            MaxValueValidator(Decimal('100.00')),
        ],
        verbose_name='Umbral de alerta (%)',
        help_text='Porcentaje de ejecución del presupuesto que activa una alerta.',
    )

    currency = models.CharField(
        max_length=3,
        default='COP',
        verbose_name='Moneda (ISO 4217)',
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table            = 'project_budgets'
        verbose_name        = 'Presupuesto de Proyecto'
        verbose_name_plural = 'Presupuestos de Proyectos'
        indexes = [
            models.Index(fields=['company', 'approved_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(planned_labor_cost__gte=Decimal('0.00')),
                name='project_budget_labor_non_negative',
            ),
            models.CheckConstraint(
                condition=Q(planned_expense_cost__gte=Decimal('0.00')),
                name='project_budget_expense_non_negative',
            ),
            models.CheckConstraint(
                condition=Q(planned_total_budget__gte=Decimal('0.00')),
                name='project_budget_total_non_negative',
            ),
        ]

    @property
    def is_approved(self) -> bool:
        return self.approved_date is not None

    def __str__(self):
        return f'Budget {self.project.codigo} — {self.planned_total_budget} {self.currency}'


class ExpenseCategory(models.TextChoices):
    MATERIALS     = 'materials',     'Materiales'
    EQUIPMENT     = 'equipment',     'Equipos'
    TRAVEL        = 'travel',        'Viáticos y transporte'
    SUBCONTRACTOR = 'subcontractor', 'Subcontratista'
    SOFTWARE      = 'software',      'Software / licencias'
    TRAINING      = 'training',      'Capacitación'
    OTHER         = 'other',         'Otro'


class ProjectExpense(BaseModel):
    """
    Gasto real incurrido en un proyecto.

    Los gastos pueden ser facturables (se incluyen en invoice_data)
    o no facturables (costos internos).

    El campo `amount` siempre es positivo. Para anular un gasto usar
    soft-delete (activo=False de BaseModel) — nunca importes negativos.

    El campo `approved_date` indica aprobación (approved_date IS NOT NULL ↔ aprobado).
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name='Proyecto',
    )
    category = models.CharField(
        max_length=20,
        choices=ExpenseCategory.choices,
        verbose_name='Categoría',
    )
    description = models.CharField(max_length=255, verbose_name='Descripción')
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto',
    )
    currency = models.CharField(
        max_length=3,
        default='COP',
        verbose_name='Moneda (ISO 4217)',
    )
    expense_date = models.DateField(verbose_name='Fecha del gasto')
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses_paid',
        verbose_name='Pagado por',
    )
    receipt_url = models.URLField(
        blank=True,
        verbose_name='URL comprobante',
        help_text='URL del recibo en S3 o servicio de almacenamiento.',
    )
    billable = models.BooleanField(default=True, verbose_name='Facturable')

    # Aprobación
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_expenses',
        verbose_name='Aprobado por',
    )
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de aprobación',
    )

    notes = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        db_table            = 'project_expenses'
        verbose_name        = 'Gasto de Proyecto'
        verbose_name_plural = 'Gastos de Proyecto'
        ordering            = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['project', 'expense_date']),
            models.Index(fields=['project', 'billable']),
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'expense_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=Decimal('0.00')),
                name='project_expense_amount_positive',
            ),
        ]

    @property
    def is_approved(self) -> bool:
        return self.approved_date is not None

    def __str__(self):
        return (
            f'{self.project.codigo} — {self.get_category_display()} '
            f'{self.amount} {self.currency}'
        )


class BudgetSnapshot(BaseModel):
    """
    Foto diaria del estado financiero del proyecto.

    Se genera automáticamente (via tarea periódica Celery o llamada explícita
    a create_budget_snapshot()) y sirve como serie temporal para gráficos
    de burn-rate y tendencias de costo.

    unique_together garantiza una sola foto por proyecto por día.
    Si se necesita re-generar el mismo día, create_budget_snapshot() usa
    update_or_create — la constraint no genera error en el flujo normal.
    """
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='budget_snapshots',
        verbose_name='Proyecto',
    )
    snapshot_date = models.DateField(verbose_name='Fecha del snapshot')

    # Costos reales al momento del snapshot
    labor_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo mano de obra real',
    )
    expense_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo gastos reales',
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo total real',
    )

    # Referencia presupuestal en el momento del snapshot
    planned_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Presupuesto planificado (en fecha)',
        help_text='Copia del planned_total_budget o approved_budget vigente al tomar el snapshot.',
    )

    # Variación
    variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Variación (planned - actual)',
        help_text='Positivo = bajo presupuesto. Negativo = sobre presupuesto.',
    )
    variance_percentage = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Variación (%)',
    )

    class Meta:
        db_table            = 'budget_snapshots'
        verbose_name        = 'Snapshot de Presupuesto'
        verbose_name_plural = 'Snapshots de Presupuesto'
        ordering            = ['-snapshot_date']
        unique_together     = [['project', 'snapshot_date']]
        indexes = [
            models.Index(fields=['company', 'snapshot_date']),
            models.Index(fields=['project', 'snapshot_date']),
        ]

    def __str__(self):
        return f'Snapshot {self.project.codigo} @ {self.snapshot_date} — {self.total_cost}'


# ─────────────────────────────────────────────────────────────────────────────
# Feature #8 — Project Templates
# ─────────────────────────────────────────────────────────────────────────────

class PlantillaCategoria(models.TextChoices):
    CONSTRUCCION    = 'construccion',    'Construcción'
    SOFTWARE        = 'software',        'Desarrollo de Software'
    EVENTO          = 'evento',          'Evento'
    MARKETING       = 'marketing',       'Marketing'
    PRODUCT_LAUNCH  = 'product_launch',  'Lanzamiento de Producto'


class PlantillaProyecto(BaseModel):
    """
    Plantilla reutilizable para crear proyectos con estructura predefinida.
    Contiene fases, tareas y dependencias que se clonan al instanciar un proyecto.
    """
    nombre              = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion         = models.TextField(blank=True, verbose_name='Descripción')
    tipo                = models.CharField(
        max_length=30,
        choices=ProjectType.choices,
        default=ProjectType.OTHER,
        verbose_name='Tipo de proyecto',
        help_text='Tipo de proyecto que genera esta plantilla. Determina el consecutivo de código.',
    )
    icono               = models.CharField(
        max_length=50,
        default='folder',
        verbose_name='Icono',
        help_text='Nombre del Material Icon para representar la plantilla.',
    )
    duracion_estimada   = models.IntegerField(
        default=30,
        verbose_name='Duración estimada (días)',
        help_text='Duración total estimada del proyecto en días calendario.',
    )
    is_active           = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Activa',
    )

    class Meta:
        verbose_name        = 'Plantilla de Proyecto'
        verbose_name_plural = 'Plantillas de Proyecto'
        ordering            = ['tipo', 'nombre']

    def __str__(self):
        return f'[{self.get_tipo_display()}] {self.nombre}'


class PlantillaFase(BaseModel):
    """
    Fase dentro de una plantilla de proyecto.
    El orden determina la secuencia de creación y el cálculo de fechas.
    """
    plantilla_proyecto  = models.ForeignKey(
        PlantillaProyecto,
        on_delete=models.CASCADE,
        related_name='fases_plantilla',
        verbose_name='Plantilla',
    )
    nombre              = models.CharField(max_length=255, verbose_name='Nombre')
    descripcion         = models.TextField(blank=True, verbose_name='Descripción')
    orden               = models.PositiveIntegerField(default=0, verbose_name='Orden')
    porcentaje_duracion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        verbose_name='Porcentaje de duración',
        help_text='Qué porcentaje de la duración total ocupa esta fase (0-100).',
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('100.00'))],
    )

    class Meta:
        verbose_name        = 'Fase de Plantilla'
        verbose_name_plural = 'Fases de Plantilla'
        ordering            = ['orden']
        unique_together     = [('plantilla_proyecto', 'orden')]

    def __str__(self):
        return f'{self.plantilla_proyecto.nombre} / Fase {self.orden}: {self.nombre}'


class PlantillaTarea(BaseModel):
    """
    Tarea dentro de una fase de plantilla.
    Se clona a Task al instanciar el proyecto desde la plantilla.
    """
    plantilla_fase      = models.ForeignKey(
        PlantillaFase,
        on_delete=models.CASCADE,
        related_name='tareas_plantilla',
        verbose_name='Fase de plantilla',
    )
    nombre              = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion         = models.TextField(blank=True, verbose_name='Descripción')
    orden               = models.PositiveIntegerField(default=0, verbose_name='Orden')
    duracion_dias       = models.IntegerField(
        default=1,
        verbose_name='Duración (días)',
        help_text='Duración estimada de la tarea en días calendario.',
        validators=[MinValueValidator(1)],
    )
    prioridad           = models.IntegerField(
        default=2,
        choices=[
            (1, 'Baja'),
            (2, 'Normal'),
            (3, 'Alta'),
            (4, 'Urgente'),
        ],
        verbose_name='Prioridad',
    )
    actividad_saiopen   = models.ForeignKey(
        'Activity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plantilla_tareas',
        verbose_name='Actividad',
    )

    class Meta:
        verbose_name        = 'Tarea de Plantilla'
        verbose_name_plural = 'Tareas de Plantilla'
        ordering            = ['orden']
        unique_together     = [('plantilla_fase', 'orden')]

    def __str__(self):
        return f'{self.plantilla_fase.nombre} / Tarea {self.orden}: {self.nombre}'


class PlantillaDependencia(BaseModel):
    """
    Dependencia entre tareas de una plantilla.
    Se clona a TaskDependency al instanciar el proyecto desde la plantilla.
    """
    tarea_predecesora   = models.ForeignKey(
        PlantillaTarea,
        on_delete=models.CASCADE,
        related_name='sucesoras_plantilla',
        verbose_name='Tarea predecesora',
    )
    tarea_sucesora      = models.ForeignKey(
        PlantillaTarea,
        on_delete=models.CASCADE,
        related_name='predecesoras_plantilla',
        verbose_name='Tarea sucesora',
    )
    tipo_dependencia    = models.CharField(
        max_length=2,
        choices=DependencyType.choices,
        default=DependencyType.FINISH_TO_START,
        verbose_name='Tipo de dependencia',
    )
    lag_time            = models.IntegerField(
        default=0,
        verbose_name='Lag time (días)',
        help_text='Días de desfase. Puede ser negativo para adelantar.',
    )

    class Meta:
        verbose_name        = 'Dependencia de Plantilla'
        verbose_name_plural = 'Dependencias de Plantilla'
        unique_together     = [('tarea_predecesora', 'tarea_sucesora')]

    def __str__(self):
        return (
            f'{self.tarea_predecesora.nombre} → {self.tarea_sucesora.nombre} '
            f'({self.tipo_dependencia})'
        )
