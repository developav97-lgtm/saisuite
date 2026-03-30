"""
SaiSuite — Modelo User
Usuario custom que reemplaza al User de Django.
Usa email como identificador en lugar de username.
"""
import uuid
import logging
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Usuario de SaiSuite. Usa email como login.
    Los roles se asignan por empresa via company FK.
    """

    class Role(models.TextChoices):
        COMPANY_ADMIN  = 'company_admin',  'Administrador de empresa'
        SELLER         = 'seller',         'Vendedor'
        COLLECTOR      = 'collector',      'Cobrador'
        VIEWER         = 'viewer',         'Solo lectura'
        VALMEN_ADMIN   = 'valmen_admin',   'Admin ValMen Tech'
        VALMEN_SUPPORT = 'valmen_support', 'Soporte ValMen Tech'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email          = models.EmailField(unique=True)
    first_name     = models.CharField(max_length=150, blank=True)
    last_name      = models.CharField(max_length=150, blank=True)
    role           = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    company        = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='users',
    )
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)
    is_superadmin  = models.BooleanField(
        default=False,
        help_text='Superadmin global ValMen Tech',
    )
    tenant_activo  = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='soporte_activos',
        help_text='Tenant activo seleccionado por usuario soporte',
    )
    rol_granular   = models.ForeignKey(
        'users.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        help_text='Rol granular con permisos específicos',
    )
    created_at     = models.DateTimeField(default=timezone.now)
    updated_at     = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['email']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def tipo_usuario(self) -> str:
        if self.is_superadmin or self.is_superuser:
            return 'superadmin'
        if self.is_staff:
            return 'soporte'
        if self.role == self.Role.COMPANY_ADMIN:
            return 'admin_tenant'
        return 'usuario_tenant'

    def tiene_permiso(self, codigo_permiso: str) -> bool:
        """Verifica si el usuario tiene un permiso granular específico."""
        if self.is_superuser or self.is_staff:
            return True
        if not self.rol_granular_id:
            return False
        return self.rol_granular.permisos.filter(codigo=codigo_permiso).exists()

    def permisos_por_modulo(self) -> dict:
        """Retorna dict {modulo: [accion, ...]} con los permisos del rol."""
        if not self.rol_granular_id:
            return {}
        resultado: dict = {}
        for permiso in self.rol_granular.permisos.all():
            resultado.setdefault(permiso.modulo, []).append(permiso.accion)
        return resultado

    @property
    def effective_company(self):
        """
        Retorna la empresa activa efectiva del usuario.
        - Soporte: tenant_activo (empresa que está inspeccionando)
        - Usuario normal: company (su empresa asignada)
        """
        if self.is_staff and not (self.is_superadmin or self.is_superuser):
            return self.tenant_activo
        return self.company


class Permission(models.Model):
    """
    Permiso granular formato modulo.accion
    Ejemplo: 'proyectos.edit', 'crm.create'
    """
    codigo      = models.CharField(
        max_length=100,
        unique=True,
        help_text="Formato: modulo.accion (ej: proyectos.edit)",
    )
    nombre      = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    modulo      = models.CharField(max_length=50)
    accion      = models.CharField(max_length=50)
    created_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['modulo', 'accion']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        indexes = [
            models.Index(fields=['modulo', 'accion']),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"


class Role(models.Model):
    """
    Rol con conjunto de permisos asignados por empresa.
    Los roles de sistema (es_sistema=True) no pueden eliminarse.
    """

    class Tipo(models.TextChoices):
        ADMIN    = 'admin',    'Administrador'
        READONLY = 'readonly', 'Solo Lectura'
        CUSTOM   = 'custom',   'Personalizado'

    nombre      = models.CharField(max_length=100)
    tipo        = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.CUSTOM)
    descripcion = models.TextField(blank=True, default='')
    permisos    = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True,
    )
    empresa     = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='roles',
    )
    es_sistema  = models.BooleanField(
        default=False,
        help_text='True para roles Admin y Solo Lectura — no se pueden eliminar',
    )
    created_at  = models.DateTimeField(default=timezone.now)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('empresa', 'nombre')]
        ordering = ['nombre']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return f"{self.nombre} ({self.empresa.name})"


class UserCompany(models.Model):
    """
    Relación User-Company con rol por empresa.
    Permite que un usuario pertenezca a múltiples empresas con distintos roles.
    """

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='user_companies',
    )
    company         = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='user_companies',
    )
    role            = models.CharField(
        max_length=20,
        choices=User.Role.choices,
        default=User.Role.VIEWER,
    )
    modules_access  = models.JSONField(
        default=list,
        blank=True,
        help_text='Subset de módulos activos de la empresa a los que tiene acceso este usuario.',
    )
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Usuario-Empresa'
        verbose_name_plural = 'Usuarios-Empresa'
        unique_together = ('user', 'company')

    def __str__(self):
        return f'{self.user.email} @ {self.company.name} ({self.role})'


class UserSession(models.Model):
    """
    Sesión activa de un usuario autenticado.
    Permite controlar sesiones concurrentes por empresa.
    Un usuario solo puede tener UNA sesión activa — si inicia sesión en otro dispositivo,
    la sesión anterior se invalida.
    """

    SESSION_TIMEOUT_MINUTES = 480  # 8 horas de inactividad

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user         = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    session_id   = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    login_time   = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    user_agent   = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Sesión de usuario'
        verbose_name_plural = 'Sesiones de usuario'
        ordering = ['-login_time']

    def __str__(self):
        return f'{self.user.email} — sesión {str(self.session_id)[:8]} ({self.login_time:%Y-%m-%d %H:%M})'

    def is_active(self) -> bool:
        """Sesión activa si tuvo actividad reciente (dentro del timeout)."""
        delta = timezone.now() - self.last_activity
        return delta < timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)

    def touch(self) -> None:
        """Actualiza last_activity (llamar en cada request autenticado)."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
