"""
SaiSuite — Management command: Migrar ActividadProyecto → Tarea
Uso:
    python manage.py migrar_actividades_a_tareas
    python manage.py migrar_actividades_a_tareas --dry-run
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.proyectos.models import ActividadProyecto, Tarea

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migra ActividadProyecto a Tarea'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la migración sin escribir en BD'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN - No se escribirá en BD'))

        migradas = 0
        errores = 0

        actividades = ActividadProyecto.all_objects.select_related(
            'proyecto', 'fase', 'actividad', 'company'
        ).all()

        total = actividades.count()
        self.stdout.write(f'Total de actividades a migrar: {total}')

        for ap in actividades:
            try:
                # Verificar si ya fue migrada
                if Tarea.all_objects.filter(actividad_proyecto_id=ap.id).exists():
                    self.stdout.write(f'  Ya migrada: {ap.id}')
                    continue

                # Calcular estado y porcentaje
                if ap.cantidad_planificada > 0:
                    porcentaje = int(
                        (ap.cantidad_ejecutada / ap.cantidad_planificada) * 100
                    )
                else:
                    porcentaje = 0

                if ap.cantidad_ejecutada >= ap.cantidad_planificada and ap.cantidad_planificada > 0:
                    estado = 'completada'
                elif ap.cantidad_ejecutada > 0:
                    estado = 'en_progreso'
                else:
                    estado = 'por_hacer'

                if not dry_run:
                    with transaction.atomic():
                        Tarea.all_objects.create(
                            company=ap.company,
                            proyecto=ap.proyecto,
                            fase=ap.fase,
                            nombre=ap.actividad.nombre,
                            descripcion=ap.actividad.descripcion or '',
                            horas_estimadas=ap.cantidad_planificada,
                            horas_registradas=ap.cantidad_ejecutada,
                            porcentaje_completado=min(porcentaje, 100),
                            estado=estado,
                            actividad_proyecto_id=ap.id
                        )

                migradas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Migrada: {ap.actividad.nombre}')
                )

            except Exception as e:
                errores += 1
                logger.error(
                    'migrar_actividades_error',
                    extra={'actividad_proyecto_id': str(ap.id), 'error': str(e)}
                )
                self.stdout.write(
                    self.style.ERROR(f'✗ Error {ap.id}: {e}')
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n{"[DRY-RUN] " if dry_run else ""}Total: {migradas} migradas, {errores} errores'
        ))
