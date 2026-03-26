"""
SaiSuite — Proyectos: Tests de Views (endpoints)
"""
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito, EstadoProyecto,
)

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
        tipo='civil_works',
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
        self.url = '/api/v1/projects/'

    def test_listar_proyectos(self):
        crear_proyecto_db(self.company, self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_crear_proyecto(self):
        data = {
            'nombre': 'Nuevo Proyecto',
            'tipo': 'services',
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
            'nombre': 'X', 'tipo': 'services', 'cliente_id': '1',
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
        self.url = f'/api/v1/projects/{self.proyecto.id}/'

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
        self.url = f'/api/v1/projects/{self.proyecto.id}/cambiar-estado/'

    def test_cambiar_a_planificado_sin_fases(self):
        resp = self.client.post(self.url, {'nuevo_estado': 'planned'}, format='json')
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
        resp = self.client.post(self.url, {'nuevo_estado': 'planned'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'planned')

    def test_estado_invalido(self):
        resp = self.client.post(self.url, {'nuevo_estado': 'inexistente'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class EstadoFinancieroActionTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/estado-financiero/'

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
        self.url = f'/api/v1/projects/{self.proyecto.id}/phases/'

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
        self.url = f'/api/v1/projects/phases/{self.fase.id}/'

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


# ══════════════════════════════════════════════
# Fase B — TerceroProyecto
# ══════════════════════════════════════════════

def crear_fase_db(company, proyecto, orden=1, **kwargs):
    defaults = dict(
        nombre=f'Fase {orden}',
        orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('200000'),
    )
    defaults.update(kwargs)
    return Fase.all_objects.create(company=company, proyecto=proyecto, **defaults)


def crear_documento_db(company, proyecto, fase=None, saiopen_doc_id='DOC-001', **kwargs):
    defaults = dict(
        tipo_documento='purchase_invoice',
        numero_documento='FC-001',
        fecha_documento='2026-05-01',
        tercero_id='900123456',
        tercero_nombre='Proveedor Test',
        valor_bruto=Decimal('100000'),
        valor_neto=Decimal('100000'),
    )
    defaults.update(kwargs)
    return DocumentoContable.all_objects.create(
        company=company, proyecto=proyecto, fase=fase,
        saiopen_doc_id=saiopen_doc_id, **defaults,
    )


class TerceroProyectoViewTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/stakeholders/'

    def test_listar_terceros_vacio(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_vincular_tercero(self):
        data = {
            'tercero_id': '900111',
            'tercero_nombre': 'Subcontratista SA',
            'rol': 'subcontractor',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['tercero_id'], '900111')
        self.assertEqual(resp.data['rol'], 'subcontractor')

    def test_vincular_tercero_sin_rol_falla(self):
        data = {'tercero_id': '900111', 'tercero_nombre': 'X'}
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_terceros_muestra_vinculados(self):
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='111', tercero_nombre='A', rol='client',
        )
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.data), 1)

    def test_desvincular_tercero(self):
        tercero = TerceroProyecto.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            tercero_id='999', tercero_nombre='Del', rol='vendor',
        )
        url_delete = f'{self.url}{tercero.id}/'
        resp = self.client.delete(url_delete)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        tercero.refresh_from_db()
        self.assertFalse(tercero.activo)

    def test_viewer_puede_listar_terceros(self):
        """Viewer tiene acceso de solo lectura."""
        viewer = crear_usuario(self.company, 'viewer@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_no_puede_vincular(self):
        viewer = crear_usuario(self.company, 'viewer@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        data = {'tercero_id': '111', 'tercero_nombre': 'X', 'rol': 'client'}
        resp = self.client.post(self.url, data, format='json')
        self.assertIn(resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])

    def test_vincular_con_fase(self):
        fase = crear_fase_db(self.company, self.proyecto)
        data = {
            'tercero_id': '900222',
            'tercero_nombre': 'Interventor',
            'rol': 'inspector',
            'fase': str(fase.id),
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(resp.data['fase']), str(fase.id))

    def test_aislamiento_proyecto(self):
        """No se deben ver terceros de otro proyecto."""
        otro_user     = crear_usuario(self.company, 'otro@test.com')
        otro_proyecto = crear_proyecto_db(self.company, otro_user, codigo='PRY-002')
        TerceroProyecto.all_objects.create(
            company=self.company, proyecto=otro_proyecto,
            tercero_id='888', tercero_nombre='Ajeno', rol='vendor',
        )
        resp = self.client.get(self.url)
        ids = [t['tercero_id'] for t in resp.data]
        self.assertNotIn('888', ids)


# ══════════════════════════════════════════════
# Fase B — DocumentoContable
# ══════════════════════════════════════════════

class DocumentoContableViewTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(self.company, self.user)
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/documents/'

    def test_listar_documentos_vacio(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_listar_documentos(self):
        crear_documento_db(self.company, self.proyecto, saiopen_doc_id='DOC-A')
        crear_documento_db(self.company, self.proyecto, saiopen_doc_id='DOC-B')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_no_permite_crear_documento(self):
        """Los documentos son solo lectura (los crea el agente Go)."""
        data = {
            'tipo_documento': 'purchase_invoice',
            'numero_documento': 'FC-999',
            'fecha_documento': '2026-06-01',
        }
        resp = self.client.post(self.url, data, format='json')
        # Debe retornar 405 Method Not Allowed
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_obtener_detalle_documento(self):
        doc = crear_documento_db(self.company, self.proyecto, saiopen_doc_id='DOC-DET')
        resp = self.client.get(f'{self.url}{doc.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['saiopen_doc_id'], 'DOC-DET')
        # Detalle incluye campos adicionales
        self.assertIn('valor_bruto', resp.data)
        self.assertIn('valor_descuento', resp.data)

    def test_filtrar_documentos_por_fase(self):
        fase1 = crear_fase_db(self.company, self.proyecto, orden=1)
        fase2 = crear_fase_db(self.company, self.proyecto, orden=2, nombre='Fase 2')
        crear_documento_db(self.company, self.proyecto, fase=fase1, saiopen_doc_id='DOC-F1')
        crear_documento_db(self.company, self.proyecto, fase=fase2, saiopen_doc_id='DOC-F2')
        resp = self.client.get(self.url, {'fase': str(fase1.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['saiopen_doc_id'], 'DOC-F1')  # type: ignore[index]

    def test_aislamiento_proyecto(self):
        otro_user     = crear_usuario(self.company, 'otro2@test.com')
        otro_proyecto = crear_proyecto_db(self.company, otro_user, codigo='PRY-003')
        crear_documento_db(self.company, otro_proyecto, saiopen_doc_id='DOC-OTRO')
        resp = self.client.get(self.url)
        saiopen_ids = [d['saiopen_doc_id'] for d in resp.data]  # type: ignore[index]
        self.assertNotIn('DOC-OTRO', saiopen_ids)

    def test_viewer_puede_ver_documentos(self):
        viewer = crear_usuario(self.company, 'viewer3@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ══════════════════════════════════════════════
# Fase B — Hito
# ══════════════════════════════════════════════

class HitoViewTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(
            self.company, self.user, presupuesto_total=Decimal('1000000')
        )
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/milestones/'

    def test_listar_hitos_vacio(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_crear_hito(self):
        data = {
            'nombre': 'Hito 1',
            'porcentaje_proyecto': '25.00',
            'valor_facturar': '250000.00',
            'facturable': True,
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['nombre'], 'Hito 1')
        self.assertFalse(resp.data['facturado'])

    def test_crear_hito_porcentaje_cero_falla(self):
        data = {
            'nombre': 'Hito Malo',
            'porcentaje_proyecto': '0',
            'valor_facturar': '100000.00',
            'facturable': True,
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_hito_valor_cero_falla(self):
        data = {
            'nombre': 'Hito Malo',
            'porcentaje_proyecto': '10',
            'valor_facturar': '0',
            'facturable': True,
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_hito_porcentaje_supera_100_falla(self):
        Hito.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            nombre='H Existente', porcentaje_proyecto=Decimal('80'),
            valor_facturar=Decimal('800000'), facturable=True,
        )
        data = {
            'nombre': 'Hito Extra',
            'porcentaje_proyecto': '30',
            'valor_facturar': '300000.00',
            'facturable': True,
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_hitos_muestra_creados(self):
        Hito.all_objects.create(
            company=self.company, proyecto=self.proyecto,
            nombre='H1', porcentaje_proyecto=Decimal('50'),
            valor_facturar=Decimal('500000'), facturable=True,
        )
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.data), 1)

    def test_viewer_puede_listar_hitos(self):
        viewer = crear_usuario(self.company, 'viewer4@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_no_puede_crear_hito(self):
        viewer = crear_usuario(self.company, 'viewer5@test.com', role='viewer')
        self.client.force_authenticate(user=viewer)
        data = {
            'nombre': 'X', 'porcentaje_proyecto': '10',
            'valor_facturar': '100000', 'facturable': True,
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertIn(resp.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED])


class GenerarFacturaViewTest(APITestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto_db(
            self.company, self.user, presupuesto_total=Decimal('1000000'),
            sincronizado_con_saiopen=True,
        )
        self.hito = Hito.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Hito Facturable',
            porcentaje_proyecto=Decimal('25'),
            valor_facturar=Decimal('250000'),
            facturable=True,
        )
        self.client.force_authenticate(user=self.user)
        self.url = f'/api/v1/projects/{self.proyecto.id}/milestones/{self.hito.id}/generate-invoice/'

    def test_generar_factura_exitosa(self):
        resp = self.client.post(self.url, {'confirmar': True}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['facturado'])
        self.assertIsNotNone(resp.data['fecha_facturacion'])

    def test_generar_factura_sin_confirmar_falla(self):
        resp = self.client.post(self.url, {'confirmar': False}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generar_factura_sin_payload_falla(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generar_factura_segunda_vez_falla(self):
        self.client.post(self.url, {'confirmar': True}, format='json')
        resp = self.client.post(self.url, {'confirmar': True}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generar_factura_sin_sync_saiopen_falla(self):
        self.proyecto.sincronizado_con_saiopen = False
        self.proyecto.save()
        resp = self.client.post(self.url, {'confirmar': True}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
