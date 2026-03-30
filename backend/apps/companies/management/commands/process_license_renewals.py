"""
Management command: process_license_renewals
Dos operaciones en un run:
1. Genera renovaciones pendientes para licencias que expiran pronto
2. Activa renovaciones confirmadas cuyas licencias ya vencieron
"""
import logging
from datetime import date
from django.core.management.base import BaseCommand

from apps.companies.models import CompanyLicense, LicenseRenewal
from apps.companies.services import LicenseService, RenewalService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Procesa renovaciones de licencias: genera pendientes y activa confirmadas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=5,
            help='Días de anticipación para generar renovaciones (default: 5)',
        )
        parser.add_argument(
            '--only-generate', action='store_true',
            help='Solo generar renovaciones pendientes, sin activar',
        )
        parser.add_argument(
            '--only-activate', action='store_true',
            help='Solo activar renovaciones confirmadas, sin generar nuevas',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Simular sin guardar cambios',
        )

    def handle(self, *args, **options):
        days      = options['days']
        dry_run   = options['dry_run']
        only_gen  = options['only_generate']
        only_act  = options['only_activate']

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN --- No se guardarán cambios'))

        # Paso 1: Generar renovaciones pendientes
        if not only_act:
            expiring = LicenseService.get_expiring_soon(days=days)
            self.stdout.write(f'Licencias por vencer en {days} días: {len(expiring)}')
            generated = 0
            for lic in expiring:
                existing = RenewalService.get_pending_renewal(lic)
                if existing:
                    self.stdout.write(f'  SKIP {lic.company.name}: ya tiene renovación {existing.status}')
                    continue
                if not dry_run:
                    renewal = RenewalService.create_renewal(lic, period=lic.period, auto_generated=True)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  GENERATED {lic.company.name}: '
                            f'{renewal.new_starts_at} → {renewal.new_expires_at}'
                        )
                    )
                else:
                    self.stdout.write(f'  [DRY-RUN] Would generate renewal for {lic.company.name}')
                generated += 1
            self.stdout.write(f'Renovaciones generadas: {generated}')

        # Paso 2: Activar renovaciones confirmadas
        if not only_gen:
            if not dry_run:
                activated = RenewalService.activate_due_renewals()
                self.stdout.write(self.style.SUCCESS(f'Renovaciones activadas: {activated}'))
            else:
                today = date.today()
                to_activate = LicenseRenewal.objects.filter(
                    status=LicenseRenewal.Status.CONFIRMED,
                    license__expires_at__lt=today,
                )
                self.stdout.write(f'[DRY-RUN] Renovaciones a activar: {to_activate.count()}')
