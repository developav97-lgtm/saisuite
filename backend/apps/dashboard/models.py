"""
SaiSuite -- Dashboard: Models
Dashboard, DashboardCard, DashboardShare, ModuleTrial.
Dashboard hereda de BaseModel. Card y Share no (no requieren company FK directa).
"""
import logging
from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class Dashboard(BaseModel):
    """
    Dashboard configurable por usuario.
    Cada dashboard pertenece a un usuario y una empresa (via BaseModel).
    """

    class Orientacion(models.TextChoices):
        PORTRAIT = 'portrait', 'Vertical'
        LANDSCAPE = 'landscape', 'Horizontal'

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dashboards',
    )
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, default='')
    es_privado = models.BooleanField(
        default=True,
        help_text='Solo visible para el creador y usuarios con share',
    )
    es_favorito = models.BooleanField(default=False)
    es_default = models.BooleanField(
        default=False,
        help_text='Dashboard por defecto del usuario. Solo uno por usuario.',
    )
    orientacion = models.CharField(
        max_length=20,
        choices=Orientacion.choices,
        default=Orientacion.PORTRAIT,
    )
    filtros_default = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Filtros predeterminados del dashboard. '
            'Se cargan automaticamente al abrir el dashboard en el viewer. '
            'Estructura: {fecha_desde, fecha_hasta, periodo, tercero_ids, '
            'proyecto_codigos, departamento_codigos, centro_costo_codigos, '
            'agrupar_por_mes, anio}'
        ),
    )

    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        ordering = ['-es_default', '-es_favorito', '-created_at']

    def __str__(self):
        return f'{self.titulo} ({self.user.email})'


class DashboardCard(models.Model):
    """
    Tarjeta individual dentro de un dashboard.
    No hereda BaseModel: no necesita company FK directa (la obtiene via dashboard).
    """

    class ChartType(models.TextChoices):
        BAR = 'bar', 'Barras'
        PIE = 'pie', 'Torta'
        LINE = 'line', 'Linea'
        KPI = 'kpi', 'KPI'
        TABLE = 'table', 'Tabla'
        AREA = 'area', 'Area'
        WATERFALL = 'waterfall', 'Cascada'
        GAUGE = 'gauge', 'Indicador'

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='cards',
    )
    card_type_code = models.CharField(
        max_length=50,
        help_text='Codigo del tipo de tarjeta del catalogo (ej: BALANCE_GENERAL)',
    )
    chart_type = models.CharField(
        max_length=20,
        choices=ChartType.choices,
        default=ChartType.BAR,
    )
    pos_x = models.SmallIntegerField(default=0)
    pos_y = models.SmallIntegerField(default=0)
    width = models.SmallIntegerField(default=2)
    height = models.SmallIntegerField(default=2)
    filtros_config = models.JSONField(
        default=dict, blank=True,
        help_text='Filtros especificos de esta tarjeta (periodos, terceros, etc.)',
    )
    titulo_personalizado = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Si esta vacio, se usa el titulo del catalogo',
    )
    orden = models.PositiveSmallIntegerField(default=0)

    # ── Tarjeta de tipo bi_report ─────────────────────────────────────────
    bi_report = models.ForeignKey(
        'ReportBI',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dashboard_cards',
        help_text='Reporte BI referenciado. Solo aplica cuando card_type_code="bi_report".',
    )

    class Meta:
        verbose_name = 'Tarjeta de dashboard'
        verbose_name_plural = 'Tarjetas de dashboard'
        ordering = ['orden', 'pos_y', 'pos_x']

    def __str__(self):
        return f'{self.card_type_code} @ {self.dashboard.titulo}'


class DashboardShare(models.Model):
    """
    Compartir un dashboard con otro usuario de la misma empresa.
    No hereda BaseModel.
    """
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='shares',
    )
    compartido_con = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dashboards_compartidos',
    )
    compartido_por = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='dashboards_compartidos_por_mi',
    )
    puede_editar = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dashboard compartido'
        verbose_name_plural = 'Dashboards compartidos'
        unique_together = [('dashboard', 'compartido_con')]

    def __str__(self):
        return f'{self.dashboard.titulo} -> {self.compartido_con.email}'


class ModuleTrial(models.Model):
    """
    Trial de un modulo para una empresa.
    No hereda BaseModel (tiene su propio esquema).
    El trial dura 14 dias y solo se puede activar una vez por modulo/empresa.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='module_trials',
    )
    module_code = models.CharField(
        max_length=50,
        help_text='Codigo del modulo (ej: dashboard)',
    )
    iniciado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField(
        help_text='iniciado_en + 14 dias',
    )

    class Meta:
        verbose_name = 'Trial de modulo'
        verbose_name_plural = 'Trials de modulo'
        unique_together = [('company', 'module_code')]

    def __str__(self):
        return f'{self.company.name} - {self.module_code} (expira: {self.expira_en})'

    def esta_activo(self) -> bool:
        """True si el trial no ha expirado."""
        return timezone.now() < self.expira_en

    def dias_restantes(self) -> int:
        """Dias restantes del trial. Retorna 0 si ya expiro."""
        delta = self.expira_en - timezone.now()
        days = delta.days
        return max(0, days)


class ReportBI(BaseModel):
    """Reporte BI personalizado con constructor visual."""

    class TipoVisualizacion(models.TextChoices):
        TABLE = 'table', 'Tabla'
        PIVOT = 'pivot', 'Tabla Dinámica'
        BAR = 'bar', 'Barras'
        LINE = 'line', 'Líneas'
        PIE = 'pie', 'Torta'
        AREA = 'area', 'Área'
        KPI = 'kpi', 'KPI'
        WATERFALL = 'waterfall', 'Cascada'

    class CategoriaGaleria(models.TextChoices):
        CONTABILIDAD = 'contabilidad', 'Contabilidad'
        CUENTAS_PAGAR = 'cuentas_pagar', 'Cuentas por Pagar'
        CUENTAS_COBRAR = 'cuentas_cobrar', 'Cuentas por Cobrar'
        VENTAS = 'ventas', 'Ventas'
        INVENTARIO = 'inventario', 'Inventario'
        COSTOS = 'costos', 'Costos y Gastos'
        PROYECTOS = 'proyectos', 'Proyectos'
        TRIBUTARIO = 'tributario', 'Tributario'
        GERENCIAL = 'gerencial', 'Gerencial / KPIs'

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reportes_bi',
    )

    titulo = models.CharField(max_length=200)
    es_privado = models.BooleanField(default=True)
    es_favorito = models.BooleanField(default=False)
    es_template = models.BooleanField(
        default=False,
        help_text='True para reportes predefinidos (templates)',
    )

    # Configuración de fuente de datos
    fuentes = models.JSONField(
        default=list,
        help_text='Lista de fuentes: ["gl", "facturacion", "cartera", "inventario"]',
    )

    # Campos seleccionados con configuración
    campos_config = models.JSONField(
        default=list,
        help_text=(
            'Campos configurados. Ejemplo: '
            '[{"source": "gl", "field": "tercero_nombre", '
            '"role": "dimension", "label": "Tercero"}]'
        ),
    )

    # Tipo de visualización
    tipo_visualizacion = models.CharField(
        max_length=20,
        choices=TipoVisualizacion.choices,
        default=TipoVisualizacion.TABLE,
    )

    # Configuración específica del tipo de visualización
    viz_config = models.JSONField(
        default=dict,
        blank=True,
        help_text='Config de pivot, chart, kpi según tipo_visualizacion',
    )

    # Filtros guardados
    filtros = models.JSONField(default=dict, blank=True)

    # Ordenamiento
    orden_config = models.JSONField(default=list, blank=True)

    # Límite de registros
    limite_registros = models.IntegerField(null=True, blank=True)

    # Template base
    template_origen = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reportes_derivados',
    )

    # Galería pública
    categoria_galeria = models.CharField(
        max_length=30,
        choices=CategoriaGaleria.choices,
        null=True,
        blank=True,
        help_text='Categoría para la galería pública. Solo aplica si es_template=True.',
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Reporte BI'
        verbose_name_plural = 'Reportes BI'

    def __str__(self):
        return f'{self.titulo} ({self.user.email})'


class ReportBIShare(models.Model):
    """Compartir reporte BI con otro usuario de la misma empresa."""
    reporte = models.ForeignKey(
        ReportBI,
        on_delete=models.CASCADE,
        related_name='shares',
    )
    compartido_con = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reportes_bi_compartidos',
    )
    compartido_por = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='reportes_bi_compartidos_por_mi',
    )
    puede_editar = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reporte BI compartido'
        verbose_name_plural = 'Reportes BI compartidos'
        unique_together = [('reporte', 'compartido_con')]

    def __str__(self):
        return f'{self.reporte.titulo} -> {self.compartido_con.email}'
