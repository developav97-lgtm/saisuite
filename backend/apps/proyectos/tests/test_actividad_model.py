"""
SaiSuite — Tests: Activity model (catálogo global por empresa)
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import ProjectStatus, PhaseStatus, ActivityType, MeasurementMode,  Activity, ActivityType, ActivityType

User = get_user_model()


def make_company(nit='903001001'):
    c = Company.objects.create(name='Act Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_actividad(company, codigo='ACT-001', **kwargs):
    defaults = dict(
        nombre='Excavación',
        unidad_medida='m3',
        tipo='material',
    )
    defaults.update(kwargs)
    return Activity.all_objects.create(company=company, codigo=codigo, **defaults)


@pytest.mark.django_db
class TestActividadModel:

    def test_crear_actividad_con_campos_obligatorios(self):
        c = make_company()
        a = make_actividad(c)
        assert a.id is not None
        assert a.codigo == 'ACT-001'
        assert a.nombre == 'Excavación'

    def test_activo_por_defecto_true(self):
        c = make_company('903001002')
        a = make_actividad(c, 'ACT-002')
        assert a.activo is True

    def test_costo_unitario_base_default_cero(self):
        c = make_company('903001003')
        a = make_actividad(c, 'ACT-003')
        assert a.costo_unitario_base == Decimal('0')

    def test_costo_unitario_base_con_valor(self):
        c = make_company('903001004')
        a = make_actividad(c, 'ACT-004', costo_unitario_base=Decimal('50000'))
        assert a.costo_unitario_base == Decimal('50000')

    def test_descripcion_por_defecto_vacia(self):
        c = make_company('903001005')
        a = make_actividad(c, 'ACT-005')
        assert a.descripcion == ''

    def test_tipos_disponibles(self):
        tipos = [t.value for t in ActivityType]
        assert 'labor' in tipos
        assert 'material' in tipos
        assert 'equipment' in tipos
        assert 'subcontract' in tipos

    def test_tipo_mano_obra(self):
        c = make_company('903001006')
        a = make_actividad(c, 'ACT-006', tipo='labor')
        assert a.tipo == ActivityType.LABOR

    def test_tipo_equipo(self):
        c = make_company('903001007')
        a = make_actividad(c, 'ACT-007', tipo='equipment')
        assert a.tipo == ActivityType.EQUIPMENT

    def test_unique_together_company_codigo(self):
        c = make_company('903001008')
        make_actividad(c, 'ACT-DUP')
        with pytest.raises(IntegrityError):
            Activity.all_objects.create(
                company=c, codigo='ACT-DUP',
                nombre='Otra', unidad_medida='m2', tipo='material',
            )

    def test_mismo_codigo_en_diferente_empresa(self):
        c1 = make_company('903001009')
        c2 = make_company('903001010')
        make_actividad(c1, 'ACT-X')
        a2 = make_actividad(c2, 'ACT-X')
        assert a2.id is not None

    def test_saiopen_no_sincronizado_por_defecto(self):
        c = make_company('903001011')
        a = make_actividad(c, 'ACT-011')
        assert a.sincronizado_con_saiopen is False
        assert a.saiopen_actividad_id is None

    def test_str_incluye_codigo_y_nombre(self):
        c = make_company('903001012')
        a = make_actividad(c, 'ACT-012', nombre='Pintura exterior')
        s = str(a)
        assert 'ACT-012' in s
        assert 'Pintura exterior' in s

    def test_ordering_por_codigo(self):
        c = make_company('903001013')
        make_actividad(c, 'ACT-Z')
        make_actividad(c, 'ACT-A')
        make_actividad(c, 'ACT-M')
        codigos = [a.codigo for a in Activity.all_objects.filter(company=c)]
        assert codigos == sorted(codigos)

    def test_company_fk(self):
        c = make_company('903001014')
        a = make_actividad(c, 'ACT-014')
        assert a.company_id == c.id

    def test_unidad_medida_variada(self):
        c = make_company('903001015')
        a = make_actividad(c, 'ACT-015', unidad_medida='hora')
        assert a.unidad_medida == 'hora'

    def test_actividad_usable_en_multiples_proyectos(self):
        """La misma actividad puede asignarse a múltiples proyectos (vía ProjectActivity)."""
        from django.contrib.auth import get_user_model
        from apps.proyectos.models import ProjectStatus, PhaseStatus, ActivityType, MeasurementMode,  Project, ProjectActivity
        from datetime import date, timedelta
        User = get_user_model()
        c = make_company('903001016')
        g = User.objects.create_user(email='gact@test.com', password='Pass!', company=c, is_active=True)
        act = make_actividad(c, 'ACT-SHARED')

        p1 = Project.all_objects.create(
            company=c, gerente=g, codigo='PRY-A1',
            nombre='P1', tipo='services',
            cliente_id='111', cliente_nombre='C1',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=60),
        )
        p2 = Project.all_objects.create(
            company=c, gerente=g, codigo='PRY-A2',
            nombre='P2', tipo='services',
            cliente_id='222', cliente_nombre='C2',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=60),
        )
        ap1 = ProjectActivity.all_objects.create(
            company=c, proyecto=p1, actividad=act,
            cantidad_planificada=Decimal('10'), costo_unitario=Decimal('5000'),
        )
        ap2 = ProjectActivity.all_objects.create(
            company=c, proyecto=p2, actividad=act,
            cantidad_planificada=Decimal('20'), costo_unitario=Decimal('5000'),
        )
        assert ap1.actividad_id == act.id
        assert ap2.actividad_id == act.id
        assert act.asignaciones.count() == 2
