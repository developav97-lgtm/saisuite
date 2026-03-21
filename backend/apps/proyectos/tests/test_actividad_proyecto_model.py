"""
SaiSuite — Tests: ActividadProyecto model + signals
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Proyecto, Fase, Actividad, ActividadProyecto,
)

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_company(nit='904001001'):
    c = Company.objects.create(name='AP Test Co', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email='gap@test.com'):
    return User.objects.create_user(
        email=email, password='Pass1234!', company=company, role='company_admin', is_active=True
    )


def make_proyecto(company, gerente, codigo='AP-PRY-001'):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente, codigo=codigo,
        nombre='AP Proyecto', tipo='obra_civil',
        cliente_id='111', cliente_nombre='C',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('10000000.00'),
    )


def make_fase(proyecto, orden=1):
    return Fase.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto, nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('1000000'),
    )


def make_actividad(company, codigo='ACT-001'):
    return Actividad.all_objects.create(
        company=company, codigo=codigo,
        nombre='Excavación', unidad_medida='m3', tipo='material',
        costo_unitario_base=Decimal('50000'),
    )


def make_ap(company, proyecto, actividad, fase=None, **kwargs):
    defaults = dict(
        cantidad_planificada=Decimal('10'),
        cantidad_ejecutada=Decimal('0'),
        costo_unitario=Decimal('50000'),
    )
    defaults.update(kwargs)
    return ActividadProyecto.all_objects.create(
        company=company,
        proyecto=proyecto,
        actividad=actividad,
        fase=fase,
        **defaults,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestActividadProyectoModel:

    def test_crear_actividad_proyecto(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        a = make_actividad(c)
        ap = make_ap(c, p, a)
        assert ap.id is not None
        assert ap.proyecto_id == p.id
        assert ap.actividad_id == a.id

    def test_cantidad_ejecutada_default_cero(self):
        c = make_company('904001002')
        g = make_user(c, 'gap2@test.com')
        p = make_proyecto(c, g, 'AP-PRY-002')
        a = make_actividad(c, 'ACT-002')
        ap = make_ap(c, p, a)
        assert ap.cantidad_ejecutada == Decimal('0')

    def test_porcentaje_avance_default_cero(self):
        c = make_company('904001003')
        g = make_user(c, 'gap3@test.com')
        p = make_proyecto(c, g, 'AP-PRY-003')
        a = make_actividad(c, 'ACT-003')
        ap = make_ap(c, p, a)
        assert ap.porcentaje_avance == Decimal('0')

    def test_property_presupuesto_total(self):
        c = make_company('904001004')
        g = make_user(c, 'gap4@test.com')
        p = make_proyecto(c, g, 'AP-PRY-004')
        a = make_actividad(c, 'ACT-004')
        ap = make_ap(c, p, a, cantidad_planificada=Decimal('10'), costo_unitario=Decimal('50000'))
        assert ap.presupuesto_total == Decimal('500000')

    def test_property_presupuesto_total_cero(self):
        c = make_company('904001005')
        g = make_user(c, 'gap5@test.com')
        p = make_proyecto(c, g, 'AP-PRY-005')
        a = make_actividad(c, 'ACT-005')
        ap = make_ap(c, p, a, cantidad_planificada=Decimal('0'), costo_unitario=Decimal('50000'))
        assert ap.presupuesto_total == Decimal('0')

    def test_unique_together_proyecto_actividad_fase(self):
        c = make_company('904001006')
        g = make_user(c, 'gap6@test.com')
        p = make_proyecto(c, g, 'AP-PRY-006')
        a = make_actividad(c, 'ACT-006')
        f = make_fase(p, orden=1)
        make_ap(c, p, a, fase=f)
        with pytest.raises(IntegrityError):
            ActividadProyecto.all_objects.create(
                company=c, proyecto=p, actividad=a, fase=f,
                cantidad_planificada=Decimal('5'),
            )

    def test_misma_actividad_en_diferente_fase(self):
        c = make_company('904001007')
        g = make_user(c, 'gap7@test.com')
        p = make_proyecto(c, g, 'AP-PRY-007')
        a = make_actividad(c, 'ACT-007')
        f1 = make_fase(p, orden=1)
        f2 = make_fase(p, orden=2)
        ap1 = make_ap(c, p, a, fase=f1)
        ap2 = make_ap(c, p, a, fase=f2)
        assert ap1.id != ap2.id

    def test_fase_es_opcional(self):
        c = make_company('904001008')
        g = make_user(c, 'gap8@test.com')
        p = make_proyecto(c, g, 'AP-PRY-008')
        a = make_actividad(c, 'ACT-008')
        ap = make_ap(c, p, a, fase=None)
        assert ap.fase is None

    def test_str_incluye_proyecto_y_actividad(self):
        c = make_company('904001009')
        g = make_user(c, 'gap9@test.com')
        p = make_proyecto(c, g, 'AP-PRY-009')
        a = make_actividad(c, 'ACT-009')
        ap = make_ap(c, p, a)
        s = str(ap)
        assert 'AP-PRY-009' in s
        assert 'ACT-009' in s


@pytest.mark.django_db
class TestActividadProyectoSignals:
    """Verifica que post_save/post_delete recalculan el avance de fase y proyecto."""

    def test_signal_post_save_recalcula_avance_fase(self):
        c = make_company('904002001')
        g = make_user(c, 'sig1@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-001')
        f = make_fase(p, orden=1)

        # Crear una actividad con 50% ejecutado — signal recalcula al crear
        ap = ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=make_actividad(c, 'SIG-ACT-001'),
            fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('5'),
            costo_unitario=Decimal('1000'),
        )

        f.refresh_from_db()
        # Fase debe tener avance > 0 (50%)
        assert f.porcentaje_avance == Decimal('50.00')

    def test_signal_post_save_recalcula_avance_proyecto(self):
        c = make_company('904002002')
        g = make_user(c, 'sig2@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-002')
        f = make_fase(p, orden=1)

        ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=make_actividad(c, 'SIG-ACT-002'),
            fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('2000'),
        )

        p.refresh_from_db()
        # Proyecto debe reflejar avance = 100%
        assert p.porcentaje_avance == Decimal('100.00')

    def test_signal_avance_cero_sin_ejecucion(self):
        c = make_company('904002003')
        g = make_user(c, 'sig3@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-003')
        f = make_fase(p, orden=1)

        ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=make_actividad(c, 'SIG-ACT-003'),
            fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('0'),
            costo_unitario=Decimal('1000'),
        )

        f.refresh_from_db()
        assert f.porcentaje_avance == Decimal('0')

    def test_signal_avance_100_ejecucion_completa(self):
        c = make_company('904002004')
        g = make_user(c, 'sig4@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-004')
        f = make_fase(p, orden=1)

        ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=make_actividad(c, 'SIG-ACT-004'),
            fase=f,
            cantidad_planificada=Decimal('8'),
            cantidad_ejecutada=Decimal('8'),
            costo_unitario=Decimal('3000'),
        )

        f.refresh_from_db()
        assert f.porcentaje_avance == Decimal('100.00')

    def test_signal_avance_ponderado_por_costo(self):
        """Actividad costosa 100% ejecutada vs actividad barata 0% → avance ponderado."""
        c = make_company('904002005')
        g = make_user(c, 'sig5@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-005')
        f = make_fase(p, orden=1)

        # Actividad cara: 10u × $10000 = $100000 planificado, 10 ejecutado
        a1 = make_actividad(c, 'SIG-ACT-005A')
        ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=a1, fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('10000'),
        )

        # Actividad barata: 10u × $1000 = $1000 planificado, 0 ejecutado
        a2 = make_actividad(c, 'SIG-ACT-005B')
        ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=a2, fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('0'),
            costo_unitario=Decimal('1000'),
        )

        f.refresh_from_db()
        # planificado_total = 100000 + 10000 = 110000
        # ejecutado_total = 100000 + 0 = 100000
        # avance = 100000 / 110000 × 100 ≈ 90.91
        expected = round(Decimal('100000') / Decimal('110000') * 100, 2)
        assert f.porcentaje_avance == expected

    def test_signal_post_delete_recalcula_avance(self):
        c = make_company('904002006')
        g = make_user(c, 'sig6@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-006')
        f = make_fase(p, orden=1)

        ap = ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=make_actividad(c, 'SIG-ACT-006'),
            fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('1000'),
        )

        f.refresh_from_db()
        assert f.porcentaje_avance == Decimal('100.00')

        ap.delete()
        f.refresh_from_db()
        # Sin actividades, avance vuelve a 0
        assert f.porcentaje_avance == Decimal('0')

    def test_signal_costo_unitario_cero_avance_cero(self):
        """Si todos los costo_unitario son 0, no hay división por cero → avance 0."""
        c = make_company('904002007')
        g = make_user(c, 'sig7@test.com')
        p = make_proyecto(c, g, 'SIG-PRY-007')
        f = make_fase(p, orden=1)

        ActividadProyecto.all_objects.create(
            company=c, proyecto=p, actividad=make_actividad(c, 'SIG-ACT-007'),
            fase=f,
            cantidad_planificada=Decimal('10'),
            cantidad_ejecutada=Decimal('10'),
            costo_unitario=Decimal('0'),
        )

        f.refresh_from_db()
        assert f.porcentaje_avance == Decimal('0')
