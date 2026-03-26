"""
SaiSuite — Proyectos: Tests de Views — Proyecto
Cubre: iniciar-ejecucion, filtros de estado, ConfiguracionModuloView.
"""
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, ProjectStatus, EstadoProyecto, ConfiguracionModulo

User = get_user_model()


def crear_empresa(nombre='PV Test Co', nit='912000001'):
    c = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def crear_usuario(company, email='gpv@test.com', role='company_admin'):
    return User.objects.create_user(
        email=email, password='Test1234!', company=company, role=role
    )


def crear_proyecto_db(company, gerente, codigo='PV-PRY-001', **kwargs):
    defaults = dict(
        nombre='Proyecto PV', tipo='civil_works',
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
    )


class IniciarEjecucionViewTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.client.force_authenticate(user=self.user)

    def test_iniciar_ejecucion_exitoso_desde_planificado(self):
        proyecto = crear_proyecto_db(
            self.company, self.user, 'IE-PRY-001',
            estado=ProjectStatus.PLANNED,
        )
        url = f'/api/v1/projects/{proyecto.id}/iniciar-ejecucion/'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], ProjectStatus.IN_PROGRESS)

    def test_iniciar_ejecucion_desde_borrador_falla(self):
        """BORRADOR → EN_EJECUCION no es una transición válida."""
        proyecto = crear_proyecto_db(self.company, self.user, 'IE-PRY-002')
        url = f'/api/v1/projects/{proyecto.id}/iniciar-ejecucion/'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_iniciar_ejecucion_requiere_sync_sin_sync_falla(self):
        proyecto = crear_proyecto_db(
            self.company, self.user, 'IE-PRY-003',
            estado=ProjectStatus.PLANNED,
            sincronizado_con_saiopen=False,
        )
        ConfiguracionModulo.objects.create(
            company=self.company,
            requiere_sync_saiopen_para_ejecucion=True,
        )
        url = f'/api/v1/projects/{proyecto.id}/iniciar-ejecucion/'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_iniciar_ejecucion_requiere_sync_con_sync_exitoso(self):
        proyecto = crear_proyecto_db(
            self.company, self.user, 'IE-PRY-004',
            estado=ProjectStatus.PLANNED,
            sincronizado_con_saiopen=True,
        )
        ConfiguracionModulo.objects.create(
            company=self.company,
            requiere_sync_saiopen_para_ejecucion=True,
        )
        url = f'/api/v1/projects/{proyecto.id}/iniciar-ejecucion/'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_iniciar_ejecucion_establece_fecha_inicio_real(self):
        proyecto = crear_proyecto_db(
            self.company, self.user, 'IE-PRY-005',
            estado=ProjectStatus.PLANNED,
        )
        url = f'/api/v1/projects/{proyecto.id}/iniciar-ejecucion/'
        self.client.post(url)
        proyecto.refresh_from_db()
        self.assertIsNotNone(proyecto.fecha_inicio_real)

    def test_iniciar_ejecucion_proyecto_otra_empresa_404(self):
        c2 = crear_empresa('Otra PV', '912000002')
        u2 = crear_usuario(c2, 'gpv2@test.com')
        p2 = crear_proyecto_db(c2, u2, 'IE-PRY-006', estado=ProjectStatus.PLANNED)
        url = f'/api/v1/projects/{p2.id}/iniciar-ejecucion/'
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewer_no_puede_iniciar_ejecucion(self):
        viewer = crear_usuario(self.company, 'gviewer@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        proyecto = crear_proyecto_db(
            self.company, self.user, 'IE-PRY-007',
            estado=ProjectStatus.PLANNED,
        )
        url = f'/api/v1/projects/{proyecto.id}/iniciar-ejecucion/'
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])


class ProyectoFiltrosViewTest(APITestCase):

    def setUp(self):
        self.company = crear_empresa('Filtros Co', '912000003')
        self.user    = crear_usuario(self.company, 'gfiltros@test.com')
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/projects/'

    def test_filtrar_por_estado_planificado(self):
        crear_proyecto_db(
            self.company, self.user, 'FLT-PRY-001',
            estado=ProjectStatus.PLANNED,
        )
        crear_proyecto_db(
            self.company, self.user, 'FLT-PRY-002',
            estado=ProjectStatus.DRAFT,
        )
        resp = self.client.get(self.url, {'estado': 'planned'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        codigos = [p['codigo'] for p in resp.data['results']]
        self.assertIn('FLT-PRY-001', codigos)
        self.assertNotIn('FLT-PRY-002', codigos)

    def test_filtrar_por_tipo(self):
        crear_proyecto_db(
            self.company, self.user, 'FLT-PRY-003', tipo='services'
        )
        crear_proyecto_db(
            self.company, self.user, 'FLT-PRY-004', tipo='civil_works'
        )
        resp = self.client.get(self.url, {'tipo': 'services'})
        codigos = [p['codigo'] for p in resp.data['results']]
        self.assertIn('FLT-PRY-003', codigos)
        self.assertNotIn('FLT-PRY-004', codigos)

    def test_filtrar_por_cliente_id(self):
        crear_proyecto_db(
            self.company, self.user, 'FLT-PRY-005', cliente_id='CLI-999'
        )
        crear_proyecto_db(
            self.company, self.user, 'FLT-PRY-006', cliente_id='CLI-888'
        )
        resp = self.client.get(self.url, {'cliente_id': 'CLI-999'})
        codigos = [p['codigo'] for p in resp.data['results']]
        self.assertIn('FLT-PRY-005', codigos)
        self.assertNotIn('FLT-PRY-006', codigos)


class ConfiguracionModuloViewTest(APITestCase):

    def setUp(self):
        self.company = crear_empresa('Config View Co', '912000004')
        self.user    = crear_usuario(self.company, 'gcfgview@test.com')
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/projects/config/'

    def test_get_config_retorna_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('requiere_sync_saiopen_para_ejecucion', resp.data)
        self.assertIn('dias_alerta_vencimiento', resp.data)

    def test_get_config_valores_por_defecto(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['requiere_sync_saiopen_para_ejecucion'])
        self.assertEqual(resp.data['dias_alerta_vencimiento'], 15)

    def test_patch_config_actualiza_requiere_sync(self):
        resp = self.client.patch(
            self.url,
            {'requiere_sync_saiopen_para_ejecucion': True},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['requiere_sync_saiopen_para_ejecucion'])

    def test_patch_config_actualiza_dias_alerta(self):
        resp = self.client.patch(
            self.url, {'dias_alerta_vencimiento': 30}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['dias_alerta_vencimiento'], 30)

    def test_patch_persiste_en_db(self):
        self.client.patch(
            self.url, {'dias_alerta_vencimiento': 7}, format='json'
        )
        config = ConfiguracionModulo.objects.get(company=self.company)
        self.assertEqual(config.dias_alerta_vencimiento, 7)

    def test_viewer_puede_get_config(self):
        viewer = crear_usuario(self.company, 'gviewercfg@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
