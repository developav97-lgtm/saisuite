"""
SaiSuite — Modelo Company
Empresa cliente. Raíz del sistema multi-tenant.
Todo modelo de negocio tiene FK a Company.
"""
import uuid
import logging
from datetime import date
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class Company(models.Model):
    """Empresa cliente registrada en SaiSuite."""

    class Plan(models.TextChoices):
        STARTER      = 'starter',      'Starter'
        PROFESSIONAL = 'professional', 'Professional'
        ENTERPRISE   = 'enterprise',   'Enterprise'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name             = models.CharField(max_length=255)
    nit              = models.CharField(max_length=20, unique=True, help_text='NIT sin dígito de verificación')
    plan             = models.CharField(max_length=20, choices=Plan.choices, default=Plan.STARTER)
    saiopen_enabled  = models.BooleanField(default=False)
    saiopen_db_path  = models.CharField(max_length=500, blank=True, default='')
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(default=timezone.now)
    updated_at       = models.DateTimeField(auto_now=True)

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


class CompanyLicense(models.Model):
    """Licencia de uso asociada a una empresa. Una empresa = una licencia activa."""

    class Status(models.TextChoices):
        TRIAL     = 'trial',     'Prueba'
        ACTIVE    = 'active',    'Activa'
        EXPIRED   = 'expired',   'Expirada'
        SUSPENDED = 'suspended', 'Suspendida'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company    = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='license',
    )
    plan       = models.CharField(max_length=20, choices=Company.Plan.choices, default=Company.Plan.STARTER)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    starts_at  = models.DateField()
    expires_at = models.DateField()
    max_users  = models.PositiveIntegerField(default=5)
    notes      = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Licencia'
        verbose_name_plural = 'Licencias'

    def __str__(self):
        return f'{self.company.name} — {self.get_status_display()} hasta {self.expires_at}'

    @property
    def is_expired(self) -> bool:
        return date.today() > self.expires_at

    @property
    def days_until_expiry(self) -> int:
        return (self.expires_at - date.today()).days


class LicensePayment(models.Model):
    """Registro de pagos asociados a una licencia."""

    class Method(models.TextChoices):
        TRANSFER = 'transfer', 'Transferencia'
        CASH     = 'cash',     'Efectivo'
        CARD     = 'card',     'Tarjeta'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license      = models.ForeignKey(CompanyLicense, on_delete=models.CASCADE, related_name='payments')
    amount       = models.DecimalField(max_digits=15, decimal_places=2)
    payment_date = models.DateField()
    method       = models.CharField(max_length=20, choices=Method.choices, default=Method.TRANSFER)
    reference    = models.CharField(max_length=100, blank=True, default='')
    notes        = models.TextField(blank=True, default='')
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Pago de licencia'
        verbose_name_plural = 'Pagos de licencia'
        ordering = ['-payment_date']

    def __str__(self):
        return f'{self.license.company.name} — ${self.amount} el {self.payment_date}'
