# Generated manually — 2026-03-19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0004_companylicense_licensepayment'),
        ('proyectos', '0002_add_actividad_actividadproyecto'),
    ]

    operations = [
        # Avance automático en Proyecto
        migrations.AddField(
            model_name='proyecto',
            name='porcentaje_avance',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                editable=False,
                help_text='Porcentaje de avance físico (0-100). Calculado automáticamente desde fases.',
                max_digits=5,
            ),
        ),
        # ConfiguracionModulo
        migrations.CreateModel(
            name='ConfiguracionModulo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requiere_sync_saiopen_para_ejecucion', models.BooleanField(
                    default=False,
                    help_text='Si True, el proyecto debe estar sincronizado con Saiopen antes de iniciar ejecución.',
                )),
                ('dias_alerta_vencimiento', models.PositiveIntegerField(
                    default=15,
                    help_text='Días antes del vencimiento de fase para mostrar alerta.',
                )),
                ('company', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='configuracion_proyectos',
                    to='companies.company',
                )),
            ],
            options={
                'verbose_name': 'Configuración de proyectos',
                'verbose_name_plural': 'Configuraciones de proyectos',
            },
        ),
    ]
