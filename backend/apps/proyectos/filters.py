"""
SaiSuite — Proyectos: Filtros
"""
import django_filters
from django.db.models import Q
from apps.proyectos.models import Project, ProjectType, ProjectStatus, Task


class ProjectFilter(django_filters.FilterSet):
    estado        = django_filters.ChoiceFilter(choices=ProjectStatus.choices)
    tipo          = django_filters.ChoiceFilter(choices=ProjectType.choices)
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
        model  = Project
        fields = [
            'estado', 'tipo', 'cliente_id', 'gerente', 'activo',
            'fecha_inicio_desde', 'fecha_inicio_hasta',
            'fecha_fin_desde', 'fecha_fin_hasta',
        ]


class TaskFilter(django_filters.FilterSet):
    """Filtros avanzados para Task."""

    # Búsqueda libre
    search = django_filters.CharFilter(method='filter_search')

    # Estado y prioridad
    estado      = django_filters.ChoiceFilter(choices=Task._meta.get_field('estado').choices)
    prioridad   = django_filters.NumberFilter()
    prioridad_min = django_filters.NumberFilter(field_name='prioridad', lookup_expr='gte')

    # Fechas
    vencidas            = django_filters.BooleanFilter(method='filter_vencidas')
    fecha_limite_desde  = django_filters.DateFilter(field_name='fecha_limite', lookup_expr='gte')
    fecha_limite_hasta  = django_filters.DateFilter(field_name='fecha_limite', lookup_expr='lte')

    # Asignación
    responsable         = django_filters.UUIDFilter(field_name='responsable__id')
    sin_responsable     = django_filters.BooleanFilter(method='filter_sin_responsable')
    solo_mis_tareas     = django_filters.BooleanFilter(method='filter_solo_mis_tareas')

    # Proyecto / Fase / Cliente / ActividadSaiopen
    proyecto           = django_filters.UUIDFilter(field_name='proyecto__id')
    fase               = django_filters.UUIDFilter(field_name='fase__id')
    actividad_saiopen  = django_filters.UUIDFilter(field_name='actividad_saiopen__id')
    cliente            = django_filters.UUIDFilter(field_name='cliente__id')

    # Jerarquía
    solo_raiz = django_filters.BooleanFilter(method='filter_solo_raiz')

    class Meta:
        model = Task
        fields = [
            'estado', 'prioridad', 'proyecto', 'fase', 'actividad_saiopen',
            'responsable', 'cliente', 'es_recurrente',
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(nombre__icontains=value) |
            Q(codigo__icontains=value) |
            Q(descripcion__icontains=value)
        )

    def filter_vencidas(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(
                fecha_limite__lt=timezone.now().date()
            ).exclude(estado__in=['completed', 'cancelled'])
        return queryset

    def filter_sin_responsable(self, queryset, name, value):
        if value:
            return queryset.filter(responsable__isnull=True)
        return queryset.filter(responsable__isnull=False)

    def filter_solo_mis_tareas(self, queryset, name, value):
        if value and self.request and self.request.user.is_authenticated:
            return queryset.filter(
                Q(responsable=self.request.user) |
                Q(followers=self.request.user)
            ).distinct()
        return queryset

    def filter_solo_raiz(self, queryset, name, value):
        if value:
            return queryset.filter(tarea_padre__isnull=True)
        return queryset


# ALIASES DE COMPATIBILIDAD — eliminar en REFT-10
ProyectoFilter = ProjectFilter
TareaFilter = TaskFilter
