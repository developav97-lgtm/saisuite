"""
Migración: rediseño de ConfiguracionConsecutivo.

Cambia el modelo de un "consecutivo por entidad/subtipo" a un
"maestro general" identificado por nombre libre.

Pasos:
  1. Agrega campo `nombre` (nullable temporalmente).
  2. Migra datos existentes: nombre = entidad + '/' + subtipo o solo entidad.
  3. Hace `nombre` NOT NULL + unique_together nuevo.
  4. Elimina campos `entidad` y `subtipo`.
"""
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


def migrar_nombre(apps, schema_editor):
    """Genera `nombre` a partir de entidad y subtipo existentes."""
    ConfiguracionConsecutivo = apps.get_model('core', 'ConfiguracionConsecutivo')
    for cfg in ConfiguracionConsecutivo.objects.all():
        entidad = getattr(cfg, 'entidad', '') or ''
        subtipo = getattr(cfg, 'subtipo', '') or ''
        if subtipo:
            cfg.nombre = f'{entidad}/{subtipo}'
        else:
            cfg.nombre = entidad or 'Sin nombre'
        cfg.save(update_fields=['nombre'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_add_configuracion_consecutivo'),
    ]

    operations = [
        # 1. Agregar `nombre` nullable
        migrations.AddField(
            model_name='configuracionconsecutivo',
            name='nombre',
            field=models.CharField(
                max_length=100,
                null=True,
                blank=True,
                help_text='Nombre descriptivo del consecutivo.',
            ),
        ),

        # 2. Migrar datos
        migrations.RunPython(migrar_nombre, migrations.RunPython.noop),

        # 3. Hacer `nombre` NOT NULL
        migrations.AlterField(
            model_name='configuracionconsecutivo',
            name='nombre',
            field=models.CharField(
                max_length=100,
                help_text='Nombre descriptivo del consecutivo. Ej: Proyectos obra civil, Facturas',
            ),
        ),

        # 4. Quitar unique_together viejo
        migrations.AlterUniqueTogether(
            name='configuracionconsecutivo',
            unique_together=set(),
        ),

        # 5. Eliminar `entidad` y `subtipo`
        migrations.RemoveField(
            model_name='configuracionconsecutivo',
            name='entidad',
        ),
        migrations.RemoveField(
            model_name='configuracionconsecutivo',
            name='subtipo',
        ),

        # 6. Nuevo unique_together y ordering
        migrations.AlterModelOptions(
            name='configuracionconsecutivo',
            options={
                'ordering': ['nombre'],
                'verbose_name': 'Configuración de consecutivo',
                'verbose_name_plural': 'Configuraciones de consecutivos',
            },
        ),
        migrations.AlterUniqueTogether(
            name='configuracionconsecutivo',
            unique_together={('company', 'nombre')},
        ),
    ]
