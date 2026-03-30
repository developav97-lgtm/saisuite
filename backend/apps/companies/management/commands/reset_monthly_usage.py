"""
SaiSuite — Management Command: reset_monthly_usage
Resetea los contadores de mensajes y tokens IA para todas las licencias activas.
Debe ejecutarse el primer día de cada mes.

Scheduling:
- AWS EventBridge: cron(0 0 1 * ? *)  — 00:00 UTC el día 1 de cada mes
- Cron sistema:   0 0 1 * * /app/manage.py reset_monthly_usage
- n8n: workflow cron mensual → HTTP call

Uso:
    python manage.py reset_monthly_usage
    python manage.py reset_monthly_usage --dry-run
"""
import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Resetea contadores mensuales de mensajes y tokens IA para todas las licencias activas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se resetearía sin hacer cambios.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        from apps.companies.models import CompanyLicense

        active_statuses = [CompanyLicense.Status.TRIAL, CompanyLicense.Status.ACTIVE]
        licenses = CompanyLicense.objects.filter(
            status__in=active_statuses
        ).select_related('company')

        total = licenses.count()
        reset_count = 0

        self.stdout.write(f'Licencias activas a procesar: {total}')
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] No se harán cambios.'))

        for lic in licenses:
            msg_used = lic.messages_used
            tok_used = lic.ai_tokens_used
            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] {lic.company.name}: '
                    f'mensajes {msg_used}→0, tokens {tok_used}→0'
                )
            else:
                try:
                    lic.reset_monthly_usage()
                    reset_count += 1
                    logger.info('monthly_reset_license', extra={
                        'license_id': str(lic.id),
                        'company': lic.company.name,
                        'messages_reset': msg_used,
                        'tokens_reset': tok_used,
                    })
                    self.stdout.write(
                        f'  ✓ {lic.company.name}: mensajes {msg_used}→0, tokens {tok_used}→0'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ {lic.company.name}: {e}')
                    )
                    logger.error('monthly_reset_error', extra={
                        'license_id': str(lic.id), 'error': str(e)
                    })

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Reset mensual completado: {reset_count}/{total} licencias.')
            )
            logger.info('monthly_reset_completed', extra={'reset_count': reset_count, 'total': total})
