"""
SaiSuite — Migration: CompanyLicense y LicensePayment
"""
import uuid
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0003_company_plan_saiopen'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyLicense',
            fields=[
                ('id',         models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('plan',       models.CharField(choices=[('starter', 'Starter'), ('professional', 'Professional'), ('enterprise', 'Enterprise')], default='starter', max_length=20)),
                ('status',     models.CharField(choices=[('trial', 'Prueba'), ('active', 'Activa'), ('expired', 'Expirada'), ('suspended', 'Suspendida')], default='trial', max_length=20)),
                ('starts_at',  models.DateField()),
                ('expires_at', models.DateField()),
                ('max_users',  models.PositiveIntegerField(default=5)),
                ('notes',      models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company',    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='license', to='companies.company')),
            ],
            options={
                'verbose_name': 'Licencia',
                'verbose_name_plural': 'Licencias',
            },
        ),
        migrations.CreateModel(
            name='LicensePayment',
            fields=[
                ('id',           models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('amount',       models.DecimalField(decimal_places=2, max_digits=15)),
                ('payment_date', models.DateField()),
                ('method',       models.CharField(choices=[('transfer', 'Transferencia'), ('cash', 'Efectivo'), ('card', 'Tarjeta')], default='transfer', max_length=20)),
                ('reference',    models.CharField(blank=True, default='', max_length=100)),
                ('notes',        models.TextField(blank=True, default='')),
                ('created_at',   models.DateTimeField(default=django.utils.timezone.now)),
                ('license',      models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='companies.companylicense')),
            ],
            options={
                'verbose_name': 'Pago de licencia',
                'verbose_name_plural': 'Pagos de licencia',
                'ordering': ['-payment_date'],
            },
        ),
    ]
