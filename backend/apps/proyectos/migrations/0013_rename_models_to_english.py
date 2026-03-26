# REFT-03 + REFT-04 — Rename Spanish model names and choice values to English.
# Generated manually — do NOT regenerate with makemigrations or the RenameModel
# operations will be lost and Django will attempt destructive DROP/CREATE.
#
# Execution order:
#   1. RenameModel (12 models without explicit db_table)
#   2. AlterField  (update choices metadata on affected fields)
#   3. RunSQL      (data migration: update stored string values in DB)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("proyectos", "0012_timesheetentry"),
        ("companies", "0004_companylicense_licensepayment"),
        ("terceros", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ================================================================
        # 1. RENAME MODELS
        #    Models with an explicit db_table (SesionTrabajo → WorkSession,
        #    TimesheetEntry) are NOT renamed here because Django keeps their
        #    physical table name unchanged via db_table. They still need a
        #    RenameModel so Django's internal state stays consistent.
        # ================================================================
        migrations.RenameModel(
            old_name="Proyecto",
            new_name="Project",
        ),
        migrations.RenameModel(
            old_name="ConfiguracionModulo",
            new_name="ModuleSettings",
        ),
        migrations.RenameModel(
            old_name="Fase",
            new_name="Phase",
        ),
        migrations.RenameModel(
            old_name="TerceroProyecto",
            new_name="ProjectStakeholder",
        ),
        migrations.RenameModel(
            old_name="DocumentoContable",
            new_name="AccountingDocument",
        ),
        migrations.RenameModel(
            old_name="Actividad",
            new_name="Activity",
        ),
        migrations.RenameModel(
            old_name="ActividadProyecto",
            new_name="ProjectActivity",
        ),
        migrations.RenameModel(
            old_name="ActividadSaiopen",
            new_name="SaiopenActivity",
        ),
        migrations.RenameModel(
            old_name="Hito",
            new_name="Milestone",
        ),
        migrations.RenameModel(
            old_name="TareaTag",
            new_name="TaskTag",
        ),
        migrations.RenameModel(
            old_name="Tarea",
            new_name="Task",
        ),
        migrations.RenameModel(
            old_name="TareaDependencia",
            new_name="TaskDependency",
        ),
        # SesionTrabajo has db_table='sesiones_trabajo' — rename model state only,
        # no physical table rename occurs.
        migrations.RenameModel(
            old_name="SesionTrabajo",
            new_name="WorkSession",
        ),

        # ================================================================
        # 2. ALTER FIELDS — update choices metadata
        #    These do NOT change the physical column; they update Django's
        #    internal choices list so validation and display are correct
        #    after the data migration in step 3.
        # ================================================================

        # Project.tipo — ProjectType choices
        migrations.AlterField(
            model_name="project",
            name="tipo",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("civil_works",   "Obra civil"),
                    ("consulting",    "Consultoría"),
                    ("manufacturing", "Manufactura"),
                    ("services",      "Servicios"),
                    ("public_tender", "Licitación pública"),
                    ("other",         "Otro"),
                ],
            ),
        ),

        # Project.estado — ProjectStatus choices
        migrations.AlterField(
            model_name="project",
            name="estado",
            field=models.CharField(
                max_length=20,
                default="draft",
                choices=[
                    ("draft",        "Borrador"),
                    ("planned",      "Planificado"),
                    ("in_progress",  "En ejecución"),
                    ("suspended",    "Suspendido"),
                    ("closed",       "Cerrado"),
                    ("cancelled",    "Cancelado"),
                ],
            ),
        ),

        # Phase.estado — PhaseStatus choices
        migrations.AlterField(
            model_name="phase",
            name="estado",
            field=models.CharField(
                max_length=20,
                default="planned",
                choices=[
                    ("planned",   "Planificada"),
                    ("active",    "Activa"),
                    ("completed", "Completada"),
                    ("cancelled", "Cancelada"),
                ],
                help_text="Estado operativo de la fase.",
            ),
        ),

        # ProjectStakeholder.rol — StakeholderRole choices
        migrations.AlterField(
            model_name="projectstakeholder",
            name="rol",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("client",        "Cliente"),
                    ("subcontractor", "Subcontratista"),
                    ("vendor",        "Proveedor"),
                    ("consultant",    "Consultor"),
                    ("inspector",     "Interventor"),
                    ("supervisor",    "Supervisor"),
                ],
            ),
        ),

        # AccountingDocument.tipo_documento — DocumentType choices
        migrations.AlterField(
            model_name="accountingdocument",
            name="tipo_documento",
            field=models.CharField(
                max_length=30,
                choices=[
                    ("sales_invoice",    "Factura de venta"),
                    ("purchase_invoice", "Factura de compra"),
                    ("purchase_order",   "Orden de compra"),
                    ("cash_receipt",     "Recibo de caja"),
                    ("expense_voucher",  "Comprobante de egreso"),
                    ("payroll",          "Nómina"),
                    ("advance",          "Anticipo"),
                    ("work_certificate", "Acta de obra"),
                ],
            ),
        ),

        # Activity.tipo — ActivityType choices
        migrations.AlterField(
            model_name="activity",
            name="tipo",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("labor",       "Mano de obra"),
                    ("material",    "Material"),
                    ("equipment",   "Equipo"),
                    ("subcontract", "Subcontrato"),
                ],
            ),
        ),

        # SaiopenActivity.unidad_medida — MeasurementMode choices
        migrations.AlterField(
            model_name="saiopenactivity",
            name="unidad_medida",
            field=models.CharField(
                max_length=20,
                default="status_only",
                choices=[
                    ("status_only", "Solo estados"),
                    ("timesheet",   "Timesheet (horas)"),
                    ("quantity",    "Cantidad ejecutada"),
                ],
                help_text="Determina el modo de medición: status_only, timesheet o quantity.",
            ),
        ),

        # Task.estado choices
        migrations.AlterField(
            model_name="task",
            name="estado",
            field=models.CharField(
                max_length=20,
                default="todo",
                choices=[
                    ("todo",        "To Do"),
                    ("in_progress", "In Progress"),
                    ("in_review",   "In Review"),
                    ("blocked",     "Blocked"),
                    ("completed",   "Completed"),
                    ("cancelled",   "Cancelled"),
                ],
            ),
        ),

        # Task.frecuencia_recurrencia choices
        migrations.AlterField(
            model_name="task",
            name="frecuencia_recurrencia",
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                choices=[
                    ("daily",   "Daily"),
                    ("weekly",  "Weekly"),
                    ("monthly", "Monthly"),
                ],
            ),
        ),

        # WorkSession.estado choices
        migrations.AlterField(
            model_name="worksession",
            name="estado",
            field=models.CharField(
                max_length=20,
                default="active",
                choices=[
                    ("active",   "Active"),
                    ("paused",   "Paused"),
                    ("finished", "Finished"),
                ],
                verbose_name="Estado",
            ),
        ),

        # ModuleSettings.modo_timesheet choices
        migrations.AlterField(
            model_name="modulesettings",
            name="modo_timesheet",
            field=models.CharField(
                max_length=20,
                default="both",
                verbose_name="Modo de timesheet",
                choices=[
                    ("manual",   "Manual — hour recording"),
                    ("timer",    "Timer — real time"),
                    ("both",     "Both modes available"),
                    ("disabled", "Disabled"),
                ],
            ),
        ),

        # ================================================================
        # 3. DATA MIGRATION — update stored string values
        #    Each RunSQL is wrapped individually so failures are isolated.
        #    reverse_sql restores the original Spanish values.
        #
        #    Table names after RenameModel (no explicit db_table):
        #      Proyecto          → proyectos_project
        #      ConfiguracionModulo → proyectos_modulesettings
        #      Fase              → proyectos_phase
        #      TerceroProyecto   → proyectos_projectstakeholder
        #      DocumentoContable → proyectos_accountingdocument
        #      Actividad         → proyectos_activity
        #      ActividadProyecto → proyectos_projectactivity
        #      ActividadSaiopen  → proyectos_saiopenactivity
        #      Hito              → proyectos_milestone
        #      TareaTag          → proyectos_tasktag
        #      Tarea             → proyectos_task
        #      TareaDependencia  → proyectos_taskdependency
        #    Tables with explicit db_table (unchanged):
        #      SesionTrabajo     → sesiones_trabajo
        #      TimesheetEntry    → timesheet_entries
        # ================================================================

        # -- ProjectStatus (Project.estado) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_project SET estado = 'draft'       WHERE estado = 'borrador';
                UPDATE proyectos_project SET estado = 'planned'     WHERE estado = 'planificado';
                UPDATE proyectos_project SET estado = 'in_progress' WHERE estado = 'en_ejecucion';
                UPDATE proyectos_project SET estado = 'suspended'   WHERE estado = 'suspendido';
                UPDATE proyectos_project SET estado = 'closed'      WHERE estado = 'cerrado';
                UPDATE proyectos_project SET estado = 'cancelled'   WHERE estado = 'cancelado';
            """,
            reverse_sql="""
                UPDATE proyectos_project SET estado = 'borrador'     WHERE estado = 'draft';
                UPDATE proyectos_project SET estado = 'planificado'  WHERE estado = 'planned';
                UPDATE proyectos_project SET estado = 'en_ejecucion' WHERE estado = 'in_progress';
                UPDATE proyectos_project SET estado = 'suspendido'   WHERE estado = 'suspended';
                UPDATE proyectos_project SET estado = 'cerrado'      WHERE estado = 'closed';
                UPDATE proyectos_project SET estado = 'cancelado'    WHERE estado = 'cancelled';
            """,
        ),

        # -- ProjectType (Project.tipo) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_project SET tipo = 'civil_works'   WHERE tipo = 'obra_civil';
                UPDATE proyectos_project SET tipo = 'consulting'     WHERE tipo = 'consultoria';
                UPDATE proyectos_project SET tipo = 'manufacturing'  WHERE tipo = 'manufactura';
                UPDATE proyectos_project SET tipo = 'services'       WHERE tipo = 'servicios';
                UPDATE proyectos_project SET tipo = 'public_tender'  WHERE tipo = 'licitacion_publica';
                UPDATE proyectos_project SET tipo = 'other'          WHERE tipo = 'otro';
            """,
            reverse_sql="""
                UPDATE proyectos_project SET tipo = 'obra_civil'         WHERE tipo = 'civil_works';
                UPDATE proyectos_project SET tipo = 'consultoria'        WHERE tipo = 'consulting';
                UPDATE proyectos_project SET tipo = 'manufactura'        WHERE tipo = 'manufacturing';
                UPDATE proyectos_project SET tipo = 'servicios'          WHERE tipo = 'services';
                UPDATE proyectos_project SET tipo = 'licitacion_publica' WHERE tipo = 'public_tender';
                UPDATE proyectos_project SET tipo = 'otro'               WHERE tipo = 'other';
            """,
        ),

        # -- PhaseStatus (Phase.estado) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_phase SET estado = 'planned'   WHERE estado = 'planificada';
                UPDATE proyectos_phase SET estado = 'active'    WHERE estado = 'activa';
                UPDATE proyectos_phase SET estado = 'completed' WHERE estado = 'completada';
                UPDATE proyectos_phase SET estado = 'cancelled' WHERE estado = 'cancelada';
            """,
            reverse_sql="""
                UPDATE proyectos_phase SET estado = 'planificada' WHERE estado = 'planned';
                UPDATE proyectos_phase SET estado = 'activa'      WHERE estado = 'active';
                UPDATE proyectos_phase SET estado = 'completada'  WHERE estado = 'completed';
                UPDATE proyectos_phase SET estado = 'cancelada'   WHERE estado = 'cancelled';
            """,
        ),

        # -- Task.estado --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_task SET estado = 'todo'        WHERE estado = 'por_hacer';
                UPDATE proyectos_task SET estado = 'in_progress' WHERE estado = 'en_progreso';
                UPDATE proyectos_task SET estado = 'in_review'   WHERE estado = 'en_revision';
                UPDATE proyectos_task SET estado = 'blocked'     WHERE estado = 'bloqueada';
                UPDATE proyectos_task SET estado = 'completed'   WHERE estado = 'completada';
                UPDATE proyectos_task SET estado = 'cancelled'   WHERE estado = 'cancelada';
            """,
            reverse_sql="""
                UPDATE proyectos_task SET estado = 'por_hacer'   WHERE estado = 'todo';
                UPDATE proyectos_task SET estado = 'en_progreso' WHERE estado = 'in_progress';
                UPDATE proyectos_task SET estado = 'en_revision' WHERE estado = 'in_review';
                UPDATE proyectos_task SET estado = 'bloqueada'   WHERE estado = 'blocked';
                UPDATE proyectos_task SET estado = 'completada'  WHERE estado = 'completed';
                UPDATE proyectos_task SET estado = 'cancelada'   WHERE estado = 'cancelled';
            """,
        ),

        # -- Task.frecuencia_recurrencia --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_task SET frecuencia_recurrencia = 'daily'   WHERE frecuencia_recurrencia = 'diaria';
                UPDATE proyectos_task SET frecuencia_recurrencia = 'weekly'  WHERE frecuencia_recurrencia = 'semanal';
                UPDATE proyectos_task SET frecuencia_recurrencia = 'monthly' WHERE frecuencia_recurrencia = 'mensual';
            """,
            reverse_sql="""
                UPDATE proyectos_task SET frecuencia_recurrencia = 'diaria'  WHERE frecuencia_recurrencia = 'daily';
                UPDATE proyectos_task SET frecuencia_recurrencia = 'semanal' WHERE frecuencia_recurrencia = 'weekly';
                UPDATE proyectos_task SET frecuencia_recurrencia = 'mensual' WHERE frecuencia_recurrencia = 'monthly';
            """,
        ),

        # -- ActivityType (Activity.tipo) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_activity SET tipo = 'labor'       WHERE tipo = 'mano_obra';
                UPDATE proyectos_activity SET tipo = 'equipment'   WHERE tipo = 'equipo';
                UPDATE proyectos_activity SET tipo = 'subcontract' WHERE tipo = 'subcontrato';
            """,
            reverse_sql="""
                UPDATE proyectos_activity SET tipo = 'mano_obra'   WHERE tipo = 'labor';
                UPDATE proyectos_activity SET tipo = 'equipo'      WHERE tipo = 'equipment';
                UPDATE proyectos_activity SET tipo = 'subcontrato' WHERE tipo = 'subcontract';
            """,
        ),

        # -- MeasurementMode (SaiopenActivity.unidad_medida) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_saiopenactivity SET unidad_medida = 'status_only' WHERE unidad_medida = 'solo_estados';
                UPDATE proyectos_saiopenactivity SET unidad_medida = 'quantity'    WHERE unidad_medida = 'cantidad';
            """,
            reverse_sql="""
                UPDATE proyectos_saiopenactivity SET unidad_medida = 'solo_estados' WHERE unidad_medida = 'status_only';
                UPDATE proyectos_saiopenactivity SET unidad_medida = 'cantidad'     WHERE unidad_medida = 'quantity';
            """,
        ),

        # -- StakeholderRole (ProjectStakeholder.rol) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_projectstakeholder SET rol = 'client'        WHERE rol = 'cliente';
                UPDATE proyectos_projectstakeholder SET rol = 'subcontractor' WHERE rol = 'subcontratista';
                UPDATE proyectos_projectstakeholder SET rol = 'vendor'        WHERE rol = 'proveedor';
                UPDATE proyectos_projectstakeholder SET rol = 'consultant'    WHERE rol = 'consultor';
                UPDATE proyectos_projectstakeholder SET rol = 'inspector'     WHERE rol = 'interventor';
            """,
            reverse_sql="""
                UPDATE proyectos_projectstakeholder SET rol = 'cliente'        WHERE rol = 'client';
                UPDATE proyectos_projectstakeholder SET rol = 'subcontratista' WHERE rol = 'subcontractor';
                UPDATE proyectos_projectstakeholder SET rol = 'proveedor'      WHERE rol = 'vendor';
                UPDATE proyectos_projectstakeholder SET rol = 'consultor'      WHERE rol = 'consultant';
                UPDATE proyectos_projectstakeholder SET rol = 'interventor'    WHERE rol = 'inspector';
            """,
        ),

        # -- DocumentType (AccountingDocument.tipo_documento) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_accountingdocument SET tipo_documento = 'sales_invoice'    WHERE tipo_documento = 'factura_venta';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'purchase_invoice' WHERE tipo_documento = 'factura_compra';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'purchase_order'   WHERE tipo_documento = 'orden_compra';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'cash_receipt'     WHERE tipo_documento = 'recibo_caja';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'expense_voucher'  WHERE tipo_documento = 'comprobante_egreso';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'payroll'          WHERE tipo_documento = 'nomina';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'advance'          WHERE tipo_documento = 'anticipo';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'work_certificate' WHERE tipo_documento = 'acta_obra';
            """,
            reverse_sql="""
                UPDATE proyectos_accountingdocument SET tipo_documento = 'factura_venta'      WHERE tipo_documento = 'sales_invoice';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'factura_compra'     WHERE tipo_documento = 'purchase_invoice';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'orden_compra'       WHERE tipo_documento = 'purchase_order';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'recibo_caja'        WHERE tipo_documento = 'cash_receipt';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'comprobante_egreso' WHERE tipo_documento = 'expense_voucher';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'nomina'             WHERE tipo_documento = 'payroll';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'anticipo'           WHERE tipo_documento = 'advance';
                UPDATE proyectos_accountingdocument SET tipo_documento = 'acta_obra'          WHERE tipo_documento = 'work_certificate';
            """,
        ),

        # -- WorkSession.estado (table: sesiones_trabajo — explicit db_table, unchanged) --
        migrations.RunSQL(
            sql="""
                UPDATE sesiones_trabajo SET estado = 'active'   WHERE estado = 'activa';
                UPDATE sesiones_trabajo SET estado = 'paused'   WHERE estado = 'pausada';
                UPDATE sesiones_trabajo SET estado = 'finished' WHERE estado = 'finalizada';
            """,
            reverse_sql="""
                UPDATE sesiones_trabajo SET estado = 'activa'     WHERE estado = 'active';
                UPDATE sesiones_trabajo SET estado = 'pausada'    WHERE estado = 'paused';
                UPDATE sesiones_trabajo SET estado = 'finalizada' WHERE estado = 'finished';
            """,
        ),

        # -- ModuleSettings.modo_timesheet (proyectos_modulesettings) --
        migrations.RunSQL(
            sql="""
                UPDATE proyectos_modulesettings SET modo_timesheet = 'timer'    WHERE modo_timesheet = 'cronometro';
                UPDATE proyectos_modulesettings SET modo_timesheet = 'both'     WHERE modo_timesheet = 'ambos';
                UPDATE proyectos_modulesettings SET modo_timesheet = 'disabled' WHERE modo_timesheet = 'desactivado';
            """,
            reverse_sql="""
                UPDATE proyectos_modulesettings SET modo_timesheet = 'cronometro'  WHERE modo_timesheet = 'timer';
                UPDATE proyectos_modulesettings SET modo_timesheet = 'ambos'       WHERE modo_timesheet = 'both';
                UPDATE proyectos_modulesettings SET modo_timesheet = 'desactivado' WHERE modo_timesheet = 'disabled';
            """,
        ),
    ]
