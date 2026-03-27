"""
SaiSuite — Proyectos: Tests complementarios de Services
Cubre: calcular_avance_fase, calcular_avance_proyecto, ConfiguracionModuloService,
       ActividadService, ActividadProyectoService y gaps del ProyectoService.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Project, Phase, ProjectStatus, ModuleSettings,
    Activity, ProjectActivity, ProjectStakeholder,
)
from apps.proyectos.services import (
    calcular_avance_fase,
    calcular_avance_proyecto,
    ConfiguracionModuloService,
    ProyectoService,
    TerceroProyectoService,
    ActividadService,
    ActividadProyectoService,
    ProyectoException,
)
from rest_framework.exceptions import ValidationError

User = get_user_model()


# ── Helpers ────────────────────────────────────────────────────────────────────

def crear_empresa(nombre='Empresa SVC', nit='910000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gsvc@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='Test1234!', company=company, role=role
    )


def crear_proyecto(company, gerente, codigo='SVC-PRY-001', **kwargs):
    defaults = dict(
        nombre='Project SVC', tipo='civil_works',
        cliente_id='900111', cliente_nombre='Cliente',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000.00'),
    )
    defaults.update(kwargs)
    return Project.all_objects.create(company=company, gerente=gerente, codigo=codigo, **defaults)


def crear_fase(company, proyecto, orden=1, **kwargs):
    defaults = dict(
        nombre=f'Phase {orden}', orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('200000'),
    )
    defaults.update(kwargs)
    return Phase.all_objects.create(company=company, proyecto=proyecto, **defaults)


def crear_actividad(company, codigo='ACT-SVC-001', **kwargs):
    defaults = dict(nombre='Excavación', unidad_medida='m3', tipo='material')
    defaults.update(kwargs)
    return Activity.all_objects.create(company=company, codigo=codigo, **defaults)


# ── calcular_avance_fase ───────────────────────────────────────────────────────

class CalcularAvanceFaseTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(self.company, self.user)
        self.fase     = crear_fase(self.company, self.proyecto)

    def test_fase_sin_actividades_retorna_cero(self):
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('0'))

    def test_fase_actividades_sin_ejecutar_retorna_cero(self):
        a = crear_actividad(self.company, 'ACT-F-001')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('0'),
            costo_unitario=Decimal('5000'),
        )
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('0'))

    def test_fase_actividades_50_ejecutadas(self):
        a = crear_actividad(self.company, 'ACT-F-002')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('5'),
            costo_unitario=Decimal('1000'),
        )
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('50.00'))

    def test_fase_actividades_100_ejecutadas(self):
        a = crear_actividad(self.company, 'ACT-F-003')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a, fase=self.fase,
            cantidad_planificada=Decimal('8'), cantidad_ejecutada=Decimal('8'),
            costo_unitario=Decimal('2000'),
        )
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('100.00'))

    def test_ponderacion_por_costo_75_pct(self):
        """
        Activity A: 10 × $100 = $1000 planificado, 5 ejecutadas = $500
        Activity B: 5 × $200 = $1000 planificado, 5 ejecutadas = $1000
        Total: $2000 planificado, $1500 ejecutado → 75.00%
        """
        a1 = crear_actividad(self.company, 'ACT-F-004A')
        a2 = crear_actividad(self.company, 'ACT-F-004B')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a1, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('5'),
            costo_unitario=Decimal('100'),
        )
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a2, fase=self.fase,
            cantidad_planificada=Decimal('5'), cantidad_ejecutada=Decimal('5'),
            costo_unitario=Decimal('200'),
        )
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('75.00'))

    def test_costo_unitario_cero_no_divide_por_cero(self):
        a = crear_actividad(self.company, 'ACT-F-005')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('0'),
        )
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('0'))

    def test_persiste_porcentaje_en_db(self):
        a = crear_actividad(self.company, 'ACT-F-006')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )
        calcular_avance_fase(self.fase.id)
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('100.00'))

    def test_resultado_no_supera_100(self):
        """Aunque ejecutado > planificado, el techo es 100."""
        a = crear_actividad(self.company, 'ACT-F-007')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=a, fase=self.fase,
            cantidad_planificada=Decimal('5'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )
        pct = calcular_avance_fase(self.fase.id)
        self.assertEqual(pct, Decimal('100.00'))


# ── calcular_avance_proyecto ───────────────────────────────────────────────────

class CalcularAvanceProyectoTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa('Empresa AVP', '910000002')
        self.user     = crear_usuario(self.company, 'gavp@test.com')
        self.proyecto = crear_proyecto(self.company, self.user, 'AVP-PRY-001')

    def test_proyecto_sin_fases_retorna_cero(self):
        pct = calcular_avance_proyecto(self.proyecto.id)
        self.assertEqual(pct, Decimal('0'))

    def test_proyecto_promedio_de_fases(self):
        f1 = crear_fase(self.company, self.proyecto, orden=1)
        f2 = crear_fase(self.company, self.proyecto, orden=2)
        Phase.all_objects.filter(id=f1.id).update(porcentaje_avance=Decimal('50'))
        Phase.all_objects.filter(id=f2.id).update(porcentaje_avance=Decimal('100'))
        pct = calcular_avance_proyecto(self.proyecto.id)
        self.assertEqual(pct, Decimal('75.00'))

    def test_proyecto_persiste_en_db(self):
        f = crear_fase(self.company, self.proyecto, orden=1)
        Phase.all_objects.filter(id=f.id).update(porcentaje_avance=Decimal('40'))
        calcular_avance_proyecto(self.proyecto.id)
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.porcentaje_avance, Decimal('40.00'))

    def test_fases_inactivas_no_cuentan(self):
        f1 = crear_fase(self.company, self.proyecto, orden=1)
        f2 = crear_fase(self.company, self.proyecto, orden=2)
        Phase.all_objects.filter(id=f1.id).update(porcentaje_avance=Decimal('100'))
        Phase.all_objects.filter(id=f2.id).update(activo=False, porcentaje_avance=Decimal('0'))
        pct = calcular_avance_proyecto(self.proyecto.id)
        self.assertEqual(pct, Decimal('100.00'))


# ── ConfiguracionModuloService ─────────────────────────────────────────────────

class ConfiguracionModuloServiceTest(TestCase):

    def setUp(self):
        self.company = crear_empresa('Empresa CFG', '910000003')

    def test_get_or_create_crea_nuevo(self):
        config = ConfiguracionModuloService.get_or_create(self.company)
        self.assertIsNotNone(config.id)
        self.assertEqual(config.company, self.company)

    def test_get_or_create_devuelve_existente(self):
        ModuleSettings.objects.create(company=self.company)
        config = ConfiguracionModuloService.get_or_create(self.company)
        self.assertEqual(ModuleSettings.objects.filter(company=self.company).count(), 1)
        self.assertIsNotNone(config.id)

    def test_update_requiere_sync(self):
        config = ConfiguracionModuloService.update(
            self.company, {'requiere_sync_saiopen_para_ejecucion': True}
        )
        self.assertTrue(config.requiere_sync_saiopen_para_ejecucion)
        config.refresh_from_db()
        self.assertTrue(config.requiere_sync_saiopen_para_ejecucion)

    def test_update_dias_alerta(self):
        config = ConfiguracionModuloService.update(
            self.company, {'dias_alerta_vencimiento': 30}
        )
        self.assertEqual(config.dias_alerta_vencimiento, 30)

    def test_update_crea_si_no_existe(self):
        self.assertFalse(ModuleSettings.objects.filter(company=self.company).exists())
        config = ConfiguracionModuloService.update(self.company, {'dias_alerta_vencimiento': 7})
        self.assertIsNotNone(config.id)


# ── ProyectoService gaps ───────────────────────────────────────────────────────

class ProyectoServiceGapTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa('Empresa GAP', '910000004')
        self.user     = crear_usuario(self.company, 'ggap@test.com')
        self.proyecto = crear_proyecto(self.company, self.user, 'GAP-PRY-001')

    def test_get_proyecto_por_id(self):
        found = ProyectoService.get_proyecto(self.proyecto.id)
        self.assertEqual(found.id, self.proyecto.id)

    def test_generar_codigo_autoincremental(self):
        # Hay PRY-001 ya creado; el siguiente debe ser PRY-002
        crear_proyecto(self.company, self.user, 'PRY-001', nombre='Base')
        data = {
            'nombre': 'Segundo', 'tipo': 'services',
            'cliente_id': '111', 'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': Decimal('100000'),
            'gerente': self.user.id,
        }
        p = ProyectoService.create_proyecto(data, self.user)
        self.assertEqual(p.codigo, 'PRY-002')

    def test_generar_codigo_en_empresa_sin_proyectos(self):
        c2 = crear_empresa('Sin Proyectos', '910000005')
        u2 = crear_usuario(c2, 'gsinpry@test.com')
        data = {
            'nombre': 'Primero', 'tipo': 'services',
            'cliente_id': '111', 'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': Decimal('100000'),
            'gerente': u2.id,
        }
        p = ProyectoService.create_proyecto(data, u2)
        self.assertEqual(p.codigo, 'PRY-001')

    def test_validar_coordinador_misma_empresa(self):
        coord = crear_usuario(self.company, 'gcoord@test.com')
        data = {
            'nombre': 'Con coord', 'tipo': 'services',
            'cliente_id': '111', 'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': Decimal('100000'),
            'gerente': self.user.id,
            'coordinador': coord.id,
        }
        p = ProyectoService.create_proyecto(data, self.user)
        self.assertEqual(p.coordinador_id, coord.id)

    def test_validar_coordinador_otra_empresa_falla(self):
        c2 = crear_empresa('Otra', '910000006')
        u2 = crear_usuario(c2, 'gotro@test.com')
        data = {
            'nombre': 'X', 'tipo': 'services',
            'cliente_id': '111', 'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': Decimal('100000'),
            'gerente': self.user.id,
            'coordinador': u2.id,
        }
        with self.assertRaises(ProyectoException):
            ProyectoService.create_proyecto(data, self.user)

    def test_update_con_nuevo_gerente(self):
        nuevo = crear_usuario(self.company, 'gnuevo@test.com')
        p = ProyectoService.update_proyecto(self.proyecto, {'gerente': nuevo.id})
        self.assertEqual(p.gerente_id, nuevo.id)

    def test_update_con_coordinador(self):
        coord = crear_usuario(self.company, 'gcoord2@test.com')
        p = ProyectoService.update_proyecto(self.proyecto, {'coordinador': coord.id})
        self.assertEqual(p.coordinador_id, coord.id)

    def test_update_coordinador_a_none(self):
        p = ProyectoService.update_proyecto(self.proyecto, {'coordinador': None})
        self.assertIsNone(p.coordinador)


# ── TerceroProyectoService gaps ────────────────────────────────────────────────

class TerceroProyectoServiceGapTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa('Empresa TP', '910000007')
        self.user     = crear_usuario(self.company, 'gtp@test.com')
        self.proyecto = crear_proyecto(self.company, self.user, 'TP-SVC-001')

    def test_list_terceros_todos(self):
        ProjectStakeholder.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='111', tercero_nombre='A', rol='client',
        )
        qs = TerceroProyectoService.list_terceros(self.proyecto)
        self.assertEqual(qs.count(), 1)

    def test_list_terceros_filtra_por_fase(self):
        fase = crear_fase(self.company, self.proyecto)
        ProjectStakeholder.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='111', tercero_nombre='A', rol='client', fase=fase,
        )
        ProjectStakeholder.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='222', tercero_nombre='B', rol='vendor', fase=None,
        )
        qs = TerceroProyectoService.list_terceros(self.proyecto, fase_id=str(fase.id))
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().tercero_id, '111')

    def test_vincular_tercero_duplicado_lanza_error(self):
        ProjectStakeholder.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='333', tercero_nombre='C', rol='client', fase=None,
        )
        with self.assertRaises(ValidationError):
            TerceroProyectoService.vincular_tercero(self.proyecto, {
                'tercero_id': '333', 'tercero_nombre': 'C', 'rol': 'client', 'fase': None,
            })


# ── ActividadService ───────────────────────────────────────────────────────────

class ActividadServiceTest(TestCase):

    def setUp(self):
        self.company = crear_empresa('Empresa ACT', '910000008')
        self.user    = crear_usuario(self.company, 'gact@test.com')

    def test_list_actividades_por_empresa(self):
        crear_actividad(self.company, 'ACT-LST-001')
        crear_actividad(self.company, 'ACT-LST-002')
        qs = ActividadService.list_actividades(company=self.company)
        self.assertEqual(qs.count(), 2)

    def test_list_actividades_sin_company(self):
        crear_actividad(self.company, 'ACT-LST-003')
        qs = ActividadService.list_actividades()
        self.assertGreaterEqual(qs.count(), 1)

    def test_get_actividad(self):
        a = crear_actividad(self.company, 'ACT-GET-001')
        found = ActividadService.get_actividad(a.id)
        self.assertEqual(found.id, a.id)

    def test_create_actividad_autocodigo(self):
        data = {'nombre': 'Pintura', 'tipo': 'material', 'unidad_medida': 'm2'}
        a = ActividadService.create_actividad(data, self.user)
        self.assertIsNotNone(a.id)
        self.assertTrue(a.codigo.startswith('ACT-'))

    def test_create_actividad_codigo_manual(self):
        data = {
            'codigo': 'ACT-MANUAL',
            'nombre': 'Manual', 'tipo': 'labor', 'unidad_medida': 'hora',
        }
        a = ActividadService.create_actividad(data, self.user)
        self.assertEqual(a.codigo, 'ACT-MANUAL')

    def test_create_actividad_pertenece_a_empresa(self):
        data = {'nombre': 'Concreto', 'tipo': 'material', 'unidad_medida': 'm3'}
        a = ActividadService.create_actividad(data, self.user)
        self.assertEqual(a.company_id, self.company.id)

    def test_update_actividad_nombre(self):
        a = crear_actividad(self.company, 'ACT-UPD-001')
        updated = ActividadService.update_actividad(a, {'nombre': 'Nuevo Nombre'})
        self.assertEqual(updated.nombre, 'Nuevo Nombre')

    def test_update_actividad_persiste(self):
        a = crear_actividad(self.company, 'ACT-UPD-002')
        ActividadService.update_actividad(a, {'costo_unitario_base': Decimal('75000')})
        a.refresh_from_db()
        self.assertEqual(a.costo_unitario_base, Decimal('75000'))

    def test_soft_delete_sin_asignaciones(self):
        a = crear_actividad(self.company, 'ACT-DEL-001')
        ActividadService.soft_delete_actividad(a)
        a.refresh_from_db()
        self.assertFalse(a.activo)

    def test_soft_delete_con_asignaciones_falla(self):
        a = crear_actividad(self.company, 'ACT-DEL-002')
        p = crear_proyecto(self.company, self.user, 'ACT-PRY-DEL')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=p, actividad=a,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        with self.assertRaises(ValidationError):
            ActividadService.soft_delete_actividad(a)

    def test_actividades_inactivas_no_aparecen(self):
        a = crear_actividad(self.company, 'ACT-INACT-001')
        a.activo = False
        a.save()
        qs = ActividadService.list_actividades(company=self.company)
        ids = list(qs.values_list('id', flat=True))
        self.assertNotIn(a.id, ids)


# ── ActividadProyectoService ───────────────────────────────────────────────────

class ActividadProyectoServiceTest(TestCase):

    def setUp(self):
        self.company   = crear_empresa('Empresa APSVC', '910000009')
        self.user      = crear_usuario(self.company, 'gap2svc@test.com')
        self.proyecto  = crear_proyecto(self.company, self.user, 'AP-SVC-001')
        self.fase      = crear_fase(self.company, self.proyecto)
        self.actividad = crear_actividad(self.company, 'ACT-AP-001')

    def test_list_actividades_proyecto(self):
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        qs = ActividadProyectoService.list_actividades_proyecto(self.proyecto)
        self.assertEqual(qs.count(), 1)

    def test_list_actividades_proyecto_filtra_por_fase(self):
        a2 = crear_actividad(self.company, 'ACT-AP-002')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=a2, fase=None,
            cantidad_planificada=Decimal('5'), costo_unitario=Decimal('500'),
        )
        qs = ActividadProyectoService.list_actividades_proyecto(
            self.proyecto, fase_id=str(self.fase.id)
        )
        self.assertEqual(qs.count(), 1)

    def test_asignar_actividad(self):
        ap = ActividadProyectoService.asignar_actividad(self.proyecto, {
            'actividad': self.actividad,
            'cantidad_planificada': Decimal('10'),
            'costo_unitario': Decimal('5000'),
        })
        self.assertIsNotNone(ap.id)
        self.assertEqual(ap.proyecto, self.proyecto)

    def test_asignar_usa_costo_base_si_no_se_provee(self):
        self.actividad.costo_unitario_base = Decimal('3000')
        self.actividad.save()
        ap = ActividadProyectoService.asignar_actividad(self.proyecto, {
            'actividad': self.actividad,
            'cantidad_planificada': Decimal('5'),
        })
        self.assertEqual(ap.costo_unitario, Decimal('3000'))

    def test_asignar_actividad_pertenece_empresa(self):
        ap = ActividadProyectoService.asignar_actividad(self.proyecto, {
            'actividad': self.actividad,
            'cantidad_planificada': Decimal('10'),
            'costo_unitario': Decimal('1000'),
        })
        self.assertEqual(ap.company_id, self.company.id)

    def test_update_actividad_proyecto(self):
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        updated = ActividadProyectoService.update_actividad_proyecto(
            ap, {'cantidad_ejecutada': Decimal('5')}
        )
        self.assertEqual(updated.cantidad_ejecutada, Decimal('5'))

    def test_update_persiste_en_db(self):
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        ActividadProyectoService.update_actividad_proyecto(ap, {'costo_unitario': Decimal('2000')})
        ap.refresh_from_db()
        self.assertEqual(ap.costo_unitario, Decimal('2000'))

    def test_desasignar_actividad(self):
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        ap_id = ap.id
        ActividadProyectoService.desasignar_actividad(ap)
        self.assertFalse(ProjectActivity.all_objects.filter(id=ap_id).exists())
