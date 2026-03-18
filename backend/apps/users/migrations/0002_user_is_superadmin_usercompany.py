# Generated manually — SaiSuite multi-tenant v2
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0003_company_plan_saiopen'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_superadmin',
            field=models.BooleanField(
                default=False,
                help_text='Superadmin global ValMen Tech',
            ),
        ),
        migrations.CreateModel(
            name='UserCompany',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('role', models.CharField(
                    choices=[
                        ('company_admin',  'Administrador de empresa'),
                        ('seller',         'Vendedor'),
                        ('collector',      'Cobrador'),
                        ('viewer',         'Solo lectura'),
                        ('valmen_admin',   'Admin ValMen Tech'),
                        ('valmen_support', 'Soporte ValMen Tech'),
                    ],
                    default='viewer',
                    max_length=20,
                )),
                ('modules_access', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Subset de módulos activos de la empresa a los que tiene acceso este usuario.',
                )),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_companies',
                    to='companies.company',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_companies',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Usuario-Empresa',
                'verbose_name_plural': 'Usuarios-Empresa',
            },
        ),
        migrations.AlterUniqueTogether(
            name='usercompany',
            unique_together={('user', 'company')},
        ),
    ]
