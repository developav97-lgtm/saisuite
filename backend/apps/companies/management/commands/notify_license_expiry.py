"""
SaiSuite — Management command: notify_license_expiry

Notifica a los administradores de empresas cuyas licencias vencen en N días.
Ejecutar diariamente via cron o scheduler:
    python manage.py notify_license_expiry
    python manage.py notify_license_expiry --days 5

Configurar variables de entorno para email:
    EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
    EMAIL_USE_TLS, DEFAULT_FROM_EMAIL
"""
import logging
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

from apps.companies.services import LicenseService
from apps.users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía notificaciones por email a empresas con licencia próxima a vencer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=5,
            help='Días de anticipación para notificar (default: 5)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué enviaría, sin enviar emails reales',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        expiring = LicenseService.get_expiring_soon(days=days)

        if not expiring:
            self.stdout.write(self.style.SUCCESS(f'No hay licencias que venzan en {days} días.'))
            return

        sent = 0
        for lic in expiring:
            company = lic.company
            admins = User.objects.filter(
                company=company,
                is_active=True,
            ).exclude(email='')

            emails = list(admins.values_list('email', flat=True))
            if not emails:
                self.stdout.write(self.style.WARNING(f'  {company.name}: sin admins con email — omitido'))
                continue

            subject = f'[SaiSuite] Tu licencia vence en {days} días — {company.name}'
            body = (
                f'Hola,\n\n'
                f'La licencia de {company.name} vence el {lic.expires_at}.\n'
                f'Quedan {lic.days_until_expiry} días para renovarla.\n\n'
                f'Por favor, contacta a ValMen Tech para gestionar la renovación.\n\n'
                f'— SaiSuite\n'
            )

            if dry_run:
                self.stdout.write(f'[DRY-RUN] A: {emails} | {subject}')
            else:
                try:
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@saisuite.com'),
                        recipient_list=emails,
                        fail_silently=False,
                    )
                    logger.info(
                        'license_expiry_notified',
                        extra={'company_id': str(company.id), 'emails': emails, 'expires_at': str(lic.expires_at)},
                    )
                    sent += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {company.name} → {emails}'))
                except Exception as exc:
                    logger.error('license_expiry_notify_failed', extra={'company_id': str(company.id), 'error': str(exc)})
                    self.stdout.write(self.style.ERROR(f'  ✗ {company.name}: {exc}'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\nNotificaciones enviadas: {sent}/{len(expiring)}'))
