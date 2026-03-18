"""
SaiSuite — Modelo Company
Empresa cliente. Raíz del sistema multi-tenant.
Todo modelo de negocio tiene FK a Company.
"""
import uuid
import logging
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Company(models.Model):
    """Empresa cliente registrada en SaiSuite."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=255)
    nit        = models.CharField(max_length=20, unique=True, help_text='NIT sin dígito de verificación')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.nit})'


class CompanyModule(models.Model):
    """Módulos activos por empresa. Controla acceso a SaiVentas, SaiCobros, etc."""

    class Module(models.TextChoices):
        VENTAS     = 'ventas',     'SaiVentas'
        COBROS     = 'cobros',     'SaiCobros'
        DASHBOARD  = 'dashboard',  'SaiDashboard'
        PROYECTOS  = 'proyectos',  'SaiProyectos'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='modules')
    module     = models.CharField(max_length=20, choices=Module.choices)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Módulo de empresa'
        verbose_name_plural = 'Módulos de empresa'
        unique_together = ('company', 'module')

    def __str__(self):
        return f'{self.company.name} — {self.get_module_display()}'