import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0003_proyecto_porcentaje_avance_configuracion_modulo'),
        ('terceros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='terceroproyecto',
            name='tercero_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='proyectos_vinculados',
                to='terceros.tercero',
            ),
        ),
    ]
