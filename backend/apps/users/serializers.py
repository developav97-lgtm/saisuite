"""
SaiSuite — Users Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers

from .models import User


class CompanySummarySerializer(serializers.Serializer):
    id   = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    nit  = serializers.CharField(read_only=True)


class UserMeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    company   = CompanySummarySerializer(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'is_superadmin', 'company']
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        return obj.full_name


class LoginSerializer(serializers.Serializer):
    email    = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# ---------------------------------------------------------------------------
# UserCompany summary — usado en UserMeCompaniesView
# ---------------------------------------------------------------------------

class UserCompanySummarySerializer(serializers.Serializer):
    """Empresa vista desde el UserCompany: incluye el rol que tiene el usuario en esa empresa."""

    id   = serializers.UUIDField(source='company.id', read_only=True)
    name = serializers.CharField(source='company.name', read_only=True)
    nit  = serializers.CharField(source='company.nit', read_only=True)
    plan = serializers.CharField(source='company.plan', read_only=True)
    role = serializers.CharField(read_only=True)


# ---------------------------------------------------------------------------
# Registro de empresa + primer usuario admin
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.Serializer):
    """Registro inicial: crea empresa + primer usuario admin en una transacción atómica."""

    # Datos empresa
    company_name = serializers.CharField(max_length=255)
    company_nit  = serializers.CharField(max_length=20)
    company_plan = serializers.ChoiceField(
        choices=['starter', 'professional', 'enterprise'],
        default='starter',
    )

    # Datos usuario
    email      = serializers.EmailField()
    password   = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name  = serializers.CharField(max_length=150)

    def validate_company_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El nombre de la empresa no puede estar vacío.')
        return value

    def validate_company_nit(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El NIT no puede estar vacío.')
        return value

    def validate_email(self, value: str) -> str:
        from .models import User
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value


# ---------------------------------------------------------------------------
# Creación de usuarios adicionales dentro de una empresa
# ---------------------------------------------------------------------------

class UserCreateSerializer(serializers.ModelSerializer):
    """Para crear usuarios adicionales en una empresa."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role']

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value

    def validate_role(self, value: str) -> str:
        # valmen_admin y valmen_support no se pueden crear desde este endpoint
        restricted = ('valmen_admin', 'valmen_support')
        if value in restricted:
            raise serializers.ValidationError(
                'No se pueden crear usuarios con roles de ValMen Tech desde este endpoint.'
            )
        return value


# ---------------------------------------------------------------------------
# Listado de usuarios de una empresa
# ---------------------------------------------------------------------------

class UserListSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    full_name    = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role', 'is_active', 'company_name', 'created_at']
        read_only_fields = fields

    def get_company_name(self, obj: User) -> str:
        return obj.company.name if obj.company else ''

    def get_full_name(self, obj: User) -> str:
        return obj.full_name


# ---------------------------------------------------------------------------
# Actualización de usuario (PATCH)
# ---------------------------------------------------------------------------

class UserUpdateSerializer(serializers.Serializer):
    """Campos que company_admin puede modificar en un usuario de su empresa."""

    first_name = serializers.CharField(max_length=150, required=False)
    last_name  = serializers.CharField(max_length=150, required=False)
    role       = serializers.ChoiceField(
        choices=['seller', 'collector', 'viewer', 'company_admin'],
        required=False,
    )
    is_active  = serializers.BooleanField(required=False)


# ---------------------------------------------------------------------------
# Cambio de empresa activa
# ---------------------------------------------------------------------------

class SwitchCompanySerializer(serializers.Serializer):
    company_id = serializers.UUIDField()
