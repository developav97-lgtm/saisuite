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

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name             = models.CharField(max_length=255)
    nit              = models.CharField(max_length=20, unique=True, help_text='NIT sin dígito de verificación')
    saiopen_enabled  = models.BooleanField(default=False)
    saiopen_db_path  = models.CharField(max_length=500, blank=True, default='')
    logo             = models.ImageField(
                           upload_to='company_logos/',
                           null=True,
                           blank=True,
                           help_text='Logo de la empresa para reportes PDF',
                       )
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

    class RenewalType(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        AUTO   = 'auto',   'Automática'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company    = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='license',
    )
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    renewal_type = models.CharField(
        max_length=10,
        choices=RenewalType.choices,
        default=RenewalType.MANUAL,
        help_text='Manual: el admin confirma la renovación. Automática: N8N genera la solicitud 5 días antes.',
    )
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

    # Contador de mensajes IA enviados (sin cuota — solo informativo)
    messages_used   = models.PositiveIntegerField(default=0, help_text='Mensajes IA enviados en el período actual')

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


class LicensePackage(models.Model):
    """Paquete configurable para licencias. Catalogo global, no multi-tenant."""

    class PackageType(models.TextChoices):
        MODULE      = 'module',      'Modulo'
        USER_SEATS  = 'user_seats',  'Puestos de usuario'
        AI_TOKENS   = 'ai_tokens',   'Tokens IA'
        AI_MESSAGES = 'ai_messages', 'Mensajes IA'

    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code          = models.CharField(max_length=50, unique=True, help_text='Slug unico: mod_dashboard, seats_5, ai_1000')
    name          = models.CharField(max_length=100)
    description   = models.TextField(blank=True, default='')
    package_type  = models.CharField(max_length=20, choices=PackageType.choices)
    module_code   = models.CharField(max_length=50, blank=True, default='', help_text='Solo para type=module. Ej: dashboard, proyectos')
    quantity      = models.PositiveIntegerField(default=0, help_text='Cantidad: seats o tokens segun tipo')
    price_monthly = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Precio mensual COP')
    price_annual  = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Precio anual COP')
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(default=timezone.now)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paquete de licencia'
        verbose_name_plural = 'Paquetes de licencia'
        ordering = ['package_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class LicensePackageItem(models.Model):
    """Paquete asignado a una licencia especifica."""

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license  = models.ForeignKey(CompanyLicense, on_delete=models.CASCADE, related_name='package_items')
    package  = models.ForeignKey(LicensePackage, on_delete=models.PROTECT, related_name='assignments')
    quantity = models.PositiveIntegerField(default=1, help_text='Cantidad de este paquete asignado')
    added_at = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='package_assignments')

    class Meta:
        verbose_name = 'Paquete asignado'
        verbose_name_plural = 'Paquetes asignados'
        unique_together = ('license', 'package')
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.license.company.name} — {self.package.name} x{self.quantity}'


class MonthlyLicenseSnapshot(models.Model):
    """Snapshot mensual del estado de una licencia. Registro historico."""

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license    = models.ForeignKey(CompanyLicense, on_delete=models.CASCADE, related_name='snapshots')
    month      = models.DateField(help_text='Primer dia del mes del snapshot')
    snapshot   = models.JSONField(default=dict, help_text='Estado completo de la licencia al momento del snapshot')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Snapshot mensual de licencia'
        verbose_name_plural = 'Snapshots mensuales de licencia'
        unique_together = ('license', 'month')
        ordering = ['-month']

    def __str__(self):
        return f'{self.license.company.name} — {self.month:%Y-%m}'


class AIUsageLog(models.Model):
    """Registro de uso de IA por request. Tracking granular por usuario."""

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company           = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='ai_usage_logs')
    user              = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='ai_usage_logs')
    request_type      = models.CharField(max_length=50, help_text='Tipo: cfo_virtual, project_assistant, manual_guide')
    module_context    = models.CharField(max_length=50, help_text='Modulo: dashboard, proyectos, general')
    prompt_tokens     = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens      = models.PositiveIntegerField(default=0)
    model_used        = models.CharField(max_length=50, default='gpt-4o-mini')
    question_preview  = models.CharField(max_length=200, blank=True, default='', help_text='Primeros 200 chars de la pregunta')
    created_at        = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Registro de uso IA'
        verbose_name_plural = 'Registros de uso IA'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.email} — {self.request_type} ({self.total_tokens} tokens)'


class ModuleTrial(models.Model):
    """
    Trial de 14 días para un módulo específico por empresa.
    Solo se puede activar UNA VEZ por empresa/módulo.
    Lo activa únicamente el company_admin desde configuración de empresa.
    """
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company     = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_module_trials',
    )
    module_code = models.CharField(
        max_length=50,
        help_text='Código del módulo: dashboard, proyectos, crm, soporte',
    )
    iniciado_en = models.DateTimeField(default=timezone.now)
    expira_en   = models.DateTimeField(
        help_text='iniciado_en + 14 días',
    )

    class Meta:
        verbose_name = 'Trial de módulo'
        verbose_name_plural = 'Trials de módulo'
        unique_together = [('company', 'module_code')]
        ordering = ['-iniciado_en']

    def __str__(self):
        return f'{self.company.name} — {self.module_code} (expira: {self.expira_en:%Y-%m-%d})'

    @property
    def esta_activo(self) -> bool:
        return timezone.now() < self.expira_en

    @property
    def dias_restantes(self) -> int:
        delta = self.expira_en - timezone.now()
        return max(0, delta.days)


class AgentToken(models.Model):
    """
    Token estático de larga vida para autenticar el agente Go en los endpoints de sync.
    No expira — se revoca manualmente rotando el token.
    Un company puede tener múltiples tokens (multi-PC), pero normalmente uno activo.
    """
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company         = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='agent_tokens')
    token           = models.CharField(max_length=64, unique=True, editable=False)
    label           = models.CharField(max_length=100, blank=True, help_text='Etiqueta para identificar el equipo, ej: "PC principal oficina"')
    is_active       = models.BooleanField(default=True)
    # URL de la cola SQS de entrada del agente (dirección SaiCloud → Sai).
    # Cada empresa debe tener su propia cola dedicada para que los mensajes
    # no sean visibles a otros agentes. Ejemplo:
    #   https://sqs.us-east-1.amazonaws.com/123456789/cloud-to-saicloud-empresa1
    # Dejar vacío si no se usa push Cloud→Sai.
    sync_server_url = models.CharField(
        max_length=500, blank=True, default='',
        help_text='URL de la cola SQS de entrada del agente (Cloud→Sai), ej: https://sqs.us-east-1.amazonaws.com/.../cloud-to-saicloud-empresa1'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    last_used       = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Token de agente'
        verbose_name_plural = 'Tokens de agente'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.token:
            import secrets
            self.token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.company.name} — {self.label or self.id} ({"activo" if self.is_active else "revocado"})'


class LicenseRequest(models.Model):
    """
    Solicitud de ampliación de licencia iniciada por el company_admin.
    Tipos:
      - user_seats : solicita un paquete adicional de usuarios
      - module     : solicita licenciar un módulo (después del trial)
      - ai_tokens  : solicita cambiar el paquete de tokens IA (reemplaza el anterior)
    El superadmin aprueba → el sistema aplica el paquete automáticamente.
    """

    class RequestType(models.TextChoices):
        USER_SEATS = 'user_seats', 'Usuarios adicionales'
        MODULE     = 'module',     'Módulo'
        AI_TOKENS  = 'ai_tokens',  'Tokens IA'

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company      = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='license_requests')
    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    package      = models.ForeignKey(
        LicensePackage,
        on_delete=models.PROTECT,
        related_name='license_requests',
        help_text='Paquete específico que se solicita agregar/reemplazar',
    )
    status       = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    notes        = models.TextField(blank=True, default='', help_text='Nota opcional del solicitante')
    review_notes = models.TextField(blank=True, default='', help_text='Nota del admin al aprobar/rechazar')
    created_by   = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='license_requests_created',
    )
    reviewed_by  = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='license_requests_reviewed',
    )
    reviewed_at  = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Solicitud de licencia'
        verbose_name_plural = 'Solicitudes de licencia'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.company.name} — {self.get_request_type_display()} — {self.get_status_display()}'
