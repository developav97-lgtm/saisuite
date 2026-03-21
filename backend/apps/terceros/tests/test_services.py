"""
SaiSuite — Tests de services Tercero.
Cobertura objetivo: 80%+ en services.py
"""
import pytest
from apps.terceros.models import Tercero, TerceroDireccion
from apps.terceros.services import TerceroService, TerceroDireccionService


def make_tercero_data(**kwargs):
    """Datos mínimos válidos para crear un Tercero."""
    defaults = dict(
        tipo_identificacion='cc',
        numero_identificacion='1234567890',
        primer_nombre='Juan',
        primer_apellido='Pérez',
        tipo_persona='natural',
        tipo_tercero='cliente',
    )
    defaults.update(kwargs)
    return defaults


def make_direccion_data(**kwargs):
    """Datos mínimos válidos para crear una TerceroDireccion."""
    defaults = dict(
        tipo='principal',
        departamento='Valle del Cauca',
        ciudad='Cali',
        direccion_linea1='Calle 5 # 12-34',
    )
    defaults.update(kwargs)
    return defaults


@pytest.mark.django_db
class TestTerceroServiceCreate:

    def test_create_genera_codigo_automatico(self, company):
        """create() genera código automáticamente si no se proporciona."""
        data = make_tercero_data()
        t = TerceroService.create(company, data)
        assert t.codigo is not None
        assert len(t.codigo) > 0

    def test_create_usa_codigo_proporcionado(self, company):
        """create() respeta el código si el usuario lo pasa."""
        data = make_tercero_data(codigo='MI-001')
        t = TerceroService.create(company, data)
        assert t.codigo == 'MI-001'

    def test_create_persona_natural(self, company):
        """create() crea persona natural correctamente."""
        data = make_tercero_data()
        t = TerceroService.create(company, data)
        assert t.id is not None
        assert t.nombre_completo == 'Juan Pérez'
        assert t.company_id == company.id

    def test_create_persona_juridica(self, company):
        """create() crea persona jurídica con razon_social."""
        data = dict(
            tipo_identificacion='nit',
            numero_identificacion='900123456',
            razon_social='Empresa XYZ S.A.S.',
            tipo_persona='juridica',
            tipo_tercero='proveedor',
        )
        t = TerceroService.create(company, data)
        assert t.nombre_completo == 'Empresa XYZ S.A.S.'

    def test_create_codigo_secuencial_si_no_hay_consecutivo(self, company):
        """Sin consecutivo_id, el código sigue formato TER-XXXX."""
        data = make_tercero_data()
        t = TerceroService.create(company, data)
        assert t.codigo.startswith('TER-')


@pytest.mark.django_db
class TestTerceroServiceList:

    @pytest.fixture(autouse=True)
    def setup(self, company):
        self.company = company
        self.t1 = TerceroService.create(company, make_tercero_data(
            numero_identificacion='1111111111',
            primer_nombre='Ana',
            tipo_tercero='cliente',
        ))
        self.t2 = TerceroService.create(company, make_tercero_data(
            numero_identificacion='2222222222',
            primer_nombre='Carlos',
            tipo_tercero='proveedor',
        ))

    def test_list_sin_filtros_retorna_todos(self):
        qs = TerceroService.list(self.company)
        assert qs.count() == 2

    def test_list_filtro_por_tipo_tercero(self):
        qs = TerceroService.list(self.company, tipo_tercero='cliente')
        assert qs.count() == 1
        assert qs.first().primer_nombre == 'Ana'

    def test_list_filtro_por_search_nombre(self):
        qs = TerceroService.list(self.company, search='Carlos')
        assert qs.count() == 1

    def test_list_filtro_por_search_identificacion(self):
        qs = TerceroService.list(self.company, search='1111111111')
        assert qs.count() == 1

    def test_list_filtro_activo(self):
        TerceroService.delete(self.t1)
        qs_activos = TerceroService.list(self.company, activo=True)
        qs_inactivos = TerceroService.list(self.company, activo=False)
        assert qs_activos.count() == 1
        assert qs_inactivos.count() == 1

    def test_list_aislamiento_por_empresa(self, company2):
        """No deben filtrarse terceros de otra empresa."""
        qs = TerceroService.list(company2)
        assert qs.count() == 0


@pytest.mark.django_db
class TestTerceroServiceUpdate:

    def test_update_campos_simples(self, company):
        """update() modifica campos correctamente."""
        t = TerceroService.create(company, make_tercero_data())
        t = TerceroService.update(t, {'email': 'nuevo@test.com', 'celular': '3101234567'})
        assert t.email == 'nuevo@test.com'
        assert t.celular == '3101234567'

    def test_update_recalcula_nombre_completo(self, company):
        """update() con cambio de nombre recalcula nombre_completo al guardar."""
        t = TerceroService.create(company, make_tercero_data())
        t = TerceroService.update(t, {'segundo_nombre': 'Alberto'})
        assert 'Alberto' in t.nombre_completo


@pytest.mark.django_db
class TestTerceroServiceDelete:

    def test_delete_desactiva_en_lugar_de_eliminar(self, company):
        """delete() hace soft-delete: activo=False."""
        t = TerceroService.create(company, make_tercero_data())
        TerceroService.delete(t)
        t.refresh_from_db()
        assert t.activo is False
        assert Tercero.all_objects.filter(id=t.id).exists()


@pytest.mark.django_db
class TestTerceroDireccionService:

    @pytest.fixture
    def tercero(self, company):
        return TerceroService.create(company, make_tercero_data())

    def test_create_direccion(self, tercero):
        """create() crea dirección asociada al tercero."""
        d = TerceroDireccionService.create(tercero, make_direccion_data())
        assert d.id is not None
        assert d.tercero_id == tercero.id

    def test_create_direccion_principal_desactiva_anterior(self, tercero):
        """Al crear dirección principal, la anterior pierde es_principal=True."""
        d1 = TerceroDireccionService.create(tercero, make_direccion_data(es_principal=True))
        assert d1.es_principal is True

        d2 = TerceroDireccionService.create(
            tercero, make_direccion_data(ciudad='Bogotá', es_principal=True)
        )
        d1.refresh_from_db()
        assert d1.es_principal is False
        assert d2.es_principal is True

    def test_list_by_tercero(self, tercero):
        """list_by_tercero() retorna todas las direcciones del tercero."""
        TerceroDireccionService.create(tercero, make_direccion_data(ciudad='Cali'))
        TerceroDireccionService.create(tercero, make_direccion_data(ciudad='Bogotá', tipo='sucursal'))
        result = TerceroDireccionService.list_by_tercero(str(tercero.id), tercero.company)
        assert len(result) == 2

    def test_update_direccion(self, tercero):
        """update() modifica campos de la dirección."""
        d = TerceroDireccionService.create(tercero, make_direccion_data())
        d = TerceroDireccionService.update(d, {'ciudad': 'Medellín'})
        assert d.ciudad == 'Medellín'

    def test_update_a_principal_desactiva_otras(self, tercero):
        """Actualizar es_principal=True desactiva la principal anterior."""
        d1 = TerceroDireccionService.create(tercero, make_direccion_data(es_principal=True))
        d2 = TerceroDireccionService.create(tercero, make_direccion_data(ciudad='Bogotá'))

        TerceroDireccionService.update(d2, {'es_principal': True})
        d1.refresh_from_db()
        assert d1.es_principal is False
        assert d2.es_principal is True

    def test_delete_direccion(self, tercero):
        """delete() elimina físicamente la dirección."""
        d = TerceroDireccionService.create(tercero, make_direccion_data())
        dir_id = d.id
        TerceroDireccionService.delete(d)
        assert not TerceroDireccion.objects.filter(id=dir_id).exists()
