"""
Migración: agrega tipo, subtipo al consecutivo.

El `nombre` sigue como campo libre. Se agrega:
  - tipo:    proyecto | actividad | factura
  - subtipo: subtipo de la entidad (blank=True)
  unique_together cambia de (company, nombre) → (company, prefijo)

Data migration: intenta parsear el `nombre` actual (formato 'tipo/subtipo' o 'tipo')
para poblar los nuevos campos.
"""
from django.db import migrations, models


def inferir_tipo_subtipo(apps, schema_editor):
    """Parsea 'tipo/subtipo' o 'tipo' del campo nombre existente."""
    TIPOS_VALIDOS = {'proyecto', 'actividad', 'factura'}
    ConfiguracionConsecutivo = apps.get_model('core', 'ConfiguracionConsecutivo')
    for cfg in ConfiguracionConsecutivo.objects.all():
        nombre = cfg.nombre or ''
        if '/' in nombre:
            partes = nombre.split('/', 1)
            tipo_raw    = partes[0].strip()
            subtipo_raw = partes[1].strip()
        else:
            tipo_raw    = nombre.strip()
            subtipo_raw = ''

        cfg.tipo    = tipo_raw if tipo_raw in TIPOS_VALIDOS else 'proyecto'
        cfg.subtipo = subtipo_raw
        cfg.save(update_fields=['tipo', 'subtipo'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_consecutivo_redesign'),
    ]

    operations = [
        # 1. Agrega `tipo` nullable
        migrations.AddField(
            model_name='configuracionconsecutivo',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('proyecto',  'Proyecto'),
                    ('actividad', 'Actividad'),
                    ('factura',   'Factura'),
                ],
                max_length=30,
                null=True,
                blank=True,
            ),
        ),

        # 2. Agrega `subtipo`
        migrations.AddField(
            model_name='configuracionconsecutivo',
            name='subtipo',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Subtipo de la entidad. Vacío = aplica a todos los subtipos.',
                max_length=50,
            ),
        ),

        # 3. Data migration
        migrations.RunPython(inferir_tipo_subtipo, migrations.RunPython.noop),

        # 4. Hace `tipo` NOT NULL
        migrations.AlterField(
            model_name='configuracionconsecutivo',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('proyecto',  'Proyecto'),
                    ('actividad', 'Actividad'),
                    ('factura',   'Factura'),
                ],
                max_length=30,
            ),
        ),

        # 5. Quita unique_together viejo (company, nombre)
        migrations.AlterUniqueTogether(
            name='configuracionconsecutivo',
            unique_together=set(),
        ),

        # 6. Nuevo unique_together (company, prefijo)
        migrations.AlterUniqueTogether(
            name='configuracionconsecutivo',
            unique_together={('company', 'prefijo')},
        ),

        # 7. Actualiza ordering
        migrations.AlterModelOptions(
            name='configuracionconsecutivo',
            options={
                'ordering': ['tipo', 'subtipo', 'nombre'],
                'verbose_name': 'Configuración de consecutivo',
                'verbose_name_plural': 'Configuraciones de consecutivos',
            },
        ),
    ]
