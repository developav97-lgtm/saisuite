"""
SaiSuite — Auto-genera renovaciones para licencias proximas a expirar.
Ejecutar diariamente: python manage.py auto_generate_renewals
"""
from django.core.management.base import BaseCommand
from apps.companies.services import RenewalService


class Command(BaseCommand):
    help = 'Auto-genera renovaciones para licencias que expiran en 5 dias o menos.'

    def handle(self, *args, **options):
        count = RenewalService.auto_generate_renewals()
        self.stdout.write(self.style.SUCCESS(f'{count} renovacion(es) auto-generada(s).'))
