# companies — admin
from django.contrib import admin
from .models import Company, CompanyModule


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
