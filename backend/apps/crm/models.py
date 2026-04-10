"""
SaiSuite — Módulo CRM
Pipeline de ventas, Leads, Oportunidades, Actividades, Cotizaciones.
"""
import logging
from django.conf import settings
from django.db import models
from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# PIPELINE Y ETAPAS
# ─────────────────────────────────────────────

class CrmPipeline(BaseModel):
    """Pipeline de ventas. Una empresa puede tener múltiples pipelines."""
    nombre      = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    es_default  = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Pipeline CRM'
        verbose_name_plural = 'Pipelines CRM'
        ordering            = ['-es_default', 'nombre']

    def __str__(self):
        return f'{self.nombre} ({self.company})'


class CrmEtapa(BaseModel):
    """Etapa dentro de un pipeline. Define el orden y la probabilidad de cierre."""
    pipeline     = models.ForeignKey(CrmPipeline, on_delete=models.CASCADE, related_name='etapas')
    nombre       = models.CharField(max_length=100)
    orden        = models.PositiveSmallIntegerField(default=0)
    probabilidad = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100%
    es_ganado    = models.BooleanField(default=False)
    es_perdido   = models.BooleanField(default=False)
    color        = models.CharField(max_length=7, default='#2196F3')  # hex

    class Meta:
        verbose_name        = 'Etapa CRM'
        verbose_name_plural = 'Etapas CRM'
        ordering            = ['pipeline', 'orden']
        unique_together     = [('pipeline', 'orden')]

    def __str__(self):
        return f'{self.pipeline.nombre} › {self.nombre}'


# ─────────────────────────────────────────────
# LEADS
# ─────────────────────────────────────────────

class FuenteLead(models.TextChoices):
    MANUAL  = 'manual',  'Manual'
    CSV     = 'csv',     'Importación CSV/Excel'
    WEBHOOK = 'webhook', 'Formulario web (webhook)'
    EMAIL   = 'email',   'Correo entrante'
    OTRO    = 'otro',    'Otro'


class CrmLead(BaseModel):
    """
    Prospecto antes de ser calificado como oportunidad.
    Una vez convertido, genera un CrmOportunidad (y opcionalmente un Tercero).
    """
    nombre       = models.CharField(max_length=200)
    empresa      = models.CharField(max_length=200, blank=True)
    email        = models.EmailField(blank=True)
    telefono     = models.CharField(max_length=50, blank=True)
    cargo        = models.CharField(max_length=100, blank=True)
    fuente       = models.CharField(max_length=20, choices=FuenteLead.choices, default=FuenteLead.MANUAL)
    notas        = models.TextField(blank=True)
    score        = models.PositiveSmallIntegerField(default=0)  # 0-100

    pipeline     = models.ForeignKey(CrmPipeline, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    asignado_a   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='crm_leads')

    convertido   = models.BooleanField(default=False)
    convertido_en = models.DateTimeField(null=True, blank=True)
    oportunidad  = models.OneToOneField(
        'CrmOportunidad', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lead_origen_rel',
    )
    tercero      = models.ForeignKey(
        'terceros.Tercero', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='crm_leads',
    )

    class Meta:
        verbose_name        = 'Lead CRM'
        verbose_name_plural = 'Leads CRM'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.nombre} ({self.empresa or "sin empresa"})'


class OperadorRegla(models.TextChoices):
    EQ        = 'eq',        'Igual a'
    CONTAINS  = 'contains',  'Contiene'
    GTE       = 'gte',       'Mayor o igual a'
    LTE       = 'lte',       'Menor o igual a'
    NOT_EMPTY = 'not_empty', 'No está vacío'
    IS_EMPTY  = 'is_empty',  'Está vacío'


class CrmLeadScoringRule(BaseModel):
    """Regla de puntuación automática para leads."""
    nombre   = models.CharField(max_length=100)
    campo    = models.CharField(max_length=50, help_text='Ej: fuente, empresa, email, telefono')
    operador = models.CharField(max_length=20, choices=OperadorRegla.choices)
    valor    = models.CharField(max_length=200, blank=True, help_text='Valor a comparar')
    puntos   = models.SmallIntegerField(help_text='Positivo suma, negativo resta')
    orden    = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name        = 'Regla de scoring'
        verbose_name_plural = 'Reglas de scoring'
        ordering            = ['orden']

    def __str__(self):
        return f'{self.nombre} ({self.puntos:+d} pts)'


# ─────────────────────────────────────────────
# OPORTUNIDADES
# ─────────────────────────────────────────────

class CrmOportunidad(BaseModel):
    """
    Oportunidad de venta. Núcleo del CRM.
    Vinculada a un Tercero (cliente), pipeline, etapa y vendedor.
    """
    titulo                  = models.CharField(max_length=200)
    contacto                = models.ForeignKey(
        'terceros.Tercero', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='crm_oportunidades',
    )
    pipeline                = models.ForeignKey(CrmPipeline, on_delete=models.PROTECT, related_name='oportunidades')
    etapa                   = models.ForeignKey(CrmEtapa, on_delete=models.PROTECT, related_name='oportunidades')
    valor_esperado          = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    probabilidad            = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_cierre_estimada   = models.DateField(null=True, blank=True)
    asignado_a              = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='crm_oportunidades',
    )
    descripcion             = models.TextField(blank=True)

    # Tracking de estados
    ganada_en               = models.DateTimeField(null=True, blank=True)
    perdida_en              = models.DateTimeField(null=True, blank=True)
    motivo_perdida          = models.CharField(max_length=200, blank=True)

    # Próxima actividad (denormalizado para performance en kanban)
    proxima_actividad_fecha = models.DateTimeField(null=True, blank=True)
    proxima_actividad_tipo  = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name        = 'Oportunidad CRM'
        verbose_name_plural = 'Oportunidades CRM'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.titulo} [{self.etapa.nombre}]'

    @property
    def valor_ponderado(self):
        """Valor esperado × probabilidad de etapa."""
        return self.valor_esperado * (self.etapa.probabilidad / 100)

    @property
    def esta_ganada(self):
        return self.etapa.es_ganado

    @property
    def esta_perdida(self):
        return self.etapa.es_perdido


# ─────────────────────────────────────────────
# ACTIVIDADES Y TIMELINE
# ─────────────────────────────────────────────

class TipoActividad(models.TextChoices):
    LLAMADA  = 'llamada',  'Llamada'
    REUNION  = 'reunion',  'Reunión'
    EMAIL    = 'email',    'Email'
    TAREA    = 'tarea',    'Tarea'


class CrmActividad(BaseModel):
    """Actividad programada sobre una oportunidad o un lead."""
    oportunidad      = models.ForeignKey(
        CrmOportunidad, on_delete=models.CASCADE, related_name='actividades',
        null=True, blank=True,
    )
    lead             = models.ForeignKey(
        CrmLead, on_delete=models.CASCADE, related_name='actividades',
        null=True, blank=True,
    )
    tipo             = models.CharField(max_length=20, choices=TipoActividad.choices)
    titulo           = models.CharField(max_length=200)
    descripcion      = models.TextField(blank=True)
    fecha_programada = models.DateTimeField()
    completada       = models.BooleanField(default=False)
    completada_en    = models.DateTimeField(null=True, blank=True)
    asignado_a       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='crm_actividades',
    )
    resultado        = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Actividad CRM'
        verbose_name_plural = 'Actividades CRM'
        ordering            = ['fecha_programada']

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.titulo}'


class TipoTimelineEvent(models.TextChoices):
    NOTA               = 'nota',               'Nota'
    CAMBIO_ETAPA       = 'cambio_etapa',       'Cambio de etapa'
    ACTIVIDAD_COMP     = 'actividad_completada','Actividad completada'
    EMAIL_ENVIADO      = 'email_enviado',      'Email enviado'
    COTIZACION_CREADA  = 'cotizacion_creada',  'Cotización creada'
    COTIZACION_ACEPT   = 'cotizacion_aceptada','Cotización aceptada'
    LEAD_CONVERTIDO    = 'lead_convertido',    'Lead convertido'
    SISTEMA            = 'sistema',            'Sistema'


class CrmTimelineEvent(BaseModel):
    """
    Evento inmutable en el muro/timeline de una oportunidad.
    No se elimina — is_active siempre True para este modelo.
    """
    oportunidad = models.ForeignKey(CrmOportunidad, on_delete=models.CASCADE, related_name='timeline')
    tipo        = models.CharField(max_length=30, choices=TipoTimelineEvent.choices)
    descripcion = models.TextField()
    usuario     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='crm_timeline_events',
    )
    metadata    = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name        = 'Evento timeline CRM'
        verbose_name_plural = 'Eventos timeline CRM'
        ordering            = ['-created_at']

    def __str__(self):
        return f'[{self.get_tipo_display()}] {self.oportunidad.titulo}'


# ─────────────────────────────────────────────
# CATÁLOGO: IMPUESTOS Y PRODUCTOS
# ─────────────────────────────────────────────

class CrmImpuesto(BaseModel):
    """
    Tarifa de impuesto (IVA u otro).
    Sincronizado desde Saiopen TAXAUTH.
    """
    nombre         = models.CharField(max_length=50)
    porcentaje     = models.DecimalField(max_digits=6, decimal_places=4, default=0)  # 0.1900 = 19%
    es_default     = models.BooleanField(default=False)
    # Sync Saiopen TAXAUTH
    sai_key        = models.CharField(max_length=20, null=True, blank=True)  # TAXAUTH.CODIGO
    saiopen_synced = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Impuesto CRM'
        verbose_name_plural = 'Impuestos CRM'
        ordering            = ['nombre']
        unique_together     = [('company', 'sai_key')]

    def __str__(self):
        return f'{self.nombre} ({self.porcentaje * 100:.0f}%)'


class CrmProducto(BaseModel):
    """
    Producto o servicio del catálogo. Sincronizado desde Saiopen ITEM.
    Solo lectura desde CRM — los productos se gestionan en Saiopen.
    """
    codigo         = models.CharField(max_length=30, db_index=True)    # ITEM.ITEM
    nombre         = models.CharField(max_length=200)                   # ITEM.DESCRIPCION
    descripcion    = models.TextField(blank=True)
    precio_base    = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # ITEM.PRICE
    unidad_venta   = models.CharField(max_length=20, blank=True)        # ITEM.UOFMSALES
    impuesto       = models.ForeignKey(CrmImpuesto, on_delete=models.SET_NULL, null=True, blank=True)
    clase          = models.CharField(max_length=10, blank=True)        # ITEM.CLASS
    grupo          = models.CharField(max_length=10, blank=True)        # ITEM.GRUPO
    is_active      = models.BooleanField(default=True)                      # ITEM.ESTADO
    # Sync Saiopen ITEM
    sai_key        = models.CharField(max_length=30, null=True, blank=True)  # ITEM.ITEM
    saiopen_synced = models.BooleanField(default=False)
    ultima_sync    = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Producto CRM'
        verbose_name_plural = 'Productos CRM'
        ordering            = ['nombre']
        unique_together     = [('company', 'sai_key')]

    def __str__(self):
        return f'[{self.codigo}] {self.nombre}'


# ─────────────────────────────────────────────
# COTIZACIONES
# ─────────────────────────────────────────────

class EstadoCotizacion(models.TextChoices):
    BORRADOR  = 'borrador',  'Borrador'
    ENVIADA   = 'enviada',   'Enviada'
    ACEPTADA  = 'aceptada',  'Aceptada'
    RECHAZADA = 'rechazada', 'Rechazada'
    VENCIDA   = 'vencida',   'Vencida'
    ANULADA   = 'anulada',   'Anulada'


class CrmCotizacion(BaseModel):
    """
    Cotización vinculada a una oportunidad.
    Se sincroniza con Saiopen COTIZACI solo cuando el estado = 'aceptada'.
    """
    oportunidad             = models.ForeignKey(CrmOportunidad, on_delete=models.CASCADE, related_name='cotizaciones')
    numero_interno          = models.CharField(max_length=20)
    titulo                  = models.CharField(max_length=200)
    contacto                = models.ForeignKey(
        'terceros.Tercero', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='crm_cotizaciones',
    )
    validez_dias            = models.PositiveSmallIntegerField(default=30)
    fecha_vencimiento       = models.DateField(null=True, blank=True)
    estado                  = models.CharField(max_length=20, choices=EstadoCotizacion.choices, default=EstadoCotizacion.BORRADOR)

    # Totales (se recalculan al guardar líneas)
    subtotal                = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento_adicional_p   = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento_adicional_val = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_iva               = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total                   = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    observaciones           = models.TextField(blank=True)
    condiciones             = models.TextField(blank=True)

    # Sync Saiopen COTIZACI (se llena solo cuando estado='aceptada')
    sai_numero              = models.IntegerField(null=True, blank=True)
    sai_tipo                = models.CharField(max_length=3, null=True, blank=True)
    sai_empresa             = models.SmallIntegerField(null=True, blank=True)
    sai_sucursal            = models.SmallIntegerField(null=True, blank=True)
    sai_key                 = models.CharField(max_length=50, null=True, blank=True)
    saiopen_synced          = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Cotización CRM'
        verbose_name_plural = 'Cotizaciones CRM'
        ordering            = ['-created_at']
        unique_together     = [('company', 'sai_key')]

    def __str__(self):
        return f'{self.numero_interno} — {self.titulo} [{self.get_estado_display()}]'


class CrmLineaCotizacion(BaseModel):
    """Línea de producto en una cotización. Mapea a DET_PROD de Saiopen."""
    cotizacion       = models.ForeignKey(CrmCotizacion, on_delete=models.CASCADE, related_name='lineas')
    conteo           = models.PositiveSmallIntegerField()               # DET_PROD.CONTEO (orden de línea)
    producto         = models.ForeignKey(CrmProducto, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion      = models.CharField(max_length=200)                 # DET_PROD.DESCRIPCION
    descripcion_adic = models.TextField(blank=True)                     # DET_PROD.DESCRIPCION_ADIC
    cantidad         = models.DecimalField(max_digits=15, decimal_places=4, default=1)
    vlr_unitario     = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento_p      = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # DET_PROD.DESCTOP
    impuesto         = models.ForeignKey(CrmImpuesto, on_delete=models.SET_NULL, null=True, blank=True)
    iva_valor        = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_parcial    = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # DET_PROD.TOTAL_PARC

    # Saiopen extras para sync fiel
    proyecto         = models.CharField(max_length=10, blank=True)
    actividad        = models.CharField(max_length=3, blank=True)

    class Meta:
        verbose_name        = 'Línea de cotización'
        verbose_name_plural = 'Líneas de cotización'
        ordering            = ['conteo']
        unique_together     = [('cotizacion', 'conteo')]

    def __str__(self):
        return f'[{self.conteo}] {self.descripcion} × {self.cantidad}'
