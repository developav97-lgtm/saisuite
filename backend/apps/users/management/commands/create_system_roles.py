"""
Crea los roles de sistema (Administrador + Solo Lectura) para cada empresa.
Idempotente: si ya existen no genera duplicados.
Ejecutar: python manage.py create_system_roles
"""
import logging
from django.core.management.base import BaseCommand

from apps.companies.models import Company
from apps.users.models import Permission, Role

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crea roles de sistema para cada empresa registrada'

    def handle(self, *args: object, **kwargs: object) -> None:
        empresas = Company.objects.filter(is_active=True)
        todos_permisos   = Permission.objects.all()
        permisos_view    = Permission.objects.filter(accion__endswith='view')

        if not todos_permisos.exists():
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  No hay permisos en la base de datos. '
                    'Ejecuta primero: python manage.py create_permissions'
                )
            )
            return

        created_count = 0

        for empresa in empresas:
            # ── Rol Administrador (todos los permisos) ──────────────────────
            admin_role, created = Role.objects.get_or_create(
                empresa=empresa,
                nombre='Administrador',
                defaults={
                    'tipo':        Role.Tipo.ADMIN,
                    'descripcion': 'Acceso total al sistema',
                    'es_sistema':  True,
                },
            )
            if created:
                admin_role.permisos.set(todos_permisos)
                created_count += 1
                logger.info('rol_admin_creado', extra={
                    'empresa_id': str(empresa.id), 'empresa': empresa.name,
                })
            else:
                # Actualizar permisos aunque el rol ya exista
                admin_role.permisos.set(todos_permisos)

            # ── Rol Solo Lectura (solo permisos .view) ──────────────────────
            readonly_role, created = Role.objects.get_or_create(
                empresa=empresa,
                nombre='Solo Lectura',
                defaults={
                    'tipo':        Role.Tipo.READONLY,
                    'descripcion': 'Solo visualización, sin edición ni creación',
                    'es_sistema':  True,
                },
            )
            if created:
                readonly_role.permisos.set(permisos_view)
                created_count += 1
                logger.info('rol_readonly_creado', extra={
                    'empresa_id': str(empresa.id), 'empresa': empresa.name,
                })
            else:
                readonly_role.permisos.set(permisos_view)

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {created_count} roles creados para {empresas.count()} empresas'
            )
        )
