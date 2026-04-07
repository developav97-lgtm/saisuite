# companies — admin
from django.contrib import admin
from .models import (
    Company, CompanyModule, CompanyLicense, LicenseHistory,
    LicensePayment, LicenseRenewal, LicensePackage,
    LicensePackageItem, MonthlyLicenseSnapshot, AIUsageLog, AgentToken,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display  = ['name', 'nit', 'plan', 'is_active', 'created_at']
    list_filter   = ['plan', 'is_active']
    search_fields = ['name', 'nit']
    fields        = ['name', 'nit', 'plan', 'logo', 'saiopen_enabled', 'saiopen_db_path', 'is_active']


@admin.register(CompanyModule)
class CompanyModuleAdmin(admin.ModelAdmin):
    list_display  = ['company', 'module', 'is_active']
    list_filter   = ['module', 'is_active']


@admin.register(LicensePackage)
class LicensePackageAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code', 'package_type', 'quantity', 'price_monthly', 'price_annual', 'is_active']
    list_filter   = ['package_type', 'is_active']
    search_fields = ['name', 'code', 'module_code']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(LicensePackageItem)
class LicensePackageItemAdmin(admin.ModelAdmin):
    list_display  = ['license', 'package', 'quantity', 'added_at', 'added_by']
    list_filter   = ['package__package_type']
    search_fields = ['license__company__name', 'package__name']
    readonly_fields = ['id', 'added_at']


@admin.register(MonthlyLicenseSnapshot)
class MonthlyLicenseSnapshotAdmin(admin.ModelAdmin):
    list_display  = ['license', 'month', 'created_at']
    list_filter   = ['month']
    search_fields = ['license__company__name']
    readonly_fields = ['id', 'created_at']


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'company', 'request_type', 'module_context', 'total_tokens', 'model_used', 'created_at']
    list_filter   = ['request_type', 'module_context', 'model_used']
    search_fields = ['user__email', 'company__name', 'question_preview']
    readonly_fields = ['id', 'created_at']


@admin.register(AgentToken)
class AgentTokenAdmin(admin.ModelAdmin):
    list_display   = ['company', 'label', 'is_active', 'last_used', 'created_at']
    list_filter    = ['is_active', 'company']
    search_fields  = ['company__name', 'label']
    readonly_fields = ['id', 'token', 'created_at', 'last_used']
