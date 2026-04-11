"""
SaiSuite — Tests: Company y CompanyModule models
"""
import pytest
from django.db import IntegrityError
from apps.companies.models import Company, CompanyModule


def make_company(nit='900000001', name='Empresa Test'):
    return Company.objects.create(name=name, nit=nit)


@pytest.mark.django_db
class TestCompanyModel:

    def test_crear_company_con_campos_minimos(self):
        c = make_company()
        assert c.id is not None
        assert c.name == 'Empresa Test'
        assert c.nit == '900000001'

    def test_nit_unico_global(self):
        make_company(nit='900000002')
        with pytest.raises(IntegrityError):
            Company.objects.create(name='Duplicada', nit='900000002')

    def test_is_active_por_defecto_true(self):
        c = make_company(nit='900000003')
        assert c.is_active is True

    def test_created_at_se_genera_automaticamente(self):
        c = make_company(nit='900000004')
        assert c.created_at is not None

    def test_updated_at_se_genera_automaticamente(self):
        c = make_company(nit='900000005')
        assert c.updated_at is not None

    def test_saiopen_enabled_por_defecto_false(self):
        c = make_company(nit='900000006')
        assert c.saiopen_enabled is False

    def test_saiopen_db_path_por_defecto_vacio(self):
        c = make_company(nit='900000007')
        assert c.saiopen_db_path == ''

    def test_str_retorna_nombre_y_nit(self):
        c = make_company(nit='900000008', name='Mi Empresa')
        assert 'Mi Empresa' in str(c)
        assert '900000008' in str(c)

    def test_ordering_por_nombre(self):
        Company.objects.create(name='Zebra Corp', nit='ZZ001')
        Company.objects.create(name='Alpha SA',   nit='AA001')
        companies = list(Company.objects.all())
        names = [c.name for c in companies]
        assert names == sorted(names)


@pytest.mark.django_db
class TestCompanyModuleModel:

    def test_crear_modulo_en_empresa(self):
        c = make_company(nit='800000001')
        m = CompanyModule.objects.create(company=c, module='crm')
        assert m.id is not None
        assert m.module == 'crm'

    def test_is_active_por_defecto_true(self):
        c = make_company(nit='800000002')
        m = CompanyModule.objects.create(company=c, module='crm')
        assert m.is_active is True

    def test_modulos_disponibles(self):
        modulos = [m.value for m in CompanyModule.Module]
        assert 'crm' in modulos
        assert 'dashboard' in modulos
        assert 'proyectos' in modulos

    def test_unique_together_company_module(self):
        c = make_company(nit='800000003')
        CompanyModule.objects.create(company=c, module='crm')
        with pytest.raises(IntegrityError):
            CompanyModule.objects.create(company=c, module='crm')

    def test_misma_empresa_puede_tener_varios_modulos(self):
        c = make_company(nit='800000004')
        CompanyModule.objects.create(company=c, module='crm')
        CompanyModule.objects.create(company=c, module='proyectos')
        assert CompanyModule.objects.filter(company=c).count() == 2

    def test_str_incluye_empresa_y_modulo(self):
        c = make_company(nit='800000005', name='Co Test')
        m = CompanyModule.objects.create(company=c, module='crm')
        s = str(m)
        assert 'Co Test' in s
