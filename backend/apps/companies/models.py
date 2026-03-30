"""
SaiSuite — Modelo Company
Empresa cliente. Raíz del sistema multi-tenant.
Todo modelo de negocio tiene FK a Company.
"""
import uuid
import logging
from datetime import date
import zoneinfo
from django.db import models
from django.utils import timezone

# Zona horaria de Colombia (UTC-5, sin horario de verano)
_TZ_COLOMBIA = zoneinfo.ZoneInfo('America/Bogota')

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
    """Módulos activos por empresa. Controla acceso a CRM, Soporte, etc."""

    class Module(models.TextChoices):
        CRM        = 'crm',        'CRM'
        SOPORTE    = 'soporte',    'Soporte'
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

    class Period(models.TextChoices):
        TRIAL      = 'trial',      'Prueba (14 días)'
        MONTHLY    = 'monthly',    'Mensual (30 días)'
        BIMONTHLY  = 'bimonthly',  'Bimestral (60 días)'
        QUARTERLY  = 'quarterly',  'Trimestral (90 días)'
        ANNUAL     = 'annual',     'Anual (360 días)'

    PERIOD_DAYS = {
        'trial':     14,
        'monthly':   30,
        'bimonthly': 60,
        'quarterly': 90,
        'annual':    360,
    }

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company    = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='license',
    )
    plan       = models.CharField(max_length=20, choices=Company.Plan.choices, default=Company.Plan.STARTER)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    period     = models.CharField(
        max_length=20,
        choices=Period.choices,
        default=Period.TRIAL,
        help_text='Período de la licencia.',
    )
    starts_at  = models.DateField()
    expires_at = models.DateField()
    max_users  = models.PositiveIntegerField(default=5)

    # Control de sesiones concurrentes
    concurrent_users = models.PositiveIntegerField(
        default=1,
        help_text='Número máximo de usuarios simultáneos permitidos',
    )

    # Módulos incluidos en la licencia
    modules_included = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de slugs de módulos incluidos. Ej: ["proyectos", "crm"]',
    )

    # Cuota de mensajes IA (por mes)
    messages_quota  = models.PositiveIntegerField(default=0, help_text='Mensajes IA disponibles por mes')
    messages_used   = models.PositiveIntegerField(default=0, help_text='Mensajes IA usados en el período actual')

    # Cuota de tokens IA (por mes)
    ai_tokens_quota = models.PositiveIntegerField(default=0, help_text='Tokens IA disponibles por mes')
    ai_tokens_used  = models.PositiveIntegerField(default=0, help_text='Tokens IA usados en el período actual')

    # Control de reset mensual
    last_reset_date = models.DateField(null=True, blank=True, help_text='Última vez que se resetearon los contadores mensuales')

    # Auditoría
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='licenses_created',
        help_text='Superadmin que creó esta licencia',
    )
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
        today_col = timezone.now().astimezone(_TZ_COLOMBIA).date()
        return today_col > self.expires_at

    @property
    def days_until_expiry(self) -> int:
        # Usar la fecha local de Colombia (UTC-5) para que el conteo no cambie
        # a medianoche UTC (que llega a las 7pm Colombia).
        today_col = timezone.now().astimezone(_TZ_COLOMBIA).date()
        return (self.expires_at - today_col).days

    @property
    def is_active_and_valid(self) -> bool:
        return self.status in (self.Status.TRIAL, self.Status.ACTIVE) and not self.is_expired

    def reset_monthly_usage(self) -> None:
        """Reinicia contadores de mensajes y tokens al inicio del mes."""
        self.messages_used  = 0
        self.ai_tokens_used = 0
        self.last_reset_date = date.today()
        self.save(update_fields=['messages_used', 'ai_tokens_used', 'last_reset_date'])


class LicenseHistory(models.Model):
    """
    Historial de cambios sobre una licencia.
    Se crea un registro cada vez que la licencia se actualiza (renovación, suspensión, etc.)
    """

    class ChangeType(models.TextChoices):
        CREATED            = 'created',            'Creada'
        RENEWED            = 'renewed',            'Renovada'
        EXTENDED           = 'extended',           'Extendida'
        SUSPENDED          = 'suspended',          'Suspendida'
        ACTIVATED          = 'activated',          'Activada'
        MODIFIED           = 'modified',           'Modificada'
        RENEWAL_GENERATED  = 'renewal_generated',  'Renovación generada'
        RENEWAL_CONFIRMED  = 'renewal_confirmed',  'Pago confirmado'
        RENEWAL_ACTIVATED  = 'renewal_activated',  'Renovación activada'
        RENEWAL_CANCELLED  = 'renewal_cancelled',  'Renovación cancelada'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license     = models.ForeignKey(
        CompanyLicense,
        on_delete=models.CASCADE,
        related_name='history',
    )
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    changed_by  = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='license_changes',
    )
    # Snapshot del estado anterior (JSON)
    previous_state = models.JSONField(default=dict, blank=True)
    notes          = models.TextField(blank=True, default='')
    created_at     = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Historial de licencia'
        verbose_name_plural = 'Historial de licencias'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.license.company.name} — {self.get_change_type_display()} ({self.created_at:%Y-%m-%d})'


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


class LicenseRenewal(models.Model):
    """
    Renovación pendiente de una licencia.
    Permite el flujo: pendiente → confirmado → activado.
    Diseñado para soportar pasarela de pago futura.
    """

    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pendiente de pago'
        CONFIRMED = 'confirmed', 'Pago confirmado'
        ACTIVATED = 'activated', 'Activada'
        CANCELLED = 'cancelled', 'Cancelada'

    class PaymentMethod(models.TextChoices):
        MANUAL  = 'manual',  'Manual'
        GATEWAY = 'gateway', 'Pasarela de pago'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license        = models.ForeignKey(
        CompanyLicense, on_delete=models.CASCADE, related_name='renewals',
    )
    period         = models.CharField(max_length=20, choices=CompanyLicense.Period.choices)
    new_starts_at  = models.DateField()
    new_expires_at = models.DateField()
    status         = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.MANUAL,
    )
    gateway_reference = models.CharField(max_length=255, blank=True, default='')
    gateway_payload   = models.JSONField(default=dict, blank=True)
    auto_generated    = models.BooleanField(
        default=False, help_text='Generada automáticamente por el sistema',
    )
    confirmed_by   = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='renewals_confirmed',
    )
    confirmed_at   = models.DateTimeField(null=True, blank=True)
    activated_at   = models.DateTimeField(null=True, blank=True)
    notes          = models.TextField(blank=True, default='')
    created_at     = models.DateTimeField(default=timezone.now)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Renovación de licencia'
        verbose_name_plural = 'Renovaciones de licencia'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.license.company.name} — renovación {self.get_status_display()} ({self.new_expires_at})'
