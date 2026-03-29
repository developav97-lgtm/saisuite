"""
SaiSuite — Tests: Feature #4 Resource Management — Servicios
BK-27 — Cobertura objetivo: >= 85% de apps.proyectos.resource_services

Cubre:
- assign_resource_to_task:       camino feliz + 6 validaciones
- remove_resource_from_task:     ok + ya inactiva + no existe
- detect_overallocation_conflicts: sin conflictos, con conflictos, threshold custom, exclude_id
- calculate_user_workload:       valores numéricos, sin capacidad, utilización >100%
- _count_business_days:          fin de semana, rango vacío, semana completa
- get_team_availability_timeline: equipo vacío, un usuario con asignaciones+ausencias
- set_user_capacity:             crear, actualizar, solapamiento
- register_availability:         ok + solapamiento mismo tipo + distinto tipo ok
- approve_availability:          aprobar, rechazar, no existe
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Project, Phase, Task,
    ResourceAssignment, ResourceCapacity, ResourceAvailability,
    AvailabilityType,
)
from apps.proyectos.resource_services import (
    assign_resource_to_task,
    remove_resource_from_task,
    detect_overallocation_conflicts,
    calculate_user_workload,
    _count_business_days,
    get_team_availability_timeline,
    set_user_capacity,
    register_availability,
    approve_availability,
)

# ── Counters ──────────────────────────────────────────────────────────────────

_NIT   = [600_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'rs_{_EMAIL[0]}@test.com'


# ── Factories ─────────────────────────────────────────────────────────────────

def make_company():
    c = Company.objects.create(name=f'RS Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role=role,
    )


def make_proyecto(company, gerente, estado='in_progress'):
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'RS-{_nit()}',
        nombre='Project RS Test',
        tipo='services',
        estado=estado,
        cliente_id='001',
        cliente_nombre='Cliente RS',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('5000000.00'),
    )


def make_fase(company, proyecto):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre='Fase RS', orden=1,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
    )


def make_tarea(company, proyecto, fase, responsable, estado='todo'):
    return Task.objects.create(
        company=company, proyecto=proyecto, fase=fase,
        nombre='Tarea RS', responsable=responsable, estado=estado,
    )


def make_capacity(company, user, horas=Decimal('40.00'), fecha_inicio=date(2020, 1, 1)):
    return ResourceCapacity.objects.create(
        company=company, usuario=user,
        horas_por_semana=horas,
        fecha_inicio=fecha_inicio,
        activo=True,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

TODAY = date.today()
IN_30 = TODAY + timedelta(days=30)


# ═══════════════════════════════════════════════════════════════════════════════
# assign_resource_to_task
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAssignResourceToTask:

    def setup_method(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.user2    = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.user)

    def test_asignacion_ok(self):
        a = assign_resource_to_task(
            tarea=self.tarea,
            usuario_id=str(self.user.id),
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=TODAY,
            fecha_fin=IN_30,
        )
        assert a.id is not None
        assert a.usuario == self.user
        assert a.tarea   == self.tarea
        assert a.activo  is True

    def test_dos_usuarios_distintos_misma_tarea(self):
        a1 = assign_resource_to_task(
            tarea=self.tarea, usuario_id=str(self.user.id),
            porcentaje_asignacion=Decimal('40.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30,
        )
        a2 = assign_resource_to_task(
            tarea=self.tarea, usuario_id=str(self.user2.id),
            porcentaje_asignacion=Decimal('60.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30,
        )
        assert a1.id != a2.id

    def test_falla_tarea_completada(self):
        self.tarea.estado = 'done'
        self.tarea.save()
        with pytest.raises(ValidationError) as exc:
            assign_resource_to_task(
                tarea=self.tarea, usuario_id=str(self.user.id),
                porcentaje_asignacion=Decimal('50.00'),
                fecha_inicio=TODAY, fecha_fin=IN_30,
            )
        assert 'tarea' in exc.value.message_dict

    def test_falla_proyecto_cerrado(self):
        self.proyecto.estado = 'closed'
        self.proyecto.save()
        with pytest.raises(ValidationError) as exc:
            assign_resource_to_task(
                tarea=self.tarea, usuario_id=str(self.user.id),
                porcentaje_asignacion=Decimal('50.00'),
                fecha_inicio=TODAY, fecha_fin=IN_30,
            )
        assert 'tarea' in exc.value.message_dict

    def test_falla_fecha_fin_anterior(self):
        with pytest.raises(ValidationError) as exc:
            assign_resource_to_task(
                tarea=self.tarea, usuario_id=str(self.user.id),
                porcentaje_asignacion=Decimal('50.00'),
                fecha_inicio=IN_30, fecha_fin=TODAY,
            )
        assert 'fecha_fin' in exc.value.message_dict

    def test_falla_usuario_otra_empresa(self):
        otra_company = make_company()
        otro_user    = make_user(otra_company)
        with pytest.raises(ValidationError) as exc:
            assign_resource_to_task(
                tarea=self.tarea, usuario_id=str(otro_user.id),
                porcentaje_asignacion=Decimal('50.00'),
                fecha_inicio=TODAY, fecha_fin=IN_30,
            )
        assert 'usuario_id' in exc.value.message_dict

    def test_falla_doble_asignacion_mismo_usuario(self):
        assign_resource_to_task(
            tarea=self.tarea, usuario_id=str(self.user.id),
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30,
        )
        with pytest.raises(ValidationError) as exc:
            assign_resource_to_task(
                tarea=self.tarea, usuario_id=str(self.user.id),
                porcentaje_asignacion=Decimal('30.00'),
                fecha_inicio=TODAY, fecha_fin=IN_30,
            )
        assert 'usuario_id' in exc.value.message_dict

    def test_porcentaje_cero_falla(self):
        with pytest.raises(ValidationError) as exc:
            assign_resource_to_task(
                tarea=self.tarea, usuario_id=str(self.user.id),
                porcentaje_asignacion=Decimal('0.00'),
                fecha_inicio=TODAY, fecha_fin=IN_30,
            )
        assert 'porcentaje_asignacion' in exc.value.message_dict


# ═══════════════════════════════════════════════════════════════════════════════
# remove_resource_from_task
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestRemoveResourceFromTask:

    def setup_method(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.user)
        self.asignacion = assign_resource_to_task(
            tarea=self.tarea, usuario_id=str(self.user.id),
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30,
        )

    def test_soft_delete_ok(self):
        remove_resource_from_task(
            asignacion_id=str(self.asignacion.id),
            company_id=str(self.company.id),
        )
        self.asignacion.refresh_from_db()
        assert self.asignacion.activo is False

    def test_soft_delete_no_elimina_registro(self):
        pk = self.asignacion.id
        remove_resource_from_task(str(pk), str(self.company.id))
        assert ResourceAssignment.objects.filter(id=pk).exists()

    def test_falla_ya_inactiva(self):
        remove_resource_from_task(str(self.asignacion.id), str(self.company.id))
        with pytest.raises(ValidationError) as exc:
            remove_resource_from_task(str(self.asignacion.id), str(self.company.id))
        assert 'asignacion_id' in exc.value.message_dict

    def test_falla_no_existe(self):
        import uuid
        with pytest.raises(ValidationError) as exc:
            remove_resource_from_task(str(uuid.uuid4()), str(self.company.id))
        assert 'asignacion_id' in exc.value.message_dict


# ═══════════════════════════════════════════════════════════════════════════════
# _count_business_days
# ═══════════════════════════════════════════════════════════════════════════════

class TestCountBusinessDays:
    """No requiere BD — tests puros."""

    def test_lunes_a_viernes_5_dias(self):
        lunes   = date(2026, 3, 23)  # Lunes
        viernes = date(2026, 3, 27)  # Viernes
        assert _count_business_days(lunes, viernes) == 5

    def test_lunes_a_domingo_5_dias(self):
        lunes   = date(2026, 3, 23)
        domingo = date(2026, 3, 29)
        assert _count_business_days(lunes, domingo) == 5

    def test_rango_vacio_devuelve_cero(self):
        manana = date(2026, 3, 24)
        hoy    = date(2026, 3, 23)
        assert _count_business_days(manana, hoy) == 0

    def test_mismo_dia_lunes_es_1(self):
        lunes = date(2026, 3, 23)
        assert _count_business_days(lunes, lunes) == 1

    def test_fin_de_semana_completo_es_0(self):
        sabado = date(2026, 3, 28)
        domingo = date(2026, 3, 29)
        assert _count_business_days(sabado, domingo) == 0

    def test_dos_semanas_son_10_dias(self):
        lunes  = date(2026, 3, 23)
        viernes2 = date(2026, 4, 3)
        assert _count_business_days(lunes, viernes2) == 10


# ═══════════════════════════════════════════════════════════════════════════════
# detect_overallocation_conflicts
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestDetectOverallocationConflicts:

    def setup_method(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)

    def _make_tarea(self, nombre='Tarea'):
        return make_tarea(self.company, self.proyecto, self.fase, self.user)

    def _assign(self, tarea, porcentaje, inicio=None, fin=None):
        start = inicio or TODAY
        end   = fin   or IN_30
        return ResourceAssignment.objects.create(
            company=self.company, tarea=tarea, usuario=self.user,
            porcentaje_asignacion=Decimal(str(porcentaje)),
            fecha_inicio=start, fecha_fin=end, activo=True,
        )

    def test_sin_asignaciones_devuelve_lista_vacia(self):
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert result == []

    def test_una_asignacion_80_sin_conflicto(self):
        t1 = self._make_tarea()
        self._assign(t1, 80)
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert result == []

    def test_dos_asignaciones_suman_110_genera_conflicto(self):
        t1 = self._make_tarea()
        t2 = Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Tarea 2', estado='todo',
        )
        self._assign(t1, 60)
        self._assign(t2, 50)
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert len(result) > 0
        assert result[0].porcentaje_total == Decimal('110')
        assert len(result[0].asignaciones) == 2

    def test_conflicto_solo_en_solapamiento(self):
        """Asignaciones que NO se solapan → sin conflicto."""
        t1 = self._make_tarea()
        t2 = Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Tarea 3', estado='todo',
        )
        # a1: hoy → hoy+10  | a2: hoy+11 → hoy+30 → no se solapan
        a1_fin   = TODAY + timedelta(days=10)
        a2_inicio = TODAY + timedelta(days=11)
        self._assign(t1, 80, fin=a1_fin)
        self._assign(t2, 80, inicio=a2_inicio)
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert result == []

    def test_threshold_custom(self):
        """Con threshold=120 una suma de 110 NO genera conflicto."""
        t1 = self._make_tarea()
        t2 = Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Tarea 4', estado='todo',
        )
        self._assign(t1, 60)
        self._assign(t2, 50)
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
            threshold=Decimal('120.00'),
        )
        assert result == []

    def test_exclude_asignacion_id(self):
        """Excluir una asignación debe eliminar el conflicto."""
        t1 = self._make_tarea()
        t2 = Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Tarea 5', estado='todo',
        )
        a1 = self._assign(t1, 60)
        a2 = self._assign(t2, 50)
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
            exclude_asignacion_id=str(a2.id),
        )
        assert result == []

    def test_resultado_ordenado_por_fecha(self):
        """Los conflictos deben estar ordenados cronológicamente."""
        t1 = self._make_tarea()
        t2 = Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Tarea 6', estado='todo',
        )
        self._assign(t1, 70)
        self._assign(t2, 60)
        result = detect_overallocation_conflicts(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        fechas = [c.fecha for c in result]
        assert fechas == sorted(fechas)


# ═══════════════════════════════════════════════════════════════════════════════
# calculate_user_workload
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCalculateUserWorkload:

    def setup_method(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.user)

    def test_sin_capacidad_horas_cero(self):
        """Sin ResourceCapacity → horas_capacidad = 0 y utilización = 0."""
        wl = calculate_user_workload(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert wl.horas_capacidad == Decimal('0.00')
        assert wl.porcentaje_utilizacion == Decimal('0.00')

    def test_capacidad_indefinida_calcula_horas(self):
        """Capacidad 40h/semana indefinida desde 2020."""
        make_capacity(self.company, self.user)
        wl = calculate_user_workload(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=date(2026, 3, 2),   # Lunes
            end_date=date(2026, 3, 6),     # Viernes = 5 días laborales
        )
        # 5 días laborales × (40h / 5 días) = 40h
        assert wl.horas_capacidad == Decimal('40.00')
        assert wl.horas_registradas == Decimal('0.00')
        assert wl.horas_asignadas == Decimal('0.00')

    def test_horas_asignadas_calculadas(self):
        """Con 50% de 40h/semana durante 5 días → 20h asignadas."""
        make_capacity(self.company, self.user)
        ResourceAssignment.objects.create(
            company=self.company, tarea=self.tarea, usuario=self.user,
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=date(2026, 3, 2),
            fecha_fin=date(2026, 3, 6),
            activo=True,
        )
        wl = calculate_user_workload(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 6),
        )
        assert wl.horas_asignadas == Decimal('20.00')

    def test_usuario_id_inexistente_retorna_ceros(self):
        """UUID que no existe → no crash, retorna ceros."""
        import uuid
        wl = calculate_user_workload(
            usuario_id=str(uuid.uuid4()),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert wl.horas_capacidad == Decimal('0.00')


# ═══════════════════════════════════════════════════════════════════════════════
# get_team_availability_timeline
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestGetTeamAvailabilityTimeline:

    def setup_method(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.user)

    def test_sin_assignments_ni_responsable_devuelve_lista_vacia(self):
        """Sin ResourceAssignment ni Task.responsable no hay equipo."""
        # Tarea sin responsable
        Task.objects.filter(id=self.tarea.id).update(responsable=None)
        result = get_team_availability_timeline(
            proyecto_id=str(self.proyecto.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert result == []

    def test_responsable_sin_assignment_aparece_en_timeline(self):
        """Un responsable de tarea sin ResourceAssignment debe aparecer en el timeline."""
        result = get_team_availability_timeline(
            proyecto_id=str(self.proyecto.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert len(result) == 1
        assert result[0].usuario_id == str(self.user.id)
        # La asignación viene de Task.responsable (fuente='responsable')
        assert len(result[0].asignaciones) == 1
        assert result[0].asignaciones[0]['fuente'] == 'responsable'

    def test_un_usuario_con_asignacion(self):
        ResourceAssignment.objects.create(
            company=self.company, tarea=self.tarea, usuario=self.user,
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30, activo=True,
        )
        result = get_team_availability_timeline(
            proyecto_id=str(self.proyecto.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert len(result) == 1
        assert result[0].usuario_id == str(self.user.id)
        assert len(result[0].asignaciones) == 1

    def test_ausencias_aprobadas_incluidas(self):
        ResourceAssignment.objects.create(
            company=self.company, tarea=self.tarea, usuario=self.user,
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30, activo=True,
        )
        ResourceAvailability.objects.create(
            company=self.company, usuario=self.user,
            tipo=AvailabilityType.VACATION,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
            aprobado=True, activo=True,
        )
        result = get_team_availability_timeline(
            proyecto_id=str(self.proyecto.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert len(result[0].ausencias) == 1

    def test_ausencias_no_aprobadas_excluidas(self):
        ResourceAssignment.objects.create(
            company=self.company, tarea=self.tarea, usuario=self.user,
            porcentaje_asignacion=Decimal('50.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30, activo=True,
        )
        ResourceAvailability.objects.create(
            company=self.company, usuario=self.user,
            tipo=AvailabilityType.VACATION,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
            aprobado=False, activo=True,
        )
        result = get_team_availability_timeline(
            proyecto_id=str(self.proyecto.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        assert len(result[0].ausencias) == 0

    def test_no_incluye_usuarios_de_otro_proyecto(self):
        """user2 con assignment en otro proyecto NO debe aparecer en self.proyecto."""
        otro_proyecto = make_proyecto(self.company, self.user)
        otra_fase     = make_fase(self.company, otro_proyecto)
        otra_tarea    = make_tarea(self.company, otro_proyecto, otra_fase, self.user)
        user2         = make_user(self.company)
        ResourceAssignment.objects.create(
            company=self.company, tarea=otra_tarea, usuario=user2,
            porcentaje_asignacion=Decimal('100.00'),
            fecha_inicio=TODAY, fecha_fin=IN_30, activo=True,
        )
        result = get_team_availability_timeline(
            proyecto_id=str(self.proyecto.id),
            company_id=str(self.company.id),
            start_date=TODAY,
            end_date=IN_30,
        )
        # self.user es responsable de self.tarea (en self.proyecto) → aparece
        # user2 solo tiene assignment en otro_proyecto → NO debe aparecer
        result_ids = [r.usuario_id for r in result]
        assert str(user2.id) not in result_ids
        assert str(self.user.id) in result_ids


# ═══════════════════════════════════════════════════════════════════════════════
# set_user_capacity
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestSetUserCapacity:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)

    def test_crear_capacidad_ok(self):
        cap = set_user_capacity(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            horas_por_semana=Decimal('40.00'),
            fecha_inicio=date(2024, 1, 1),
        )
        assert cap.id is not None
        assert cap.horas_por_semana == Decimal('40.00')
        assert cap.fecha_fin is None

    def test_actualizar_capacidad_existente(self):
        cap = set_user_capacity(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            horas_por_semana=Decimal('40.00'),
            fecha_inicio=date(2024, 1, 1),
        )
        cap_actualizada = set_user_capacity(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            horas_por_semana=Decimal('32.00'),
            fecha_inicio=date(2024, 1, 1),
            capacity_id=str(cap.id),
        )
        assert cap_actualizada.id == cap.id
        assert cap_actualizada.horas_por_semana == Decimal('32.00')

    def test_solapamiento_genera_error(self):
        set_user_capacity(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            horas_por_semana=Decimal('40.00'),
            fecha_inicio=date(2024, 1, 1),
        )
        with pytest.raises(ValidationError) as exc:
            set_user_capacity(
                usuario_id=str(self.user.id),
                company_id=str(self.company.id),
                horas_por_semana=Decimal('32.00'),
                fecha_inicio=date(2025, 6, 1),
            )
        assert 'fecha_inicio' in exc.value.message_dict

    def test_usuario_otra_empresa_falla(self):
        otra = make_company()
        otro_user = make_user(otra)
        with pytest.raises(ValidationError) as exc:
            set_user_capacity(
                usuario_id=str(otro_user.id),
                company_id=str(self.company.id),
                horas_por_semana=Decimal('40.00'),
                fecha_inicio=date(2024, 1, 1),
            )
        assert 'usuario_id' in exc.value.message_dict

    def test_fecha_fin_igual_inicio_falla(self):
        with pytest.raises(ValidationError) as exc:
            set_user_capacity(
                usuario_id=str(self.user.id),
                company_id=str(self.company.id),
                horas_por_semana=Decimal('40.00'),
                fecha_inicio=date(2024, 6, 1),
                fecha_fin=date(2024, 6, 1),
            )
        assert 'fecha_fin' in exc.value.message_dict


# ═══════════════════════════════════════════════════════════════════════════════
# register_availability
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestRegisterAvailability:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)

    def test_registrar_ausencia_ok(self):
        av = register_availability(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            tipo=AvailabilityType.VACATION,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
        )
        assert av.id is not None
        assert av.aprobado is False

    def test_solapamiento_mismo_tipo_falla(self):
        register_availability(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            tipo=AvailabilityType.VACATION,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
        )
        with pytest.raises(ValidationError) as exc:
            register_availability(
                usuario_id=str(self.user.id),
                company_id=str(self.company.id),
                tipo=AvailabilityType.VACATION,
                fecha_inicio=TODAY + timedelta(days=3),
                fecha_fin=TODAY + timedelta(days=10),
            )
        assert 'fecha_inicio' in exc.value.message_dict

    def test_distinto_tipo_mismas_fechas_ok(self):
        register_availability(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            tipo=AvailabilityType.VACATION,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
        )
        av2 = register_availability(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            tipo=AvailabilityType.TRAINING,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
        )
        assert av2.id is not None

    def test_tipo_invalido_falla(self):
        with pytest.raises(ValidationError) as exc:
            register_availability(
                usuario_id=str(self.user.id),
                company_id=str(self.company.id),
                tipo='not_a_valid_type',
                fecha_inicio=TODAY,
                fecha_fin=TODAY + timedelta(days=3),
            )
        assert 'tipo' in exc.value.message_dict

    def test_fecha_fin_anterior_inicio_falla(self):
        with pytest.raises(ValidationError) as exc:
            register_availability(
                usuario_id=str(self.user.id),
                company_id=str(self.company.id),
                tipo=AvailabilityType.SICK_LEAVE,
                fecha_inicio=TODAY + timedelta(days=5),
                fecha_fin=TODAY,
            )
        assert 'fecha_fin' in exc.value.message_dict

    def test_usuario_otra_empresa_falla(self):
        otra = make_company()
        otro = make_user(otra)
        with pytest.raises(ValidationError) as exc:
            register_availability(
                usuario_id=str(otro.id),
                company_id=str(self.company.id),
                tipo=AvailabilityType.VACATION,
                fecha_inicio=TODAY,
                fecha_fin=TODAY + timedelta(days=3),
            )
        assert 'usuario_id' in exc.value.message_dict


# ═══════════════════════════════════════════════════════════════════════════════
# approve_availability
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestApproveAvailability:

    def setup_method(self):
        self.company   = make_company()
        self.user      = make_user(self.company)
        self.aprobador = make_user(self.company)
        self.ausencia  = register_availability(
            usuario_id=str(self.user.id),
            company_id=str(self.company.id),
            tipo=AvailabilityType.VACATION,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=5),
        )

    def test_aprobar_ok(self):
        av = approve_availability(
            ausencia_id=str(self.ausencia.id),
            company_id=str(self.company.id),
            aprobador_id=str(self.aprobador.id),
            aprobar=True,
        )
        assert av.aprobado is True
        assert av.aprobado_por == self.aprobador
        assert av.fecha_aprobacion is not None

    def test_rechazar_limpia_aprobador(self):
        # Primero aprobamos
        approve_availability(
            ausencia_id=str(self.ausencia.id),
            company_id=str(self.company.id),
            aprobador_id=str(self.aprobador.id),
            aprobar=True,
        )
        # Luego rechazamos
        av = approve_availability(
            ausencia_id=str(self.ausencia.id),
            company_id=str(self.company.id),
            aprobador_id=str(self.aprobador.id),
            aprobar=False,
        )
        assert av.aprobado is False
        assert av.aprobado_por is None
        assert av.fecha_aprobacion is None

    def test_ausencia_inexistente_falla(self):
        import uuid
        with pytest.raises(ValidationError) as exc:
            approve_availability(
                ausencia_id=str(uuid.uuid4()),
                company_id=str(self.company.id),
                aprobador_id=str(self.aprobador.id),
            )
        assert 'ausencia_id' in exc.value.message_dict

    def test_aprobador_otra_empresa_falla(self):
        otra        = make_company()
        otro_aprob  = make_user(otra)
        with pytest.raises(ValidationError) as exc:
            approve_availability(
                ausencia_id=str(self.ausencia.id),
                company_id=str(self.company.id),
                aprobador_id=str(otro_aprob.id),
            )
        assert 'aprobador_id' in exc.value.message_dict

    def test_ausencia_otra_empresa_falla(self):
        """No debe poder aprobarse una ausencia de otra empresa."""
        otra       = make_company()
        otro_user  = make_user(otra)
        otro_aprob = make_user(otra)
        otra_aus   = register_availability(
            usuario_id=str(otro_user.id),
            company_id=str(otra.id),
            tipo=AvailabilityType.SICK_LEAVE,
            fecha_inicio=TODAY,
            fecha_fin=TODAY + timedelta(days=3),
        )
        with pytest.raises(ValidationError):
            approve_availability(
                ausencia_id=str(otra_aus.id),
                company_id=str(self.company.id),  # empresa incorrecta
                aprobador_id=str(self.aprobador.id),
            )
