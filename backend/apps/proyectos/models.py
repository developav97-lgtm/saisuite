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
    cliente_id     = models.CharField(max_length=50)
    cliente_nombre = models.CharField(max_length=255)

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
                if um == 'hora':
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
        return f'{self.usuario.get_full_name()} — {self.tarea.codigo} ({self.estado})'

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
                raise ValidationError({'horas': 'Las horas deben ser mayores a 0.'})
            if self.horas > 24:
                raise ValidationError({'horas': 'Las horas no pueden superar 24 por día.'})


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


# ============================================================
# ALIASES DE COMPATIBILIDAD — eliminar en REFT-10
# ============================================================
TipoProyecto = ProjectType
EstadoProyecto = ProjectStatus
RolTercero = StakeholderRole
TipoDocumento = DocumentType
EstadoFase = PhaseStatus
ModoMedicion = MeasurementMode
TipoActividad = ActivityType
TipoDependencia = DependencyType
Proyecto = Project
ConfiguracionModulo = ModuleSettings
Fase = Phase
TerceroProyecto = ProjectStakeholder
DocumentoContable = AccountingDocument
Actividad = Activity
ActividadProyecto = ProjectActivity
ActividadSaiopen = SaiopenActivity
Hito = Milestone
TareaTag = TaskTag
Tarea = Task
SesionTrabajo = WorkSession
TareaDependencia = TaskDependency
