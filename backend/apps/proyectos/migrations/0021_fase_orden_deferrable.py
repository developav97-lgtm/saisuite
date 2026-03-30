"""
Migration 0021 — Make the unique_together(fase, orden) constraint DEFERRABLE.

PostgreSQL validates row-level unique constraints immediately by default, which
means any UPDATE that swaps two orden values fails mid-statement.
Marking it DEFERRABLE INITIALLY DEFERRED defers validation to end-of-transaction,
allowing us to reassign all orden values atomically without conflicts.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('proyectos', '0020_alter_activity_tipo_add_milestone'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE proyectos_phase
                    DROP CONSTRAINT proyectos_fase_proyecto_id_orden_1e760b89_uniq;

                ALTER TABLE proyectos_phase
                    ADD CONSTRAINT proyectos_fase_proyecto_id_orden_1e760b89_uniq
                        UNIQUE (proyecto_id, orden)
                        DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                ALTER TABLE proyectos_phase
                    DROP CONSTRAINT proyectos_fase_proyecto_id_orden_1e760b89_uniq;

                ALTER TABLE proyectos_phase
                    ADD CONSTRAINT proyectos_fase_proyecto_id_orden_1e760b89_uniq
                        UNIQUE (proyecto_id, orden);
            """,
        ),
    ]
