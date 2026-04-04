"""
Migration: PlantillaTarea.actividad_saiopen FK
  SaiopenActivity → Activity (catálogo gestionado en la app)

Razón: Los usuarios gestionan actividades en Activity (via UI),
no en SaiopenActivity (sync externo Saiopen).
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0023_plantilla_tipo_replace_categoria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plantillatarea',
            name='actividad_saiopen',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='plantilla_tareas',
                to='proyectos.activity',
                verbose_name='Actividad',
            ),
        ),
    ]
