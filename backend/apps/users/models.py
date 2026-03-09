"""
SaiSuite — Modelo User
Usuario custom que reemplaza al User de Django.
Usa email como identificador en lugar de username.
"""
import uuid
import logging
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
        COMPANY_ADMIN = 'company_admin', 'Administrador de empresa'
        SELLER       = 'seller',        'Vendedor'
        COLLECTOR    = 'collector',     'Cobrador'
        VIEWER       = 'viewer',        'Solo lectura'
        VALMEN_ADMIN = 'valmen_admin',  'Admin ValMen Tech'
        VALMEN_SUPPORT = 'valmen_support', 'Soporte ValMen Tech'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name  = models.CharField(max_length=150, blank=True)
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    company    = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='users',
    )
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

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