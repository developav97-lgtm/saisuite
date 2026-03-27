"""
SaiSuite — Proyectos: Tests de Views — FaseViewSet (complementarios)
Cubre casos no presentes en test_views.py: porcentaje_avance, ordenamiento.
"""
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Phase

User = get_user_model()


def crear_empresa(nombre='FV Test Co', nit='915000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gfv@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='Test1234!', company=company, role=role
    )


def crear_proyecto_db(company, gerente, codigo='FV-PRY-001', **kwargs):
    defaults = dict(
        nombre='Project FV', tipo='civil_works',
        cliente_id='900111', cliente_nombre='Cliente',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )
    defaults.update(kwargs)
    return Project.all_objects.create(company=company, gerente=gerente, codigo=codigo, **defaults)


def crear_fase_db(company, proyecto, orden=1, nombre=None, **kwargs):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=nombre or f'Phase {orden}', orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('200000'),
        **kwargs,
    )


class FaseListOrdenamientoTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/phases/'

    def _results(self, resp):
        """Desempaca paginación si existe, si no devuelve resp.data directamente."""
        if isinstance(resp.data, dict) and 'results' in resp.data:
            return resp.data['results']
        return resp.data

    def test_listado_ordenado_por_orden_asc(self):
        crear_fase_db(self.company, self.proyecto, orden=3, nombre='Tercera')
        crear_fase_db(self.company, self.proyecto, orden=1, nombre='Primera')
        crear_fase_db(self.company, self.proyecto, orden=2, nombre='Segunda')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ordenes = [f['orden'] for f in self._results(resp)]
        self.assertEqual(ordenes, sorted(ordenes))

    def test_listado_incluye_porcentaje_avance(self):
        crear_fase_db(self.company, self.proyecto, orden=1)
        resp = self.client.get(self.url)
        results = self._results(resp)
        self.assertIn('porcentaje_avance', results[0])

    def test_listado_incluye_presupuesto_total(self):
        crear_fase_db(self.company, self.proyecto, orden=1)
        resp = self.client.get(self.url)
        results = self._results(resp)
        self.assertIn('presupuesto_total', results[0])

    def test_crear_fase_sin_orden_autoasigna(self):
        crear_fase_db(self.company, self.proyecto, orden=1)
        data = {
            'nombre': 'Sin orden',
            'fecha_inicio_planificada': '2026-07-01',
            'fecha_fin_planificada': '2026-09-30',
            'presupuesto_mano_obra': '50000.00',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # orden debe ser 2 (último + 1)
        self.assertEqual(resp.data['orden'], 2)

    def test_solo_fases_activas_en_listado(self):
        crear_fase_db(self.company, self.proyecto, orden=1, nombre='Activa')
        f_inactiva = crear_fase_db(self.company, self.proyecto, orden=2, nombre='Inactiva')
        Phase.all_objects.filter(id=f_inactiva.id).update(activo=False)
        resp = self.client.get(self.url)
        nombres = [f['nombre'] for f in self._results(resp)]
        self.assertIn('Activa', nombres)
        self.assertNotIn('Inactiva', nombres)


class FaseDetailUpdateTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa('FV Detail Co', '915000002')
        self.user     = crear_usuario(self.company, 'gfvdet@test.com')
        self.proyecto = crear_proyecto_db(self.company, self.user, 'FV-PRY-DET')
        self.fase     = crear_fase_db(self.company, self.proyecto, orden=1)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/phases/{self.fase.id}/'

    def test_detalle_incluye_todos_los_campos_presupuesto(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('presupuesto_mano_obra', resp.data)
        self.assertIn('presupuesto_materiales', resp.data)

    def test_patch_nombre_y_descripcion(self):
        resp = self.client.patch(
            self.url,
            {'nombre': 'Nueva', 'descripcion': 'Descripción actualizada'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Nueva')

    def test_patch_presupuesto_excede_proyecto_retorna_400(self):
        resp = self.client.patch(
            self.url,
            {'presupuesto_mano_obra': '9999999.00'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_soft_delete_marca_inactiva(self):
        resp = self.client.delete(self.url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.fase.refresh_from_db()
        self.assertFalse(self.fase.activo)
