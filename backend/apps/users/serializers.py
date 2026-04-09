"""
SaiSuite — Users Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers

from .models import Permission, Role, User


# ---------------------------------------------------------------------------
# Permisos y Roles granulares
# ---------------------------------------------------------------------------

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ['id', 'codigo', 'nombre', 'descripcion', 'modulo', 'accion']


class RoleSerializer(serializers.ModelSerializer):
    permisos       = PermissionSerializer(many=True, read_only=True)
    usuarios_count = serializers.SerializerMethodField()

    class Meta:
        model  = Role
        fields = [
            'id', 'nombre', 'tipo', 'descripcion',
            'permisos', 'es_sistema', 'usuarios_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'es_sistema', 'created_at', 'updated_at']

    def get_usuarios_count(self, obj: Role) -> int:
        return obj.usuarios.count()


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    permisos_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model  = Role
        fields = ['nombre', 'descripcion', 'permisos_ids']

    def create(self, validated_data: dict) -> Role:
        permisos_ids = validated_data.pop('permisos_ids', [])
        validated_data['tipo']       = Role.Tipo.CUSTOM
        validated_data['es_sistema'] = False
        role = Role.objects.create(**validated_data)
        if permisos_ids:
            role.permisos.set(Permission.objects.filter(id__in=permisos_ids))
        return role

    def update(self, instance: Role, validated_data: dict) -> Role:
        permisos_ids = validated_data.pop('permisos_ids', None)
        instance.nombre      = validated_data.get('nombre',      instance.nombre)
        instance.descripcion = validated_data.get('descripcion', instance.descripcion)
        instance.save(update_fields=['nombre', 'descripcion', 'updated_at'])
        if permisos_ids is not None:
            instance.permisos.set(Permission.objects.filter(id__in=permisos_ids))
        return instance


# ---------------------------------------------------------------------------
# Serializer mínimo de rol para incluir en UserListSerializer
# ---------------------------------------------------------------------------

class RoleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Role
        fields = ['id', 'nombre', 'tipo']


class PermissionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ['id', 'codigo', 'modulo', 'accion']


class RolGranularMeSerializer(serializers.ModelSerializer):
    """Incluye el array de permisos — usado solo en /api/v1/auth/me/."""
    permisos = PermissionMiniSerializer(many=True, read_only=True)

    class Meta:
        model  = Role
        fields = ['id', 'nombre', 'tipo', 'permisos']


class LicenseSummarySerializer(serializers.Serializer):
    """Resumen mínimo de licencia incluido en el perfil de usuario."""
    status              = serializers.CharField(read_only=True)
    expires_at          = serializers.DateField(read_only=True)
    days_until_expiry   = serializers.IntegerField(read_only=True)
    is_active_and_valid = serializers.SerializerMethodField(read_only=True)
    concurrent_users    = serializers.IntegerField(read_only=True)
    modules_included    = serializers.JSONField(read_only=True)

    def get_is_active_and_valid(self, obj) -> bool:
        return obj.is_active_and_valid


class CompanySummarySerializer(serializers.Serializer):
    id      = serializers.UUIDField(read_only=True)
    name    = serializers.CharField(read_only=True)
    nit     = serializers.CharField(read_only=True)
    plan    = serializers.SerializerMethodField()
    license = serializers.SerializerMethodField()

    def get_plan(self, obj) -> str | None:
        return None

    def get_license(self, obj) -> dict | None:
        try:
            lic = obj.license
            return LicenseSummarySerializer(lic).data
        except Exception:
            return None


class UserMeSerializer(serializers.ModelSerializer):
    full_name          = serializers.SerializerMethodField()
    company            = CompanySummarySerializer(read_only=True)
    effective_company  = serializers.SerializerMethodField()
    tipo_usuario       = serializers.ReadOnlyField()
    tenant_activo      = serializers.SerializerMethodField()
    rol_granular       = RolGranularMeSerializer(read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_superadmin', 'is_staff', 'company',
            'tipo_usuario', 'tenant_activo', 'effective_company',
            'rol_granular',
        ]
        read_only_fields = fields

    def get_full_name(self, obj: User) -> str:
        return obj.full_name

    def get_tenant_activo(self, obj: User) -> dict | None:
        tenant = obj.tenant_activo
        if not tenant:
            return None
        return {'id': str(tenant.id), 'name': tenant.name, 'nit': tenant.nit}

    def get_effective_company(self, obj: User) -> dict | None:
        """La empresa activa real: tenant_activo para soporte, company para el resto."""
        ec = obj.effective_company
        if not ec:
            return None
        result = {'id': str(ec.id), 'name': ec.name, 'nit': ec.nit, 'plan': None}
        try:
            lic = ec.license
            result['license'] = {
                'status': lic.status,
                'expires_at': str(lic.expires_at),
                'days_until_expiry': lic.days_until_expiry,
                'is_active_and_valid': lic.is_active_and_valid,
                'concurrent_users': lic.concurrent_users,
                'modules_included': lic.modules_included or [],
            }
        except Exception:
            result['license'] = None
        return result


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
    plan = serializers.SerializerMethodField()
    role = serializers.CharField(read_only=True)

    def get_plan(self, obj) -> str | None:
        return None


# ---------------------------------------------------------------------------
# Registro de empresa + primer usuario admin
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.Serializer):
    """Registro inicial: crea empresa + primer usuario admin en una transacción atómica."""

    # Datos empresa
    company_name = serializers.CharField(max_length=255)
    company_nit  = serializers.CharField(max_length=20)

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

    password       = serializers.CharField(write_only=True, min_length=8)
    modules_access = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True, default=list,
    )

    class Meta:
        model  = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role', 'modules_access']

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
    company_name   = serializers.SerializerMethodField()
    full_name      = serializers.SerializerMethodField()
    modules_access = serializers.SerializerMethodField()
    rol_granular   = RoleSummarySerializer(read_only=True)

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'company_name', 'modules_access',
            'rol_granular', 'created_at',
        ]
        read_only_fields = fields

    def get_company_name(self, obj: User) -> str:
        return obj.company.name if obj.company else ''

    def get_full_name(self, obj: User) -> str:
        return obj.full_name

    def get_modules_access(self, obj: User) -> list:
        """Lee modules_access del UserCompany activo para esta empresa."""
        from .models import UserCompany
        try:
            uc = UserCompany.objects.get(user=obj, company=obj.company)
            return uc.modules_access or []
        except UserCompany.DoesNotExist:
            return []


# ---------------------------------------------------------------------------
# Actualización de usuario (PATCH)
# ---------------------------------------------------------------------------

class UserUpdateSerializer(serializers.Serializer):
    """Campos que company_admin puede modificar en un usuario de su empresa."""

    first_name       = serializers.CharField(max_length=150, required=False)
    last_name        = serializers.CharField(max_length=150, required=False)
    role             = serializers.ChoiceField(
        choices=['company_admin', 'seller', 'viewer'],
        required=False,
    )
    is_active        = serializers.BooleanField(required=False)
    modules_access   = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True,
    )
    rol_granular_id  = serializers.IntegerField(required=False, allow_null=True)


# ---------------------------------------------------------------------------
# Cambio de empresa activa
# ---------------------------------------------------------------------------

class SwitchCompanySerializer(serializers.Serializer):
    company_id = serializers.UUIDField()


# ---------------------------------------------------------------------------
# Recuperación de contraseña
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Usuarios internos ValMen Tech (superadmin + soporte)
# ---------------------------------------------------------------------------

class InternalUserCreateSerializer(serializers.Serializer):
    email       = serializers.EmailField()
    password    = serializers.CharField(write_only=True, min_length=8)
    first_name  = serializers.CharField(max_length=150)
    last_name   = serializers.CharField(max_length=150)
    is_staff    = serializers.BooleanField(default=True)
    is_superadmin = serializers.BooleanField(default=False)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value


class InternalUserUpdateSerializer(serializers.Serializer):
    first_name    = serializers.CharField(max_length=150, required=False)
    last_name     = serializers.CharField(max_length=150, required=False)
    is_staff      = serializers.BooleanField(required=False)
    is_superadmin = serializers.BooleanField(required=False)
    is_active     = serializers.BooleanField(required=False)
    password      = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid      = serializers.CharField()
    token    = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
