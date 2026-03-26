"""
SaiSuite — Proyectos: Tests de Views — ActividadProyectoViewSet
Cubre: GET/POST/PATCH/DELETE /api/v1/projects/{id}/activities/
"""
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (ProjectStatus, PhaseStatus, ActivityType, MeasurementMode,
    Proyecto, Fase, Actividad, ActividadProyecto, EstadoProyecto,
)

User = get_user_model()


def crear_empresa(nombre='APV Test Co', nit='914000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gapv@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='Test1234!', company=company, role=role
    )


def crear_proyecto_db(company, gerente, codigo='APV-PRY-001', **kwargs):
    defaults = dict(
        nombre='Proyecto APV', tipo='civil_works',
        cliente_id='900111', cliente_nombre='Cliente',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )
    defaults.update(kwargs)
    return Proyecto.all_objects.create(company=company, gerente=gerente, codigo=codigo, **defaults)


def crear_fase_db(company, proyecto, orden=1):
    return Fase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('500000'),
    )


def crear_actividad_db(company, codigo='ACT-APV-001'):
    return Actividad.all_objects.create(
        company=company, codigo=codigo,
        nombre='Actividad APV', unidad_medida='m2', tipo='material',
        costo_unitario_base=Decimal('10000'),
    )


class ActividadProyectoListCreateTest(APITestCase):

    def setUp(self):
        self.company   = crear_empresa()
        self.user      = crear_usuario(self.company)
        self.proyecto  = crear_proyecto_db(self.company, self.user)
        self.fase      = crear_fase_db(self.company, self.proyecto)
        self.actividad = crear_actividad_db(self.company)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/activities/'

    def test_listar_actividades_proyecto_vacio(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_listar_actividades_proyecto(self):
        ActividadProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('5000'),
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_filtrar_por_fase(self):
        f2 = crear_fase_db(self.company, self.proyecto, orden=2)
        a2 = crear_actividad_db(self.company, 'ACT-APV-002')
        ActividadProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        ActividadProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=a2, fase=f2,
            cantidad_planificada=Decimal('5'), costo_unitario=Decimal('2000'),
        )
        resp = self.client.get(self.url, {'fase': str(self.fase.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_listado_incluye_presupuesto_total(self):
        ActividadProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('5000'),
        )
        resp = self.client.get(self.url)
        self.assertIn('presupuesto_total', resp.data[0])

    def test_crear_actividad_proyecto(self):
        data = {
            'actividad': str(self.actividad.id),
            'cantidad_planificada': '10.00',
            'costo_unitario': '5000.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_crear_con_fase(self):
        data = {
            'actividad': str(self.actividad.id),
            'fase': str(self.fase.id),
            'cantidad_planificada': '5.00',
            'costo_unitario': '10000.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(resp.data['fase']), str(self.fase.id))

    def test_crear_sin_costo_usa_base(self):
        """Si no se provee costo_unitario, el service usa costo_unitario_base."""
        data = {
            'actividad': str(self.actividad.id),
            'cantidad_planificada': '8.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['costo_unitario'], '10000.00')

    def test_crear_cantidad_negativa_retorna_400(self):
        data = {
            'actividad': str(self.actividad.id),
            'cantidad_planificada': '-1.00',
            'costo_unitario': '1000.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cantidad_ejecutada_en_borrador_retorna_400(self):
        """No se puede registrar ejecución si el proyecto no está en_ejecucion."""
        data = {
            'actividad': str(self.actividad.id),
            'cantidad_planificada': '10.00',
            'cantidad_ejecutada': '5.00',
            'costo_unitario': '1000.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cantidad_ejecutada_permitida_en_ejecucion(self):
        proyecto_en_ejec = crear_proyecto_db(
            self.company, self.user, 'APV-PRY-002',
            estado=ProjectStatus.IN_PROGRESS,
        )
        url = f'/api/v1/projects/{proyecto_en_ejec.id}/activities/'
        data = {
            'actividad': str(self.actividad.id),
            'cantidad_planificada': '10.00',
            'cantidad_ejecutada': '5.00',
            'costo_unitario': '1000.00',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_signal_recalcula_avance_al_crear(self):
        """Crear ActividadProyecto actualiza porcentaje_avance de la fase."""
        data = {
            'actividad': str(self.actividad.id),
            'fase': str(self.fase.id),
            'cantidad_planificada': '10.00',
            'cantidad_ejecutada': '0.00',
            'costo_unitario': '1000.00',
        }
        self.client.post(self.url, data, format='json')
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('0'))


class ActividadProyectoUpdateDeleteTest(APITestCase):

    def setUp(self):
        self.company   = crear_empresa('APV Update Co', '914000002')
        self.user      = crear_usuario(self.company, 'gapvupd@test.com')
        self.proyecto  = crear_proyecto_db(
            self.company, self.user, 'APV-UPD-001',
            estado=ProjectStatus.IN_PROGRESS,
        )
        self.fase      = crear_fase_db(self.company, self.proyecto)
        self.actividad = crear_actividad_db(self.company, 'ACT-APV-UPD')
        self.ap = ActividadProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            actividad=self.actividad, fase=self.fase,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('5000'),
        )
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/activities/{self.ap.id}/'

    def test_actualizar_cantidad_ejecutada(self):
        data = {'cantidad_ejecutada': '7.00'}
        resp = self.client.patch(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.ap.refresh_from_db()
        self.assertEqual(self.ap.cantidad_ejecutada, Decimal('7'))

    def test_actualizar_recalcula_avance_fase(self):
        data = {'cantidad_ejecutada': '10.00'}
        self.client.patch(self.url, data, format='json')
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('100.00'))

    def test_eliminar_actividad_proyecto(self):
        # La regla de negocio permite eliminar sólo en estado 'draft'.
        proyecto_draft = crear_proyecto_db(
            self.company, self.user, 'APV-UPD-DEL',
            estado=ProjectStatus.DRAFT,
        )
        fase_draft = crear_fase_db(self.company, proyecto_draft)
        ap_draft = ActividadProyecto.all_objects.create(
            company=self.company, proyecto=proyecto_draft,
            actividad=self.actividad, fase=fase_draft,
            cantidad_planificada=Decimal('5'), costo_unitario=Decimal('1000'),
        )
        url = f'/api/v1/projects/{proyecto_draft.id}/activities/{ap_draft.id}/'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ActividadProyecto.all_objects.filter(id=ap_draft.id).exists()
        )

    def test_eliminar_recalcula_avance_fase_a_cero(self):
        # Establecer algo de ejecución primero
        ActividadProyecto.all_objects.filter(id=self.ap.id).update(
            cantidad_ejecutada=Decimal('10')
        )
        self.client.delete(self.url)
        self.fase.refresh_from_db()
        self.assertEqual(self.fase.porcentaje_avance, Decimal('0'))
