"""
SaiSuite — Data migration: seed module LicensePackages.
Creates one LicensePackage per platform module with price=0.
The admin sets prices later from the packages catalog.
"""
from django.db import migrations


MODULES = [
    ('mod_proyectos', 'SaiProyectos', 'proyectos'),
    ('mod_dashboard', 'SaiDashboard', 'dashboard'),
    ('mod_crm',       'CRM',          'crm'),
    ('mod_soporte',   'Soporte',      'soporte'),
]


def seed_module_packages(apps, schema_editor):
    LicensePackage = apps.get_model('companies', 'LicensePackage')
    for code, name, module_code in MODULES:
        LicensePackage.objects.get_or_create(
            code=code,
            defaults={
                'name':          name,
                'package_type':  'module',
                'module_code':   module_code,
                'price_monthly': 0,
                'price_annual':  0,
                'is_active':     True,
            },
        )


def remove_module_packages(apps, schema_editor):
    LicensePackage = apps.get_model('companies', 'LicensePackage')
    codes = [row[0] for row in MODULES]
    LicensePackage.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0011_remove_plan_add_renewal_type_add_module_trial'),
    ]

    operations = [
        migrations.RunPython(seed_module_packages, remove_module_packages),
    ]
