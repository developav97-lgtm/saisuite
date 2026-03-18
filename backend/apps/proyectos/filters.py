"""
SaiSuite — Proyectos: Filtros
"""
import django_filters
from apps.proyectos.models import Proyecto, TipoProyecto, EstadoProyecto


class ProyectoFilter(django_filters.FilterSet):
    estado        = django_filters.ChoiceFilter(choices=EstadoProyecto.choices)
    tipo          = django_filters.ChoiceFilter(choices=TipoProyecto.choices)
    cliente_id    = django_filters.CharFilter(lookup_expr='iexact')
    gerente       = django_filters.UUIDFilter(field_name='gerente__id')
    activo        = django_filters.BooleanFilter()

    fecha_inicio_desde = django_filters.DateFilter(
        field_name='fecha_inicio_planificada', lookup_expr='gte'
    )
    fecha_inicio_hasta = django_filters.DateFilter(
        field_name='fecha_inicio_planificada', lookup_expr='lte'
    )
    fecha_fin_desde = django_filters.DateFilter(
        field_name='fecha_fin_planificada', lookup_expr='gte'
    )
    fecha_fin_hasta = django_filters.DateFilter(
        field_name='fecha_fin_planificada', lookup_expr='lte'
    )

    class Meta:
        model  = Proyecto
        fields = [
            'estado', 'tipo', 'cliente_id', 'gerente', 'activo',
            'fecha_inicio_desde', 'fecha_inicio_hasta',
            'fecha_fin_desde', 'fecha_fin_hasta',
        ]
