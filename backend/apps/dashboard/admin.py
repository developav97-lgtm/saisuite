"""
SaiSuite -- Dashboard: Admin
Registro en Django Admin para modelos de dashboard.
"""
from django.contrib import admin

from apps.dashboard.models import (
    Dashboard,
    DashboardCard,
    DashboardShare,
    ModuleTrial,
)


class DashboardCardInline(admin.TabularInline):
    model = DashboardCard
    extra = 0
    readonly_fields = ['card_type_code', 'chart_type', 'pos_x', 'pos_y', 'width', 'height']


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin para dashboards."""
    list_display = [
        'titulo', 'user', 'company', 'es_default', 'es_favorito',
        'es_privado', 'card_count', 'created_at',
    ]
    list_filter = ['company', 'es_default', 'es_favorito', 'es_privado']
    search_fields = ['titulo', 'user__email']
    inlines = [DashboardCardInline]
    readonly_fields = ['id', 'created_at', 'updated_at']

    def card_count(self, obj) -> int:
        return obj.cards.count()
    card_count.short_description = 'Tarjetas'


@admin.register(DashboardCard)
class DashboardCardAdmin(admin.ModelAdmin):
    """Admin para tarjetas de dashboard."""
    list_display = [
        'dashboard', 'card_type_code', 'chart_type',
        'pos_x', 'pos_y', 'width', 'height', 'orden',
    ]
    list_filter = ['card_type_code', 'chart_type']
    search_fields = ['dashboard__titulo']


@admin.register(DashboardShare)
class DashboardShareAdmin(admin.ModelAdmin):
    """Admin para shares de dashboard."""
    list_display = [
        'dashboard', 'compartido_con', 'compartido_por',
        'puede_editar', 'creado_en',
    ]
    list_filter = ['puede_editar']
    search_fields = [
        'dashboard__titulo',
        'compartido_con__email',
        'compartido_por__email',
    ]
    readonly_fields = ['creado_en']


@admin.register(ModuleTrial)
class ModuleTrialAdmin(admin.ModelAdmin):
    """Admin para trials de modulos."""
    list_display = [
        'company', 'module_code', 'iniciado_en', 'expira_en',
        'trial_status',
    ]
    list_filter = ['module_code']
    search_fields = ['company__name']
    readonly_fields = ['iniciado_en']

    def trial_status(self, obj) -> str:
        if obj.esta_activo():
            return f'Activo ({obj.dias_restantes()} dias)'
        return 'Expirado'
    trial_status.short_description = 'Estado'
