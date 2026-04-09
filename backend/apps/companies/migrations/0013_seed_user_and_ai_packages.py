"""
SaiSuite — Data migration: seed user_seats and ai_tokens / ai_messages packages.

Design:
  - users_base_2      : 2 usuarios base incluidos con cualquier módulo (price=0)
  - users_add_*       : paquetes adicionales de puestos de usuario
  - ai_tokens_base_10k: 10K tokens IA base incluidos (price=0)
  - ai_tokens_*       : paquetes adicionales de tokens IA
  - ai_messages_base_50: 50 mensajes IA base incluidos (price=0)
  - ai_messages_*     : paquetes adicionales de mensajes IA

Prices in COP. Annual prices reflect ~20% discount vs monthly × 12.
"""
from django.db import migrations


USER_PACKAGES = [
    # (code, name, description, quantity, price_monthly, price_annual)
    (
        'users_base_2',
        '2 usuarios base',
        'Incluye 2 puestos de usuario. Se agrega con cada módulo adquirido.',
        2, 0, 0,
    ),
    (
        'users_add_5',
        '+5 usuarios adicionales',
        'Agrega 5 puestos de usuario extra a la licencia.',
        5, 250_000, 2_400_000,
    ),
    (
        'users_add_10',
        '+10 usuarios adicionales',
        'Agrega 10 puestos de usuario extra a la licencia.',
        10, 450_000, 4_320_000,
    ),
    (
        'users_add_20',
        '+20 usuarios adicionales',
        'Agrega 20 puestos de usuario extra a la licencia.',
        20, 850_000, 8_160_000,
    ),
]

AI_TOKEN_PACKAGES = [
    # (code, name, description, quantity, price_monthly, price_annual)
    (
        'ai_tokens_base_10k',
        '10K tokens IA base',
        '10.000 tokens de IA incluidos en la licencia base.',
        10_000, 0, 0,
    ),
    (
        'ai_tokens_50k',
        '+50K tokens IA',
        'Agrega 50.000 tokens de IA por mes a la licencia.',
        50_000, 80_000, 768_000,
    ),
    (
        'ai_tokens_200k',
        '+200K tokens IA',
        'Agrega 200.000 tokens de IA por mes a la licencia.',
        200_000, 280_000, 2_688_000,
    ),
    (
        'ai_tokens_500k',
        '+500K tokens IA',
        'Agrega 500.000 tokens de IA por mes a la licencia.',
        500_000, 600_000, 5_760_000,
    ),
]

AI_MESSAGE_PACKAGES = [
    # (code, name, description, quantity, price_monthly, price_annual)
    (
        'ai_messages_base_50',
        '50 mensajes IA base',
        '50 mensajes de chat IA incluidos en la licencia base.',
        50, 0, 0,
    ),
    (
        'ai_messages_200',
        '+200 mensajes IA',
        'Agrega 200 mensajes de chat IA por mes a la licencia.',
        200, 50_000, 480_000,
    ),
    (
        'ai_messages_1000',
        '+1.000 mensajes IA',
        'Agrega 1.000 mensajes de chat IA por mes a la licencia.',
        1_000, 190_000, 1_824_000,
    ),
]


def seed_packages(apps, schema_editor):
    LicensePackage = apps.get_model('companies', 'LicensePackage')

    for code, name, desc, qty, pm, pa in USER_PACKAGES:
        LicensePackage.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': desc,
                'package_type': 'user_seats',
                'quantity': qty,
                'price_monthly': pm,
                'price_annual': pa,
                'is_active': True,
            },
        )

    for code, name, desc, qty, pm, pa in AI_TOKEN_PACKAGES:
        LicensePackage.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': desc,
                'package_type': 'ai_tokens',
                'quantity': qty,
                'price_monthly': pm,
                'price_annual': pa,
                'is_active': True,
            },
        )

    for code, name, desc, qty, pm, pa in AI_MESSAGE_PACKAGES:
        LicensePackage.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': desc,
                'package_type': 'ai_messages',
                'quantity': qty,
                'price_monthly': pm,
                'price_annual': pa,
                'is_active': True,
            },
        )


def remove_packages(apps, schema_editor):
    LicensePackage = apps.get_model('companies', 'LicensePackage')
    codes = (
        [row[0] for row in USER_PACKAGES]
        + [row[0] for row in AI_TOKEN_PACKAGES]
        + [row[0] for row in AI_MESSAGE_PACKAGES]
    )
    LicensePackage.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0012_seed_module_packages'),
    ]

    operations = [
        migrations.RunPython(seed_packages, remove_packages),
    ]
