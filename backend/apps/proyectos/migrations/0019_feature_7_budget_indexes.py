"""
Migration 0019 — Feature #7: Budget & Cost Tracking
Custom partial unique index for ResourceCostRate.

Django's Meta.constraints cannot express PostgreSQL partial unique indexes
(WHERE clause). This migration creates:

    UNIQUE INDEX resource_cost_rates_open_rate_unique
        ON resource_cost_rates (user_id, company_id)
        WHERE end_date IS NULL;

This guarantees that only ONE active (open-ended) rate exists per
(user, company) pair. Overlapping closed ranges are validated in
budget_services.py before any INSERT/UPDATE.

Reversible: the index is dropped on migration reversal.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0018_feature_7_budget_models'),
    ]

    operations = [
        # Partial unique index: solo una tarifa "abierta" (end_date IS NULL)
        # por (user, company). No expresable como Meta.constraints estándar.
        migrations.RunSQL(
            sql="""
                CREATE UNIQUE INDEX resource_cost_rates_open_rate_unique
                    ON resource_cost_rates (user_id, company_id)
                    WHERE end_date IS NULL;
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS resource_cost_rates_open_rate_unique;
            """,
        ),
        # Índice compuesto para consultas de varianza presupuestal a nivel empresa
        migrations.RunSQL(
            sql="""
                CREATE INDEX idx_budget_snapshots_company_date
                    ON budget_snapshots (company_id, snapshot_date DESC);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_budget_snapshots_company_date;
            """,
        ),
        # Índice compuesto para lookup de tarifas vigentes: el hot path de
        # get_effective_rate() — user_id + company_id + rangos de fecha
        migrations.RunSQL(
            sql="""
                CREATE INDEX idx_cost_rates_user_company_dates
                    ON resource_cost_rates (user_id, company_id, start_date, end_date NULLS LAST);
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_cost_rates_user_company_dates;
            """,
        ),
    ]
