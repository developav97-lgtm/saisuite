"""
SaiSuite — Tests de modelos Tercero y TerceroDireccion.
Cobertura objetivo: 85%+ en models.py
"""
import pytest
from django.db import IntegrityError
from apps.terceros.models import Tercero, TerceroDireccion


def make_tercero(company, numero_identificacion='1234567890', **kwargs):
    """Helper para crear un Tercero con valores mínimos."""
    defaults = dict(
        tipo_identificacion='cc',
        numero_identificacion=numero_identificacion,
        primer_nombre='Juan',
        primer_apellido='Pérez',
        tipo_persona='natural',
        tipo_tercero='cliente',
        codigo=f'CLI-{numero_identificacion[-4:]}',
    )
    defaults.update(kwargs)
    return Tercero.objects.create(company=company, **defaults)


def make_direccion(tercero, es_principal=False, ciudad='Cali', **kwargs):
    """Helper para crear una TerceroDireccion."""
    defaults = dict(
        tipo='principal',
        departamento='Valle del Cauca',
        ciudad=ciudad,
        direccion_linea1='Calle 5 # 12-34',
        es_principal=es_principal,
    )
    defaults.update(kwargs)
    return TerceroDireccion.objects.create(
        tercero=tercero,
        company=tercero.company,
        **defaults,
    )


@pytest.mark.django_db
class TestTerceroModel:

    def test_crear_persona_natural_completo(self, company):
        """Crea persona natural con todos los campos de nombre."""
        t = make_tercero(
            company,
            segundo_nombre='Carlos',
            segundo_apellido='González',
        )
        assert t.id is not None
        assert t.nombre_completo == 'Juan Carlos Pérez González'
        assert t.activo is True

    def test_crear_persona_natural_minimo(self, company):
        """Nombre completo solo con primer nombre y primer apellido."""
        t = make_tercero(company)
        assert t.nombre_completo == 'Juan Pérez'

    def test_crear_persona_juridica(self, company):
        """Persona jurídica usa razon_social como nombre_completo."""
        t = Tercero.objects.create(
            company=company,
            tipo_identificacion='nit',
            numero_identificacion='900123456',
            razon_social='Constructora ABC S.A.S.',
            tipo_persona='juridica',
            tipo_tercero='proveedor',
            codigo='PRO-0001',
        )
        assert t.nombre_completo == 'Constructora ABC S.A.S.'
        assert t.tipo_persona == 'juridica'

    def test_nombre_completo_se_actualiza_al_guardar(self, company):
        """nombre_completo se recalcula en cada save()."""
        t = make_tercero(company)
        t.segundo_nombre = 'Alberto'
        t.save()
        assert 'Alberto' in t.nombre_completo

    def test_str_incluye_identificacion(self, company):
        """__str__ retorna nombre + número de identificación."""
        t = make_tercero(company)
        assert '1234567890' in str(t)
        assert 'Juan' in str(t)

    def test_unique_identificacion_por_empresa(self, company):
        """No permite duplicar tipo+numero_identificacion en la misma empresa."""
        make_tercero(company, '1111111111')
        with pytest.raises(IntegrityError):
            Tercero.objects.create(
                company=company,
                tipo_identificacion='cc',
                numero_identificacion='1111111111',
                primer_nombre='Otro',
                primer_apellido='Apellido',
                tipo_persona='natural',
                codigo='CLI-9999',
            )

    def test_misma_identificacion_diferente_empresa_permitida(self, company, company2):
        """La misma identificación puede existir en empresas distintas."""
        t1 = make_tercero(company, '5555555555')
        t2 = make_tercero(company2, '5555555555', codigo='CLI-5555')
        assert t1.id != t2.id

    def test_persona_natural_sin_segundo_nombre(self, company):
        """Nombre completo omite partes vacías."""
        t = make_tercero(company, segundo_nombre='', segundo_apellido='')
        assert t.nombre_completo == 'Juan Pérez'
        assert '  ' not in t.nombre_completo  # sin doble espacio

    def test_activo_default_true(self, company):
        """El campo activo es True por defecto."""
        t = make_tercero(company)
        assert t.activo is True

    def test_saiopen_synced_default_false(self, company):
        """saiopen_synced es False por defecto."""
        t = make_tercero(company)
        assert t.saiopen_synced is False


@pytest.mark.django_db
class TestTerceroDireccionModel:

    @pytest.fixture
    def tercero(self, company):
        return make_tercero(company)

    def test_crear_direccion_con_campos_requeridos(self, tercero):
        """Crea dirección con campos mínimos requeridos."""
        d = make_direccion(tercero)
        assert d.id is not None
        assert d.pais == 'Colombia'
        assert d.activa is True

    def test_direccion_hereda_company_del_tercero(self, tercero):
        """TerceroDireccion pertenece a la misma company que el tercero."""
        d = make_direccion(tercero)
        assert d.company_id == tercero.company_id

    def test_str_incluye_ciudad_y_direccion(self, tercero):
        """__str__ contiene dirección y ciudad."""
        d = make_direccion(tercero, ciudad='Bogotá', direccion_linea1='Cra 7 # 32-10')
        assert 'Bogotá' in str(d)
        assert 'Cra 7 # 32-10' in str(d)

    def test_multiples_direcciones_por_tercero(self, tercero):
        """Un tercero puede tener varias direcciones."""
        make_direccion(tercero, ciudad='Cali', tipo='principal')
        make_direccion(tercero, ciudad='Bogotá', tipo='sucursal')
        make_direccion(tercero, ciudad='Medellín', tipo='bodega')
        assert tercero.direcciones.count() == 3

    def test_pais_default_colombia(self, tercero):
        """El campo pais tiene 'Colombia' como valor por defecto."""
        d = make_direccion(tercero)
        assert d.pais == 'Colombia'

    def test_es_principal_default_false(self, tercero):
        """es_principal es False por defecto."""
        d = make_direccion(tercero)
        assert d.es_principal is False

    def test_activa_default_true(self, tercero):
        """activa es True por defecto."""
        d = make_direccion(tercero)
        assert d.activa is True
