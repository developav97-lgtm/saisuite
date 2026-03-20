"""
Script de seed: Configuraciones de consecutivos para empresa demo.

Uso:
    docker-compose exec backend python manage.py shell < scripts/create_consecutivos_demo.py
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.companies.models import Company
from apps.core.models import ConfiguracionConsecutivo

company = Company.objects.first()
if not company:
    print('ERROR: No hay empresa demo. Corre create_demo_company.py primero.')
    raise SystemExit(1)

print(f'Creando consecutivos para: {company.name}')

CONSECUTIVOS = [
    # ── Proyectos ──────────────────────────────────────────────────
    {'entidad': 'proyecto', 'subtipo': 'obra_civil',         'prefijo': 'OBR', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'proyecto', 'subtipo': 'consultoria',        'prefijo': 'CON', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'proyecto', 'subtipo': 'manufactura',        'prefijo': 'MAN', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'proyecto', 'subtipo': 'servicios',          'prefijo': 'SRV', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'proyecto', 'subtipo': 'licitacion_publica', 'prefijo': 'LIC', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'proyecto', 'subtipo': 'otro',               'prefijo': 'PRY', 'formato': '{prefijo}-{numero:04d}'},
    # ── Actividades ────────────────────────────────────────────────
    {'entidad': 'actividad', 'subtipo': 'mano_obra',   'prefijo': 'MOB', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'actividad', 'subtipo': 'material',    'prefijo': 'MAT', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'actividad', 'subtipo': 'equipo',      'prefijo': 'EQP', 'formato': '{prefijo}-{numero:04d}'},
    {'entidad': 'actividad', 'subtipo': 'subcontrato', 'prefijo': 'SUB', 'formato': '{prefijo}-{numero:04d}'},
    # ── Terceros ───────────────────────────────────────────────────
    {'entidad': 'tercero',   'subtipo': '',             'prefijo': 'TER', 'formato': '{prefijo}-{numero:04d}'},
]

created = 0
updated = 0
for cfg in CONSECUTIVOS:
    obj, is_new = ConfiguracionConsecutivo.objects.update_or_create(
        company=company,
        entidad=cfg['entidad'],
        subtipo=cfg['subtipo'],
        defaults={
            'prefijo':  cfg['prefijo'],
            'formato':  cfg['formato'],
            'activo':   True,
        },
    )
    estado = 'CREADO' if is_new else 'ACTUALIZADO'
    print(f'  [{estado}] {obj}')
    if is_new:
        created += 1
    else:
        updated += 1

print(f'\nListo: {created} creados, {updated} actualizados.')
