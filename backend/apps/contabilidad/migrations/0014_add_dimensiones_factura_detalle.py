from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0013_add_retenciones_factura_encabezado'),
    ]

    operations = [
        migrations.AddField(
            model_name='facturadetalle',
            name='departamento_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='centro_costo_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='actividad_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
    ]
