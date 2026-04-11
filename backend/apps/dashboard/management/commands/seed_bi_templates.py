"""
Management command: seed_bi_templates
Creates the 12 predefined BI report templates for a given company.
Templates are created with es_template=True and are visible to all company users.

Usage:
    python manage.py seed_bi_templates <company_id>
    python manage.py seed_bi_templates <company_id> --force  # delete existing + recreate
"""
import logging

from django.core.management.base import BaseCommand, CommandError

from apps.dashboard.bi_templates import REPORT_TEMPLATES
from apps.dashboard.models import ReportBI

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed 12 predefined BI report templates for a company.'

    def add_arguments(self, parser):
        parser.add_argument('company_id', type=str, help='UUID of the company')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing templates and recreate them.',
        )

    def handle(self, *args, **options):
        from apps.companies.models import Company
        from apps.users.models import User

        company_id = options['company_id']
        force = options['force']

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            raise CommandError(f'Company not found: {company_id}')

        # Use the first admin user as template owner
        admin_user = User.objects.filter(
            company=company,
            is_active=True,
        ).order_by('-is_staff', 'created_at').first()

        if not admin_user:
            raise CommandError(f'No active users found for company {company.name}')

        if force:
            deleted, _ = ReportBI.all_objects.filter(
                company=company,
                es_template=True,
            ).delete()
            self.stdout.write(f'Deleted {deleted} existing templates.')

        created = 0
        skipped = 0

        for tpl_data in REPORT_TEMPLATES:
            exists = ReportBI.all_objects.filter(
                company=company,
                es_template=True,
                titulo=tpl_data['titulo'],
            ).exists()

            if exists and not force:
                skipped += 1
                continue

            ReportBI.objects.create(
                user=admin_user,
                company=company,
                titulo=tpl_data['titulo'],
                descripcion=tpl_data['descripcion'],
                es_privado=False,
                es_template=True,
                fuentes=tpl_data['fuentes'],
                campos_config=tpl_data['campos_config'],
                tipo_visualizacion=tpl_data['tipo_visualizacion'],
                viz_config=tpl_data['viz_config'],
                filtros=tpl_data['filtros'],
                orden_config=tpl_data['orden_config'],
                limite_registros=tpl_data['limite_registros'],
            )
            created += 1

        logger.info(
            'bi_templates_seeded',
            extra={
                'company_id': str(company_id),
                'templates_created': created,
                'templates_skipped': skipped,
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f'Done: {created} templates created, {skipped} skipped for {company.name}.'
        ))
