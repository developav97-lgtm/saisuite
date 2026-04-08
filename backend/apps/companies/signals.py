"""
Signals de la app companies.
Al crear una empresa nueva se generan automáticamente:
  - Rol "Administrador" (es_sistema=True, todos los permisos)
  - Rol "Solo Lectura" (es_sistema=True, solo permisos .view)
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='companies.Company')
def crear_roles_sistema(sender, instance, created, **kwargs):
    """Crea los roles de sistema cuando se registra una empresa nueva."""
    if not created:
        return

    # Importación diferida para evitar circular imports
    from apps.users.models import Permission, Role

    todos_permisos = Permission.objects.all()
    permisos_view  = Permission.objects.filter(accion__endswith='view')

    if not todos_permisos.exists():
        logger.warning('crear_roles_sistema_sin_permisos', extra={
            'empresa_id': str(instance.id),
            'nota': 'No hay permisos en BD — ejecutar create_permissions primero',
        })
        return

    admin_role, _ = Role.objects.get_or_create(
        empresa=instance,
        nombre='Administrador',
        defaults={
            'tipo':        Role.Tipo.ADMIN,
            'descripcion': 'Acceso total al sistema',
            'es_sistema':  True,
        },
    )
    admin_role.permisos.set(todos_permisos)

    readonly_role, _ = Role.objects.get_or_create(
        empresa=instance,
        nombre='Solo Lectura',
        defaults={
            'tipo':        Role.Tipo.READONLY,
            'descripcion': 'Solo visualización, sin edición ni creación',
            'es_sistema':  True,
        },
    )
    readonly_role.permisos.set(permisos_view)

    logger.info('roles_sistema_creados', extra={
        'empresa_id': str(instance.id),
        'empresa': instance.name,
    })
