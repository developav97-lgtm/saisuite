"""
SaiSuite — Companies: Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers

from .models import Company, CompanyModule, CompanyLicense, LicensePayment


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


class CompanyLicenseSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura para mostrar licencia de empresa."""

    payments        = LicensePaymentSerializer(many=True, read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_expired      = serializers.BooleanField(read_only=True)
    company_name    = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = CompanyLicense
        fields = [
            'id', 'company', 'company_name', 'plan', 'status',
            'starts_at', 'expires_at', 'max_users', 'notes',
            'days_until_expiry', 'is_expired',
            'payments', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'days_until_expiry', 'is_expired', 'created_at', 'updated_at']


class CompanyLicenseWriteSerializer(serializers.ModelSerializer):
    """Serializer de escritura para crear/actualizar licencia."""

    class Meta:
        model = CompanyLicense
        fields = ['company', 'plan', 'status', 'starts_at', 'expires_at', 'max_users', 'notes']
