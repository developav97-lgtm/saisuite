"""
SaiSuite — Genera snapshots mensuales de licencias.
Ejecutar el primer dia de cada mes: python manage.py generate_monthly_snapshots
"""
from django.core.management.base import BaseCommand
from apps.companies.services import SnapshotService


class Command(BaseCommand):
    help = 'Genera snapshot mensual del estado de todas las licencias activas.'

    def handle(self, *args, **options):
        count = SnapshotService.generate_monthly_snapshots()
        self.stdout.write(self.style.SUCCESS(f'{count} snapshot(s) generado(s).'))
