# Generated manually 2026-03-23
# DEC-020, DEC-021, DEC-022: ActividadSaiopen + EstadoFase + Tarea campos nuevos

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


def crear_fases_por_defecto_y_asignar(apps, schema_editor):
    """
    Data migration: crea una Fase "General" por empresa/proyecto para los
    proyectos que tengan tareas sin fase asignada, y asigna esas tareas.
    """
    Proyecto = apps.get_model('proyectos', 'Proyecto')
    Fase = apps.get_model('proyectos', 'Fase')
    Tarea = apps.get_model('proyectos', 'Tarea')

    proyectos_con_tareas_sin_fase = (
        Proyecto.objects.filter(tareas__fase__isnull=True).distinct()
    )

    for proyecto in proyectos_con_tareas_sin_fase:
        # Calcular siguiente orden disponible
        max_orden = Fase.objects.filter(proyecto=proyecto).order_by('-orden').values_list('orden', flat=True).first()
        siguiente_orden = (max_orden or 0) + 1

        fase_general, _ = Fase.objects.get_or_create(
            proyecto=proyecto,
            nombre='General',
            defaults={
                'id': uuid.uuid4(),
                'company': proyecto.company,
                'descripcion': 'Fase creada automáticamente para tareas sin fase asignada.',
                'orden': siguiente_orden,
                'fecha_inicio_planificada': proyecto.fecha_inicio_planificada,
                'fecha_fin_planificada': proyecto.fecha_fin_planificada,
                'activo': True,
            },
        )
        # Asignar tareas sin fase a esta fase
        Tarea.objects.filter(proyecto=proyecto, fase__isnull=True).update(fase=fase_general)


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0004_companylicense_licensepayment'),
        ('proyectos', '0007_add_modo_timesheet_and_sesiones'),
    ]

    operations = [
        # ── 1. Crear ActividadSaiopen ─────────────────────────────────────────
        migrations.CreateModel(
            name='ActividadSaiopen',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('codigo', models.CharField(db_index=True, max_length=50)),
                ('nombre', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True)),
                ('unidad_medida', models.CharField(
                    choices=[
                        ('solo_estados', 'Solo estados'),
                        ('timesheet', 'Timesheet (horas)'),
                        ('cantidad', 'Cantidad ejecutada'),
                    ],
                    default='solo_estados',
                    help_text='Determina el modo de medición: solo_estados, timesheet o cantidad.',
                    max_length=20,
                )),
                ('costo_unitario_base', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('activo', models.BooleanField(db_index=True, default=True)),
                ('saiopen_actividad_id', models.CharField(blank=True, max_length=50, null=True)),
                ('sincronizado_con_saiopen', models.BooleanField(default=False)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='%(class)s_set',
                    to='companies.company',
                )),
            ],
            options={
                'verbose_name': 'Actividad Saiopen',
                'verbose_name_plural': 'Actividades Saiopen',
                'ordering': ['codigo'],
                'unique_together': {('company', 'codigo')},
            },
        ),

        # ── 2. Agregar estado a Fase ──────────────────────────────────────────
        migrations.AddField(
            model_name='fase',
            name='estado',
            field=models.CharField(
                choices=[
                    ('planificada', 'Planificada'),
                    ('activa', 'Activa'),
                    ('completada', 'Completada'),
                    ('cancelada', 'Cancelada'),
                ],
                default='planificada',
                help_text='Estado operativo de la fase.',
                max_length=20,
            ),
        ),

        # ── 3. Agregar actividad_saiopen (nullable) a Tarea ──────────────────
        migrations.AddField(
            model_name='tarea',
            name='actividad_saiopen',
            field=models.ForeignKey(
                blank=True,
                help_text='Actividad de Saiopen que determina el modo de medición.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tareas',
                to='proyectos.actividadsaiopen',
            ),
        ),

        # ── 4. Agregar cantidad_objetivo, cantidad_registrada a Tarea ─────────
        migrations.AddField(
            model_name='tarea',
            name='cantidad_objetivo',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Cantidad objetivo (aplica cuando actividad_saiopen.unidad_medida = cantidad).',
                max_digits=15,
            ),
        ),
        migrations.AddField(
            model_name='tarea',
            name='cantidad_registrada',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Cantidad ejecutada registrada.',
                max_digits=15,
            ),
        ),

        # ── 5. Data migration: asignar fase a tareas huérfanas ────────────────
        migrations.RunPython(
            crear_fases_por_defecto_y_asignar,
            reverse_code=migrations.RunPython.noop,
        ),

        # ── 6. Hacer fase NOT NULL en Tarea ───────────────────────────────────
        migrations.AlterField(
            model_name='tarea',
            name='fase',
            field=models.ForeignKey(
                help_text='Fase a la que pertenece esta tarea (obligatoria).',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tareas',
                to='proyectos.fase',
            ),
        ),

        # ── 7. Marcar proyecto como editable=False (solo informativo en Python) ─
        migrations.AlterField(
            model_name='tarea',
            name='proyecto',
            field=models.ForeignKey(
                editable=False,
                help_text='Auto-derivado de fase.proyecto. No editar directamente.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tareas',
                to='proyectos.proyecto',
            ),
        ),

        # ── 8. Nuevo índice fase+estado ───────────────────────────────────────
        migrations.AddIndex(
            model_name='tarea',
            index=models.Index(fields=['fase', 'estado'], name='proyectos_t_fase_es_idx'),
        ),
    ]
