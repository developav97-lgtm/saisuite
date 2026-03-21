"""
SaiSuite — Proyectos: Tests de Services
Cobertura objetivo: 80%+ en services.py
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito,
    EstadoProyecto, ConfiguracionModulo,
)
from apps.proyectos.services import (
    ProyectoService,
    FaseService,
    TerceroProyectoService,
    DocumentoContableService,
    HitoService,
    TransicionEstadoInvalidaException,
    PresupuestoExcedidoException,
    ProyectoNoEditableException,
    ProyectoException,
)
from rest_framework.exceptions import ValidationError

User = get_user_model()


def crear_empresa(nombre='Empresa Test', nit='900000001'):
    company = Company.objects.create(name=nombre, nit=nit)
    CompanyModule.objects.create(company=company, module='proyectos', is_active=True)
    return company


def crear_usuario(company, email='gerente@test.com', role='company_admin'):
    user = User.objects.create_user(
        email=email,
        password='test1234',
        company=company,
        role=role,
    )
    return user


def crear_proyecto(company, gerente, **kwargs):
    defaults = dict(
        codigo='PRY-001',
        nombre='Proyecto Test',
        tipo='obra_civil',
        cliente_id='900111222',
        cliente_nombre='Cliente Test',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000.00'),
    )
    defaults.update(kwargs)
    return Proyecto.all_objects.create(
        company=company, gerente=gerente, **defaults
    )


class ProyectoServiceCreateTest(TestCase):

    def setUp(self):
        self.company = crear_empresa()
        self.user    = crear_usuario(self.company)

    def test_create_proyecto_exitoso(self):
        data = {
            'nombre': 'Proyecto A',
            'tipo': 'obra_civil',
            'cliente_id': '900111',
            'cliente_nombre': 'Cliente A',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': Decimal('500000.00'),
            'gerente': self.user.id,
        }
        proyecto = ProyectoService.create_proyecto(data, self.user)
        self.assertIsNotNone(proyecto.id)
        self.assertEqual(proyecto.company, self.company)
        self.assertEqual(proyecto.gerente, self.user)
        self.assertTrue(proyecto.codigo.startswith('PRY-'))

    def test_create_proyecto_autocodigo(self):
        data = {
            'nombre': 'Sin codigo',
            'tipo': 'servicios',
            'cliente_id': '111',
            'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-06-30',
            'presupuesto_total': Decimal('100000.00'),
            'gerente': self.user.id,
        }
        proyecto = ProyectoService.create_proyecto(data, self.user)
        self.assertEqual(proyecto.codigo, 'PRY-001')

    def test_create_proyecto_gerente_otra_empresa(self):
        otra_empresa = crear_empresa('Otra', '900000002')
        otro_user    = crear_usuario(otra_empresa, email='otro@otro.com')
        data = {
            'nombre': 'X',
            'tipo': 'servicios',
            'cliente_id': '111',
            'cliente_nombre': 'X',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-06-30',
            'presupuesto_total': Decimal('100000.00'),
            'gerente': otro_user.id,
        }
        with self.assertRaises(ProyectoException):
            ProyectoService.create_proyecto(data, self.user)


class ProyectoServiceUpdateTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(self.company, self.user)

    def test_update_en_borrador(self):
        proyecto = ProyectoService.update_proyecto(
            self.proyecto, {'nombre': 'Nombre actualizado'}
        )
        self.assertEqual(proyecto.nombre, 'Nombre actualizado')

    def test_update_en_cerrado_falla(self):
        self.proyecto.estado = EstadoProyecto.CERRADO
        self.proyecto.save()
        with self.assertRaises(ProyectoNoEditableException):
            ProyectoService.update_proyecto(self.proyecto, {'nombre': 'X'})

    def test_soft_delete_cascada_fases(self):
        Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
        )
        ProyectoService.soft_delete_proyecto(self.proyecto)
        self.proyecto.refresh_from_db()
        self.assertFalse(self.proyecto.activo)
        self.assertEqual(
            Fase.all_objects.filter(proyecto=self.proyecto, activo=True).count(), 0
        )


class ProyectoServiceEstadoTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(self.company, self.user)

    def test_transicion_borrador_a_planificado_sin_fases(self):
        with self.assertRaises(TransicionEstadoInvalidaException):
            ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.PLANIFICADO)

    def test_transicion_borrador_a_planificado_exitosa(self):
        Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
        )
        proyecto = ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.PLANIFICADO)
        self.assertEqual(proyecto.estado, EstadoProyecto.PLANIFICADO)

    def test_transicion_planificado_a_ejecucion_sin_sync(self):
        # El service solo bloquea si ConfiguracionModulo.requiere_sync_saiopen_para_ejecucion=True
        ConfiguracionModulo.objects.create(
            company=self.company,
            requiere_sync_saiopen_para_ejecucion=True,
        )
        self.proyecto.estado = EstadoProyecto.PLANIFICADO
        self.proyecto.save()
        with self.assertRaises(TransicionEstadoInvalidaException):
            ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.EN_EJECUCION)

    def test_transicion_planificado_a_ejecucion_con_sync(self):
        self.proyecto.estado = EstadoProyecto.PLANIFICADO
        self.proyecto.sincronizado_con_saiopen = True
        self.proyecto.save()
        proyecto = ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.EN_EJECUCION)
        self.assertEqual(proyecto.estado, EstadoProyecto.EN_EJECUCION)
        self.assertIsNotNone(proyecto.fecha_inicio_real)

    def test_transicion_invalida(self):
        with self.assertRaises(TransicionEstadoInvalidaException):
            ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.CERRADO)

    def test_transicion_estado_terminal(self):
        self.proyecto.estado = EstadoProyecto.CERRADO
        self.proyecto.save()
        with self.assertRaises(TransicionEstadoInvalidaException):
            ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.BORRADOR)

    def test_cerrar_con_fases_incompletas_sin_forzar(self):
        self.proyecto.estado = EstadoProyecto.EN_EJECUCION
        self.proyecto.save()
        Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            porcentaje_avance=Decimal('50'),
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
        )
        with self.assertRaises(TransicionEstadoInvalidaException):
            ProyectoService.cambiar_estado(self.proyecto, EstadoProyecto.CERRADO, forzar=False)

    def test_cerrar_con_fases_incompletas_con_forzar(self):
        self.proyecto.estado = EstadoProyecto.EN_EJECUCION
        self.proyecto.save()
        Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            porcentaje_avance=Decimal('50'),
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
        )
        proyecto = ProyectoService.cambiar_estado(
            self.proyecto, EstadoProyecto.CERRADO, forzar=True
        )
        self.assertEqual(proyecto.estado, EstadoProyecto.CERRADO)


class FaseServiceTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(
            self.company, self.user, presupuesto_total=Decimal('1000000.00')
        )

    def _data_fase(self, **kwargs):
        defaults = dict(
            nombre='Fase Test',
            orden=1,
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
            presupuesto_mano_obra=Decimal('200000'),
            presupuesto_materiales=Decimal('100000'),
            presupuesto_subcontratos=Decimal('0'),
            presupuesto_equipos=Decimal('0'),
            presupuesto_otros=Decimal('0'),
        )
        defaults.update(kwargs)
        return defaults

    def test_crear_fase_exitosa(self):
        fase = FaseService.create_fase(self.proyecto, self._data_fase())
        self.assertIsNotNone(fase.id)
        self.assertEqual(fase.company, self.company)

    def test_crear_fase_excede_presupuesto(self):
        with self.assertRaises(PresupuestoExcedidoException):
            FaseService.create_fase(
                self.proyecto,
                self._data_fase(presupuesto_mano_obra=Decimal('1500000')),
            )

    def test_crear_multiples_fases_hasta_limite(self):
        # Cada fase tiene exactamente 500000 (sin presupuesto_materiales default)
        base = dict(presupuesto_materiales=Decimal('0'), presupuesto_subcontratos=Decimal('0'))
        FaseService.create_fase(self.proyecto, self._data_fase(orden=1, presupuesto_mano_obra=Decimal('500000'), **base))
        FaseService.create_fase(self.proyecto, self._data_fase(orden=2, nombre='Fase 2', presupuesto_mano_obra=Decimal('500000'), **base))
        # Ahora está al límite — agregar 1 peso más debe fallar
        with self.assertRaises(PresupuestoExcedidoException):
            FaseService.create_fase(self.proyecto, self._data_fase(orden=3, nombre='Fase 3', presupuesto_mano_obra=Decimal('1'), **base))

    def test_soft_delete_fase(self):
        fase = FaseService.create_fase(self.proyecto, self._data_fase())
        FaseService.soft_delete_fase(fase)
        fase.refresh_from_db()
        self.assertFalse(fase.activo)

    def test_update_fase_valida_presupuesto(self):
        fase = FaseService.create_fase(self.proyecto, self._data_fase(presupuesto_mano_obra=Decimal('400000')))
        # Actualizar a 600000 — aún dentro del presupuesto
        fase_actualizada = FaseService.update_fase(fase, {'presupuesto_mano_obra': Decimal('600000')})
        self.assertEqual(fase_actualizada.presupuesto_mano_obra, Decimal('600000'))

    def test_update_fase_excede_presupuesto(self):
        fase = FaseService.create_fase(self.proyecto, self._data_fase(presupuesto_mano_obra=Decimal('400000')))
        with self.assertRaises(PresupuestoExcedidoException):
            FaseService.update_fase(fase, {'presupuesto_mano_obra': Decimal('1500000')})

    def test_crear_fase_en_proyecto_cerrado(self):
        self.proyecto.estado = EstadoProyecto.CERRADO
        self.proyecto.save()
        with self.assertRaises(ProyectoNoEditableException):
            FaseService.create_fase(self.proyecto, self._data_fase())

    def test_crear_fase_sin_orden_autoincremental(self):
        data = self._data_fase()
        del data['orden']
        fase1 = FaseService.create_fase(self.proyecto, data.copy())
        data2 = self._data_fase(nombre='Fase 2')
        del data2['orden']
        fase2 = FaseService.create_fase(self.proyecto, data2)
        self.assertEqual(fase1.orden, 1)
        self.assertEqual(fase2.orden, 2)


class ProyectoServiceFinancieroTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(
            self.company, self.user, presupuesto_total=Decimal('1000000.00')
        )

    def test_estado_financiero_sin_fases(self):
        resultado = ProyectoService.get_estado_financiero(self.proyecto)
        self.assertIn('presupuesto_total', resultado)
        self.assertIn('costo_ejecutado', resultado)
        self.assertIn('aiu', resultado)
        self.assertEqual(resultado['presupuesto_costos'], '0')

    def test_estado_financiero_con_fases(self):
        Fase.all_objects.create(
            company=self.company,
            proyecto=self.proyecto,
            nombre='Fase 1',
            orden=1,
            fecha_inicio_planificada='2026-04-01',
            fecha_fin_planificada='2026-06-30',
            presupuesto_mano_obra=Decimal('400000'),
            presupuesto_materiales=Decimal('200000'),
        )
        resultado = ProyectoService.get_estado_financiero(self.proyecto)
        self.assertEqual(Decimal(resultado['presupuesto_costos']), Decimal('600000.00'))
        # AIU = 600000 * (1 + 0.10 + 0.05 + 0.10) = 600000 * 1.25 = 750000
        self.assertEqual(Decimal(resultado['precio_venta_aiu']), Decimal('750000.00'))


class MultiTenantTest(TestCase):
    """Verifica aislamiento de datos entre empresas."""

    def setUp(self):
        self.company_a = crear_empresa('Empresa A', '900000001')
        self.company_b = crear_empresa('Empresa B', '900000002')
        self.user_a    = crear_usuario(self.company_a, 'a@a.com')
        self.user_b    = crear_usuario(self.company_b, 'b@b.com')
        crear_proyecto(self.company_a, self.user_a, codigo='PRY-A')

    def test_empresa_b_no_ve_proyectos_empresa_a(self):
        """CompanyManager filtra automáticamente por company del thread local."""
        from apps.core import middleware as mw
        mw._thread_locals.company = self.company_b
        try:
            count = Proyecto.objects.filter(codigo='PRY-A').count()
            self.assertEqual(count, 0)
        finally:
            mw._thread_locals.company = None

    def test_all_objects_sin_filtro(self):
        """all_objects retorna todos los proyectos sin filtrar por empresa."""
        crear_proyecto(self.company_b, self.user_b, codigo='PRY-B')
        count = Proyecto.all_objects.count()
        self.assertGreaterEqual(count, 2)


# ══════════════════════════════════════════════
# Helpers Fase B
# ══════════════════════════════════════════════

def crear_fase(company, proyecto, orden=1, presupuesto_mano_obra=Decimal('200000'), **kwargs):
    defaults = dict(
        nombre=f'Fase {orden}',
        orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=presupuesto_mano_obra,
    )
    defaults.update(kwargs)
    return Fase.all_objects.create(company=company, proyecto=proyecto, **defaults)


def crear_documento(company, proyecto, fase=None, **kwargs):
    defaults = dict(
        saiopen_doc_id=f'DOC-{Decimal(str(id(kwargs)))}',
        tipo_documento='factura_compra',
        numero_documento='FC-001',
        fecha_documento='2026-05-01',
        tercero_id='900123456',
        tercero_nombre='Proveedor Test',
        valor_bruto=Decimal('100000'),
        valor_neto=Decimal('100000'),
    )
    defaults.update(kwargs)
    return DocumentoContable.all_objects.create(
        company=company, proyecto=proyecto, fase=fase, **defaults
    )


# ══════════════════════════════════════════════
# TerceroProyectoService Tests
# ══════════════════════════════════════════════

class TerceroProyectoServiceTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(
            self.company, self.user, presupuesto_total=Decimal('1000000')
        )

    def test_vincular_tercero_exitoso(self):
        tercero = TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '900111',
            'tercero_nombre': 'Subcontratista SA',
            'rol': 'subcontratista',
            'fase': None,
        })
        self.assertIsNotNone(tercero.id)
        self.assertEqual(tercero.proyecto, self.proyecto)
        self.assertEqual(tercero.company, self.company)

    def test_vincular_mismo_tercero_dos_roles_distintos(self):
        """Un tercero puede tener múltiples roles en el mismo proyecto."""
        TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '900111',
            'tercero_nombre': 'Empresa XYZ',
            'rol': 'subcontratista',
            'fase': None,
        })
        # Mismo tercero, rol distinto — debe funcionar
        tercero2 = TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '900111',
            'tercero_nombre': 'Empresa XYZ',
            'rol': 'proveedor',
            'fase': None,
        })
        self.assertIsNotNone(tercero2.id)

    def test_vincular_tercero_duplicado_falla(self):
        """Mismo tercero + mismo rol + misma fase = error unique_together."""
        data = {
            'tercero_id': '900111',
            'tercero_nombre': 'Empresa XYZ',
            'rol': 'subcontratista',
            'fase': None,
        }
        TerceroProyectoService.vincular_tercero(self.proyecto, data.copy())
        with self.assertRaises(ValidationError):
            TerceroProyectoService.vincular_tercero(self.proyecto, data.copy())

    def test_desvincular_tercero_soft_delete(self):
        tercero = TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '900222',
            'tercero_nombre': 'Consultor Test',
            'rol': 'consultor',
            'fase': None,
        })
        TerceroProyectoService.desvincular_tercero(tercero)
        tercero.refresh_from_db()
        self.assertFalse(tercero.activo)

    def test_list_terceros_solo_activos(self):
        """list_terceros no retorna terceros desvinculados."""
        t1 = TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '111', 'tercero_nombre': 'A', 'rol': 'cliente', 'fase': None,
        })
        t2 = TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '222', 'tercero_nombre': 'B', 'rol': 'proveedor', 'fase': None,
        })
        TerceroProyectoService.desvincular_tercero(t2)
        qs = TerceroProyectoService.list_terceros(self.proyecto)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().id, t1.id)

    def test_vincular_tercero_con_fase(self):
        """Un tercero puede vincularse a una fase específica."""
        fase = crear_fase(self.company, self.proyecto)
        tercero = TerceroProyectoService.vincular_tercero(self.proyecto, {
            'tercero_id': '900333',
            'tercero_nombre': 'Interventor',
            'rol': 'interventor',
            'fase': fase,
        })
        self.assertEqual(tercero.fase, fase)


# ══════════════════════════════════════════════
# DocumentoContableService Tests
# ══════════════════════════════════════════════

class DocumentoContableServiceTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(
            self.company, self.user, presupuesto_total=Decimal('1000000')
        )
        self.fase1 = crear_fase(self.company, self.proyecto, orden=1)
        self.fase2 = crear_fase(self.company, self.proyecto, orden=2, nombre='Fase 2')

    def test_list_documentos_del_proyecto(self):
        crear_documento(self.company, self.proyecto, saiopen_doc_id='DOC-001')
        crear_documento(self.company, self.proyecto, saiopen_doc_id='DOC-002')
        qs = DocumentoContableService.list_documentos(self.proyecto)
        self.assertEqual(qs.count(), 2)

    def test_list_documentos_filtrado_por_fase(self):
        crear_documento(self.company, self.proyecto, fase=self.fase1, saiopen_doc_id='DOC-F1')
        crear_documento(self.company, self.proyecto, fase=self.fase2, saiopen_doc_id='DOC-F2')
        qs = DocumentoContableService.list_documentos(self.proyecto, fase_id=self.fase1.id)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().saiopen_doc_id, 'DOC-F1')

    def test_list_documentos_no_incluye_otro_proyecto(self):
        """Documentos de otro proyecto no aparecen en el listado."""
        otro_user     = crear_usuario(self.company, email='otro@test.com')
        otro_proyecto = crear_proyecto(
            self.company, otro_user, codigo='PRY-002', presupuesto_total=Decimal('500000')
        )
        crear_documento(self.company, self.proyecto,    saiopen_doc_id='DOC-MIO')
        crear_documento(self.company, otro_proyecto, saiopen_doc_id='DOC-OTRO')
        qs = DocumentoContableService.list_documentos(self.proyecto)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().saiopen_doc_id, 'DOC-MIO')

    def test_get_documento(self):
        doc = crear_documento(self.company, self.proyecto, saiopen_doc_id='DOC-GET')
        resultado = DocumentoContableService.get_documento(str(doc.id))
        self.assertEqual(resultado.id, doc.id)


# ══════════════════════════════════════════════
# HitoService Tests
# ══════════════════════════════════════════════

class HitoServiceTest(TestCase):

    def setUp(self):
        self.company  = crear_empresa()
        self.user     = crear_usuario(self.company)
        self.proyecto = crear_proyecto(
            self.company, self.user, presupuesto_total=Decimal('1000000')
        )

    def _data_hito(self, **kwargs):
        defaults = dict(
            nombre='Hito Test',
            descripcion='',
            porcentaje_proyecto=Decimal('25.00'),
            valor_facturar=Decimal('250000.00'),
            facturable=True,
            fase=None,
        )
        defaults.update(kwargs)
        return defaults

    def test_crear_hito_exitoso(self):
        hito = HitoService.create_hito(self.proyecto, self._data_hito())
        self.assertIsNotNone(hito.id)
        self.assertEqual(hito.proyecto, self.proyecto)
        self.assertFalse(hito.facturado)

    def test_crear_hito_porcentaje_total_100(self):
        """Cuatro hitos de 25% — el quinto debe fallar."""
        for i in range(4):
            HitoService.create_hito(
                self.proyecto,
                self._data_hito(nombre=f'Hito {i}', porcentaje_proyecto=Decimal('25.00')),
            )
        with self.assertRaises(ValidationError):
            HitoService.create_hito(
                self.proyecto,
                self._data_hito(nombre='Hito 5', porcentaje_proyecto=Decimal('1.00')),
            )

    def test_crear_hito_porcentaje_exactamente_100(self):
        """Un hito de 100% es válido."""
        hito = HitoService.create_hito(
            self.proyecto,
            self._data_hito(porcentaje_proyecto=Decimal('100.00')),
        )
        self.assertIsNotNone(hito.id)

    def test_crear_hito_supera_100_falla(self):
        HitoService.create_hito(
            self.proyecto,
            self._data_hito(porcentaje_proyecto=Decimal('80.00')),
        )
        with self.assertRaises(ValidationError):
            HitoService.create_hito(
                self.proyecto,
                self._data_hito(nombre='Hito 2', porcentaje_proyecto=Decimal('30.00')),
            )

    def test_generar_factura_exitosa(self):
        self.proyecto.sincronizado_con_saiopen = True
        self.proyecto.save()
        hito = HitoService.create_hito(self.proyecto, self._data_hito())
        hito_actualizado = HitoService.generar_factura(hito, self.user)
        self.assertTrue(hito_actualizado.facturado)
        self.assertIsNotNone(hito_actualizado.fecha_facturacion)

    def test_generar_factura_sin_sync_saiopen_falla(self):
        """No se puede facturar si el proyecto no está sincronizado."""
        hito = HitoService.create_hito(self.proyecto, self._data_hito())
        with self.assertRaises(ValidationError):
            HitoService.generar_factura(hito, self.user)

    def test_generar_factura_hito_ya_facturado_falla(self):
        self.proyecto.sincronizado_con_saiopen = True
        self.proyecto.save()
        hito = HitoService.create_hito(self.proyecto, self._data_hito())
        HitoService.generar_factura(hito, self.user)
        hito.refresh_from_db()
        with self.assertRaises(ValidationError):
            HitoService.generar_factura(hito, self.user)

    def test_generar_factura_hito_no_facturable_falla(self):
        self.proyecto.sincronizado_con_saiopen = True
        self.proyecto.save()
        hito = HitoService.create_hito(
            self.proyecto, self._data_hito(facturable=False)
        )
        with self.assertRaises(ValidationError):
            HitoService.generar_factura(hito, self.user)

    def test_list_hitos_del_proyecto(self):
        HitoService.create_hito(self.proyecto, self._data_hito(nombre='H1', porcentaje_proyecto=Decimal('30')))
        HitoService.create_hito(self.proyecto, self._data_hito(nombre='H2', porcentaje_proyecto=Decimal('20')))
        qs = HitoService.list_hitos(self.proyecto)
        self.assertEqual(qs.count(), 2)
