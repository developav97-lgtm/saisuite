"""
SaiSuite — Tests: Feature #4 Resource Management — Modelos
BK-26

Cubre:
- ResourceAssignment: unique_together, CheckConstraint fecha, validadores porcentaje
- ResourceCapacity: CheckConstraint horas/fechas, validador horas
- ResourceAvailability: CheckConstraint fechas, choices tipo
- AvailabilityType: valores de choices
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Project, Phase, Task,
    ResourceAssignment, ResourceCapacity, ResourceAvailability,
    AvailabilityType,
)

# ── Counters ──────────────────────────────────────────────────────────────────

_NIT   = [700_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'rm_{_EMAIL[0]}@test.com'


# ── Factories ─────────────────────────────────────────────────────────────────

def make_company():
    from django.contrib.auth import get_user_model
    c = Company.objects.create(name=f'RM Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role=role,
    )


def make_proyecto(company, gerente):
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'RM-{_nit()}',
        nombre='Project RM Test',
        tipo='services',
        estado='in_progress',
        cliente_id='001',
        cliente_nombre='Cliente RM',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('5000000.00'),
    )


def make_fase(company, proyecto):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre='Fase RM',
        orden=1,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
    )


def make_tarea(company, proyecto, fase, responsable):
    return Task.objects.create(
        company=company, proyecto=proyecto, fase=fase,
        nombre='Tarea RM',
        responsable=responsable,
        estado='todo',
    )


# ── Tests: AvailabilityType ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAvailabilityType:
    def test_choices_incluyen_todos_los_valores(self):
        values = {c[0] for c in AvailabilityType.choices}
        assert 'vacation'   in values
        assert 'sick_leave' in values
        assert 'holiday'    in values
        assert 'training'   in values
        assert 'other'      in values

    def test_labels_en_espanol(self):
        labels = dict(AvailabilityType.choices)
        assert labels['vacation']   == 'Vacaciones'
        assert labels['sick_leave'] == 'Incapacidad'
        assert labels['holiday']    == 'Festivo'
        assert labels['training']   == 'Capacitación'
        assert labels['other']      == 'Otro'


# ── Tests: ResourceAssignment ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestResourceAssignmentModel:

    def setup_method(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.user2    = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.user)

    def _make_assignment(self, usuario=None, porcentaje='50.00', days_offset=0):
        start = date.today() + timedelta(days=days_offset)
        end   = start + timedelta(days=30)
        return ResourceAssignment.objects.create(
            company=self.company,
            tarea=self.tarea,
            usuario=usuario or self.user,
            porcentaje_asignacion=Decimal(porcentaje),
            fecha_inicio=start,
            fecha_fin=end,
            activo=True,
        )

    def test_crear_asignacion_ok(self):
        a = self._make_assignment()
        assert a.id is not None
        assert a.activo is True
        assert a.porcentaje_asignacion == Decimal('50.00')

    def test_unique_together_company_tarea_usuario(self):
        self._make_assignment(usuario=self.user)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                self._make_assignment(usuario=self.user)

    def test_dos_usuarios_distintos_misma_tarea_ok(self):
        a1 = self._make_assignment(usuario=self.user)
        a2 = self._make_assignment(usuario=self.user2)
        assert a1.id != a2.id

    def test_constraint_fecha_fin_gte_inicio(self):
        """La BD debe rechazar fecha_fin < fecha_inicio."""
        with pytest.raises(Exception):
            with transaction.atomic():
                ResourceAssignment.objects.create(
                    company=self.company,
                    tarea=self.tarea,
                    usuario=self.user,
                    porcentaje_asignacion=Decimal('30.00'),
                    fecha_inicio=date.today() + timedelta(days=10),
                    fecha_fin=date.today(),
                    activo=True,
                )

    def test_str_representacion(self):
        a = self._make_assignment()
        # El modelo debe ser representable como string sin errores
        assert str(a) or a.id is not None

    def test_soft_delete_no_elimina_registro(self):
        a = self._make_assignment()
        pk = a.id
        a.activo = False
        a.save(update_fields=['activo'])
        assert ResourceAssignment.objects.filter(id=pk).exists()
        assert not ResourceAssignment.objects.get(id=pk).activo


# ── Tests: ResourceCapacity ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestResourceCapacityModel:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)

    def test_crear_capacidad_ok(self):
        cap = ResourceCapacity.objects.create(
            company=self.company,
            usuario=self.user,
            horas_por_semana=Decimal('40.00'),
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=None,
            activo=True,
        )
        assert cap.id is not None
        assert cap.horas_por_semana == Decimal('40.00')
        assert cap.fecha_fin is None

    def test_fecha_fin_puede_ser_null(self):
        cap = ResourceCapacity.objects.create(
            company=self.company,
            usuario=self.user,
            horas_por_semana=Decimal('32.00'),
            fecha_inicio=date(2020, 1, 1),
            activo=True,
        )
        assert cap.fecha_fin is None

    def test_constraint_fecha_fin_gt_inicio(self):
        """fecha_fin debe ser > fecha_inicio (no igual, no menor)."""
        with pytest.raises(Exception):
            with transaction.atomic():
                ResourceCapacity.objects.create(
                    company=self.company,
                    usuario=self.user,
                    horas_por_semana=Decimal('40.00'),
                    fecha_inicio=date(2024, 6, 1),
                    fecha_fin=date(2024, 6, 1),  # igual → debe fallar
                    activo=True,
                )

    def test_constraint_horas_positivas(self):
        """horas_por_semana > 0."""
        with pytest.raises(Exception):
            with transaction.atomic():
                ResourceCapacity.objects.create(
                    company=self.company,
                    usuario=self.user,
                    horas_por_semana=Decimal('0.00'),
                    fecha_inicio=date(2024, 1, 1),
                    activo=True,
                )

    def test_multiples_capacidades_mismo_usuario(self):
        """Un usuario puede tener varias capacidades en períodos distintos."""
        c1 = ResourceCapacity.objects.create(
            company=self.company, usuario=self.user,
            horas_por_semana=Decimal('40.00'),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2022, 12, 31),
            activo=True,
        )
        c2 = ResourceCapacity.objects.create(
            company=self.company, usuario=self.user,
            horas_por_semana=Decimal('32.00'),
            fecha_inicio=date(2023, 1, 1),
            activo=True,
        )
        assert c1.id != c2.id


# ── Tests: ResourceAvailability ───────────────────────────────────────────────

@pytest.mark.django_db
class TestResourceAvailabilityModel:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.user2   = make_user(self.company)

    def test_crear_ausencia_ok(self):
        av = ResourceAvailability.objects.create(
            company=self.company,
            usuario=self.user,
            tipo=AvailabilityType.VACATION,
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=5),
            aprobado=False,
            activo=True,
        )
        assert av.id is not None
        assert av.aprobado is False
        assert av.aprobado_por is None

    def test_constraint_fecha_fin_gte_inicio(self):
        with pytest.raises(Exception):
            with transaction.atomic():
                ResourceAvailability.objects.create(
                    company=self.company,
                    usuario=self.user,
                    tipo=AvailabilityType.SICK_LEAVE,
                    fecha_inicio=date.today() + timedelta(days=5),
                    fecha_fin=date.today(),  # anterior → falla
                    activo=True,
                )

    def test_tipos_distintos_mismas_fechas_permitido(self):
        """Vacation y training el mismo día: válido."""
        av1 = ResourceAvailability.objects.create(
            company=self.company, usuario=self.user,
            tipo=AvailabilityType.VACATION,
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            activo=True,
        )
        av2 = ResourceAvailability.objects.create(
            company=self.company, usuario=self.user,
            tipo=AvailabilityType.TRAINING,
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            activo=True,
        )
        assert av1.id != av2.id

    def test_aprobacion_guarda_aprobador(self):
        av = ResourceAvailability.objects.create(
            company=self.company, usuario=self.user,
            tipo=AvailabilityType.VACATION,
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=3),
            activo=True,
        )
        from django.utils import timezone
        av.aprobado        = True
        av.aprobado_por    = self.user2
        av.fecha_aprobacion = timezone.now()
        av.save()
        av.refresh_from_db()
        assert av.aprobado is True
        assert av.aprobado_por == self.user2
        assert av.fecha_aprobacion is not None

    def test_get_tipo_display(self):
        av = ResourceAvailability(tipo=AvailabilityType.SICK_LEAVE)
        assert av.get_tipo_display() == 'Incapacidad'
