"""
SaiSuite — Tests: ConfiguracionModulo model
"""
import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import ConfiguracionModulo

User = get_user_model()


def make_company(nit='908001001'):
    c = Company.objects.create(name='Config Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


@pytest.mark.django_db
class TestConfiguracionModuloModel:

    def test_crear_configuracion_modulo(self):
        c = make_company()
        config = ConfiguracionModulo.objects.create(company=c)
        assert config.id is not None
        assert config.company_id == c.id

    def test_company_fk_one_to_one(self):
        c = make_company('908001002')
        ConfiguracionModulo.objects.create(company=c)
        with pytest.raises(IntegrityError):
            ConfiguracionModulo.objects.create(company=c)

    def test_requiere_sync_saiopen_default_false(self):
        c = make_company('908001003')
        config = ConfiguracionModulo.objects.create(company=c)
        assert config.requiere_sync_saiopen_para_ejecucion is False

    def test_requiere_sync_saiopen_se_puede_activar(self):
        c = make_company('908001004')
        config = ConfiguracionModulo.objects.create(
            company=c, requiere_sync_saiopen_para_ejecucion=True
        )
        assert config.requiere_sync_saiopen_para_ejecucion is True

    def test_dias_alerta_vencimiento_default_15(self):
        c = make_company('908001005')
        config = ConfiguracionModulo.objects.create(company=c)
        assert config.dias_alerta_vencimiento == 15

    def test_dias_alerta_vencimiento_personalizado(self):
        c = make_company('908001006')
        config = ConfiguracionModulo.objects.create(company=c, dias_alerta_vencimiento=30)
        assert config.dias_alerta_vencimiento == 30

    def test_dias_alerta_vencimiento_rechaza_negativos(self):
        """PositiveIntegerField rechaza valores negativos a nivel de validación."""
        c = make_company('908001007')
        config = ConfiguracionModulo(company=c, dias_alerta_vencimiento=-1)
        with pytest.raises(ValidationError):
            config.full_clean()

    def test_solo_una_configuracion_por_empresa(self):
        c = make_company('908001008')
        config1 = ConfiguracionModulo.objects.create(company=c)
        assert ConfiguracionModulo.objects.filter(company=c).count() == 1
        assert config1.company_id == c.id

    def test_get_or_create_devuelve_existente(self):
        c = make_company('908001009')
        config1, created1 = ConfiguracionModulo.objects.get_or_create(company=c)
        assert created1 is True
        config2, created2 = ConfiguracionModulo.objects.get_or_create(company=c)
        assert created2 is False
        assert config1.id == config2.id

    def test_get_or_create_crea_nueva_si_no_existe(self):
        c = make_company('908001010')
        assert ConfiguracionModulo.objects.filter(company=c).count() == 0
        config, created = ConfiguracionModulo.objects.get_or_create(company=c)
        assert created is True
        assert config.company_id == c.id
        assert ConfiguracionModulo.objects.filter(company=c).count() == 1

    def test_related_name_configuracion_proyectos(self):
        c = make_company('908001011')
        config = ConfiguracionModulo.objects.create(company=c)
        assert c.configuracion_proyectos == config

    def test_str_incluye_company(self):
        c = make_company('908001012')
        config = ConfiguracionModulo.objects.create(company=c)
        s = str(config)
        assert 'Config proyectos' in s

    def test_diferentes_empresas_tienen_configuraciones_independientes(self):
        c1 = make_company('908001013')
        c2 = make_company('908001014')
        config1 = ConfiguracionModulo.objects.create(
            company=c1, dias_alerta_vencimiento=7
        )
        config2 = ConfiguracionModulo.objects.create(
            company=c2, dias_alerta_vencimiento=30
        )
        assert config1.id != config2.id
        assert config1.dias_alerta_vencimiento == 7
        assert config2.dias_alerta_vencimiento == 30
