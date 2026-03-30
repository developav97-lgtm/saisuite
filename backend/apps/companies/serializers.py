"""
SaiSuite — Companies: Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers

from .models import Company, CompanyModule, CompanyLicense, LicensePayment, LicenseHistory, LicenseRenewal


class CompanyModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyModule
        fields = ['id', 'module', 'is_active']
        read_only_fields = fields


class CompanyListSerializer(serializers.ModelSerializer):
    """Campos mínimos para listados."""

    class Meta:
        model = Company
        fields = ['id', 'name', 'nit', 'plan', 'is_active', 'created_at']
        read_only_fields = fields


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Todos los campos más lista de módulos activos."""

    modules = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'nit',
            'plan',
            'saiopen_enabled',
            'saiopen_db_path',
            'is_active',
            'created_at',
            'updated_at',
            'modules',
        ]
        read_only_fields = fields

    def get_modules(self, obj: Company) -> list[dict]:
        qs = CompanyModule.objects.filter(company=obj)
        return CompanyModuleSerializer(qs, many=True).data


class CompanyCreateSerializer(serializers.Serializer):
    """Para crear una nueva empresa."""

    name            = serializers.CharField(max_length=255)
    nit             = serializers.CharField(max_length=20)
    plan            = serializers.ChoiceField(
        choices=Company.Plan.choices,
        default=Company.Plan.STARTER,
    )
    saiopen_enabled = serializers.BooleanField(default=False, required=False)
    saiopen_db_path = serializers.CharField(max_length=500, allow_blank=True, default='', required=False)

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El nombre no puede estar vacío.')
        return value

    def validate_nit(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El NIT no puede estar vacío.')
        return value


class CompanyUpdateSerializer(serializers.ModelSerializer):
    """Para actualizar una empresa. NIT es read_only."""

    class Meta:
        model = Company
        fields = ['name', 'plan', 'saiopen_enabled', 'saiopen_db_path', 'nit']
        read_only_fields = ['nit']

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('El nombre no puede estar vacío.')
        return value


# ── Licencias ────────────────────────────────────────────────────────────────

class LicensePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LicensePayment
        fields = ['id', 'amount', 'payment_date', 'method', 'reference', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class LicenseHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True, default=None)

    class Meta:
        model = LicenseHistory
        fields = [
            'id', 'change_type', 'changed_by', 'changed_by_email',
            'previous_state', 'notes', 'created_at',
        ]
        read_only_fields = fields


class LicenseRenewalSerializer(serializers.ModelSerializer):
    confirmed_by_email = serializers.CharField(source='confirmed_by.email', read_only=True, default=None)
    period_display     = serializers.CharField(source='get_period_display', read_only=True)
    status_display     = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = LicenseRenewal
        fields = [
            'id', 'period', 'period_display', 'status', 'status_display',
            'new_starts_at', 'new_expires_at',
            'payment_method', 'gateway_reference',
            'auto_generated',
            'confirmed_by', 'confirmed_by_email', 'confirmed_at',
            'activated_at', 'notes', 'created_at',
        ]
        read_only_fields = ['id', 'confirmed_at', 'activated_at', 'created_at']


class CompanyLicenseSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura para mostrar licencia de empresa."""

    payments          = LicensePaymentSerializer(many=True, read_only=True)
    history           = LicenseHistorySerializer(many=True, read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_expired        = serializers.BooleanField(read_only=True)
    is_active_and_valid = serializers.BooleanField(read_only=True)
    company_name      = serializers.CharField(source='company.name', read_only=True)
    company_nit       = serializers.CharField(source='company.nit', read_only=True)
    created_by_email  = serializers.CharField(source='created_by.email', read_only=True, default=None)
    pending_renewal   = serializers.SerializerMethodField()
    period_display    = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = CompanyLicense
        fields = [
            'id', 'company', 'company_name', 'company_nit',
            'plan', 'status',
            'period', 'period_display',
            'starts_at', 'expires_at', 'max_users', 'concurrent_users',
            'modules_included',
            'messages_quota', 'messages_used',
            'ai_tokens_quota', 'ai_tokens_used',
            'last_reset_date',
            'notes',
            'days_until_expiry', 'is_expired', 'is_active_and_valid',
            'created_by', 'created_by_email',
            'pending_renewal',
            'payments', 'history',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'days_until_expiry', 'is_expired', 'is_active_and_valid',
            'created_at', 'updated_at',
        ]

    def get_pending_renewal(self, obj):
        from .services import RenewalService
        renewal = RenewalService.get_pending_renewal(obj)
        if renewal:
            return LicenseRenewalSerializer(renewal).data
        return None


class CompanyLicenseSummarySerializer(serializers.ModelSerializer):
    """Serializer ligero para listas (sin pagos ni historial)."""

    days_until_expiry   = serializers.IntegerField(read_only=True)
    is_expired          = serializers.BooleanField(read_only=True)
    is_active_and_valid = serializers.BooleanField(read_only=True)
    company_name        = serializers.CharField(source='company.name', read_only=True)
    company_nit         = serializers.CharField(source='company.nit', read_only=True)

    class Meta:
        model = CompanyLicense
        fields = [
            'id', 'company', 'company_name', 'company_nit',
            'plan', 'status',
            'starts_at', 'expires_at', 'max_users', 'concurrent_users',
            'days_until_expiry', 'is_expired', 'is_active_and_valid',
            'updated_at',
        ]
        read_only_fields = fields


class CompanyLicenseWriteSerializer(serializers.Serializer):
    """Serializer de escritura para crear/actualizar licencia."""

    plan               = serializers.ChoiceField(choices=Company.Plan.choices, required=False)
    status             = serializers.ChoiceField(choices=CompanyLicense.Status.choices, required=False)
    period             = serializers.ChoiceField(choices=CompanyLicense.Period.choices, required=False)
    starts_at          = serializers.DateField()
    expires_at         = serializers.DateField(required=False)  # Optional: calculated from period+starts_at
    max_users          = serializers.IntegerField(min_value=1, default=5, required=False)
    concurrent_users   = serializers.IntegerField(min_value=1, default=1, required=False)
    modules_included   = serializers.ListField(
        child=serializers.CharField(), default=list, required=False,
        help_text='Lista de slugs de módulos: ["proyectos", "crm"]',
    )
    messages_quota     = serializers.IntegerField(min_value=0, default=0, required=False)
    ai_tokens_quota    = serializers.IntegerField(min_value=0, default=0, required=False)
    notes              = serializers.CharField(allow_blank=True, default='', required=False)


class TenantCreateSerializer(serializers.Serializer):
    """Serializer para crear empresa + licencia inicial en un solo paso."""

    # Datos empresa
    name             = serializers.CharField(max_length=255)
    nit              = serializers.CharField(max_length=20)
    email            = serializers.EmailField(required=False, allow_blank=True, default='')
    telefono         = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    plan             = serializers.ChoiceField(choices=Company.Plan.choices, default=Company.Plan.STARTER)
    saiopen_enabled  = serializers.BooleanField(default=False, required=False)

    # Datos licencia inicial
    license_status      = serializers.ChoiceField(
        choices=CompanyLicense.Status.choices,
        default=CompanyLicense.Status.TRIAL,
    )
    license_period      = serializers.ChoiceField(
        choices=CompanyLicense.Period.choices,
        default=CompanyLicense.Period.TRIAL,
    )
    license_starts_at   = serializers.DateField()
    license_expires_at  = serializers.DateField(required=False)  # Optional override
    concurrent_users    = serializers.IntegerField(min_value=1, default=1)
    max_users           = serializers.IntegerField(min_value=1, default=5)
    modules_included    = serializers.ListField(child=serializers.CharField(), default=list, required=False)
    messages_quota      = serializers.IntegerField(min_value=0, default=0, required=False)
    ai_tokens_quota     = serializers.IntegerField(min_value=0, default=0, required=False)
    license_notes       = serializers.CharField(allow_blank=True, default='', required=False)

    def validate_nit(self, value: str) -> str:
        return value.strip()

    def validate(self, data: dict) -> dict:
        if data.get('license_expires_at') and data.get('license_starts_at'):
            if data['license_expires_at'] <= data['license_starts_at']:
                raise serializers.ValidationError(
                    {'license_expires_at': 'La fecha de vencimiento debe ser posterior al inicio.'}
                )
        return data


class TenantWithLicenseSerializer(serializers.ModelSerializer):
    """Empresa con resumen de licencia para el panel superadmin."""

    license          = CompanyLicenseSummarySerializer(read_only=True)
    active_users     = serializers.SerializerMethodField()
    modules          = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'nit', 'plan',
            'is_active', 'created_at',
            'license', 'active_users', 'modules',
        ]
        read_only_fields = fields

    def get_active_users(self, obj: Company) -> int:
        from apps.users.models import UserSession
        from django.utils import timezone
        from datetime import timedelta
        timeout_threshold = timezone.now() - timedelta(minutes=UserSession.SESSION_TIMEOUT_MINUTES)
        return UserSession.objects.filter(
            user__company=obj,
            last_activity__gte=timeout_threshold,
        ).count()

    def get_modules(self, obj: Company) -> list[str]:
        from .models import CompanyModule
        return list(
            CompanyModule.objects.filter(company=obj, is_active=True).values_list('module', flat=True)
        )
