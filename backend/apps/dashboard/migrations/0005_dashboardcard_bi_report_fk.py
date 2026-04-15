"""
Migration: Add bi_report FK to DashboardCard.

Sprint 4 — Dashboard ↔ BI integration.
Permite que una tarjeta de tipo 'bi_report' referencie un ReportBI.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_add_categoria_galeria'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboardcard',
            name='bi_report',
            field=models.ForeignKey(
                blank=True,
                help_text='Reporte BI referenciado. Solo aplica cuando card_type_code="bi_report".',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='dashboard_cards',
                to='dashboard.reportbi',
            ),
        ),
    ]
