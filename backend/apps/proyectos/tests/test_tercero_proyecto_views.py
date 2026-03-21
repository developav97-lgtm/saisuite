"""
SaiSuite — Proyectos: Tests de Views — TerceroProyectoViewSet (complementarios)
Cubre: filtro por fase, duplicado con misma fase, filtro por rol.
"""
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, TerceroProyecto

User = get_user_model()


def crear_empresa(nombre='TPV Test Co', nit='916000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gtpv@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='Test1234!', company=company, role=role
    )


def crear_proyecto_db(company, gerente, codigo='TPV-PRY-001'):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='Proyecto TPV', tipo='obra_civil',
        cliente_id='900111', cliente_nombre='Cliente',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )


def crear_fase_db(company, proyecto, orden=1):
    return Fase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('200000'),
    )


class TerceroFiltroFaseTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.fase1    = crear_fase_db(self.company, self.proyecto, orden=1)
        self.fase2    = crear_fase_db(self.company, self.proyecto, orden=2)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/proyectos/{self.proyecto.id}/terceros/'

    def test_filtrar_por_fase(self):
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='111', tercero_nombre='A', rol='cliente', fase=self.fase1,
        )
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='222', tercero_nombre='B', rol='proveedor', fase=self.fase2,
        )
        resp = self.client.get(self.url, {'fase': str(self.fase1.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [t['tercero_id'] for t in resp.data]
        self.assertIn('111', ids)
        self.assertNotIn('222', ids)

    def test_vincular_con_misma_fase_mismo_rol_duplicado_retorna_400(self):
        """El service valida explícitamente duplicados (NULL safe)."""
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='333', tercero_nombre='C', rol='interventor', fase=self.fase1,
        )
        data = {
            'tercero_id': '333', 'tercero_nombre': 'C',
            'rol': 'interventor', 'fase': str(self.fase1.id),
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mismo_tercero_distinta_fase_permitido(self):
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='444', tercero_nombre='D', rol='subcontratista', fase=self.fase1,
        )
        data = {
            'tercero_id': '444', 'tercero_nombre': 'D',
            'rol': 'subcontratista', 'fase': str(self.fase2.id),
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_mismo_tercero_distinto_rol_mismo_proyecto_permitido(self):
        """Un tercero puede ser cliente y proveedor en el mismo proyecto."""
        data1 = {'tercero_id': '555', 'tercero_nombre': 'E', 'rol': 'cliente'}
        data2 = {'tercero_id': '555', 'tercero_nombre': 'E', 'rol': 'proveedor'}
        resp1 = self.client.post(self.url, data1, format='json')
        resp2 = self.client.post(self.url, data2, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)

    def test_listado_incluye_rol(self):
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='666', tercero_nombre='F', rol='consultor',
        )
        resp = self.client.get(self.url)
        roles = [t['rol'] for t in resp.data]
        self.assertIn('consultor', roles)

    def test_vincular_sin_tercero_id_retorna_400(self):
        data = {'tercero_nombre': 'Sin ID', 'rol': 'proveedor'}
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicado_sin_fase_retorna_400(self):
        """Validación explícita en service cubre el caso NULL fase."""
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='777', tercero_nombre='G', rol='supervisor', fase=None,
        )
        data = {'tercero_id': '777', 'tercero_nombre': 'G', 'rol': 'supervisor'}
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
