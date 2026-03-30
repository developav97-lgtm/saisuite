#!/usr/bin/env python
"""
Script de seed data para SaiSuite.
Crea empresa demo + usuario admin para desarrollo/testing.

Uso:
    docker compose exec backend python scripts/create_demo_company.py
    -- o --
    python manage.py shell < scripts/create_demo_company.py
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Setup Django si se ejecuta directamente
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import django
    django.setup()

from apps.companies.models import Company, CompanyModule
from apps.users.models import User, UserCompany


def create_demo() -> None:
    logger.info('seed_start', extra={'script': 'create_demo_company'})

    # ------------------------------------------------------------------
    # Empresa demo
    # ------------------------------------------------------------------
    company, created = Company.objects.get_or_create(
        nit='900123456',
        defaults={
            'name':            'ValMen Tech Demo',
            'plan':            Company.Plan.PROFESSIONAL,
            'is_active':       True,
            'saiopen_enabled': False,
        },
    )
    if created:
        logger.info('company_created', extra={'company_id': str(company.id), 'company_name': company.name})
    else:
        logger.info('company_exists', extra={'company_id': str(company.id), 'company_name': company.name})

    # ------------------------------------------------------------------
    # Módulos
    # ------------------------------------------------------------------
    for module in [
        CompanyModule.Module.PROYECTOS,
        CompanyModule.Module.VENTAS,
        CompanyModule.Module.COBROS,
        CompanyModule.Module.DASHBOARD,
    ]:
        _, created_mod = CompanyModule.objects.get_or_create(
            company=company,
            module=module,
            defaults={'is_active': True},
        )
        if created_mod:
            logger.info('module_activated', extra={'company_id': str(company.id), 'module_name': module})

    # ------------------------------------------------------------------
    # Usuario company_admin
    # ------------------------------------------------------------------
    user, user_created = User.objects.get_or_create(
        email='admin@demo.com',
        defaults={
            'first_name':    'Admin',
            'last_name':     'Demo',
            'role':          User.Role.COMPANY_ADMIN,
            'company':       company,
            'is_active':     True,
            'is_superadmin': False,
        },
    )
    if user_created:
        user.set_password('demo123')
        user.save()
        logger.info('user_created', extra={'email': user.email, 'company_id': str(company.id)})
    else:
        logger.info('user_exists', extra={'email': user.email})

    UserCompany.objects.get_or_create(
        user=user,
        company=company,
        defaults={
            'role':           User.Role.COMPANY_ADMIN,
            'modules_access': ['proyectos', 'crm', 'soporte', 'dashboard'],
            'is_active':      True,
        },
    )

    # ------------------------------------------------------------------
    # Superadmin ValMen Tech
    # ------------------------------------------------------------------
    superadmin, sa_created = User.objects.get_or_create(
        email='superadmin@valmentech.com',
        defaults={
            'first_name':    'Super',
            'last_name':     'Admin',
            'role':          User.Role.VALMEN_ADMIN,
            'company':       company,
            'is_active':     True,
            'is_staff':      True,
            'is_superadmin': True,
        },
    )
    if sa_created:
        superadmin.set_password('valmen2026!')
        superadmin.save()
        logger.info('superadmin_created', extra={'email': superadmin.email})
    else:
        logger.info('superadmin_exists', extra={'email': superadmin.email})

    logger.info(
        'seed_complete',
        extra={
            'company_name': company.name,
            'nit':          company.nit,
            'admin':        'admin@demo.com',
            'superadmin':   'superadmin@valmentech.com',
        },
    )


if __name__ == '__main__':
    # Configurar logging básico para salida en consola al ejecutar directamente
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    create_demo()
