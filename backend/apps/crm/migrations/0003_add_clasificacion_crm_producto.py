from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_actividad_add_lead_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='crmproducto',
            name='reffabrica',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='crmproducto',
            name='linea_codigo',
            field=models.CharField(blank=True, default='', max_length=10),
        ),
        migrations.AddField(
            model_name='crmproducto',
            name='linea_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
        migrations.AddField(
            model_name='crmproducto',
            name='grupo_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
        migrations.AddField(
            model_name='crmproducto',
            name='subgrupo_descripcion',
            field=models.CharField(blank=True, default='', max_length=60),
        ),
    ]
