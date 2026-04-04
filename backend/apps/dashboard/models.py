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
