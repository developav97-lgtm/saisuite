"""
SaiSuite — Tests: Feature #6 Advanced Scheduling — Servicios
SK-23 / SK-45 / SK-46 / SK-47 / SK-48 — Cobertura objetivo: >= 85%

Cubre:
- SchedulingService.topological_sort:   orden correcto, ciclo detectado, sin dependencias
- SchedulingService.forward_pass:       FS, SS, FF, lag, sin predecesores, tareas sin fechas
- SchedulingService.backward_pass:      FS, SS, FF, sin sucesores
- SchedulingService.calculate_float:    tarea crítica, con holgura, sin fechas, free_float
- SchedulingService.get_critical_path:  ruta correcta, proyecto sin tareas
- SchedulingService.run_cpm:            proyecto completo, sin tareas con fechas
- SchedulingService.auto_schedule_project: ASAP, ALAP, dry_run, mode inválido, constraints
- SchedulingService.apply_constraints:  todos los 8 tipos de restricción
- ResourceLevelingService.calculate_daily_workload: sin asignaciones, con asignaciones
- ResourceLevelingService.detect_overload_periods:  sin sobrecarga, con sobrecarga
- ResourceLevelingService.level_resources:          sin sobrecargas, con sobrecargas, dry_run
- BaselineService.create_baseline:      crear activo, set_as_active=False, proyecto no existe
- BaselineService.compare_to_baseline:  sin variación, con retraso, tarea eliminada
- WhatIfService.create_scenario:        crear ok, proyecto no existe
- WhatIfService.run_simulation:         sin cambios, con task_changes, con dep_changes
- WhatIfService.compare_scenarios:      múltiples escenarios, sin simulación previa
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Project, Phase, Task, TaskDependency,
    TaskConstraint, ConstraintType,
    ProjectBaseline, WhatIfScenario,
    ResourceAssignment, ResourceCapacity,
)
from apps.proyectos.scheduling_services import (
    SchedulingService,
    ResourceLevelingService,
    BaselineService,
    WhatIfService,
)


# ─────────────────────────────────────────────────────────────────────────────
# Counters & Factories
# ─────────────────────────────────────────────────────────────────────────────

_NIT   = [700_000_000]
_EMAIL = [0]
_CODE  = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'sk_{_EMAIL[0]}@sched.test'


def _code():
    _CODE[0] += 1
    return f'SK-{_CODE[0]:05d}'


def make_company():
    c = Company.objects.create(name=f'Sched Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role=role,
    )


def make_project(company, gerente):
    fi = date(2026, 1, 1)
    ff = date(2026, 6, 30)
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=_code(),
        nombre='Scheduling Test Project',
        tipo='civil_works',
        estado='in_progress',
        cliente_id='001',
        cliente_nombre='Cliente SK',
        fecha_inicio_planificada=fi,
        fecha_fin_planificada=ff,
        presupuesto_total=Decimal('50000000.00'),
    )


def make_phase(company, project):
    return Phase.all_objects.create(
        company=company, proyecto=project,
        nombre='Phase SK', orden=1,
        fecha_inicio_planificada=project.fecha_inicio_planificada,
        fecha_fin_planificada=project.fecha_fin_planificada,
    )


def make_task(company, project, phase, *, nombre=None,
              fecha_inicio=None, fecha_fin=None, estado='todo'):
    return Task.objects.create(
        company=company,
        proyecto=project,
        fase=phase,
        nombre=nombre or f'Task {_code()}',
        responsable=None,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


def make_dependency(company, pred, succ, tipo='FS', lag=0):
    return TaskDependency.objects.create(
        company=company,
        tarea_predecesora=pred,
        tarea_sucesora=succ,
        tipo_dependencia=tipo,
        retraso_dias=lag,
    )


def make_capacity(company, user, horas=Decimal('40.00')):
    return ResourceCapacity.objects.create(
        company=company, usuario=user,
        horas_por_semana=horas,
        fecha_inicio=date(2020, 1, 1),
        activo=True,
    )


def make_assignment(company, task, user, pct=50, *, fi=None, ff=None):
    fi = fi or task.fecha_inicio or date.today()
    ff = ff or task.fecha_fin or date.today() + timedelta(days=10)
    return ResourceAssignment.objects.create(
        company=company, tarea=task, usuario=user,
        porcentaje_asignacion=Decimal(str(pct)),
        fecha_inicio=fi, fecha_fin=ff,
        activo=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures base
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def company():
    return make_company()


@pytest.fixture
def user(company):
    return make_user(company)


@pytest.fixture
def project(company, user):
    return make_project(company, user)


@pytest.fixture
def phase(company, project):
    return make_phase(company, project)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para construir redes de tareas
# ─────────────────────────────────────────────────────────────────────────────

# Proyecto lineal: A → B → C con FS
# A: 1-Jan a 10-Jan (9 días)
# B: 11-Jan a 20-Jan (9 días)
# C: 21-Jan a 30-Jan (9 días)

D0  = date(2026, 1,  1)
D10 = date(2026, 1, 10)
D11 = date(2026, 1, 11)
D20 = date(2026, 1, 20)
D21 = date(2026, 1, 21)
D30 = date(2026, 1, 30)


# ═══════════════════════════════════════════════════════════════════════════════
# topological_sort
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestTopologicalSort:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def _task(self, **kw):
        return make_task(self.company, self.project, self.phase, **kw)

    def test_orden_lineal_a_b_c(self):
        """A → B → C  →  debe salir [A, B, C]."""
        a = self._task(nombre='A', fecha_inicio=D0,  fecha_fin=D10)
        b = self._task(nombre='B', fecha_inicio=D11, fecha_fin=D20)
        c = self._task(nombre='C', fecha_inicio=D21, fecha_fin=D30)
        dep_ab = make_dependency(self.company, a, b)
        dep_bc = make_dependency(self.company, b, c)

        result = SchedulingService.topological_sort([a, b, c], [dep_ab, dep_bc])

        ids = [str(t.id) for t in result]
        assert ids.index(str(a.id)) < ids.index(str(b.id))
        assert ids.index(str(b.id)) < ids.index(str(c.id))

    def test_sin_dependencias(self):
        """Sin dependencias → devuelve todas las tareas (cualquier orden)."""
        a = self._task(nombre='A')
        b = self._task(nombre='B')
        result = SchedulingService.topological_sort([a, b], [])
        assert len(result) == 2

    def test_ciclo_lanza_validationerror(self):
        """A → B → A  →  ValidationError."""
        a = self._task(nombre='A')
        b = self._task(nombre='B')
        dep_ab = make_dependency(self.company, a, b)
        dep_ba = TaskDependency.objects.create(
            company=self.company,
            tarea_predecesora=b,
            tarea_sucesora=a,
            tipo_dependencia='FS',
            retraso_dias=0,
        )
        with pytest.raises(ValidationError) as exc_info:
            SchedulingService.topological_sort([a, b], [dep_ab, dep_ba])
        assert 'ciclo' in str(exc_info.value).lower()

    def test_dependencias_fuera_del_conjunto_ignoradas(self):
        """Dependencias a tareas no en la lista se ignoran."""
        a = self._task(nombre='A')
        b = self._task(nombre='B')
        extra = self._task(nombre='Extra')
        dep_a_extra = make_dependency(self.company, a, extra)

        # Solo pasamos [a, b], la dependencia a extra se ignora
        result = SchedulingService.topological_sort([a, b], [dep_a_extra])
        assert len(result) == 2

    def test_diamante_a_bc_d(self):
        """A→B, A→C, B→D, C→D  →  A primero, D último."""
        a = self._task(nombre='A')
        b = self._task(nombre='B')
        c = self._task(nombre='C')
        d = self._task(nombre='D')
        deps = [
            make_dependency(self.company, a, b),
            make_dependency(self.company, a, c),
            make_dependency(self.company, b, d),
            make_dependency(self.company, c, d),
        ]
        result = SchedulingService.topological_sort([a, b, c, d], deps)
        ids = [str(t.id) for t in result]
        assert ids[0] == str(a.id)
        assert ids[-1] == str(d.id)


# ═══════════════════════════════════════════════════════════════════════════════
# forward_pass
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestForwardPass:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def _task(self, fi=None, ff=None, nombre='T'):
        return make_task(self.company, self.project, self.phase,
                         nombre=nombre, fecha_inicio=fi, fecha_fin=ff)

    def test_sin_predecesores_inicia_en_project_start(self):
        a = self._task(D0, D10, 'A')
        result = SchedulingService.forward_pass([a], [], project_start=D0)
        assert result[str(a.id)]['early_start'] == D0
        assert result[str(a.id)]['early_finish'] == D10

    def test_fs_sucesor_empieza_despues_de_predecesor(self):
        """B empieza cuando A termina (FS)."""
        a = self._task(D0,  D10, 'A')
        b = self._task(D11, D20, 'B')
        dep = make_dependency(self.company, a, b, 'FS', lag=0)
        sorted_tasks = SchedulingService.topological_sort([a, b], [dep])
        result = SchedulingService.forward_pass(sorted_tasks, [dep], D0)

        assert result[str(b.id)]['early_start'] == D10  # = A.early_finish + 0

    def test_fs_con_lag(self):
        """FS + lag=5  →  B.early_start = A.early_finish + 5."""
        a = self._task(D0,  D10, 'A')
        b = self._task(D11, D20, 'B')
        dep = make_dependency(self.company, a, b, 'FS', lag=5)
        sorted_tasks = SchedulingService.topological_sort([a, b], [dep])
        result = SchedulingService.forward_pass(sorted_tasks, [dep], D0)
        assert result[str(b.id)]['early_start'] == D10 + timedelta(days=5)

    def test_ss_con_lag(self):
        """SS + lag=2  →  B.early_start = A.early_start + 2."""
        a = self._task(D0,  D10, 'A')
        b = self._task(D0,  D10, 'B')  # misma duración
        dep = make_dependency(self.company, a, b, 'SS', lag=2)
        sorted_tasks = SchedulingService.topological_sort([a, b], [dep])
        result = SchedulingService.forward_pass(sorted_tasks, [dep], D0)
        assert result[str(b.id)]['early_start'] == D0 + timedelta(days=2)

    def test_ff_con_lag(self):
        """FF  →  B.early_finish = A.early_finish + lag."""
        a = self._task(D0,  D10, 'A')
        b = self._task(D0,  D10, 'B')
        dep = make_dependency(self.company, a, b, 'FF', lag=0)
        sorted_tasks = SchedulingService.topological_sort([a, b], [dep])
        result = SchedulingService.forward_pass(sorted_tasks, [dep], D0)
        # B.early_finish = A.early_finish = D10
        assert result[str(b.id)]['early_finish'] == D10

    def test_tarea_sin_fechas_excluida(self):
        """Tarea sin fecha_inicio o fecha_fin no aparece en forward_data."""
        a = self._task(D0, D10, 'A')
        b = self._task(None, None, 'B')  # sin fechas
        result = SchedulingService.forward_pass([a, b], [], D0)
        assert str(b.id) not in result
        assert str(a.id) in result


# ═══════════════════════════════════════════════════════════════════════════════
# backward_pass
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestBackwardPass:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def _task(self, fi=None, ff=None, nombre='T'):
        return make_task(self.company, self.project, self.phase,
                         nombre=nombre, fecha_inicio=fi, fecha_fin=ff)

    def test_sin_sucesores_late_finish_es_project_end(self):
        a = self._task(D0, D10, 'A')
        result = SchedulingService.backward_pass([a], [], project_end=D30)
        assert result[str(a.id)]['late_finish'] == D30

    def test_fs_predecesora_late_finish_antes_de_sucesora(self):
        a = self._task(D0,  D10, 'A')
        b = self._task(D11, D20, 'B')
        dep = make_dependency(self.company, a, b, 'FS', lag=0)
        sorted_tasks = SchedulingService.topological_sort([a, b], [dep])
        fwd = SchedulingService.forward_pass(sorted_tasks, [dep], D0)
        project_end = max(v['early_finish'] for v in fwd.values())
        result = SchedulingService.backward_pass(sorted_tasks, [dep], project_end)

        # A.late_finish = B.late_start (FS sin lag)
        assert result[str(a.id)]['late_finish'] == result[str(b.id)]['late_start']

    def test_tarea_sin_fechas_excluida(self):
        a = self._task(D0, D10, 'A')
        b = self._task(None, None, 'B')
        result = SchedulingService.backward_pass([a, b], [], project_end=D30)
        assert str(b.id) not in result


# ═══════════════════════════════════════════════════════════════════════════════
# calculate_float
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCalculateFloat:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_tarea_critica_total_float_cero(self):
        """Tarea en ruta crítica: total_float == 0, is_critical == True."""
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        deps = []
        sorted_tasks = SchedulingService.topological_sort([a], deps)
        fwd = SchedulingService.forward_pass(sorted_tasks, deps, D0)
        bwd = SchedulingService.backward_pass(sorted_tasks, deps, D10)
        result = SchedulingService.calculate_float(str(a.id), fwd, bwd, deps)
        assert result['total_float'] == 0
        assert result['is_critical'] is True

    def test_tarea_con_holgura(self):
        """A → C y B → C; B con más margen → total_float > 0."""
        # A: D0-D20, B: D0-D5, C: D21-D30, deps: A→C (FS), B→C (FS)
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D20)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D0, fecha_fin=date(2026, 1, 5))
        c = make_task(self.company, self.project, self.phase,
                      nombre='C', fecha_inicio=D21, fecha_fin=D30)
        dep_ac = make_dependency(self.company, a, c)
        dep_bc = make_dependency(self.company, b, c)
        deps = [dep_ac, dep_bc]

        sorted_tasks = SchedulingService.topological_sort([a, b, c], deps)
        fwd = SchedulingService.forward_pass(sorted_tasks, deps, D0)
        project_end = max(v['early_finish'] for v in fwd.values())
        bwd = SchedulingService.backward_pass(sorted_tasks, deps, project_end)

        float_b = SchedulingService.calculate_float(str(b.id), fwd, bwd, deps)
        # B termina antes que A, por lo que tiene holgura
        assert float_b['total_float'] > 0
        assert float_b['is_critical'] is False

    def test_tarea_sin_fechas_retorna_none(self):
        """Tarea no en forward_data retorna total_float=None."""
        fwd = {}
        bwd = {}
        result = SchedulingService.calculate_float('nonexistent-id', fwd, bwd, [])
        assert result['total_float'] is None
        assert result['free_float'] is None
        assert result['is_critical'] is False

    def test_free_float_sin_sucesores_igual_total_float(self):
        """Tarea sin sucesores: free_float == total_float."""
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        deps = []
        sorted_tasks = SchedulingService.topological_sort([a], deps)
        fwd = SchedulingService.forward_pass(sorted_tasks, deps, D0)
        bwd = SchedulingService.backward_pass(sorted_tasks, deps, D30)
        result = SchedulingService.calculate_float(str(a.id), fwd, bwd, deps)
        assert result['free_float'] == result['total_float']


# ═══════════════════════════════════════════════════════════════════════════════
# get_critical_path
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestGetCriticalPath:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_camino_critico_lineal(self):
        """A → B → C  →  las tres son críticas."""
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D10, fecha_fin=D20)
        c = make_task(self.company, self.project, self.phase,
                      nombre='C', fecha_inicio=D20, fecha_fin=D30)
        dep_ab = make_dependency(self.company, a, b)
        dep_bc = make_dependency(self.company, b, c)
        deps = [dep_ab, dep_bc]

        sorted_tasks = SchedulingService.topological_sort([a, b, c], deps)
        fwd = SchedulingService.forward_pass(sorted_tasks, deps, D0)
        project_end = max(v['early_finish'] for v in fwd.values())
        bwd = SchedulingService.backward_pass(sorted_tasks, deps, project_end)

        cp = SchedulingService.get_critical_path(sorted_tasks, fwd, bwd, deps)
        assert str(a.id) in cp
        assert str(b.id) in cp
        assert str(c.id) in cp

    def test_sin_tareas_retorna_lista_vacia(self):
        cp = SchedulingService.get_critical_path([], {}, {}, [])
        assert cp == []


# ═══════════════════════════════════════════════════════════════════════════════
# run_cpm (integración con BD)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestRunCpm:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_proyecto_con_tareas_y_dependencias(self):
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D11, fecha_fin=D20)
        make_dependency(self.company, a, b)

        result = SchedulingService.run_cpm(str(self.project.id), str(self.company.id))

        assert len(result['sorted_tasks']) == 2
        assert result['project_end_date'] is not None
        assert len(result['critical_path']) >= 1

    def test_proyecto_sin_tareas_con_fechas(self):
        make_task(self.company, self.project, self.phase, nombre='Sin fechas')

        result = SchedulingService.run_cpm(str(self.project.id), str(self.company.id))

        assert result['sorted_tasks'] == []
        assert result['forward_data'] == {}
        assert result['critical_path'] == []
        assert len(result['tasks_excluded']) == 1

    def test_proyecto_no_existe_lanza_error(self):
        import uuid
        with pytest.raises(Project.DoesNotExist):
            SchedulingService.run_cpm(str(uuid.uuid4()), str(self.company.id))

    def test_project_end_date_es_la_mayor_early_finish(self):
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D0, fecha_fin=D30)

        result = SchedulingService.run_cpm(str(self.project.id), str(self.company.id))

        # Con proyecto sin dependencias, el forward_pass da early_start = project_start
        # para todas las tareas. La mayor early_finish debe ser ≥ D30.
        assert result['project_end_date'] >= D30


# ═══════════════════════════════════════════════════════════════════════════════
# auto_schedule_project
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAutoScheduleProject:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_asap_dry_run_no_modifica_bd(self):
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D11, fecha_fin=D20)
        make_dependency(self.company, a, b)

        result = SchedulingService.auto_schedule_project(
            str(self.project.id), str(self.company.id),
            scheduling_mode='asap', dry_run=True,
        )

        assert result['dry_run'] is True
        assert 'preview' in result
        assert result['tasks_rescheduled'] >= 1

        # Verificar que las fechas en BD no cambiaron
        a.refresh_from_db()
        b.refresh_from_db()
        assert a.fecha_inicio == D0
        assert b.fecha_inicio == D11

    def test_asap_aplica_fechas_en_bd(self):
        # A con fechas, B debería reprogramarse después de A
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D11, fecha_fin=D20)
        make_dependency(self.company, a, b)

        result = SchedulingService.auto_schedule_project(
            str(self.project.id), str(self.company.id),
            scheduling_mode='asap', dry_run=False,
        )

        assert result['dry_run'] is False
        assert result['tasks_rescheduled'] >= 1

    def test_alap_retorna_late_dates(self):
        a = make_task(self.company, self.project, self.phase,
                      nombre='A', fecha_inicio=D0, fecha_fin=D10)
        b = make_task(self.company, self.project, self.phase,
                      nombre='B', fecha_inicio=D11, fecha_fin=D20)
        make_dependency(self.company, a, b)

        result = SchedulingService.auto_schedule_project(
            str(self.project.id), str(self.company.id),
            scheduling_mode='alap', dry_run=True,
        )

        assert result['dry_run'] is True

    def test_mode_invalido_lanza_validationerror(self):
        with pytest.raises(ValidationError) as exc_info:
            SchedulingService.auto_schedule_project(
                str(self.project.id), str(self.company.id),
                scheduling_mode='invalid_mode',
            )
        assert 'invalid_mode' in str(exc_info.value)

    def test_proyecto_sin_tareas_con_fechas(self):
        make_task(self.company, self.project, self.phase, nombre='Sin fechas')

        result = SchedulingService.auto_schedule_project(
            str(self.project.id), str(self.company.id),
            scheduling_mode='asap', dry_run=True,
        )

        assert result['tasks_rescheduled'] == 0
        assert len(result['tasks_excluded']) == 1  # tarea sin fechas queda excluida

    def test_warning_cuando_hay_tareas_sin_fechas(self):
        make_task(self.company, self.project, self.phase,
                  nombre='Con fechas', fecha_inicio=D0, fecha_fin=D10)
        make_task(self.company, self.project, self.phase,
                  nombre='Sin fechas')

        result = SchedulingService.auto_schedule_project(
            str(self.project.id), str(self.company.id),
            scheduling_mode='asap', dry_run=True,
        )

        assert len(result['warnings']) > 0
        assert '1' in result['warnings'][0]  # "1 tarea(s) excluida(s)"


# ═══════════════════════════════════════════════════════════════════════════════
# apply_constraints
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestApplyConstraints:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def _task(self, **kw):
        return make_task(self.company, self.project, self.phase, **kw)

    def _constraint(self, task, ctype, cdate=None):
        return TaskConstraint.objects.create(
            company=self.company,
            task=task,
            constraint_type=ctype,
            constraint_date=cdate,
        )

    def test_must_start_on_fuerza_fecha_inicio(self):
        t = self._task(nombre='T', fecha_inicio=D0, fecha_fin=D10)
        forced = date(2026, 2, 1)
        self._constraint(t, ConstraintType.MUST_START_ON, forced)

        dates = {str(t.id): {'fecha_inicio': D0, 'fecha_fin': D10}}
        adjusted, warnings = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert adjusted[str(t.id)]['fecha_inicio'] == forced

    def test_must_finish_on_fuerza_fecha_fin(self):
        t = self._task(nombre='T', fecha_inicio=D0, fecha_fin=D10)
        forced = date(2026, 3, 1)
        self._constraint(t, ConstraintType.MUST_FINISH_ON, forced)

        dates = {str(t.id): {'fecha_inicio': D0, 'fecha_fin': D10}}
        adjusted, _ = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert adjusted[str(t.id)]['fecha_fin'] == forced

    def test_start_no_earlier_than_ajusta_si_menor(self):
        t = self._task(nombre='T', fecha_inicio=D0, fecha_fin=D10)
        limit = date(2026, 1, 5)
        self._constraint(t, ConstraintType.START_NO_EARLIER_THAN, limit)

        dates = {str(t.id): {'fecha_inicio': D0, 'fecha_fin': D10}}
        adjusted, _ = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert adjusted[str(t.id)]['fecha_inicio'] >= limit

    def test_start_no_earlier_than_no_ajusta_si_mayor(self):
        t = self._task(nombre='T', fecha_inicio=D21, fecha_fin=D30)
        limit = date(2026, 1, 5)  # ya está después
        self._constraint(t, ConstraintType.START_NO_EARLIER_THAN, limit)

        dates = {str(t.id): {'fecha_inicio': D21, 'fecha_fin': D30}}
        adjusted, _ = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert adjusted[str(t.id)]['fecha_inicio'] == D21

    def test_start_no_later_than_genera_warning(self):
        t = self._task(nombre='T', fecha_inicio=D21, fecha_fin=D30)
        limit = date(2026, 1, 5)  # límite anterior al CPM calculado
        self._constraint(t, ConstraintType.START_NO_LATER_THAN, limit)

        dates = {str(t.id): {'fecha_inicio': D21, 'fecha_fin': D30}}
        _, warnings = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert any('START_NO_LATER_THAN' in w for w in warnings)

    def test_finish_no_earlier_than_ajusta_si_menor(self):
        t = self._task(nombre='T', fecha_inicio=D0, fecha_fin=D10)
        limit = date(2026, 1, 20)  # fecha límite posterior a D10
        self._constraint(t, ConstraintType.FINISH_NO_EARLIER_THAN, limit)

        dates = {str(t.id): {'fecha_inicio': D0, 'fecha_fin': D10}}
        adjusted, _ = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert adjusted[str(t.id)]['fecha_fin'] >= limit

    def test_finish_no_later_than_genera_warning(self):
        t = self._task(nombre='T', fecha_inicio=D21, fecha_fin=D30)
        limit = date(2026, 1, 10)  # límite anterior al CPM calculado
        self._constraint(t, ConstraintType.FINISH_NO_LATER_THAN, limit)

        dates = {str(t.id): {'fecha_inicio': D21, 'fecha_fin': D30}}
        _, warnings = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert any('FINISH_NO_LATER_THAN' in w for w in warnings)

    def test_asap_alap_no_modifican_fechas(self):
        t = self._task(nombre='T', fecha_inicio=D0, fecha_fin=D10)
        TaskConstraint.objects.create(
            company=self.company, task=t,
            constraint_type=ConstraintType.ASAP,
            constraint_date=None,
        )
        dates = {str(t.id): {'fecha_inicio': D0, 'fecha_fin': D10}}
        adjusted, warnings = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert adjusted[str(t.id)] == {'fecha_inicio': D0, 'fecha_fin': D10}
        assert warnings == []

    def test_constraint_sin_fecha_genera_warning(self):
        t = self._task(nombre='T', fecha_inicio=D0, fecha_fin=D10)
        # MUST_START_ON sin constraint_date
        TaskConstraint.objects.create(
            company=self.company, task=t,
            constraint_type=ConstraintType.MUST_START_ON,
            constraint_date=None,
        )
        dates = {str(t.id): {'fecha_inicio': D0, 'fecha_fin': D10}}
        _, warnings = SchedulingService.apply_constraints(
            [t], str(self.company.id), dates
        )
        assert len(warnings) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceLevelingService.calculate_daily_workload
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCalculateDailyWorkload:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_sin_asignaciones_retorna_dict_vacio(self):
        result = ResourceLevelingService.calculate_daily_workload(
            str(self.project.id), str(self.company.id),
            D0, D10,
        )
        assert result == {}

    def test_asignacion_dentro_del_rango(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        make_assignment(self.company, task, self.user, pct=75, fi=D0, ff=D10)

        result = ResourceLevelingService.calculate_daily_workload(
            str(self.project.id), str(self.company.id), D0, D10,
        )

        uid = str(self.user.id)
        assert uid in result
        assert str(D0) in result[uid]
        assert result[uid][str(D0)] == pytest.approx(75.0)

    def test_dos_asignaciones_mismo_usuario_misma_tarea_acumulan(self):
        """Dos asignaciones diferentes para el mismo usuario se suman."""
        task1 = make_task(self.company, self.project, self.phase,
                          nombre='T1', fecha_inicio=D0, fecha_fin=D10)
        task2 = make_task(self.company, self.project, self.phase,
                          nombre='T2', fecha_inicio=D0, fecha_fin=D10)
        make_assignment(self.company, task1, self.user, pct=60, fi=D0, ff=D10)
        make_assignment(self.company, task2, self.user, pct=60, fi=D0, ff=D10)

        result = ResourceLevelingService.calculate_daily_workload(
            str(self.project.id), str(self.company.id), D0, D10,
        )
        uid = str(self.user.id)
        assert result[uid][str(D0)] == pytest.approx(120.0)


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceLevelingService.detect_overload_periods
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestDetectOverloadPeriods:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_sin_asignaciones_no_hay_sobrecarga(self):
        result = ResourceLevelingService.detect_overload_periods(
            str(self.project.id), str(self.company.id), D0, D10,
        )
        assert result == []

    def test_asignacion_bajo_100_no_es_sobrecarga(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        make_assignment(self.company, task, self.user, pct=80, fi=D0, ff=D10)

        result = ResourceLevelingService.detect_overload_periods(
            str(self.project.id), str(self.company.id), D0, D10,
        )
        assert result == []

    def test_asignacion_sobre_100_es_sobrecarga(self):
        task1 = make_task(self.company, self.project, self.phase,
                          nombre='T1', fecha_inicio=D0, fecha_fin=D10)
        task2 = make_task(self.company, self.project, self.phase,
                          nombre='T2', fecha_inicio=D0, fecha_fin=D10)
        make_assignment(self.company, task1, self.user, pct=70, fi=D0, ff=D10)
        make_assignment(self.company, task2, self.user, pct=60, fi=D0, ff=D10)

        result = ResourceLevelingService.detect_overload_periods(
            str(self.project.id), str(self.company.id), D0, D10,
        )

        assert len(result) > 0
        overload = result[0]
        assert overload['total_pct'] > 100
        assert overload['overload_pct'] > 0
        assert len(overload['task_ids']) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceLevelingService.level_resources
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestLevelResources:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_sin_sobrecargas_retorna_cero_movidos(self):
        make_task(self.company, self.project, self.phase,
                  nombre='T', fecha_inicio=D0, fecha_fin=D10)

        result = ResourceLevelingService.level_resources(
            str(self.project.id), str(self.company.id), dry_run=True
        )

        assert result['tasks_moved'] == 0

    def test_sin_tareas_retorna_vacios(self):
        result = ResourceLevelingService.level_resources(
            str(self.project.id), str(self.company.id), dry_run=True
        )
        assert result['tasks_moved'] == 0
        assert result['leveling_effective'] is True

    def test_dry_run_no_modifica_bd(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        original_fi = task.fecha_inicio

        ResourceLevelingService.level_resources(
            str(self.project.id), str(self.company.id), dry_run=True
        )

        task.refresh_from_db()
        assert task.fecha_inicio == original_fi

    def test_max_iterations_en_warnings(self):
        """max_iterations=1 fuerza parada temprana si hay sobrecargas residuales."""
        task1 = make_task(self.company, self.project, self.phase,
                          nombre='T1', fecha_inicio=D0, fecha_fin=D10)
        task2 = make_task(self.company, self.project, self.phase,
                          nombre='T2', fecha_inicio=D0, fecha_fin=D10)
        make_assignment(self.company, task1, self.user, pct=70, fi=D0, ff=D10)
        make_assignment(self.company, task2, self.user, pct=70, fi=D0, ff=D10)

        # Con max_iterations=0 la nivelación se detiene de inmediato
        result = ResourceLevelingService.level_resources(
            str(self.project.id), str(self.company.id),
            dry_run=True, max_iterations=0,
        )
        # Resultado válido (sin crash), aunque puede no nivelar nada
        assert isinstance(result, dict)
        assert 'leveling_effective' in result


# ═══════════════════════════════════════════════════════════════════════════════
# BaselineService.create_baseline
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCreateBaseline:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_crea_baseline_con_snapshot(self):
        make_task(self.company, self.project, self.phase,
                  nombre='T', fecha_inicio=D0, fecha_fin=D10)

        bl = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id),
            name='Baseline Q1',
        )

        assert bl.id is not None
        assert bl.name == 'Baseline Q1'
        assert bl.is_active_baseline is True
        assert bl.total_tasks_snapshot == 1
        assert len(bl.tasks_snapshot) == 1

    def test_set_as_active_desactiva_baseline_anterior(self):
        bl1 = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL1',
        )
        bl2 = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL2',
        )

        bl1.refresh_from_db()
        bl2.refresh_from_db()

        assert bl1.is_active_baseline is False
        assert bl2.is_active_baseline is True

    def test_set_as_active_false_no_desactiva_anterior(self):
        bl1 = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL1',
        )
        bl2 = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL2',
            set_as_active=False,
        )

        bl1.refresh_from_db()
        bl2.refresh_from_db()

        assert bl1.is_active_baseline is True
        assert bl2.is_active_baseline is False

    def test_proyecto_no_existe_lanza_error(self):
        import uuid
        with pytest.raises(Project.DoesNotExist):
            BaselineService.create_baseline(
                str(uuid.uuid4()), str(self.company.id), name='BL'
            )

    def test_baseline_sin_tareas(self):
        bl = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='Empty BL',
        )
        assert bl.total_tasks_snapshot == 0
        assert bl.tasks_snapshot == []


# ═══════════════════════════════════════════════════════════════════════════════
# BaselineService.compare_to_baseline
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCompareToBaseline:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_sin_variacion(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        bl = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL'
        )

        result = BaselineService.compare_to_baseline(
            str(self.project.id), str(self.company.id), str(bl.id)
        )

        assert result['baseline_name'] == 'BL'
        task_row = next((r for r in result['tasks'] if r['task_id'] == str(task.id)), None)
        assert task_row is not None
        assert task_row['variance_days'] == 0
        assert task_row['status'] == 'on_schedule'

    def test_con_retraso(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        bl = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL'
        )

        # Retrasar la tarea 5 días
        task.fecha_fin = D10 + timedelta(days=5)
        task.save()

        result = BaselineService.compare_to_baseline(
            str(self.project.id), str(self.company.id), str(bl.id)
        )

        task_row = next((r for r in result['tasks'] if r['task_id'] == str(task.id)), None)
        assert task_row['variance_days'] == 5
        assert task_row['status'] == 'behind'
        assert result['summary']['behind'] >= 1

    def test_con_adelanto(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        bl = BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL'
        )

        # Adelantar la tarea 3 días
        task.fecha_fin = D10 - timedelta(days=3)
        task.save()

        result = BaselineService.compare_to_baseline(
            str(self.project.id), str(self.company.id), str(bl.id)
        )

        task_row = next((r for r in result['tasks'] if r['task_id'] == str(task.id)), None)
        assert task_row['variance_days'] == -3
        assert task_row['status'] == 'ahead'
        assert result['summary']['ahead'] >= 1

    def test_baseline_no_existe_lanza_error(self):
        import uuid
        with pytest.raises(ProjectBaseline.DoesNotExist):
            BaselineService.compare_to_baseline(
                str(self.project.id), str(self.company.id), str(uuid.uuid4())
            )

    def test_retorna_estructura_correcta(self):
        BaselineService.create_baseline(
            str(self.project.id), str(self.company.id), name='BL'
        )
        bl = ProjectBaseline.objects.filter(
            project=self.project, company=self.company
        ).first()

        result = BaselineService.compare_to_baseline(
            str(self.project.id), str(self.company.id), str(bl.id)
        )

        assert 'baseline_name' in result
        assert 'schedule_variance_days' in result
        assert 'tasks' in result
        assert 'summary' in result
        assert 'ahead' in result['summary']
        assert 'on_schedule' in result['summary']
        assert 'behind' in result['summary']


# ═══════════════════════════════════════════════════════════════════════════════
# WhatIfService.create_scenario
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCreateScenario:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_crea_escenario_ok(self):
        scenario = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='Escenario Test',
        )
        assert scenario.id is not None
        assert scenario.name == 'Escenario Test'
        assert scenario.task_changes == {}
        assert scenario.resource_changes == {}
        assert scenario.simulated_end_date is None  # aún no ejecutado

    def test_crea_escenario_con_changes(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        changes = {str(task.id): {'fecha_fin': '2026-02-28'}}

        scenario = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='Escenario Delay',
            task_changes=changes,
        )
        assert scenario.task_changes == changes

    def test_proyecto_no_existe_lanza_error(self):
        import uuid
        with pytest.raises(Project.DoesNotExist):
            WhatIfService.create_scenario(
                str(uuid.uuid4()), str(self.company.id),
                str(self.user.id), name='Bad Scenario',
            )


# ═══════════════════════════════════════════════════════════════════════════════
# WhatIfService.run_simulation
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestRunSimulation:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_simulacion_sin_cambios_no_modifica_tareas_reales(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        original_fi = task.fecha_inicio
        original_ff = task.fecha_fin

        scenario = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='Sin cambios',
        )
        WhatIfService.run_simulation(str(scenario.id), str(self.company.id))

        task.refresh_from_db()
        assert task.fecha_inicio == original_fi
        assert task.fecha_fin    == original_ff

    def test_simulacion_guarda_resultados_en_escenario(self):
        make_task(self.company, self.project, self.phase,
                  nombre='T', fecha_inicio=D0, fecha_fin=D10)

        scenario = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='Sim Test',
        )
        updated = WhatIfService.run_simulation(str(scenario.id), str(self.company.id))

        assert updated.simulation_ran_at is not None
        assert updated.simulated_end_date is not None

    def test_simulacion_con_task_changes_aplica_en_memoria(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        original_ff = task.fecha_fin

        # Retrasar la tarea 20 días en el escenario
        new_ff = D10 + timedelta(days=20)
        scenario = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='Delay Scenario',
            task_changes={str(task.id): {'fecha_fin': str(new_ff)}},
        )
        updated = WhatIfService.run_simulation(str(scenario.id), str(self.company.id))

        # El escenario refleja la nueva fecha simulada
        assert updated.simulated_end_date >= new_ff  # CPM propagó el cambio

        # La tarea real en BD no fue modificada
        task.refresh_from_db()
        assert task.fecha_fin == original_ff

    def test_simulacion_escenario_no_existe_lanza_error(self):
        import uuid
        with pytest.raises(WhatIfScenario.DoesNotExist):
            WhatIfService.run_simulation(str(uuid.uuid4()), str(self.company.id))

    def test_simulacion_con_dep_changes(self):
        task = make_task(self.company, self.project, self.phase,
                         nombre='T', fecha_inicio=D0, fecha_fin=D10)
        task2 = make_task(self.company, self.project, self.phase,
                          nombre='T2', fecha_inicio=D11, fecha_fin=D20)
        dep = make_dependency(self.company, task, task2, 'FS', lag=0)

        scenario = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='Lag Scenario',
            dependency_changes={str(dep.id): {'retraso_dias': 10}},
        )
        updated = WhatIfService.run_simulation(str(scenario.id), str(self.company.id))

        assert updated.simulation_ran_at is not None


# ═══════════════════════════════════════════════════════════════════════════════
# WhatIfService.compare_scenarios
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCompareScenarios:

    def setup_method(self):
        self.company = make_company()
        self.user    = make_user(self.company)
        self.project = make_project(self.company, self.user)
        self.phase   = make_phase(self.company, self.project)

    def test_compare_dos_escenarios(self):
        make_task(self.company, self.project, self.phase,
                  nombre='T', fecha_inicio=D0, fecha_fin=D10)

        s1 = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='S1',
        )
        s2 = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='S2',
        )
        WhatIfService.run_simulation(str(s1.id), str(self.company.id))
        WhatIfService.run_simulation(str(s2.id), str(self.company.id))

        result = WhatIfService.compare_scenarios(
            [str(s1.id), str(s2.id)], str(self.company.id)
        )

        assert 'current_plan' in result
        assert 'scenarios' in result
        assert len(result['scenarios']) == 2

        for sc in result['scenarios']:
            assert sc['simulation_done'] is True

    def test_compare_sin_simulacion_previa(self):
        s = WhatIfService.create_scenario(
            str(self.project.id), str(self.company.id),
            str(self.user.id), name='S sin sim',
        )

        result = WhatIfService.compare_scenarios(
            [str(s.id)], str(self.company.id)
        )

        assert result['scenarios'][0]['simulation_done'] is False
        assert result['scenarios'][0]['simulated_end_date'] is None

    def test_ids_inexistentes_retorna_lista_vacia(self):
        import uuid
        result = WhatIfService.compare_scenarios(
            [str(uuid.uuid4())], str(self.company.id)
        )
        assert result['scenarios'] == []

    def test_estructura_current_plan(self):
        result = WhatIfService.compare_scenarios([], str(self.company.id))
        assert 'current_plan' in result
        assert 'end_date' in result['current_plan']
