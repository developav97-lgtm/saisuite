"""
SaiSuite — Tests: LicenseRequestService
Cubre: create_request, approve, reject, list_for_company, list_all.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.exceptions import ValidationError

from apps.companies.models import (
    Company, CompanyLicense, LicensePackage, LicensePackageItem, LicenseRequest,
)
from apps.companies.services import LicenseRequestService


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def make_company(nit, name='Test Co'):
    return Company.objects.create(name=name, nit=nit)


def make_license(company, status='active', days_ahead=30):
    return CompanyLicense.objects.create(
        company=company,
        status=status,
        period='monthly',
        starts_at=date.today() - timedelta(days=1),
        expires_at=date.today() + timedelta(days=days_ahead),
    )


def make_package(code, package_type, name=None):
    return LicensePackage.objects.create(
        code=code,
        name=name or code,
        package_type=package_type,
        quantity=5,
        is_active=True,
    )


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

@pytest.fixture
def company(db):
    return make_company('900700001', 'LR Test Co')


@pytest.fixture
def license_obj(db, company):
    return make_license(company)


@pytest.fixture
def seats_package(db):
    return make_package('seats_5_test', LicensePackage.PackageType.USER_SEATS, 'Puestos ×5')


@pytest.fixture
def module_package(db):
    return make_package('mod_crm_test', LicensePackage.PackageType.MODULE, 'Módulo CRM')


@pytest.fixture
def ai_package(db):
    return make_package('ai_1000_test', LicensePackage.PackageType.AI_TOKENS, 'IA 1000 tokens')


@pytest.fixture
def ai_package_2(db):
    return make_package('ai_5000_test', LicensePackage.PackageType.AI_TOKENS, 'IA 5000 tokens')


@pytest.fixture
def admin_user(db, company):
    from apps.users.models import User
    return User.objects.create_user(
        email='admin@lrtest.com', password='test1234',
        company=company, role='company_admin',
    )


@pytest.fixture
def superadmin_user(db):
    from apps.users.models import User
    sa_company = make_company('900700099', 'ValMen SA')
    return User.objects.create_user(
        email='super@valmen.com', password='test1234',
        company=sa_company, role='superadmin',
    )


# ─────────────────────────────────────────────
# create_request
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseRequestCreate:

    def test_crea_solicitud_user_seats(self, company, seats_package, admin_user):
        req = LicenseRequestService.create_request(
            company=company,
            package_id=str(seats_package.id),
            request_type=LicenseRequest.RequestType.USER_SEATS,
            notes='Necesitamos 5 puestos más',
            created_by=admin_user,
        )
        assert req.id is not None
        assert req.company == company
        assert req.package == seats_package
        assert req.status == LicenseRequest.Status.PENDING
        assert req.notes == 'Necesitamos 5 puestos más'
        assert req.created_by == admin_user

    def test_crea_solicitud_module(self, company, module_package, admin_user):
        req = LicenseRequestService.create_request(
            company=company,
            package_id=str(module_package.id),
            request_type=LicenseRequest.RequestType.MODULE,
            notes='',
            created_by=admin_user,
        )
        assert req.request_type == LicenseRequest.RequestType.MODULE
        assert req.package == module_package

    def test_crea_solicitud_ai_tokens(self, company, ai_package, admin_user):
        req = LicenseRequestService.create_request(
            company=company,
            package_id=str(ai_package.id),
            request_type=LicenseRequest.RequestType.AI_TOKENS,
            notes='Upgrade IA',
            created_by=admin_user,
        )
        assert req.status == LicenseRequest.Status.PENDING

    def test_paquete_no_encontrado_lanza_error(self, company, admin_user):
        import uuid
        with pytest.raises(ValidationError, match='Paquete no encontrado'):
            LicenseRequestService.create_request(
                company=company,
                package_id=str(uuid.uuid4()),
                request_type=LicenseRequest.RequestType.USER_SEATS,
                notes='',
                created_by=admin_user,
            )

    def test_paquete_inactivo_lanza_error(self, company, admin_user):
        pkg = make_package('inactive_test', LicensePackage.PackageType.USER_SEATS, 'Inactivo')
        pkg.is_active = False
        pkg.save()
        with pytest.raises(ValidationError, match='Paquete no encontrado'):
            LicenseRequestService.create_request(
                company=company,
                package_id=str(pkg.id),
                request_type=LicenseRequest.RequestType.USER_SEATS,
                notes='',
                created_by=admin_user,
            )

    def test_tipo_incoherente_lanza_error(self, company, seats_package, admin_user):
        """Solicitar módulo con paquete de user_seats debe fallar."""
        with pytest.raises(ValidationError, match='tipo de solicitud no coincide'):
            LicenseRequestService.create_request(
                company=company,
                package_id=str(seats_package.id),
                request_type=LicenseRequest.RequestType.MODULE,  # incorrecto
                notes='',
                created_by=admin_user,
            )

    def test_duplicado_pendiente_lanza_error(self, company, seats_package, admin_user):
        """No se puede crear dos solicitudes pendientes para el mismo paquete."""
        LicenseRequestService.create_request(
            company=company,
            package_id=str(seats_package.id),
            request_type=LicenseRequest.RequestType.USER_SEATS,
            notes='Primera',
            created_by=admin_user,
        )
        with pytest.raises(ValidationError, match='Ya existe una solicitud pendiente'):
            LicenseRequestService.create_request(
                company=company,
                package_id=str(seats_package.id),
                request_type=LicenseRequest.RequestType.USER_SEATS,
                notes='Segunda (duplicada)',
                created_by=admin_user,
            )

    def test_paquete_aprobado_permite_nueva_solicitud(self, company, seats_package, admin_user):
        """Si la solicitud anterior fue aprobada, se puede hacer una nueva."""
        LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.APPROVED,
        )
        req = LicenseRequestService.create_request(
            company=company,
            package_id=str(seats_package.id),
            request_type=LicenseRequest.RequestType.USER_SEATS,
            notes='Nueva solicitud post-aprobación',
            created_by=admin_user,
        )
        assert req.status == LicenseRequest.Status.PENDING


# ─────────────────────────────────────────────
# approve
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseRequestApprove:

    def test_aprueba_solicitud_pendiente(self, company, license_obj, seats_package, admin_user, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.PENDING,
            created_by=admin_user,
        )
        result = LicenseRequestService.approve(req, reviewed_by=superadmin_user)
        assert result.status == LicenseRequest.Status.APPROVED
        assert result.reviewed_by == superadmin_user
        assert result.reviewed_at is not None

    def test_aprobacion_agrega_paquete_a_licencia(self, company, license_obj, seats_package, admin_user, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.PENDING,
            created_by=admin_user,
        )
        LicenseRequestService.approve(req, reviewed_by=superadmin_user)
        assert LicensePackageItem.objects.filter(license=license_obj, package=seats_package).exists()

    def test_aprobacion_modulo_agrega_paquete(self, company, license_obj, module_package, admin_user, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=module_package,
            request_type=LicenseRequest.RequestType.MODULE,
            status=LicenseRequest.Status.PENDING,
            created_by=admin_user,
        )
        LicenseRequestService.approve(req, reviewed_by=superadmin_user)
        assert LicensePackageItem.objects.filter(license=license_obj, package=module_package).exists()

    def test_aprobacion_ai_tokens_reemplaza_paquete_anterior(
        self, company, license_obj, ai_package, ai_package_2, admin_user, superadmin_user
    ):
        """Aprobar ai_tokens elimina el paquete ai_tokens existente antes de agregar el nuevo."""
        # Primero agregar un paquete ai_tokens a la licencia
        LicensePackageItem.objects.create(
            license=license_obj,
            package=ai_package,
            quantity=1,
            added_by=superadmin_user,
        )
        assert LicensePackageItem.objects.filter(
            license=license_obj,
            package__package_type=LicensePackage.PackageType.AI_TOKENS,
        ).count() == 1

        # Solicitar el upgrade de tokens
        req = LicenseRequest.objects.create(
            company=company,
            package=ai_package_2,
            request_type=LicenseRequest.RequestType.AI_TOKENS,
            status=LicenseRequest.Status.PENDING,
            created_by=admin_user,
        )
        LicenseRequestService.approve(req, reviewed_by=superadmin_user)

        # Solo debe existir el paquete nuevo
        ai_items = LicensePackageItem.objects.filter(
            license=license_obj,
            package__package_type=LicensePackage.PackageType.AI_TOKENS,
        )
        assert ai_items.count() == 1
        assert ai_items.first().package == ai_package_2

    def test_aprobar_solicitud_no_pendiente_lanza_error(self, company, seats_package, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.APPROVED,
        )
        with pytest.raises(ValidationError, match='pendientes'):
            LicenseRequestService.approve(req, reviewed_by=superadmin_user)

    def test_aprobar_solicitud_rechazada_lanza_error(self, company, seats_package, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.REJECTED,
        )
        with pytest.raises(ValidationError, match='pendientes'):
            LicenseRequestService.approve(req, reviewed_by=superadmin_user)


# ─────────────────────────────────────────────
# reject
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseRequestReject:

    def test_rechaza_solicitud_pendiente(self, company, seats_package, admin_user, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.PENDING,
            created_by=admin_user,
        )
        result = LicenseRequestService.reject(req, reviewed_by=superadmin_user, review_notes='Presupuesto insuficiente')
        assert result.status == LicenseRequest.Status.REJECTED
        assert result.reviewed_by == superadmin_user
        assert result.reviewed_at is not None
        assert result.review_notes == 'Presupuesto insuficiente'

    def test_rechazo_persiste_en_bd(self, company, seats_package, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.PENDING,
        )
        LicenseRequestService.reject(req, reviewed_by=superadmin_user, review_notes='Motivo test')
        req.refresh_from_db()
        assert req.status == LicenseRequest.Status.REJECTED
        assert req.review_notes == 'Motivo test'

    def test_rechazo_sin_notas(self, company, seats_package, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.PENDING,
        )
        result = LicenseRequestService.reject(req, reviewed_by=superadmin_user)
        assert result.status == LicenseRequest.Status.REJECTED
        assert result.review_notes == ''

    def test_rechazar_solicitud_no_pendiente_lanza_error(self, company, seats_package, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.APPROVED,
        )
        with pytest.raises(ValidationError, match='pendientes'):
            LicenseRequestService.reject(req, reviewed_by=superadmin_user)

    def test_rechazar_ya_rechazada_lanza_error(self, company, seats_package, superadmin_user):
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.REJECTED,
        )
        with pytest.raises(ValidationError, match='pendientes'):
            LicenseRequestService.reject(req, reviewed_by=superadmin_user)

    def test_rechazar_no_modifica_licencia(self, company, license_obj, seats_package, admin_user, superadmin_user):
        """Rechazar no agrega paquete a la licencia."""
        req = LicenseRequest.objects.create(
            company=company,
            package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS,
            status=LicenseRequest.Status.PENDING,
            created_by=admin_user,
        )
        LicenseRequestService.reject(req, reviewed_by=superadmin_user)
        assert not LicensePackageItem.objects.filter(license=license_obj, package=seats_package).exists()


# ─────────────────────────────────────────────
# list_for_company
# ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLicenseRequestList:

    def test_list_for_company_filtra_empresa(self, company, seats_package):
        otra = make_company('900700002', 'Otra Co')
        otro_pkg = make_package('seats_otra', LicensePackage.PackageType.USER_SEATS, 'Seats Otra')

        LicenseRequest.objects.create(
            company=company, package=seats_package,
            request_type=LicenseRequest.RequestType.USER_SEATS, status=LicenseRequest.Status.PENDING,
        )
        LicenseRequest.objects.create(
            company=otra, package=otro_pkg,
            request_type=LicenseRequest.RequestType.USER_SEATS, status=LicenseRequest.Status.PENDING,
        )

        result = LicenseRequestService.list_for_company(company)
        assert all(r.company_id == company.id for r in result)

    def test_list_for_company_retorna_vacio_si_no_hay(self, company):
        result = LicenseRequestService.list_for_company(company)
        assert result.count() == 0
