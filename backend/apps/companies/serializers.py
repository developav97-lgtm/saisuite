"""
SaiSuite — Companies: Serializers
Los serializers SOLO transforman datos. Sin lógica de negocio.
"""
from rest_framework import serializers

from .models import Company, CompanyModule


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

    def get_modules(self, obj: Company) -> list[str]:
        return list(
            CompanyModule.objects.filter(company=obj, is_active=True)
            .values_list('module', flat=True)
        )


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
