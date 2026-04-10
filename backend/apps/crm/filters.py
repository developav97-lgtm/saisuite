"""SaiSuite — CRM Filters"""
import django_filters
from .models import CrmLead, CrmOportunidad, CrmActividad, CrmProducto


class CrmLeadFilter(django_filters.FilterSet):
    fuente     = django_filters.CharFilter(field_name='fuente')
    convertido = django_filters.BooleanFilter(field_name='convertido')
    search     = django_filters.CharFilter(method='filter_search')
    pipeline   = django_filters.UUIDFilter(field_name='pipeline__id')

    class Meta:
        model  = CrmLead
        fields = ['fuente', 'convertido', 'pipeline']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(empresa__icontains=value) |
            Q(email__icontains=value)
        )


class CrmOportunidadFilter(django_filters.FilterSet):
    pipeline    = django_filters.UUIDFilter(field_name='pipeline__id')
    etapa       = django_filters.UUIDFilter(field_name='etapa__id')
    asignado_a  = django_filters.UUIDFilter(field_name='asignado_a__id')
    ganada      = django_filters.BooleanFilter(field_name='etapa__es_ganado')
    perdida     = django_filters.BooleanFilter(field_name='etapa__es_perdido')
    search      = django_filters.CharFilter(method='filter_search')

    class Meta:
        model  = CrmOportunidad
        fields = ['pipeline', 'etapa', 'asignado_a']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(titulo__icontains=value) |
            Q(contacto__nombre_completo__icontains=value)
        )


class CrmActividadFilter(django_filters.FilterSet):
    completada = django_filters.BooleanFilter(field_name='completada')
    tipo       = django_filters.CharFilter(field_name='tipo')

    class Meta:
        model  = CrmActividad
        fields = ['completada', 'tipo']


class CrmProductoFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search')
    grupo  = django_filters.CharFilter(field_name='grupo')
    clase  = django_filters.CharFilter(field_name='clase')

    class Meta:
        model  = CrmProducto
        fields = ['grupo', 'clase']

    def filter_search(self, queryset, name, value):
        from django.db.models import Q
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(codigo__icontains=value) |
            Q(descripcion__icontains=value)
        )
