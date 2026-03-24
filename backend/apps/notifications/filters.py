"""
SaiSuite — Notifications: Filtros
"""
import django_filters
from .models import Notificacion, Comentario


class NotificacionFilter(django_filters.FilterSet):
    leida = django_filters.BooleanFilter()
    tipo  = django_filters.ChoiceFilter(choices=Notificacion.TIPOS)

    class Meta:
        model  = Notificacion
        fields = ['leida', 'tipo']


class ComentarioFilter(django_filters.FilterSet):
    """
    Filtros para comentarios.
    Requiere content_type_model + object_id para listar comentarios de un objeto.
    """
    content_type_model = django_filters.CharFilter(
        field_name='content_type__model',
        lookup_expr='iexact',
    )
    object_id = django_filters.UUIDFilter()
    solo_raiz = django_filters.BooleanFilter(method='filter_solo_raiz')

    class Meta:
        model  = Comentario
        fields = ['content_type_model', 'object_id']

    def filter_solo_raiz(self, queryset, name, value):
        if value:
            return queryset.filter(padre__isnull=True)
        return queryset
