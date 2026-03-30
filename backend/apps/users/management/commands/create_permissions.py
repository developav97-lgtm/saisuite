"""
Crea los permisos base del sistema.
Ejecutar: python manage.py create_permissions
"""
from django.core.management.base import BaseCommand

from apps.users.models import Permission


PERMISOS_BASE = [
    # ── Proyectos ────────────────────────────────────────────────────────────
    ('proyectos.view',    'Ver proyectos',          'proyectos', 'view',    'Visualizar lista y detalle de proyectos'),
    ('proyectos.create',  'Crear proyectos',         'proyectos', 'create',  'Crear nuevos proyectos'),
    ('proyectos.edit',    'Editar proyectos',         'proyectos', 'edit',    'Modificar proyectos existentes'),
    ('proyectos.delete',  'Eliminar proyectos',       'proyectos', 'delete',  'Eliminar proyectos'),
    ('proyectos.execute', 'Iniciar ejecución',        'proyectos', 'execute', 'Iniciar y avanzar fases del proyecto'),
    ('proyectos.approve', 'Aprobar proyectos',        'proyectos', 'approve', 'Aprobar proyectos y entregables'),

    # ── Actividades ──────────────────────────────────────────────────────────
    ('actividades.view',   'Ver actividades',   'actividades', 'view',   'Visualizar actividades del proyecto'),
    ('actividades.create', 'Crear actividades', 'actividades', 'create', 'Crear nuevas actividades'),
    ('actividades.edit',   'Editar actividades', 'actividades', 'edit',  'Modificar actividades existentes'),
    ('actividades.delete', 'Eliminar actividades', 'actividades', 'delete', 'Eliminar actividades'),

    # ── Tareas ───────────────────────────────────────────────────────────────
    ('tareas.view',    'Ver tareas',     'tareas', 'view',    'Visualizar tareas'),
    ('tareas.create',  'Crear tareas',   'tareas', 'create',  'Crear nuevas tareas'),
    ('tareas.edit',    'Editar tareas',  'tareas', 'edit',    'Modificar tareas existentes'),
    ('tareas.delete',  'Eliminar tareas', 'tareas', 'delete', 'Eliminar tareas'),
    ('tareas.assign',  'Asignar tareas', 'tareas', 'assign',  'Asignar tareas a otros usuarios'),

    # ── Timesheets ───────────────────────────────────────────────────────────
    ('timesheets.view',   'Ver registro de horas',    'timesheets', 'view',   'Ver horas registradas'),
    ('timesheets.create', 'Registrar horas',          'timesheets', 'create', 'Registrar horas trabajadas'),
    ('timesheets.edit',   'Editar registro de horas', 'timesheets', 'edit',   'Modificar registros de horas'),
    ('timesheets.delete', 'Eliminar registro de horas', 'timesheets', 'delete', 'Eliminar registros de horas'),

    # ── Terceros ─────────────────────────────────────────────────────────────
    ('terceros.view',   'Ver terceros',      'terceros', 'view',   'Visualizar clientes, proveedores y aliados'),
    ('terceros.create', 'Crear terceros',    'terceros', 'create', 'Crear nuevos terceros'),
    ('terceros.edit',   'Editar terceros',   'terceros', 'edit',   'Modificar terceros existentes'),
    ('terceros.delete', 'Eliminar terceros', 'terceros', 'delete', 'Eliminar terceros'),

    # ── Administración ───────────────────────────────────────────────────────
    ('admin.usuarios.view',   'Ver usuarios',      'admin', 'usuarios.view',   'Visualizar usuarios de la empresa'),
    ('admin.usuarios.create', 'Crear usuarios',    'admin', 'usuarios.create', 'Crear nuevos usuarios'),
    ('admin.usuarios.edit',   'Editar usuarios',   'admin', 'usuarios.edit',   'Modificar usuarios existentes'),
    ('admin.usuarios.delete', 'Desactivar usuarios', 'admin', 'usuarios.delete', 'Desactivar usuarios'),
    ('admin.empresa.view',    'Ver datos de empresa', 'admin', 'empresa.view',  'Visualizar configuración de empresa'),
    ('admin.empresa.edit',    'Editar empresa',    'admin', 'empresa.edit',   'Modificar configuración de empresa'),
    ('admin.roles.view',      'Ver roles',         'admin', 'roles.view',     'Visualizar roles y permisos'),
    ('admin.roles.manage',    'Gestionar roles',   'admin', 'roles.manage',   'Crear, editar y eliminar roles'),
    ('admin.consecutivos.view',   'Ver consecutivos',   'admin', 'consecutivos.view',   'Visualizar consecutivos'),
    ('admin.consecutivos.manage', 'Gestionar consecutivos', 'admin', 'consecutivos.manage', 'Crear y editar consecutivos'),
]


class Command(BaseCommand):
    help = 'Crea los permisos base del sistema'

    def handle(self, *args: object, **kwargs: object) -> None:
        created_count = 0
        updated_count = 0

        for codigo, nombre, modulo, accion, descripcion in PERMISOS_BASE:
            _, created = Permission.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre':      nombre,
                    'modulo':      modulo,
                    'accion':      accion,
                    'descripcion': descripcion,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {created_count} permisos creados, {updated_count} actualizados '
                f'({len(PERMISOS_BASE)} total)'
            )
        )
