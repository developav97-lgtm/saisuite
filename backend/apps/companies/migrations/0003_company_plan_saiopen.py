# Generated manually — SaiSuite multi-tenant v2
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_alter_companymodule_module'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='plan',
            field=models.CharField(
                choices=[
                    ('starter',      'Starter'),
                    ('professional', 'Professional'),
                    ('enterprise',   'Enterprise'),
                ],
                default='starter',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='company',
            name='saiopen_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='saiopen_db_path',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
    ]
