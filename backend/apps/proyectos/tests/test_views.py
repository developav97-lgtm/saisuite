"""
SaiSuite — Proyectos: Tests de Views (endpoints)
"""
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, EstadoProyecto

User = get_user_model()


def crear_empresa(nombre='Empresa Test', nit='900000001'):
    company = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=company, module='proyectos', is_active=True)
    return company


def crear_usuario(company, email='user@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='test1234', company=company, role=role
    )


def crear_proyecto_db(company, gerente, codigo='PRY-001', **kwargs):
    defaults = dict(
        nombre='Proyecto Test',
        tipo='obra_civil',
        cliente_id='900111',
        cliente_nombre='Cliente',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )
    defaults.update(kwargs)
    return Proyecto.all_objects.create(company=company, gerente=gerente, codigo=codigo, **defaults)


class ProyectoListCreateTest(APITestCase):

    def setUp(self):
        self.company = crear_empresa()
        self.user    = crear_usuario(self.company)
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/proyectos/'

    def test_listar_proyectos(self):
        crear_proyecto_db(self.company, self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_crear_proyecto(self):
        data = {
            'nombre': 'Nuevo Proyecto',
            'tipo': 'servicios',
            'cliente_id': '111',
            'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': '500000.00',
            'gerente': str(self.user.id),
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_viewer_no_puede_crear(self):
        viewer = crear_usuario(self.company, 'viewer@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        data = {
            'nombre': 'X', 'tipo': 'servicios', 'cliente_id': '1',
            'cliente_nombre': 'X', 'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31', 'presupuesto_total': '100',
            'gerente': str(viewer.id),
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertIn(resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_aislamiento_multitenant(self):
        company_b = crear_empresa('Empresa B', '900000002')
        user_b    = crear_usuario(company_b, 'b@b.com')
        crear_proyecto_db(company_b, user_b, codigo='PRY-B')
        # Autenticado como user_a, no debe ver PRY-B
        resp = self.client.get(self.url)
        codigos = [p['codigo'] for p in resp.data['results']]
        self.assertNotIn('PRY-B', codigos)

    def test_busqueda_por_nombre(self):
        crear_proyecto_db(self.company, self.user, codigo='PRY-001', nombre='Puente Los Andes')
        crear_proyecto_db(self.company, self.user, codigo='PRY-002', nombre='Consultoría IT')
        resp = self.client.get(self.url, {'search': 'Puente'})
        self.assertEqual(resp.data['count'], 1)
        self.assertEqual(resp.data['results'][0]['nombre'], 'Puente Los Andes')


class ProyectoDetailTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/proyectos/{self.proyecto.id}/'

    def test_obtener_detalle(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['codigo'], 'PRY-001')

    def test_soft_delete(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.proyecto.refresh_from_db()
        self.assertFalse(self.proyecto.activo)

    def test_patch_nombre(self):
        resp = self.client.patch(self.url, {'nombre': 'Nuevo nombre'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class CambiarEstadoActionTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/proyectos/{self.proyecto.id}/cambiar-estado/'

    def test_cambiar_a_planificado_sin_fases(self):
        resp = self.client.post(self.url, {'nuevo_estado': 'planificado'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_a_planificado_con_fases(self):
        Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
        )
        resp = self.client.post(self.url, {'nuevo_estado': 'planificado'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'planificado')

    def test_estado_invalido(self):
        resp = self.client.post(self.url, {'nuevo_estado': 'inexistente'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class EstadoFinancieroActionTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/proyectos/{self.proyecto.id}/estado-financiero/'

    def test_obtener_estado_financiero(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('presupuesto_total', resp.data)
        self.assertIn('aiu', resp.data)
        self.assertIn('costo_ejecutado', resp.data)


class FaseListCreateTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/proyectos/{self.proyecto.id}/fases/'

    def test_listar_fases(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_crear_fase(self):
        data = {
            'nombre': 'Fase 1',
            'orden': 1,
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-06-30',
            'presupuesto_mano_obra': '200000.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_crear_fase_excede_presupuesto(self):
        data = {
            'nombre': 'Fase Gigante',
            'orden': 1,
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-06-30',
            'presupuesto_mano_obra': '9999999.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class FaseDetailTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.fase     = Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
        )
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/proyectos/fases/{self.fase.id}/'

    def test_obtener_fase(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_actualizar_fase(self):
        resp = self.client.patch(self.url, {'nombre': 'Fase Actualizada'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_eliminar_fase(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.fase.refresh_from_db()
        self.assertFalse(self.fase.activo)
