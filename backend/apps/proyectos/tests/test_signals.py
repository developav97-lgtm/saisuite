"""
SaiSuite — Proyectos: Tests de Signals
Verifica que post_save/post_delete en ProjectActivity recalculan avance.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Phase, Activity, ProjectActivity

User = get_user_model()


def crear_empresa(nombre='Sig Test Co', nit='911000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gsig@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!', company=company, role='company_admin'
    )


def crear_proyecto(company, gerente, codigo='SIG-PRY-001'):
    return Project.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='Sig Project', tipo='civil_works',
        cliente_id='111', cliente_nombre='C',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )


def crear_fase(company, proyecto, orden=1):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=f'Phase {orden}', orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('500000'),
    )


def crear_actividad(company, codigo='SIG-ACT-001'):
    return Activity.all_objects.create(
        company=company, codigo=codigo,
        nombre='Activity Señal', unidad_medida='m2', tipo='material',
    )


class SignalPostSaveTest(TestCase):

    def setUp(self):
        self.company   = crear_empresa()
        self.user      = crear_usuario(self.company)
        self.proyecto  = crear_proyecto(self.company, self.user)
        self.fase      = crear_fase(self.company, self.proyecto)
        self.actividad = crear_actividad(self.company)

    def test_create_recalcula_avance_fase(self):
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('5'),
            costo_unitario=Decimal('1000'),
        )
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('50.00'))

    def test_create_recalcula_avance_proyecto(self):
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.porcentaje_avance, Decimal('100.00'))

    def test_save_con_cantidad_actualizada_recalcula(self):
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('0'),
            costo_unitario=Decimal('1000'),
        )
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('0'))

        # Actualizar cantidad via save → trigger post_save signal
        ap.cantidad_ejecutada = Decimal('10')
        ap.save()

        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('100.00'))

    def test_signal_con_fase_none_no_falla(self):
        """Signal sin fase solo recalcula el proyecto, no la fase."""
        a2 = crear_actividad(self.company, 'SIG-ACT-NOFASE')
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=a2, fase=None,
            cantidad_planificada=Decimal('5'), cantidad_ejecutada=Decimal('5'),
            costo_unitario=Decimal('1000'),
        )
        # No debe lanzar excepción — solo recalcula proyecto
        self.proyecto.refresh_from_db()
        self.assertIsNotNone(self.proyecto.porcentaje_avance)


class SignalPostDeleteTest(TestCase):

    def setUp(self):
        self.company   = crear_empresa('Sig Delete Co', '911000002')
        self.user      = crear_usuario(self.company, 'gsigdel@test.com')
        self.proyecto  = crear_proyecto(self.company, self.user, 'SIG-DEL-001')
        self.fase      = crear_fase(self.company, self.proyecto)
        self.actividad = crear_actividad(self.company, 'SIG-ACT-DEL')

    def test_delete_recalcula_avance_fase_a_cero(self):
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('100.00'))

        ap.delete()

        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('0'))

    def test_delete_recalcula_avance_proyecto_a_cero(self):
        ap = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.porcentaje_avance, Decimal('100.00'))

        ap.delete()

        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.porcentaje_avance, Decimal('0'))

    def test_delete_con_otras_actividades_recalcula_parcial(self):
        a2 = crear_actividad(self.company, 'SIG-ACT-DEL2')
        ap1 = ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=a2, fase=self.fase,
            cantidad_planificada=Decimal('10'), cantidad_ejecutada=Decimal('0'),
            costo_unitario=Decimal('1000'),
        )

        # Avance inicial: 10000/20000 = 50%
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('50.00'))

        # Eliminar la primera (10 ej.) → queda la segunda (0 ej.) → 0%
        ap1.delete()
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('0'))
