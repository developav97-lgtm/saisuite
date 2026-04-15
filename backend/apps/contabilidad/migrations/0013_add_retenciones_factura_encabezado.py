from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0012_add_clasificacion_factura_detalle'),
    ]

    operations = [
        migrations.AddField(
            model_name='facturaencabezado',
            name='tercero_razon_social',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='tipo_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='destotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='otroscargos',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='porcrtfte',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='reteica',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='porcentaje_reteica',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='facturaencabezado',
            name='reteiva',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
