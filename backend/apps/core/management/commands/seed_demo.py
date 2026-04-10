"""
SaiSuite — Comando de seed para datos demo.
Pobla: Proyecto Demo B (Droguería), Dashboard GL 2025, CRM flujos.
Uso: python manage.py seed_demo
"""
import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed datos demo: Proyecto B, Dashboard GL 2025, CRM flujos'

    def handle(self, *args, **options):
        from apps.companies.models import Company, CompanyModule
        from apps.users.models import User

        company = Company.objects.first()
        if not company:
            self.stderr.write('No hay empresa. Crea una primero.')
            return

        self.stdout.write(f'Seeding demo para empresa: {company.name}')

        self._seed_proyecto_b(company)
        self._seed_gl_2025(company)
        self._seed_dashboards(company)
        self._seed_crm(company)

        self.stdout.write(self.style.SUCCESS('✅ Demo seed completado.'))

    # ─────────────────────────────────────────────
    # PROYECTO B — Droguería SaludTotal
    # ─────────────────────────────────────────────
    def _seed_proyecto_b(self, company):
        from apps.proyectos.models import (
            Project, Phase, Task, Activity, ProjectActivity,
            ProjectBudget, ProjectExpense, ResourceCostRate,
            TimesheetEntry, ResourceAssignment, TaskDependency,
            ProjectBaseline, WhatIfScenario,
        )
        from apps.terceros.models import Tercero
        from apps.users.models import User

        self.stdout.write('  → Proyecto B: Droguería SaludTotal...')

        # Crear tercero cliente
        tercero, _ = Tercero.objects.get_or_create(
            company=company,
            numero_identificacion='800456789',
            defaults={
                'primer_nombre': 'Droguería SaludTotal Ltda',
                'tipo_identificacion': 'NIT',
                'codigo': 'SAL001',
            }
        )

        # Crear 9 usuarios del equipo (el admin ya existe)
        equipo_data = [
            ('valentina.ospina@demo.com', 'Valentina', 'Ospina', 'company_admin', 130000),
            ('sebastian.mora@demo.com', 'Sebastián', 'Mora', 'seller', 110000),
            ('isabella.restrepo@demo.com', 'Isabella', 'Restrepo', 'seller', 95000),
            ('miguel.castro@demo.com', 'Miguel Ángel', 'Castro', 'seller', 105000),
            ('laura.quintero@demo.com', 'Laura', 'Quintero', 'seller', 80000),
            ('nicolas.jimenez@demo.com', 'Nicolás', 'Jiménez', 'seller', 90000),
            ('sara.londono@demo.com', 'Sara', 'Londoño', 'seller', 88000),
            ('felipe.arango@demo.com', 'Felipe', 'Arango', 'seller', 65000),
            ('daniela.velez@demo.com', 'Daniela', 'Vélez', 'seller', 85000),
            ('santiago.munoz@demo.com', 'Santiago', 'Muñoz', 'seller', 92000),
        ]
        usuarios = {}
        for email, fn, ln, role, tarifa in equipo_data:
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fn, 'last_name': ln,
                    'company': company, 'role': role, 'is_active': True,
                }
            )
            if created:
                u.set_password('Demo2026!')
                u.save()
            # Tarifa
            ResourceCostRate.objects.get_or_create(
                company=company, user=u,
                defaults={
                    'hourly_rate': Decimal(str(tarifa)),
                    'start_date': date(2026, 1, 1),
                    'currency': 'COP',
                }
            )
            usuarios[email] = u

        valentina = usuarios['valentina.ospina@demo.com']
        sebastian = usuarios['sebastian.mora@demo.com']
        isabella = usuarios['isabella.restrepo@demo.com']
        miguel = usuarios['miguel.castro@demo.com']
        laura = usuarios['laura.quintero@demo.com']
        nicolas = usuarios['nicolas.jimenez@demo.com']
        sara = usuarios['sara.londono@demo.com']
        felipe = usuarios['felipe.arango@demo.com']
        daniela = usuarios['daniela.velez@demo.com']
        santiago = usuarios['santiago.munoz@demo.com']

        # Actividades del catálogo
        actividades_data = [
            ('LVT-REQ', 'Levantamiento de requerimientos', 'labor'),
            ('DIS-ARQ', 'Diseño de arquitectura', 'labor'),
            ('DIS-UX', 'Diseño UX/UI', 'labor'),
            ('DIS-BD', 'Diseño de base de datos', 'labor'),
            ('CFG-CICD', 'Configuración CI/CD', 'labor'),
            ('DEV-INV', 'Desarrollo módulo inventario', 'labor'),
            ('DEV-VEN', 'Desarrollo módulo ventas', 'labor'),
            ('DEV-CLI', 'Desarrollo módulo clientes', 'labor'),
            ('INT-DIAN', 'Integración DIAN', 'labor'),
            ('DEV-POS', 'Desarrollo interfaz POS', 'labor'),
            ('DEV-REP', 'Desarrollo reportes', 'labor'),
            ('CFG-UI', 'Configuración UI', 'labor'),
            ('DEV-PWA', 'Desarrollo PWA', 'labor'),
            ('QA-PLAN', 'Plan de pruebas', 'labor'),
            ('QA-FUNC', 'Testing funcional', 'labor'),
            ('QA-INT', 'Testing integración', 'labor'),
            ('UAT', 'UAT — Pruebas con cliente', 'milestone'),
            ('DEP-PROD', 'Deploy producción', 'labor'),
            ('CAP-CLI', 'Capacitación cliente', 'labor'),
        ]
        acts = {}
        for codigo, nombre, tipo in actividades_data:
            a, _ = Activity.objects.get_or_create(
                company=company, codigo=codigo,
                defaults={'nombre': nombre, 'tipo': tipo, 'activo': True}
            )
            acts[codigo] = a

        # Proyecto
        proyecto, created = Project.objects.get_or_create(
            company=company,
            nombre='Implementación Sistema POS — Droguería SaludTotal',
            defaults={
                'codigo': 'POS-SAL-2026',
                'tipo': 'software',
                'estado': 'in_progress',
                'cliente_nombre': 'Droguería SaludTotal Ltda',
                'gerente': valentina,
                'fecha_inicio_planificada': date(2026, 1, 5),
                'fecha_fin_planificada': date(2026, 4, 30),
                'fecha_inicio_real': date(2026, 1, 5),
                'presupuesto_total': Decimal('120000000'),
                'porcentaje_administracion': Decimal('5'),
                'porcentaje_imprevistos': Decimal('8'),
                'porcentaje_utilidad': Decimal('10'),
                'porcentaje_avance': Decimal('65'),
                'activo': True,
            }
        )
        if not created:
            self.stdout.write('    Proyecto ya existe, actualizando...')

        # Presupuesto
        budget, _ = ProjectBudget.objects.get_or_create(
            company=company, project=proyecto,
            defaults={
                'planned_labor_cost': Decimal('95000000'),
                'planned_expense_cost': Decimal('25000000'),
                'planned_total_budget': Decimal('120000000'),
                'approved_budget': Decimal('120000000'),
                'approved_date': None,
                'currency': 'COP',
                'approved_by': valentina,
            }
        )

        # Fases
        fases_data = [
            (1, 'Análisis y Diseño', date(2026,1,5), date(2026,1,30), 'completed', Decimal('100')),
            (2, 'Backend Development', date(2026,2,2), date(2026,2,28), 'completed', Decimal('100')),
            (3, 'Frontend Development', date(2026,3,2), date(2026,3,28), 'active', Decimal('55')),
            (4, 'QA y Testing', date(2026,3,30), date(2026,4,17), 'planned', Decimal('0')),
            (5, 'Despliegue y Capacitación', date(2026,4,20), date(2026,4,30), 'planned', Decimal('0')),
        ]
        fases = {}
        for orden, nombre, fi, ff, estado, avance in fases_data:
            f, _ = Phase.objects.get_or_create(
                company=company, proyecto=proyecto, orden=orden,
                defaults={
                    'nombre': nombre,
                    'fecha_inicio_planificada': fi,
                    'fecha_fin_planificada': ff,
                    'estado': estado,
                    'porcentaje_avance': avance,
                    'activo': True,
                }
            )
            fases[orden] = f

        # Tareas
        tareas_data = [
            # (codigo, nombre, fase, actividad, fi, ff, estado, avance, h_est, h_reg, asignados)
            ('T1', 'Levantamiento de requerimientos POS', 1, 'LVT-REQ', date(2026,1,5), date(2026,1,16), 'completed', 100, 80, 100, [daniela, valentina]),
            ('T2', 'Diseño de arquitectura del sistema', 1, 'DIS-ARQ', date(2026,1,10), date(2026,1,23), 'completed', 100, 60, 58, [sebastian, miguel]),
            ('T3', 'Diseño UX/UI — mockups y prototipos', 1, 'DIS-UX', date(2026,1,10), date(2026,1,30), 'completed', 100, 80, 82, [sara]),
            ('T4', 'Diseño de base de datos e integraciones', 1, 'DIS-BD', date(2026,1,17), date(2026,1,30), 'completed', 100, 40, 38, [miguel]),
            ('T5', 'Configuración de entorno y CI/CD', 2, 'CFG-CICD', date(2026,2,2), date(2026,2,10), 'completed', 100, 32, 29, [miguel]),
            ('T6', 'Módulo de inventario y productos', 2, 'DEV-INV', date(2026,2,5), date(2026,2,28), 'completed', 100, 120, 193, [sebastian, nicolas]),
            ('T7', 'Módulo de ventas y facturación POS', 2, 'DEV-VEN', date(2026,2,8), date(2026,2,28), 'completed', 100, 160, 237, [sebastian, nicolas]),
            ('T8', 'Módulo de clientes y fidelización', 2, 'DEV-CLI', date(2026,2,8), date(2026,2,28), 'completed', 100, 80, 74, [nicolas]),
            ('T9', 'Integración con DIAN', 2, 'INT-DIAN', date(2026,2,18), date(2026,2,28), 'completed', 100, 96, 88, [sebastian]),
            ('T10', 'Interfaz POS principal', 3, 'DEV-POS', date(2026,3,2), date(2026,3,28), 'in_progress', 82, 120, 98, [isabella]),
            ('T11', 'Módulo de reportes y dashboards', 3, 'DEV-REP', date(2026,3,2), date(2026,3,28), 'in_progress', 60, 80, 97, [isabella, sara]),
            ('T12', 'Configuración y parametrización UI', 3, 'CFG-UI', date(2026,3,10), date(2026,3,28), 'in_progress', 55, 48, 42, [isabella]),
            ('T13', 'App móvil para inventario (PWA)', 3, 'DEV-PWA', date(2026,3,7), date(2026,3,28), 'in_progress', 60, 96, 113, [isabella, nicolas]),
            ('T14', 'Plan de pruebas y casos de test', 4, 'QA-PLAN', date(2026,3,30), date(2026,4,5), 'not_started', 0, 40, 0, [laura]),
            ('T15', 'Testing funcional módulos POS', 4, 'QA-FUNC', date(2026,4,6), date(2026,4,14), 'not_started', 0, 120, 0, [laura]),
            ('T16', 'Testing de integración DIAN', 4, 'QA-INT', date(2026,4,6), date(2026,4,14), 'not_started', 0, 40, 0, [laura, sebastian]),
            ('T17', 'UAT — Pruebas con cliente', 4, 'UAT', date(2026,4,15), date(2026,4,17), 'not_started', 0, 0, 0, [daniela, valentina]),
            ('T18', 'Despliegue en producción', 5, 'DEP-PROD', date(2026,4,20), date(2026,4,27), 'not_started', 0, 48, 0, [miguel, sebastian]),
            ('T19', 'Capacitación al equipo del cliente', 5, 'CAP-CLI', date(2026,4,28), date(2026,4,30), 'not_started', 0, 24, 0, [felipe, daniela]),
        ]

        tareas = {}
        for codigo, nombre, fase_ord, act_cod, fi, ff, estado, avance, h_est, h_reg, asignados in tareas_data:
            # ProjectActivity vincula actividad + proyecto + fase
            proj_act, _ = ProjectActivity.objects.get_or_create(
                company=company, proyecto=proyecto, actividad=acts[act_cod], fase=fases[fase_ord],
            )
            t, _ = Task.objects.get_or_create(
                company=company, codigo=codigo, proyecto=proyecto,
                defaults={
                    'nombre': nombre,
                    'fase': fases[fase_ord],
                    'actividad_proyecto': proj_act,
                    'fecha_inicio': fi,
                    'fecha_fin': ff,
                    'estado': estado,
                    'porcentaje_completado': avance,
                    'horas_estimadas': Decimal(str(h_est)),
                    'horas_registradas': Decimal(str(h_reg)),
                    'prioridad': 2,
                }
            )
            tareas[codigo] = t

            # Asignaciones de recursos
            pct = Decimal('100') // len(asignados) if len(asignados) else Decimal('100')
            for u in asignados:
                ResourceAssignment.objects.get_or_create(
                    company=company, tarea=t, usuario=u,
                    defaults={
                        'porcentaje_asignacion': pct,
                        'fecha_inicio': fi,
                        'fecha_fin': ff,
                    }
                )

        # Dependencias principales
        deps = [
            ('T1','T2','FS',0),('T1','T3','FS',0),('T2','T4','FS',0),
            ('T3','T10','FS',0),('T4','T5','FS',0),('T5','T6','FS',0),
            ('T5','T7','FS',0),('T6','T7','SS',3),('T7','T8','SS',0),
            ('T7','T9','FS',0),('T6','T11','FS',0),('T10','T12','FS',0),
            ('T10','T13','SS',5),('T9','T16','FS',0),('T12','T14','FS',0),
            ('T13','T14','FS',0),('T14','T15','FS',0),('T15','T18','FS',0),
            ('T16','T17','FS',0),('T17','T18','FS',0),('T18','T19','FS',0),
        ]
        for pred, suc, tipo, lag in deps:
            if pred in tareas and suc in tareas:
                TaskDependency.objects.get_or_create(
                    company=company,
                    tarea_predecesora=tareas[pred],
                    tarea_sucesora=tareas[suc],
                    defaults={'tipo_dependencia': tipo, 'retraso_dias': lag}
                )

        # Timesheets — registrar entradas históricas
        self._seed_timesheets(company, tareas, usuarios)

        # Gastos
        gastos = [
            ('Licencias IDE y herramientas', 'software', 3500000, date(2026,1,8), True, False, valentina),
            ('Servidor desarrollo AWS', 'software', 2800000, date(2026,1,15), True, False, miguel),
            ('Servidor producción AWS 3 meses', 'software', 8400000, date(2026,2,1), True, True, miguel),
            ('Certificado SSL y dominio', 'software', 350000, date(2026,1,20), True, True, miguel),
            ('Capacitación del equipo — cursos', 'training', 1200000, date(2026,1,25), True, False, valentina),
            ('Viajes a sede del cliente', 'travel', 950000, date(2026,2,15), True, True, daniela),
            ('Terminales POS hardware × 3', 'equipment', 4500000, date(2026,2,20), True, True, miguel),
            ('Impresoras fiscales × 2', 'equipment', 3200000, date(2026,2,22), True, True, miguel),
            ('Soporte técnico externo DIAN', 'subcontractor', 2400000, date(2026,3,5), False, True, sebastian),
            ('Materiales de capacitación', 'other', 650000, date(2026,3,10), False, False, felipe),
        ]
        for desc, cat, monto, fecha, aprobado, facturable, pagado_por in gastos:
            g, _ = ProjectExpense.objects.get_or_create(
                company=company, project=proyecto, description=desc,
                defaults={
                    'category': cat,
                    'amount': Decimal(str(monto)),
                    'currency': 'COP',
                    'expense_date': fecha,
                    'billable': facturable,
                    'approved_date': fecha + timedelta(days=2) if aprobado else None,
                    'approved_by': valentina if aprobado else None,
                    'paid_by': pagado_por,
                }
            )

        # Baselines
        ProjectBaseline.objects.get_or_create(
            company=company, project=proyecto, name='Sprint 1-2 Base',
            defaults={
                'description': 'Baseline al finalizar Análisis y Diseño',
                'is_active_baseline': False,
                'tasks_snapshot': [{'id': 'T1', 'estado': 'completed'}, {'id': 'T2', 'estado': 'completed'},
                                   {'id': 'T3', 'estado': 'completed'}, {'id': 'T4', 'estado': 'completed'}],
                'resources_snapshot': {},
                'total_tasks_snapshot': 19,
                'critical_path_snapshot': ['T1', 'T2', 'T4', 'T5', 'T7', 'T9', 'T16', 'T17', 'T18', 'T19'],
                'project_end_date_snapshot': date(2026, 4, 30),
            }
        )
        ProjectBaseline.objects.get_or_create(
            company=company, project=proyecto, name='Midpoint Review',
            defaults={
                'description': 'Revisión de mitad de proyecto — Backend completado',
                'is_active_baseline': True,
                'tasks_snapshot': [{'id': f'T{i}', 'estado': 'completed'} for i in range(1, 10)],
                'resources_snapshot': {},
                'total_tasks_snapshot': 19,
                'critical_path_snapshot': ['T1', 'T2', 'T4', 'T5', 'T7', 'T9', 'T16', 'T17', 'T18', 'T19'],
                'project_end_date_snapshot': date(2026, 4, 30),
            }
        )

        # What-if scenarios
        WhatIfScenario.objects.get_or_create(
            company=company, project=proyecto, name='Agregar QA desde Fase 3',
            defaults={
                'description': 'Incorporar Laura en testing paralelo durante T10 y T11 reduce Fase 4 en 25%',
                'task_changes': {'T14': {'reduccion': '25%'}, 'T15': {'reduccion': '25%'}},
                'resource_changes': {'Laura': {'horas_adicionales': 48}},
                'dependency_changes': {},
                'created_by': valentina,
                'simulated_end_date': date(2026, 4, 25),
                'days_delta': -5,
                'tasks_affected_count': 3,
            }
        )
        WhatIfScenario.objects.get_or_create(
            company=company, project=proyecto, name='Reducir alcance PWA',
            defaults={
                'description': 'Reducir T13 al 50% — solo consulta de inventario',
                'task_changes': {'T13': {'horas_estimadas': 48, 'horas_originales': 96}},
                'resource_changes': {},
                'dependency_changes': {},
                'created_by': valentina,
                'simulated_end_date': date(2026, 4, 25),
                'days_delta': -5,
                'tasks_affected_count': 1,
            }
        )

        self.stdout.write('    ✅ Proyecto B creado.')

    def _seed_timesheets(self, company, tareas, usuarios):
        from apps.proyectos.models import TimesheetEntry, ResourceAssignment

        # Timesheets para T1-T9 (completadas) y T10-T13 (parciales)
        ts_data = {
            'T1': [('daniela.velez@demo.com', date(2026,1,5), date(2026,1,16), 60),
                   ('valentina.ospina@demo.com', date(2026,1,5), date(2026,1,16), 40)],
            'T2': [('sebastian.mora@demo.com', date(2026,1,10), date(2026,1,23), 30),
                   ('miguel.castro@demo.com', date(2026,1,10), date(2026,1,23), 28)],
            'T3': [('sara.londono@demo.com', date(2026,1,10), date(2026,1,30), 82)],
            'T4': [('miguel.castro@demo.com', date(2026,1,17), date(2026,1,30), 38)],
            'T5': [('miguel.castro@demo.com', date(2026,2,2), date(2026,2,10), 29)],
            'T6': [('sebastian.mora@demo.com', date(2026,2,5), date(2026,2,28), 95),
                   ('nicolas.jimenez@demo.com', date(2026,2,5), date(2026,2,28), 98)],
            'T7': [('sebastian.mora@demo.com', date(2026,2,8), date(2026,2,28), 145),
                   ('nicolas.jimenez@demo.com', date(2026,2,8), date(2026,2,28), 92)],
            'T8': [('nicolas.jimenez@demo.com', date(2026,2,8), date(2026,2,28), 74)],
            'T9': [('sebastian.mora@demo.com', date(2026,2,18), date(2026,2,28), 88)],
            'T10': [('isabella.restrepo@demo.com', date(2026,3,2), date(2026,3,20), 98)],
            'T11': [('isabella.restrepo@demo.com', date(2026,3,2), date(2026,3,20), 55),
                    ('sara.londono@demo.com', date(2026,3,2), date(2026,3,20), 42)],
            'T12': [('isabella.restrepo@demo.com', date(2026,3,10), date(2026,3,20), 42)],
            'T13': [('isabella.restrepo@demo.com', date(2026,3,7), date(2026,3,20), 65),
                    ('nicolas.jimenez@demo.com', date(2026,3,7), date(2026,3,20), 48)],
        }

        for tarea_cod, asignaciones in ts_data.items():
            tarea = tareas.get(tarea_cod)
            if not tarea:
                continue
            for email, fecha_ini, fecha_fin, total_horas in asignaciones:
                usuario = usuarios.get(email)
                if not usuario:
                    continue
                # Distribuir horas en días laborables
                dias = []
                d = fecha_ini
                while d <= fecha_fin:
                    if d.weekday() < 5:  # Lun-Vie
                        dias.append(d)
                    d += timedelta(days=1)
                if not dias:
                    continue
                horas_dia = total_horas / len(dias)
                for dia in dias:
                    if TimesheetEntry.objects.filter(
                        company=company, tarea=tarea, usuario=usuario, fecha=dia
                    ).exists():
                        continue
                    h = round(random.uniform(horas_dia * 0.7, horas_dia * 1.3), 1)
                    h = max(0.5, min(10, h))
                    TimesheetEntry.objects.create(
                        company=company, tarea=tarea, usuario=usuario,
                        fecha=dia, horas=Decimal(str(h)),
                        descripcion=f'Trabajo en {tarea.nombre}',
                        validado=True,
                        fecha_validacion=dia + timedelta(days=1),
                        validado_por=usuarios.get('valentina.ospina@demo.com'),
                    )

    # ─────────────────────────────────────────────
    # GL 2025 — Movimientos contables demo
    # ─────────────────────────────────────────────
    def _seed_gl_2025(self, company):
        from apps.contabilidad.models import MovimientoContable

        self.stdout.write('  → GL 2025: movimientos contables...')

        if MovimientoContable.objects.filter(company=company, periodo__startswith='2025').exists():
            self.stdout.write('    GL 2025 ya existe.')
            return

        # Meses 2025 con datos realistas para empresa de software/consultoría
        meses = [
            ('2025-01', 285000000, 180000000, 45000000, 22000000),
            ('2025-02', 310000000, 192000000, 48000000, 24000000),
            ('2025-03', 295000000, 175000000, 52000000, 21000000),
            ('2025-04', 340000000, 210000000, 55000000, 28000000),
            ('2025-05', 320000000, 198000000, 51000000, 25000000),
            ('2025-06', 365000000, 225000000, 58000000, 32000000),
            ('2025-07', 355000000, 218000000, 57000000, 30000000),
            ('2025-08', 380000000, 235000000, 60000000, 33000000),
            ('2025-09', 410000000, 252000000, 64000000, 36000000),
            ('2025-10', 398000000, 245000000, 62000000, 34000000),
            ('2025-11', 425000000, 260000000, 66000000, 38000000),
            ('2025-12', 480000000, 295000000, 72000000, 45000000),
        ]

        # (codigo_int, titulo_int, nombre, tipo_char)
        cuentas_ing = [
            (4135, 4, 'Servicios de consultoría TI', 'I'),
            (4136, 4, 'Licencias de software', 'I'),
            (4137, 4, 'Soporte y mantenimiento', 'I'),
            (4145, 4, 'Capacitación y entrenamiento', 'I'),
        ]
        cuentas_costo = [
            (6135, 6, 'Costo labor técnica', 'E'),
            (6136, 6, 'Costo infraestructura', 'E'),
        ]
        cuentas_adm = [
            (5105, 5, 'Gastos de personal administrativo', 'E'),
            (5110, 5, 'Arrendamientos oficina', 'E'),
            (5115, 5, 'Servicios públicos y comunicaciones', 'E'),
            (5120, 5, 'Gastos de viaje y representación', 'E'),
        ]
        cuentas_vta = [
            (5205, 5, 'Gastos de ventas y marketing', 'E'),
            (5210, 5, 'Comisiones de venta', 'E'),
        ]

        clientes = [
            ('CL001', 'Grupo Empresarial Andino'),
            ('CL002', 'Constructora Bogotá 2000'),
            ('CL003', 'Clínica Santa María SAS'),
        ]
        proveedores = [
            ('PR001', 'AWS Colombia'),
            ('PR002', 'Microsoft Colombia'),
            ('PR003', 'Arrendadora Oficinas Bogotá'),
        ]

        from django.db.models import Max
        max_conteo = MovimientoContable.objects.filter(company=company).aggregate(m=Max('conteo'))['m'] or 0
        conteo = max_conteo + 1
        now_ts = timezone.now()
        for periodo, ing, costo, g_adm, g_vta in meses:
            year, month = map(int, periodo.split('-'))
            dia_base = date(year, month, 1)

            # Ingresos (créditos — cuenta clase 4)
            pcts_ing = [0.40, 0.25, 0.20, 0.15]
            for i, (cc, titulo, nombre, tipo) in enumerate(cuentas_ing):
                pct = pcts_ing[i]
                for j, (cod_t, nom_t) in enumerate(clientes):
                    monto = round(ing * pct * [0.45, 0.35, 0.20][j])
                    MovimientoContable.objects.create(
                        company=company, conteo=conteo,
                        auxiliar=Decimal(str(cc)), auxiliar_nombre=nombre,
                        titulo_codigo=titulo,
                        cuenta_codigo=cc, cuenta_nombre=nombre,
                        tercero_id=cod_t, tercero_nombre=nom_t,
                        debito=Decimal('0'), credito=Decimal(str(monto)),
                        tipo=tipo, periodo=periodo,
                        fecha=dia_base + timedelta(days=random.randint(1, 25)),
                        sincronizado_en=now_ts,
                    )
                    conteo += 1

            # Costos de ventas (débitos — cuenta clase 6)
            pcts_costo = [0.70, 0.30]
            for i, (cc, titulo, nombre, tipo) in enumerate(cuentas_costo):
                monto = round(costo * pcts_costo[i])
                MovimientoContable.objects.create(
                    company=company, conteo=conteo,
                    auxiliar=Decimal(str(cc)), auxiliar_nombre=nombre,
                    titulo_codigo=titulo,
                    cuenta_codigo=cc, cuenta_nombre=nombre,
                    tercero_id='OPERACIONES', tercero_nombre='',
                    debito=Decimal(str(monto)), credito=Decimal('0'),
                    tipo=tipo, periodo=periodo,
                    fecha=dia_base + timedelta(days=5),
                    sincronizado_en=now_ts,
                )
                conteo += 1

            # Gastos administrativos (débitos — cuenta clase 5)
            pcts_adm = [0.55, 0.20, 0.15, 0.10]
            for i, (cc, titulo, nombre, tipo) in enumerate(cuentas_adm):
                proveedor = proveedores[i % len(proveedores)]
                monto = round(g_adm * pcts_adm[i])
                MovimientoContable.objects.create(
                    company=company, conteo=conteo,
                    auxiliar=Decimal(str(cc)), auxiliar_nombre=nombre,
                    titulo_codigo=titulo,
                    cuenta_codigo=cc, cuenta_nombre=nombre,
                    tercero_id=proveedor[0], tercero_nombre=proveedor[1],
                    debito=Decimal(str(monto)), credito=Decimal('0'),
                    tipo=tipo, periodo=periodo,
                    fecha=dia_base + timedelta(days=10),
                    sincronizado_en=now_ts,
                )
                conteo += 1

            # Gastos de venta (débitos — cuenta clase 5)
            pcts_vta = [0.60, 0.40]
            for i, (cc, titulo, nombre, tipo) in enumerate(cuentas_vta):
                monto = round(g_vta * pcts_vta[i])
                MovimientoContable.objects.create(
                    company=company, conteo=conteo,
                    auxiliar=Decimal(str(cc)), auxiliar_nombre=nombre,
                    titulo_codigo=titulo,
                    cuenta_codigo=cc, cuenta_nombre=nombre,
                    tercero_id='VENTAS', tercero_nombre='',
                    debito=Decimal(str(monto)), credito=Decimal('0'),
                    tipo=tipo, periodo=periodo,
                    fecha=dia_base + timedelta(days=15),
                    sincronizado_en=now_ts,
                )
                conteo += 1

        self.stdout.write('    ✅ GL 2025 creado.')

    # ─────────────────────────────────────────────
    # DASHBOARDS
    # ─────────────────────────────────────────────
    def _seed_dashboards(self, company):
        from apps.dashboard.models import Dashboard, DashboardCard
        from apps.users.models import User

        self.stdout.write('  → Dashboards...')

        admin = User.objects.filter(company=company, role__in=['company_admin','valmen_admin']).first()

        dashboards_config = [
            {
                'titulo': 'Estado Financiero 2025',
                'descripcion': 'Visión global: ingresos, costos, márgenes y liquidez',
                'es_default': True,
                'cards': [
                    ('INGRESOS_VS_EGRESOS', 'bar', 0, 0, 6, 4, {}),
                    ('ESTADO_RESULTADOS', 'waterfall', 6, 0, 6, 4, {}),
                    ('MARGEN_BRUTO_NETO', 'kpi', 0, 4, 3, 2, {}),
                    ('EBITDA', 'kpi', 3, 4, 3, 2, {}),
                    ('INDICADORES_LIQUIDEZ', 'kpi', 6, 4, 3, 2, {}),
                    ('ENDEUDAMIENTO', 'gauge', 9, 4, 3, 2, {}),
                    ('TENDENCIA_MENSUAL', 'line', 0, 6, 12, 3, {}),
                ],
            },
            {
                'titulo': 'Cartera y Clientes',
                'descripcion': 'Concentración de ingresos, aging cartera, top clientes',
                'es_default': False,
                'cards': [
                    ('CARTERA_TOTAL', 'kpi', 0, 0, 4, 2, {}),
                    ('ROTACION_CARTERA', 'kpi', 4, 0, 4, 2, {}),
                    ('CONCENTRACION_INGRESOS_TERCERO', 'bar', 0, 2, 6, 4, {}),
                    ('TOP_CLIENTES_SALDO', 'bar', 6, 2, 6, 4, {}),
                    ('AGING_CARTERA', 'bar', 0, 6, 8, 3, {}),
                    ('MOVIMIENTO_POR_TERCERO', 'table', 8, 6, 4, 3, {}),
                ],
            },
            {
                'titulo': 'Costos y Gastos',
                'descripcion': 'Distribución de gastos operacionales y costo de ventas',
                'es_default': False,
                'cards': [
                    ('COSTO_VENTAS', 'kpi', 0, 0, 3, 2, {}),
                    ('GASTOS_OPERACIONALES', 'pie', 3, 0, 5, 4, {}),
                    ('GASTOS_POR_DEPARTAMENTO', 'bar', 8, 0, 4, 4, {}),
                    ('GASTOS_POR_CENTRO_COSTO', 'bar', 0, 4, 6, 4, {}),
                    ('COMPARATIVO_PERIODOS', 'bar', 6, 4, 6, 4, {}),
                ],
            },
            {
                'titulo': 'Proyectos — Agente Financiero',
                'descripcion': 'Rentabilidad y costos por proyecto',
                'es_default': False,
                'cards': [
                    ('INGRESOS_POR_PROYECTO', 'bar', 0, 0, 6, 4, {}),
                    ('COSTO_POR_PROYECTO', 'bar', 6, 0, 6, 4, {}),
                    ('DISTRIBUCION_POR_PROYECTO', 'bar', 0, 4, 6, 4, {}),
                    ('COSTO_POR_ACTIVIDAD', 'bar', 6, 4, 6, 4, {}),
                ],
            },
        ]

        for cfg in dashboards_config:
            db, created = Dashboard.objects.get_or_create(
                company=company, titulo=cfg['titulo'],
                defaults={
                    'user': admin,
                    'descripcion': cfg['descripcion'],
                    'es_privado': False,
                    'es_default': cfg['es_default'],
                    'orientacion': 'horizontal',
                    'filtros_default': {'periodo': '2025'},
                }
            )
            if created:
                for i, (code, chart, px, py, w, h, filtros) in enumerate(cfg['cards']):
                    DashboardCard.objects.create(
                        dashboard=db,
                        card_type_code=code,
                        chart_type=chart,
                        pos_x=px, pos_y=py,
                        width=w, height=h,
                        filtros_config={**filtros, 'periodo_inicio': '2025-01', 'periodo_fin': '2025-12'},
                        orden=i,
                    )
                self.stdout.write(f'    Dashboard "{cfg["titulo"]}" creado.')

        self.stdout.write('    ✅ Dashboards creados.')

    # ─────────────────────────────────────────────
    # CRM — Leads y Oportunidades en etapas
    # ─────────────────────────────────────────────
    def _seed_crm(self, company):
        from apps.crm.models import (
            CrmLead, CrmOportunidad, CrmEtapa, CrmPipeline,
            CrmActividad, FuenteLead, TipoActividad,
        )
        from apps.terceros.models import Tercero
        from apps.users.models import User

        self.stdout.write('  → CRM: leads y oportunidades...')

        pipeline = CrmPipeline.all_objects.filter(company=company, es_default=True).first()
        if not pipeline:
            self.stderr.write('    Sin pipeline CRM. Omitiendo.')
            return

        etapas = {e.nombre: e for e in CrmEtapa.all_objects.filter(pipeline=pipeline)}
        sellers = list(User.objects.filter(company=company, role='seller', is_active=True))
        admin = User.objects.filter(company=company, role__in=['company_admin']).first()
        todos = sellers + ([admin] if admin else [])

        def rand_user():
            return random.choice(todos) if todos else None

        now = timezone.now()

        # ── LEADS en distintas etapas ─────────────────────────────

        leads_data = [
            # (nombre, empresa, email, fuente, asignado, convertido)
            ('Carlos Mendoza', 'Ferretería Central SAS', 'cmendoza@ferrocentral.com', FuenteLead.MANUAL, rand_user(), False),
            ('Ana Gómez', 'Clínica del Norte Ltda', 'agomez@clinicadelnorte.com', FuenteLead.WEBHOOK, rand_user(), False),
            ('Pedro Vargas', 'Supermercado La Colina', 'pvargas@lacolina.com', FuenteLead.CSV, rand_user(), False),
            ('Marcela Torres', 'Constructora Ospinas', 'mtorres@ospinas.com', FuenteLead.OTRO, rand_user(), False),
            ('Jorge Herrera', 'Distribuidora Maicao', 'jherrera@maicao.com', FuenteLead.MANUAL, rand_user(), False),
            ('Lucía Ramírez', 'Cafetería El Nogal', 'lramirez@elnogal.com', FuenteLead.WEBHOOK, rand_user(), False),
            ('Andrés Salazar', 'Laboratorio BioAnalítica', 'asalazar@bioanalytica.com', FuenteLead.MANUAL, rand_user(), False),
            ('Sandra Peña', 'Hotel Chicamocha', 'spena@chicamocha.com', FuenteLead.CSV, rand_user(), False),
        ]

        leads = {}
        for nombre, empresa, email, fuente, asignado, convertido in leads_data:
            if CrmLead.all_objects.filter(company=company, email=email).exists():
                leads[nombre] = CrmLead.all_objects.get(company=company, email=email)
                continue
            l = CrmLead.all_objects.create(
                company=company, nombre=nombre, empresa=empresa,
                email=email, fuente=fuente,
                asignado_a=asignado, pipeline=pipeline,
                score=random.randint(20, 85),
                convertido=convertido,
            )
            leads[nombre] = l
            # Actividad en el lead
            CrmActividad.all_objects.create(
                company=company, lead=l,
                tipo=random.choice([TipoActividad.LLAMADA, TipoActividad.EMAIL, TipoActividad.TAREA]),
                titulo=f'Contacto inicial con {nombre}',
                fecha_programada=now + timedelta(days=random.randint(1, 7)),
            )

        # ── OPORTUNIDADES en cada etapa ───────────────────────────

        oportunidades_data = [
            # (titulo, etapa, valor, prob_override, asignado, empresa)
            ('Sistema ERP Ferretería Central', 'Prospecto', 45000000, None, rand_user(), 'Ferretería Central SAS'),
            ('Software Gestión Clínica del Norte', 'Contactado', 120000000, None, rand_user(), 'Clínica del Norte Ltda'),
            ('Plataforma POS Supermercado La Colina', 'Reunión agendada', 85000000, None, rand_user(), 'Supermercado La Colina'),
            ('Sistema Contable Constructora Ospinas', 'Propuesta enviada', 200000000, None, rand_user(), 'Constructora Ospinas'),
            ('ERP Distribuidora Maicao', 'Propuesta enviada', 155000000, None, rand_user(), 'Distribuidora Maicao'),
            ('Software Cafetería El Nogal', 'Negociación', 28000000, None, rand_user(), 'Cafetería El Nogal'),
            ('LIMS Laboratorio BioAnalítica', 'Negociación', 98000000, None, rand_user(), 'Laboratorio BioAnalítica'),
            ('PMS Hotel Chicamocha', 'Ganado', 175000000, None, rand_user(), 'Hotel Chicamocha'),
            ('Sistema CRM Logística Rápida', 'Ganado', 62000000, None, rand_user(), 'Logística Rápida SAS'),
            ('ERP Textilera Pereira', 'Perdido', 310000000, None, rand_user(), 'Textilera Pereira Ltda'),
        ]

        for titulo, etapa_nombre, valor, prob, asignado, empresa_nombre in oportunidades_data:
            if CrmOportunidad.all_objects.filter(company=company, titulo=titulo).exists():
                continue

            etapa = etapas.get(etapa_nombre)
            if not etapa:
                continue

            kwargs = {
                'company': company,
                'titulo': titulo,
                'pipeline': pipeline,
                'etapa': etapa,
                'valor_esperado': Decimal(str(valor)),
                'probabilidad': Decimal(str(etapa.probabilidad)),
                'asignado_a': asignado,
                'descripcion': f'Oportunidad de implementación de software para {empresa_nombre}',
            }

            if etapa.es_ganado:
                kwargs['ganada_en'] = now - timedelta(days=random.randint(5, 30))
            if etapa.es_perdido:
                kwargs['perdida_en'] = now - timedelta(days=random.randint(5, 20))
                kwargs['motivo_perdida'] = 'Cliente decidió con otro proveedor por precio'

            op = CrmOportunidad.all_objects.create(**kwargs)

            # Actividades en la oportunidad
            n_acts = {'Prospecto': 1, 'Contactado': 1, 'Reunión agendada': 2,
                       'Propuesta enviada': 2, 'Negociación': 3}.get(etapa_nombre, 1)
            tipos_act = [TipoActividad.LLAMADA, TipoActividad.REUNION, TipoActividad.EMAIL,
                         TipoActividad.TAREA]
            for i in range(n_acts):
                completada = (i < n_acts - 1)
                CrmActividad.all_objects.create(
                    company=company, oportunidad=op,
                    tipo=tipos_act[i % len(tipos_act)],
                    titulo=f'{"Seguimiento" if i > 0 else "Contacto inicial"} — {titulo}',
                    fecha_programada=now + timedelta(days=random.randint(-5, 14)),
                    completada=completada,
                    completada_en=now - timedelta(days=random.randint(1, 5)) if completada else None,
                    resultado='Llamada exitosa, cliente interesado' if completada else '',
                )

        self.stdout.write('    ✅ CRM: leads y oportunidades creados.')
