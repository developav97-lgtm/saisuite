from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0011_itemact_remove_item_descripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='facturadetalle',
            name='total_descuento',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='item_reffabrica',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='item_class',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='linea_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='linea_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='grupo_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='grupo_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='subgrupo_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='facturadetalle',
            name='subgrupo_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
    ]
