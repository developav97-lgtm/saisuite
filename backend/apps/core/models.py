"""
SaiSuite — BaseModel
Todo modelo de negocio hereda de aquí.
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
