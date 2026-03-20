import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tercero',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('codigo', models.CharField(db_index=True, max_length=50)),
                ('tipo_identificacion', models.CharField(
                    choices=[('nit', 'NIT'), ('cc', 'Cédula de ciudadanía'), ('ce', 'Cédula de extranjería'), ('pas', 'Pasaporte'), ('otro', 'Otro')],
                    max_length=20,
                )),
                ('numero_identificacion', models.CharField(max_length=50)),
                ('primer_nombre', models.CharField(blank=True, max_length=100)),
                ('segundo_nombre', models.CharField(blank=True, max_length=100)),
                ('primer_apellido', models.CharField(blank=True, max_length=100)),
                ('segundo_apellido', models.CharField(blank=True, max_length=100)),
                ('razon_social', models.CharField(blank=True, max_length=255)),
                ('nombre_completo', models.CharField(db_index=True, editable=False, max_length=512)),
                ('tipo_persona', models.CharField(
                    choices=[('natural', 'Persona natural'), ('juridica', 'Persona jurídica')],
                    max_length=10,
                )),
                ('tipo_tercero', models.CharField(
                    blank=True,
                    choices=[('cliente', 'Cliente'), ('proveedor', 'Proveedor'), ('subcontratista', 'Subcontratista'), ('interventor', 'Interventor'), ('consultor', 'Consultor'), ('empleado', 'Empleado'), ('otro', 'Otro')],
                    max_length=20,
                )),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('telefono', models.CharField(blank=True, max_length=30)),
                ('celular', models.CharField(blank=True, max_length=30)),
                ('saiopen_id', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('sai_key', models.CharField(blank=True, max_length=100, null=True)),
                ('saiopen_synced', models.BooleanField(default=False)),
                ('activo', models.BooleanField(db_index=True, default=True)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='%(class)s_set',
                    to='companies.company',
                    db_index=True,
                )),
            ],
            options={
                'verbose_name': 'Tercero',
                'verbose_name_plural': 'Terceros',
                'ordering': ['nombre_completo'],
                'unique_together': {('company', 'tipo_identificacion', 'numero_identificacion')},
            },
        ),
        migrations.CreateModel(
            name='TerceroDireccion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tipo', models.CharField(
                    choices=[('principal', 'Principal'), ('sucursal', 'Sucursal'), ('bodega', 'Bodega'), ('facturacion', 'Facturación'), ('otro', 'Otro')],
                    default='principal',
                    max_length=20,
                )),
                ('nombre_sucursal', models.CharField(blank=True, max_length=255)),
                ('pais', models.CharField(default='Colombia', max_length=100)),
                ('departamento', models.CharField(max_length=100)),
                ('ciudad', models.CharField(max_length=100)),
                ('direccion_linea1', models.CharField(max_length=255)),
                ('direccion_linea2', models.CharField(blank=True, max_length=255)),
                ('codigo_postal', models.CharField(blank=True, max_length=20)),
                ('nombre_contacto', models.CharField(blank=True, max_length=255)),
                ('telefono_contacto', models.CharField(blank=True, max_length=30)),
                ('email_contacto', models.EmailField(blank=True, max_length=254)),
                ('saiopen_linea_id', models.CharField(blank=True, max_length=50, null=True)),
                ('activa', models.BooleanField(default=True)),
                ('es_principal', models.BooleanField(default=False)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='%(class)s_set',
                    to='companies.company',
                    db_index=True,
                )),
                ('tercero', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='direcciones',
                    to='terceros.tercero',
                )),
            ],
            options={
                'verbose_name': 'Dirección de tercero',
                'verbose_name_plural': 'Direcciones de tercero',
                'ordering': ['-es_principal', 'tipo'],
            },
        ),
    ]
