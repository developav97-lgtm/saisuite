"""
Management command: fix_cliente_id

Corrige proyectos donde cliente_id almacena el UUID interno del Tercero en
lugar del número de identificación (NIT / cédula) real.

Uso:
    python manage.py fix_cliente_id              # aplica correcciones
    python manage.py fix_cliente_id --dry-run    # solo lista, no modifica
"""
import logging
import re

from django.core.management.base import BaseCommand

from apps.proyectos.models import Project
from apps.terceros.models import Tercero

logger = logging.getLogger(__name__)

# Patrón que detecta UUIDs v4 almacenados como texto plano en cliente_id.
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


class Command(BaseCommand):
    help = (
        'Reemplaza UUID interno en Project.cliente_id por el número de '
        'identificación real del Tercero correspondiente.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Solo lista los proyectos afectados sin modificar nada.',
        )

    def handle(self, *args, **options):
        dry_run: bool = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Modo --dry-run: no se realizarán cambios.'))

        # Obtener todos los proyectos activos; el filtrado final se hace en Python
        # para no depender de funciones de regex en BD (portabilidad PostgreSQL / SQLite en tests).
        proyectos = Project.all_objects.select_related('company').iterator()

        corregidos = 0
        no_encontrados = 0
        omitidos = 0

        for project in proyectos:
            cliente_id_actual = project.cliente_id or ''

            # Solo procesar si cliente_id tiene formato UUID
            if not UUID_PATTERN.match(cliente_id_actual):
                omitidos += 1
                continue

            # Buscar el Tercero cuyo pk coincide con el UUID almacenado
            try:
                tercero = Tercero.objects.get(
                    company=project.company,
                    id=cliente_id_actual,
                )
            except Tercero.DoesNotExist:
                logger.warning(
                    'fix_cliente_id_tercero_no_encontrado',
                    extra={
                        'project_id': str(project.id),
                        'project_codigo': project.codigo,
                        'cliente_id_uuid': cliente_id_actual,
                    },
                )
                self.stdout.write(
                    self.style.ERROR(
                        f'[NO ENCONTRADO] Proyecto {project.codigo} ({project.id}): '
                        f'UUID {cliente_id_actual} no corresponde a ningún Tercero.'
                    )
                )
                no_encontrados += 1
                continue

            nuevo_cliente_id = tercero.numero_identificacion
            nuevo_cliente_nombre = tercero.razon_social

            self.stdout.write(
                f'[{"DRY-RUN" if dry_run else "CORRECCIÓN"}] '
                f'Proyecto {project.codigo} ({project.id}): '
                f'cliente_id {cliente_id_actual!r} → {nuevo_cliente_id!r} | '
                f'cliente_nombre → {nuevo_cliente_nombre!r}'
            )

            if not dry_run:
                project.cliente_id = nuevo_cliente_id
                project.cliente_nombre = nuevo_cliente_nombre
                project.save(update_fields=['cliente_id', 'cliente_nombre', 'updated_at'])
                logger.info(
                    'fix_cliente_id_corregido',
                    extra={
                        'project_id': str(project.id),
                        'project_codigo': project.codigo,
                        'uuid_anterior': cliente_id_actual,
                        'nuevo_cliente_id': nuevo_cliente_id,
                    },
                )

            corregidos += 1

        # Resumen final
        resumen = (
            f'Resumen: corregidos={corregidos}, '
            f'no_encontrados={no_encontrados}, '
            f'omitidos (cliente_id ya correcto)={omitidos}'
        )
        self.stdout.write(self.style.SUCCESS(resumen))
        logger.info(
            'fix_cliente_id_completado',
            extra={
                'dry_run': dry_run,
                'corregidos': corregidos,
                'no_encontrados': no_encontrados,
                'omitidos': omitidos,
            },
        )
