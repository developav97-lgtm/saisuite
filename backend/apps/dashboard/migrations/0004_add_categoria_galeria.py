from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0003_add_report_bi"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportbi",
            name="categoria_galeria",
            field=models.CharField(
                blank=True,
                choices=[
                    ("contabilidad", "Contabilidad"),
                    ("cuentas_pagar", "Cuentas por Pagar"),
                    ("cuentas_cobrar", "Cuentas por Cobrar"),
                    ("ventas", "Ventas"),
                    ("inventario", "Inventario"),
                    ("costos", "Costos y Gastos"),
                    ("proyectos", "Proyectos"),
                    ("tributario", "Tributario"),
                    ("gerencial", "Gerencial / KPIs"),
                ],
                help_text="Categoría para la galería pública. Solo aplica si es_template=True.",
                max_length=30,
                null=True,
            ),
        ),
    ]
