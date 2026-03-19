"""
SaiSuite — Core Models
BaseModel + ConfiguracionConsecutivo.
Regla: nunca crear un modelo sin BaseModel si tiene datos de empresa.
"""
import uuid
import logging
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class CompanyManager(models.Manager):
    """
    Manager que filtra automáticamente por la empresa del request actual.
    Se inyecta via CompanyMiddleware en el thread local.
    """
    def get_queryset(self):
        from apps.core.middleware import get_current_company
        qs = super().get_queryset()
        company = get_current_company()
        if company is not None:
            return qs.filter(company=company)
        return qs


class BaseModel(models.Model):
    """
    Modelo base para todos los modelos de negocio de SaiSuite.

    Incluye:
    - UUID como PK (no expone volumen, sin colisiones con Firebird)
    - FK a Company (multi-tenant)
    - Timestamps automáticos
    - CompanyManager como manager por defecto
    - all_objects para acceso sin filtro de tenant (solo admin/tareas)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        related_name='%(class)s_set',
        db_index=True,
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CompanyManager()
    all_objects = models.Manager()  # Sin filtro de tenant — usar solo en admin/tareas

    class Meta:
        abstract = True
        ordering = ['-created_at']


class EntidadConsecutivo(models.TextChoices):
    PROYECTO  = 'proyecto',  'Proyecto'
    ACTIVIDAD = 'actividad', 'Actividad'
    FACTURA   = 'factura',   'Factura'


class ConfiguracionConsecutivo(BaseModel):
    """
    Maestro de consecutivos por empresa.

    Cada consecutivo tiene:
    - tipo:    a qué entidad aplica (proyecto, actividad, factura)
    - subtipo: subtipo de la entidad (ej: obra_civil, mano_obra). Vacío = aplica a todos.
    - prefijo: único por empresa (ej: OBR, MOB, PRY)
    - ultimo_numero: permite fijar el número de arranque (ej: empezar desde 10)

    Al crear un documento, el sistema filtra por tipo+subtipo y:
      • Si hay 1 resultado → lo aplica automáticamente
      • Si hay varios     → pide al usuario que elija
    """
    nombre        = models.CharField(
        max_length=100,
        help_text='Nombre descriptivo. Ej: Proyectos obra civil, Actividades material',
    )
    tipo    = models.CharField(max_length=30, choices=EntidadConsecutivo.choices)
    subtipo = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Subtipo de la entidad. Vacío = aplica a todos los subtipos.',
    )
    prefijo       = models.CharField(max_length=20, help_text='Único por empresa. Ej: OBR, MOB')
    ultimo_numero = models.PositiveIntegerField(
        default=0,
        help_text='Número desde el cual se generará el siguiente código. '
                  'Útil para continuar una secuencia existente.',
    )
    formato = models.CharField(
        max_length=100, default='{prefijo}-{numero:04d}',
        help_text='Template Python. Variables: {prefijo}, {numero}.',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Configuración de consecutivo'
        verbose_name_plural = 'Configuraciones de consecutivos'
        unique_together     = [('company', 'prefijo')]
        ordering            = ['tipo', 'subtipo', 'nombre']

    def __str__(self):
        subtipo_str = f'/{self.subtipo}' if self.subtipo else ''
        return f'[{self.tipo}{subtipo_str}] {self.nombre} → {self.prefijo} (#{self.ultimo_numero})'

    def generar_preview(self) -> str:
        """Retorna el próximo código sin incrementar el contador."""
        return self.formato.format(prefijo=self.prefijo, numero=self.ultimo_numero + 1)
