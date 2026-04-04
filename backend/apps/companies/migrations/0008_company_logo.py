from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0007_rename_ventas_cobros_to_crm_soporte"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="logo",
            field=models.ImageField(
                blank=True,
                help_text="Logo de la empresa para reportes PDF",
                null=True,
                upload_to="company_logos/",
            ),
        ),
    ]
