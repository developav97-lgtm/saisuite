# Fix unique_together for FacturaDetalle:
# OEDET.CONTEO is the line number within a single invoice (1, 2, 3...),
# NOT a global counter. Two invoices can share the same CONTEO value,
# so (company, conteo) is not unique. Correct key is (company, factura, conteo).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contabilidad", "0006_add_sync_watermarks_oe_oedet_carpro_itemact"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="facturadetalle",
            unique_together={("company", "factura", "conteo")},
        ),
    ]
