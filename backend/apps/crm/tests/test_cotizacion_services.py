"""
SaiSuite — CRM Tests: Cotización Services
"""
import pytest
from decimal import Decimal
from unittest.mock import patch

from apps.crm.models import (
    CrmPipeline, CrmEtapa, CrmOportunidad, CrmImpuesto, CrmProducto,
    CrmCotizacion, CrmLineaCotizacion, EstadoCotizacion,
)
from apps.crm.cotizacion_services import CotizacionService, SyncCotizacionService
from apps.crm.producto_services import ImpuestoSyncService, ProductoSyncService


@pytest.fixture
def company(db):
    from apps.companies.models import Company
    return Company.objects.create(name='Cot Test Co', nit='900001002')


@pytest.fixture
def pipeline(db, company):
    return CrmPipeline.all_objects.create(company=company, nombre='Pipeline', es_default=True)


@pytest.fixture
def etapa(db, pipeline):
    return CrmEtapa.all_objects.create(
        company=pipeline.company, pipeline=pipeline,
        nombre='Propuesta', orden=3, probabilidad=Decimal('50'),
    )


@pytest.fixture
def oportunidad(db, company, pipeline, etapa):
    return CrmOportunidad.all_objects.create(
        company=company, titulo='Op Test',
        pipeline=pipeline, etapa=etapa,
        valor_esperado=Decimal('5000000'), probabilidad=Decimal('50'),
    )


@pytest.fixture
def impuesto(db, company):
    return CrmImpuesto.all_objects.create(
        company=company, nombre='IVA 19%', porcentaje=Decimal('0.19'),
    )


@pytest.fixture
def producto(db, company, impuesto):
    return CrmProducto.all_objects.create(
        company=company, codigo='PROD001', nombre='Producto Test',
        precio_base=Decimal('100000'), impuesto=impuesto, sai_key='PROD001',
    )


@pytest.fixture
def cotizacion(db, oportunidad):
    return CotizacionService.create(oportunidad, {'titulo': 'Cotización Test'})


@pytest.mark.django_db
class TestCotizacionService:

    def test_create_cotizacion(self, oportunidad):
        cot = CotizacionService.create(oportunidad, {'titulo': 'Test Cot'})
        assert cot.estado == EstadoCotizacion.BORRADOR
        assert cot.numero_interno.startswith('COT-')

    def test_add_linea_calcula_totales(self, cotizacion, producto, impuesto):
        linea = CotizacionService.add_linea(cotizacion, {
            'producto': producto,
            'descripcion': 'Producto Test',
            'cantidad': Decimal('2'),
            'vlr_unitario': Decimal('100000'),
            'descuento_p': Decimal('0'),
            'impuesto': impuesto,
        })
        cotizacion.refresh_from_db()
        # 2 × 100000 = 200000 base + 19% IVA = 238000
        assert linea.iva_valor == Decimal('38000.00')
        assert linea.total_parcial == Decimal('238000.00')
        assert cotizacion.subtotal == Decimal('238000.00')
        assert cotizacion.total == Decimal('238000.00')

    def test_add_linea_con_descuento(self, cotizacion, impuesto):
        linea = CotizacionService.add_linea(cotizacion, {
            'descripcion': 'Servicio X',
            'cantidad': Decimal('1'),
            'vlr_unitario': Decimal('100000'),
            'descuento_p': Decimal('10'),
            'impuesto': impuesto,
        })
        # base = 100000, dto 10% = 90000, IVA 19% = 17100, total = 107100
        assert linea.total_parcial == Decimal('107100.00')

    def test_no_add_linea_en_cotizacion_enviada(self, cotizacion):
        cotizacion.estado = EstadoCotizacion.ENVIADA
        cotizacion.save()
        with pytest.raises(ValueError, match='borrador'):
            CotizacionService.add_linea(cotizacion, {
                'descripcion': 'X', 'cantidad': 1, 'vlr_unitario': 0,
            })

    def test_enviar_cotizacion(self, cotizacion, producto, impuesto):
        CotizacionService.add_linea(cotizacion, {
            'descripcion': 'Item', 'cantidad': 1,
            'vlr_unitario': Decimal('50000'), 'impuesto': impuesto,
        })
        with patch('apps.crm.cotizacion_services.CotizacionService._enviar_pdf_email'):
            cot = CotizacionService.enviar(cotizacion)
        assert cot.estado == EstadoCotizacion.ENVIADA
        assert cot.fecha_vencimiento is not None

    def test_aceptar_cotizacion_push_sqs(self, cotizacion):
        with patch('apps.crm.cotizacion_services.SyncCotizacionService.push_to_saiopen') as mock_sqs:
            cot = CotizacionService.aceptar(cotizacion)
        assert cot.estado == EstadoCotizacion.ACEPTADA
        mock_sqs.assert_called_once_with(cotizacion)

    def test_rechazar_cotizacion(self, cotizacion):
        cot = CotizacionService.rechazar(cotizacion)
        assert cot.estado == EstadoCotizacion.RECHAZADA

    def test_delete_solo_borrador_o_rechazada(self, cotizacion):
        cotizacion.estado = EstadoCotizacion.ENVIADA
        cotizacion.save()
        with pytest.raises(ValueError):
            CotizacionService.delete(cotizacion)

    def test_descuento_adicional_recalcula_total(self, cotizacion, impuesto):
        CotizacionService.add_linea(cotizacion, {
            'descripcion': 'Item', 'cantidad': 1,
            'vlr_unitario': Decimal('100000'), 'impuesto': impuesto,
        })
        CotizacionService.update(cotizacion, {'descuento_adicional_p': Decimal('5')})
        cotizacion.refresh_from_db()
        # subtotal = 119000 (con IVA en linea), dcto 5% = 5950
        assert cotizacion.descuento_adicional_val > 0
        assert cotizacion.total < cotizacion.subtotal

    def test_sync_confirmacion(self, cotizacion):
        SyncCotizacionService.recibir_confirmacion(
            cotizacion_id=str(cotizacion.id),
            sai_numero=1042, sai_tipo='COT', sai_empresa=1, sai_sucursal=1,
        )
        cotizacion.refresh_from_db()
        assert cotizacion.sai_key == '1042_COT_1_1'
        assert cotizacion.saiopen_synced is True


@pytest.mark.django_db
class TestProductoSyncService:

    def test_sync_impuestos(self, company):
        resultado = ImpuestoSyncService.sync_from_payload(company, [
            {'codigo': 1, 'authority': 'IVA 19%', 'rate': 0.19},
            {'codigo': 2, 'authority': 'IVA 5%', 'rate': 0.05},
        ])
        assert resultado['creados'] == 2
        assert CrmImpuesto.all_objects.filter(company=company).count() == 2

    def test_sync_impuestos_idempotente(self, company):
        ImpuestoSyncService.sync_from_payload(company, [
            {'codigo': 1, 'authority': 'IVA 19%', 'rate': 0.19},
        ])
        ImpuestoSyncService.sync_from_payload(company, [
            {'codigo': 1, 'authority': 'IVA 19% actualizado', 'rate': 0.19},
        ])
        assert CrmImpuesto.all_objects.filter(company=company).count() == 1

    def test_sync_productos(self, company, impuesto):
        resultado = ProductoSyncService.sync_from_payload(company, [
            {'item': 'PROD001', 'descripcion': 'Producto 1', 'price': 50000, 'estado': 'True'},
            {'item': 'PROD002', 'descripcion': 'Producto 2', 'price': 80000, 'estado': 'True'},
        ])
        assert resultado['creados'] == 2
        assert CrmProducto.all_objects.filter(company=company).count() == 2
