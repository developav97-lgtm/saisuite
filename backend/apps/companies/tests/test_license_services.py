"""
SaiSuite — Tests: CompanyService y LicenseService
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.exceptions import ValidationError, NotFound

from apps.companies.models import Company, CompanyModule, CompanyLicense, LicensePayment
from apps.companies.services import CompanyService, LicenseService


def make_company(nit='900500001', name='Svc Test'):
    return Company.objects.create(name=name, nit=nit)


def make_license(company, status='active', days_ahead=30):
    return CompanyLicense.objects.create(
        company=company,
        status=status,
        starts_at=date.today() - timedelta(days=1),
        expires_at=date.today() + timedelta(days=days_ahead),
    )


# ── CompanyService ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompanyServiceList:

    def test_retorna_todas_las_empresas(self):
        make_company('900500010')
        make_company('900500011')
        qs = CompanyService.list_companies()
        assert qs.count() >= 2

    def test_ordenadas_por_nombre(self):
        Company.objects.create(name='Zeta', nit='ZZZ001')
        Company.objects.create(name='Alpha', nit='AAA001')
        names = [c.name for c in CompanyService.list_companies()]
        assert names == sorted(names)


@pytest.mark.django_db
class TestCompanyServiceGet:

    def test_obtiene_empresa_por_uuid(self):
        c = make_company('900500020')
        result = CompanyService.get_company(str(c.id))
        assert result.id == c.id

    def test_uuid_inexistente_lanza_validation_error(self):
        import uuid
        with pytest.raises(ValidationError, match='no encontrada'):
            CompanyService.get_company(str(uuid.uuid4()))


@pytest.mark.django_db
class TestCompanyServiceCreate:

    def test_crea_empresa_correctamente(self):
        data = {'name': 'Nueva SA', 'nit': '900500030'}
        c = CompanyService.create_company(data)
        assert c.id is not None
        assert c.name == 'Nueva SA'

    def test_nit_duplicado_lanza_error(self):
        make_company('900500031')
        data = {'name': 'Otra', 'nit': '900500031'}
        with pytest.raises(ValidationError, match='NIT'):
            CompanyService.create_company(data)

    def test_is_active_true_por_defecto(self):
        data = {'name': 'Nueva', 'nit': '900500032'}
        c = CompanyService.create_company(data)
        assert c.is_active is True


@pytest.mark.django_db
class TestCompanyServiceUpdate:

    def test_actualiza_nombre(self):
        c = make_company('900500040')
        updated = CompanyService.update_company(c, {'name': 'Actualizado'})
        assert updated.name == 'Actualizado'

    def test_actualiza_saiopen_enabled(self):
        c = make_company('900500041')
        updated = CompanyService.update_company(c, {'saiopen_enabled': True})
        assert updated.saiopen_enabled is True

    def test_nit_no_se_actualiza(self):
        c = make_company('900500042')
        original_nit = c.nit
        CompanyService.update_company(c, {'nit': '000000000'})
        c.refresh_from_db()
        assert c.nit == original_nit  # nit no está en allowed_fields

    def test_sin_cambios_no_falla(self):
        c = make_company('900500043')
        result = CompanyService.update_company(c, {})
        assert result.id == c.id


@pytest.mark.django_db
class TestCompanyServiceModules:

    def test_activa_modulo_nuevo(self):
        c = make_company('900500050')
        obj = CompanyService.activate_module(c, 'crm')
        assert obj.is_active is True
        assert obj.module == 'crm'

    def test_reactiva_modulo_inactivo(self):
        c = make_company('900500051')
        CompanyModule.objects.create(company=c, module='proyectos', is_active=False)
        result = CompanyService.activate_module(c, 'proyectos')
        assert result.is_active is True

    def test_modulo_invalido_lanza_error(self):
        c = make_company('900500052')
        with pytest.raises(ValidationError, match='nválido'):
            CompanyService.activate_module(c, 'inexistente')

    def test_desactiva_modulo(self):
        c = make_company('900500053')
        CompanyModule.objects.create(company=c, module='crm', is_active=True)
        CompanyService.deactivate_module(c, 'crm')
        assert CompanyModule.objects.get(company=c, module='crm').is_active is False

    def test_desactivar_modulo_invalido_lanza_error(self):
        c = make_company('900500054')
        with pytest.raises(ValidationError, match='nválido'):
            CompanyService.deactivate_module(c, 'invalido')

    def test_get_active_modules_lista(self):
        c = make_company('900500055')
        CompanyModule.objects.create(company=c, module='crm', is_active=True)
        CompanyModule.objects.create(company=c, module='dashboard', is_active=False)
        activos = CompanyService.get_active_modules(c)
        assert 'crm' in activos
        assert 'dashboard' not in activos

    def test_get_active_modules_vacio(self):
        c = make_company('900500056')
        assert CompanyService.get_active_modules(c) == []


# ── LicenseService ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseServiceGet:

    def test_obtiene_licencia_de_empresa(self):
        c = make_company('900600001')
        lic = make_license(c)
        result = LicenseService.get_license(c)
        assert result.id == lic.id

    def test_empresa_sin_licencia_lanza_not_found(self):
        c = make_company('900600002')
        with pytest.raises(NotFound):
            LicenseService.get_license(c)

    def test_obtiene_licencia_por_id(self):
        c = make_company('900600003')
        lic = make_license(c)
        result = LicenseService.get_license_by_id(str(lic.id))
        assert result.id == lic.id

    def test_id_inexistente_lanza_not_found(self):
        import uuid
        with pytest.raises(NotFound):
            LicenseService.get_license_by_id(str(uuid.uuid4()))


@pytest.mark.django_db
class TestLicenseServiceList:

    def test_lista_licencias_ordenadas_por_expiry(self):
        c1 = make_company('900600010')
        c2 = make_company('900600011')
        make_license(c1, days_ahead=10)
        make_license(c2, days_ahead=20)
        licencias = LicenseService.list_licenses()
        expiraciones = [lic.expires_at for lic in licencias]
        assert expiraciones == sorted(expiraciones)


@pytest.mark.django_db
class TestLicenseServiceCreate:

    def test_crea_licencia_correctamente(self):
        c = make_company('900600020')
        data = {
            'company': c,
            'status': 'active',
            'starts_at': date.today() - timedelta(days=1),
            'expires_at': date.today() + timedelta(days=30),
            'max_users': 5,
        }
        lic = LicenseService.create_license(data)
        assert lic.id is not None

    def test_duplicado_lanza_validation_error(self):
        c = make_company('900600021')
        make_license(c)
        data = {
            'company': c,
            'status': 'active',
            'starts_at': date.today(),
            'expires_at': date.today() + timedelta(days=30),
        }
        with pytest.raises(ValidationError, match='ya tiene una licencia'):
            LicenseService.create_license(data)


@pytest.mark.django_db
class TestLicenseServiceUpdate:

    def test_actualiza_status(self):
        c = make_company('900600030')
        lic = make_license(c)
        updated = LicenseService.update_license(lic, {'status': 'suspended'})
        assert updated.status == 'suspended'

    def test_actualiza_max_users(self):
        c = make_company('900600031')
        lic = make_license(c)
        updated = LicenseService.update_license(lic, {'max_users': 20})
        assert updated.max_users == 20

    def test_actualiza_expires_at(self):
        c = make_company('900600032')
        lic = make_license(c)
        nueva_fecha = date.today() + timedelta(days=90)
        updated = LicenseService.update_license(lic, {'expires_at': nueva_fecha})
        assert updated.expires_at == nueva_fecha

    def test_sin_cambios_no_falla(self):
        c = make_company('900600033')
        lic = make_license(c)
        result = LicenseService.update_license(lic, {})
        assert result.id == lic.id


@pytest.mark.django_db
class TestLicenseServicePayment:

    def test_agrega_pago_a_licencia(self):
        c = make_company('900600040')
        lic = make_license(c)
        payment = LicenseService.add_payment(lic, {
            'amount': Decimal('500000'),
            'payment_date': date.today(),
            'method': 'transfer',
        })
        assert payment.id is not None
        assert payment.license_id == lic.id

    def test_pago_se_guarda_en_bd(self):
        c = make_company('900600041')
        lic = make_license(c)
        LicenseService.add_payment(lic, {
            'amount': Decimal('100000'),
            'payment_date': date.today(),
        })
        assert LicensePayment.objects.filter(license=lic).count() == 1


@pytest.mark.django_db
class TestLicenseServiceGetExpiringSoon:

    def test_retorna_licencias_que_vencen_exactamente_en_n_dias(self):
        c = make_company('900600050')
        lic = make_license(c, status='active', days_ahead=5)
        result = LicenseService.get_expiring_soon(days=5)
        ids = [l.id for l in result]
        assert lic.id in ids

    def test_no_retorna_licencias_con_otro_vencimiento(self):
        c = make_company('900600051')
        make_license(c, status='active', days_ahead=10)
        result = LicenseService.get_expiring_soon(days=5)
        assert len(result) == 0

    def test_no_retorna_licencias_suspendidas(self):
        c = make_company('900600052')
        CompanyLicense.objects.create(
            company=c, status='suspended',
            starts_at=date.today() - timedelta(days=1),
            expires_at=date.today() + timedelta(days=5),
        )
        result = LicenseService.get_expiring_soon(days=5)
        assert all(l.status == 'active' for l in result)

    def test_no_retorna_licencias_expiradas(self):
        c = make_company('900600053')
        CompanyLicense.objects.create(
            company=c, status='expired',
            starts_at=date.today() - timedelta(days=60),
            expires_at=date.today() + timedelta(days=5),
        )
        result = LicenseService.get_expiring_soon(days=5)
        assert all(l.status == 'active' for l in result)

    def test_default_5_dias(self):
        c = make_company('900600054')
        lic = make_license(c, status='active', days_ahead=5)
        result = LicenseService.get_expiring_soon()  # default=5
        ids = [l.id for l in result]
        assert lic.id in ids
