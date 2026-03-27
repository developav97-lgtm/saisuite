"""
SaiSuite — Proyectos: Tests de Views — ActividadViewSet
Cubre: GET/POST/PATCH/DELETE /api/v1/projects/activities/
"""
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Activity, ProjectActivity

User = get_user_model()

URL_ACTIVIDADES = '/api/v1/projects/activities/'


def crear_empresa(nombre='AV Test Co', nit='913000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gav@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='Test1234!', company=company, role=role
    )


def crear_actividad_db(company, codigo='ACT-AV-001', **kwargs):
    defaults = dict(nombre='Excavación', unidad_medida='m3', tipo='material')
    defaults.update(kwargs)
    return Activity.all_objects.create(company=company, codigo=codigo, **defaults)


def crear_proyecto_db(company, gerente, codigo='AV-PRY-001'):
    return Project.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='Project AV', tipo='civil_works',
        cliente_id='900111', cliente_nombre='Cliente',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )


class ActividadListCreateTest(APITestCase):

    def setUp(self):
        self.company = crear_empresa()
        self.user    = crear_usuario(self.company)
        self.client.force_authenticate(user=self.user)

    def test_listar_actividades_vacio(self):
        resp = self.client.get(URL_ACTIVIDADES)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_listar_actividades(self):
        crear_actividad_db(self.company, 'ACT-LST-001')
        crear_actividad_db(self.company, 'ACT-LST-002')
        resp = self.client.get(URL_ACTIVIDADES)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_aislamiento_multitenant(self):
        c2 = crear_empresa('Otra AV', '913000002')
        crear_actividad_db(c2, 'ACT-OTRA-001')
        crear_actividad_db(self.company, 'ACT-MIA-001')
        resp = self.client.get(URL_ACTIVIDADES)
        codigos = [a['codigo'] for a in resp.data['results']]
        self.assertIn('ACT-MIA-001', codigos)
        self.assertNotIn('ACT-OTRA-001', codigos)

    def test_busqueda_por_nombre(self):
        crear_actividad_db(self.company, 'ACT-SRCH-001', nombre='Excavación profunda')
        crear_actividad_db(self.company, 'ACT-SRCH-002', nombre='Pintura exterior')
        resp = self.client.get(URL_ACTIVIDADES, {'search': 'Excavación'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        nombres = [a['nombre'] for a in resp.data['results']]
        self.assertIn('Excavación profunda', nombres)
        self.assertNotIn('Pintura exterior', nombres)

    def test_filtrar_por_tipo(self):
        crear_actividad_db(self.company, 'ACT-TIPO-001', tipo='labor')
        crear_actividad_db(self.company, 'ACT-TIPO-002', tipo='equipment')
        resp = self.client.get(URL_ACTIVIDADES, {'tipo': 'labor'})
        tipos = [a['tipo'] for a in resp.data['results']]
        self.assertIn('labor', tipos)
        self.assertNotIn('equipment', tipos)

    def test_crear_actividad_exitosa(self):
        data = {
            'nombre': 'Concreto vaciado',
            'tipo': 'material',
            'unidad_medida': 'm3',
        }
        resp = self.client.post(URL_ACTIVIDADES, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_crear_actividad_autocodigo(self):
        data = {'nombre': 'Auto', 'tipo': 'equipment', 'unidad_medida': 'hora'}
        resp = self.client.post(URL_ACTIVIDADES, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data['codigo'].startswith('ACT-'))

    def test_crear_actividad_codigo_manual(self):
        data = {
            'codigo': 'MANUAL-001',
            'nombre': 'Manual', 'tipo': 'subcontract', 'unidad_medida': 'global',
        }
        resp = self.client.post(URL_ACTIVIDADES, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['codigo'], 'MANUAL-001')

    def test_crear_actividad_sin_nombre_retorna_400(self):
        data = {'tipo': 'material', 'unidad_medida': 'm2'}
        resp = self.client.post(URL_ACTIVIDADES, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_actividad_costo_negativo_retorna_400(self):
        data = {
            'nombre': 'Negativa', 'tipo': 'material', 'unidad_medida': 'm2',
            'costo_unitario_base': '-100',
        }
        resp = self.client.post(URL_ACTIVIDADES, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_puede_listar(self):
        viewer = crear_usuario(self.company, 'gvieweract@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        resp = self.client.get(URL_ACTIVIDADES)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class ActividadDetailTest(APITestCase):

    def setUp(self):
        self.company    = crear_empresa('AV Detail Co', '913000003')
        self.user       = crear_usuario(self.company, 'gavdet@test.com')
        self.actividad  = crear_actividad_db(self.company, 'ACT-DET-001')
        self.client.force_authenticate(user=self.user)
        self.url = f'{URL_ACTIVIDADES}{self.actividad.id}/'

    def test_obtener_detalle(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['codigo'], 'ACT-DET-001')

    def test_actualizar_actividad(self):
        resp = self.client.patch(self.url, {'nombre': 'Actualizada'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Actualizada')

    def test_actualizar_costo_unitario(self):
        resp = self.client.patch(
            self.url, {'costo_unitario_base': '75000.00'}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_eliminar_sin_asignaciones(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.actividad.refresh_from_db()
        self.assertFalse(self.actividad.activo)

    def test_eliminar_con_asignaciones_retorna_400(self):
        gerente = self.user
        p = crear_proyecto_db(self.company, gerente, 'AV-PRY-DEL')
        ProjectActivity.all_objects.create(
            company=self.company, proyecto=p, actividad=self.actividad,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('1000'),
        )
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_actividad_de_otra_empresa_404(self):
        c2 = crear_empresa('Otra AV Det', '913000004')
        a2 = crear_actividad_db(c2, 'ACT-OTRA-DET')
        url = f'{URL_ACTIVIDADES}{a2.id}/'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_ordering_por_codigo(self):
        crear_actividad_db(self.company, 'ACT-Z')
        crear_actividad_db(self.company, 'ACT-A')
        resp = self.client.get(URL_ACTIVIDADES)
        codigos = [a['codigo'] for a in resp.data['results'] if a['codigo'] in ('ACT-A', 'ACT-Z')]
        if len(codigos) == 2:
            self.assertEqual(codigos, sorted(codigos))
