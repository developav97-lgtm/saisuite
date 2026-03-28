"""
SaiSuite — Management command: Snapshot semanal de presupuestos

Genera un snapshot del estado presupuestario de todos los proyectos activos
y evalúa alertas. Diseñado para ejecutarse cada lunes a las 06:00 UTC.

Uso:
    python manage.py budget_weekly_snapshot
    python manage.py budget_weekly_snapshot --dry-run
    python manage.py budget_weekly_snapshot --project-id <uuid>
    python manage.py budget_weekly_snapshot --company-id <uuid>

Programación:
    - AWS EventBridge Scheduler: cron(0 6 ? * MON *)
    - n8n: workflow cron → HTTP request POST /manage/budget-snapshot/
      (requiere endpoint de gestión interno, ver docs/FEATURE-7-API-DOCS.md)
    - Cron del sistema: 0 6 * * 1 /app/manage.py budget_weekly_snapshot

Nota técnica (DEC-029):
    No usamos Celery porque el stack actual no tiene broker (Redis).
    Este comando puede ser invocado síncronamente desde EventBridge o n8n.
    Si se agrega Celery en el futuro, este comando debe envolver la task:
        @shared_task(name='budget.weekly_snapshot')
        def weekly_budget_snapshot_task():
            call_command('budget_weekly_snapshot')
"""
import logging
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.proyectos.models import Project
from apps.proyectos.budget_services import (
    BudgetSnapshotService,
    BudgetManagementService,
)

logger = logging.getLogger(__name__)

# Estados de proyecto que se consideran "activos" para snapshots
ACTIVE_STATES = ('planned', 'in_progress', 'suspended')


class Command(BaseCommand):
    help = (
        'Genera snapshot semanal de presupuesto para todos los proyectos activos '
        'y evalúa alertas de presupuesto. Ejecutar cada lunes 06:00 UTC.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Calcula snapshots sin persistir en BD. Útil para verificar.',
        )
        parser.add_argument(
            '--project-id',
            type=str,
            default=None,
            help='Ejecutar solo para un proyecto específico (UUID).',
        )
        parser.add_argument(
            '--company-id',
            type=str,
            default=None,
            help='Ejecutar solo para los proyectos de una empresa (UUID).',
        )

    def handle(self, *args, **options):
        dry_run    = options['dry_run']
        project_id = options.get('project_id')
        company_id = options.get('company_id')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'MODO DRY-RUN — No se persistirá ningún snapshot.'
            ))

        # ── 1. Obtener proyectos activos ──────────────────────────────────────
        qs = Project.objects.filter(estado__in=ACTIVE_STATES).select_related('company')

        if project_id:
            qs = qs.filter(id=project_id)
            if not qs.exists():
                raise CommandError(
                    f'Proyecto {project_id} no encontrado o no está en estado activo.'
                )

        if company_id:
            qs = qs.filter(company_id=company_id)

        projects = list(qs)
        total = len(projects)

        if total == 0:
            self.stdout.write(self.style.WARNING('No hay proyectos activos para procesar.'))
            return

        self.stdout.write(
            f'[{date.today()}] Procesando {total} proyecto(s) activo(s)…'
        )

        # ── 2. Procesar cada proyecto ─────────────────────────────────────────
        stats = {
            'snapshots_created': 0,
            'snapshots_updated': 0,
            'alerts_generated':  0,
            'errors':            0,
            'skipped_no_budget': 0,
        }

        for project in projects:
            pid = str(project.id)
            cid = str(project.company_id)

            try:
                self._process_project(project, cid, dry_run, stats)
            except Exception as exc:
                stats['errors'] += 1
                logger.error(
                    'budget_snapshot_error',
                    extra={
                        'project_id': pid,
                        'company_id': cid,
                        'error':      str(exc),
                    },
                )
                self.stdout.write(self.style.ERROR(
                    f'  ✗ [{project.codigo}] {project.nombre}: {exc}'
                ))

        # ── 3. Resumen ────────────────────────────────────────────────────────
        self._print_summary(stats, dry_run)

    def _process_project(
        self,
        project: Project,
        company_id: str,
        dry_run: bool,
        stats: dict,
    ) -> None:
        """Genera snapshot y evalúa alertas para un proyecto."""
        pid  = str(project.id)
        code = project.codigo
        name = project.nombre

        # Verificar si el proyecto tiene presupuesto definido
        from apps.proyectos.models import ProjectBudget
        has_budget = ProjectBudget.objects.filter(project_id=pid).exists()

        if not has_budget:
            stats['skipped_no_budget'] += 1
            self.stdout.write(
                f'  - [{code}] {name}: sin presupuesto — omitido.'
            )
            return

        if dry_run:
            # En dry-run: solo calcular, no persistir
            from apps.proyectos.budget_services import CostCalculationService
            costs    = CostCalculationService.get_total_cost(pid)
            variance = CostCalculationService.get_budget_variance(pid)
            alerts   = BudgetManagementService.check_budget_alerts(pid)

            self.stdout.write(
                f'  ~ [{code}] {name}: '
                f'total={costs["total_cost"]} {costs["currency"]}, '
                f'status={variance["status"]}, '
                f'alerts={len(alerts)}'
            )
            return

        # Crear/actualizar snapshot
        snapshot = BudgetSnapshotService.create_snapshot(pid, company_id)

        # Determinar si fue nuevo o actualizado (mismo día = update)
        is_new = snapshot.created_at.date() == date.today()
        if is_new:
            stats['snapshots_created'] += 1
        else:
            stats['snapshots_updated'] += 1

        # Evaluar alertas
        alerts = BudgetManagementService.check_budget_alerts(pid)
        stats['alerts_generated'] += len(alerts)

        # Log de la operación
        logger.info(
            'budget_snapshot_generated',
            extra={
                'project_id':   pid,
                'company_id':   company_id,
                'snapshot_date':str(snapshot.snapshot_date),
                'total_cost':   str(snapshot.total_cost),
                'variance':     str(snapshot.variance),
                'alerts':       len(alerts),
            },
        )

        alert_summary = ''
        if alerts:
            top = alerts[0]
            alert_summary = f' ⚠ {top["type"].upper()}: {top["message"][:60]}'

        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ [{code}] {name}: '
                f'snapshot={snapshot.snapshot_date}, '
                f'total={snapshot.total_cost} COP, '
                f'variance={snapshot.variance}{alert_summary}'
            )
        )

    def _print_summary(self, stats: dict, dry_run: bool) -> None:
        """Imprime el resumen final de la ejecución."""
        separator = '─' * 50
        self.stdout.write(separator)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                'DRY-RUN completado — ningún dato fue persistido.'
            ))
            return

        self.stdout.write(
            f'Snapshots creados:    {stats["snapshots_created"]}\n'
            f'Snapshots actualizados: {stats["snapshots_updated"]}\n'
            f'Alertas generadas:    {stats["alerts_generated"]}\n'
            f'Sin presupuesto:      {stats["skipped_no_budget"]}\n'
            f'Errores:              {stats["errors"]}'
        )

        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(
                f'\n{stats["errors"]} proyecto(s) fallaron. Revisar logs.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\nProceso completado sin errores.'))
