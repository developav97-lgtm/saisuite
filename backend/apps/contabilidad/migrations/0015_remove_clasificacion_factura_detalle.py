from django.db import migrations


class Migration(migrations.Migration):
    """
    Mueve la clasificación de producto (linea/grupo/subgrupo + reffabrica + class)
    fuera de FacturaDetalle hacia CrmProducto.
    Estos datos pertenecen al maestro ITEM, no al movimiento transaccional.
    """

    dependencies = [
        ('contabilidad', '0014_add_dimensiones_factura_detalle'),
    ]

    operations = [
        migrations.RemoveField(model_name='facturadetalle', name='item_reffabrica'),
        migrations.RemoveField(model_name='facturadetalle', name='item_class'),
        migrations.RemoveField(model_name='facturadetalle', name='linea_codigo'),
        migrations.RemoveField(model_name='facturadetalle', name='linea_descripcion'),
        migrations.RemoveField(model_name='facturadetalle', name='grupo_codigo'),
        migrations.RemoveField(model_name='facturadetalle', name='grupo_descripcion'),
        migrations.RemoveField(model_name='facturadetalle', name='subgrupo_codigo'),
        migrations.RemoveField(model_name='facturadetalle', name='subgrupo_descripcion'),
    ]
