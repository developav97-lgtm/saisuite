"""
SaiSuite — Tests: Tarea model
Cobertura objetivo: >= 85% de apps.proyectos.models (clases Tarea y TareaTag)
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, Tarea, TareaTag

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

NIT_COUNTER = [9040_10_000]


def next_nit():
    NIT_COUNTER[0] += 1
    return str(NIT_COUNTER[0])


EMAIL_COUNTER = [0]


def next_email():
    EMAIL_COUNTER[0] += 1
    return f'tarea_user_{EMAIL_COUNTER[0]}@test.com'


def make_company(nit=None):
    nit = nit or next_nit()
    c = Company.objects.create(name=f'Tarea Test Co {nit}', nit=nit)
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, email=None):
    return User.objects.create_user(
        email=email or next_email(),
        password='Pass1234!',
        company=company,
        role='company_admin',
        is_active=True,
    )


def make_proyecto(company, gerente, codigo=None):
    codigo = codigo or f'PRY-{next_nit()}'
    return Proyecto.all_objects.create(
        company=company,
        gerente=gerente,
        codigo=codigo,
        nombre='Proyecto Test Tarea',
        tipo='civil_works',
        cliente_id='111',
        cliente_nombre='Cliente',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('10000000.00'),
    )


def make_fase(proyecto, orden=None):
    if orden is None:
        max_ord = Fase.all_objects.filter(proyecto=proyecto).order_by('-orden').values_list('orden', flat=True).first()
        orden = (max_ord or 0) + 1
    return Fase.all_objects.create(
        company=proyecto.company,
        proyecto=proyecto,
        nombre=f'Fase {orden}',
        orden=orden,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('1000000'),
    )


def make_tarea(company, proyecto, **kwargs):
    # fase es obligatoria desde DEC-021; crear una por defecto si no se provee
    if 'fase' not in kwargs:
        kwargs['fase'] = make_fase(proyecto)
    defaults = dict(nombre='Tarea de prueba', estado='todo')
    defaults.update(kwargs)
    return Tarea.all_objects.create(company=company, proyecto=proyecto, **defaults)


def make_tag(company, nombre='bug', color='red'):
    return TareaTag.all_objects.create(company=company, nombre=nombre, color=color)


# ── Tests: TareaTag ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTareaTagModel:

    def test_crear_tag(self):
        c = make_company()
        tag = make_tag(c, nombre='feature', color='green')
        assert tag.id is not None
        assert tag.nombre == 'feature'
        assert tag.color == 'green'

    def test_str_retorna_nombre(self):
        c = make_company()
        tag = make_tag(c, nombre='bug')
        assert str(tag) == 'bug'

    def test_unique_together_company_nombre(self):
        from django.db import IntegrityError
        c = make_company()
        make_tag(c, nombre='duplicado')
        with pytest.raises(IntegrityError):
            TareaTag.all_objects.create(company=c, nombre='duplicado', color='blue')

    def test_mismo_nombre_diferente_empresa(self):
        c1 = make_company()
        c2 = make_company()
        t1 = make_tag(c1, nombre='shared-tag')
        t2 = make_tag(c2, nombre='shared-tag')
        assert t1.id != t2.id

    def test_color_default_blue(self):
        c = make_company()
        tag = TareaTag.all_objects.create(company=c, nombre='sin-color')
        assert tag.color == 'blue'


# ── Tests: Tarea — Básico ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTareaModelBasico:

    def test_crear_tarea_minima(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.id is not None
        assert t.proyecto_id == p.id
        assert t.estado == 'todo'

    def test_codigo_autogenerado_task(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.codigo.startswith('TASK-')
        assert len(t.codigo) == 10  # TASK-00001

    def test_codigos_secuenciales(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t1 = make_tarea(c, p, nombre='T1')
        t2 = make_tarea(c, p, nombre='T2')
        # Ambos deben ser distintos
        assert t1.codigo != t2.codigo

    def test_codigo_no_regenera_si_ya_tiene(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p, codigo='TASK-99999')
        assert t.codigo == 'TASK-99999'

    def test_str_con_codigo(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p, nombre='Mi Tarea')
        assert t.codigo in str(t)
        assert 'Mi Tarea' in str(t)

    def test_str_sin_codigo(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = Tarea(company=c, proyecto=p, nombre='Sin Código')
        assert str(t) == 'Sin Código'

    def test_estado_default_por_hacer(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.estado == 'todo'

    def test_prioridad_default_normal(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.prioridad == 2

    def test_porcentaje_completado_default_cero(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.porcentaje_completado == 0

    def test_horas_estimadas_default_cero(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.horas_estimadas == Decimal('0')

    def test_tarea_con_fase(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        f = make_fase(p)
        t = make_tarea(c, p, fase=f)
        assert t.fase_id == f.id

    def test_tarea_con_responsable(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p, responsable=g)
        assert t.responsable_id == g.id

    def test_tarea_con_tags(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        tag = make_tag(c, nombre='tag-test')
        t = make_tarea(c, p)
        t.tags.add(tag)
        assert t.tags.count() == 1

    def test_tarea_con_followers(self):
        c = make_company()
        g = make_user(c)
        u2 = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        t.followers.add(u2)
        assert t.followers.count() == 1

    def test_actividad_proyecto_id_nullable(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.actividad_proyecto_id is None


# ── Tests: Tarea — Jerarquía ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestTareaJerarquia:

    def test_subtarea_sin_padre_nivel_cero(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.nivel_jerarquia == 0

    def test_subtarea_nivel_uno(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        padre = make_tarea(c, p, nombre='Padre')
        hijo = make_tarea(c, p, nombre='Hijo', tarea_padre=padre)
        assert hijo.nivel_jerarquia == 1

    def test_subtarea_nivel_dos(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        abuelo = make_tarea(c, p, nombre='Abuelo')
        padre = make_tarea(c, p, nombre='Padre', tarea_padre=abuelo)
        nieto = make_tarea(c, p, nombre='Nieto', tarea_padre=padre)
        assert nieto.nivel_jerarquia == 2

    def test_tiene_subtareas_false(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.tiene_subtareas is False

    def test_tiene_subtareas_true(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        padre = make_tarea(c, p, nombre='Padre')
        make_tarea(c, p, nombre='Hijo', tarea_padre=padre)
        padre.refresh_from_db()
        assert padre.tiene_subtareas is True

    def test_cascade_delete_subtareas(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        padre = make_tarea(c, p, nombre='Padre')
        hijo = make_tarea(c, p, nombre='Hijo', tarea_padre=padre)
        padre_id = padre.id
        hijo_id = hijo.id
        padre.delete()
        assert not Tarea.all_objects.filter(id=hijo_id).exists()


# ── Tests: Tarea — Validaciones ───────────────────────────────────────────────

@pytest.mark.django_db
class TestTareaValidaciones:

    def test_validacion_fecha_fin_anterior_inicio(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = Tarea(
            company=c,
            proyecto=p,
            nombre='Tarea inválida',
            fecha_inicio=date.today(),
            fecha_fin=date.today() - timedelta(days=1),
        )
        with pytest.raises(ValidationError) as exc_info:
            t.clean()
        assert 'fecha_fin' in exc_info.value.message_dict

    def test_validacion_fecha_fin_igual_inicio(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        hoy = date.today()
        t = Tarea(
            company=c,
            proyecto=p,
            nombre='Tarea igual',
            fecha_inicio=hoy,
            fecha_fin=hoy,
        )
        with pytest.raises(ValidationError) as exc_info:
            t.clean()
        assert 'fecha_fin' in exc_info.value.message_dict

    def test_validacion_fecha_fin_posterior_inicio_ok(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = Tarea(
            company=c,
            proyecto=p,
            nombre='Tarea válida',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=1),
        )
        t.clean()  # No debe lanzar excepción

    def test_validacion_padre_diferente_proyecto(self):
        c = make_company()
        g = make_user(c)
        p1 = make_proyecto(c, g, codigo='PRY-VAL-001')
        p2 = make_proyecto(c, g, codigo='PRY-VAL-002')
        padre = make_tarea(c, p1, nombre='Padre P1')
        hijo = Tarea(
            company=c,
            proyecto=p2,
            nombre='Hijo P2',
            tarea_padre=padre,
        )
        with pytest.raises(ValidationError) as exc_info:
            hijo.clean()
        assert 'tarea_padre' in exc_info.value.message_dict

    def test_validacion_nivel_maximo_jerarquia(self):
        """No se puede agregar subtarea si ya está en nivel 5."""
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)

        # Crear 5 niveles de profundidad
        raiz = make_tarea(c, p, nombre='Nivel 0')
        n1 = make_tarea(c, p, nombre='Nivel 1', tarea_padre=raiz)
        n2 = make_tarea(c, p, nombre='Nivel 2', tarea_padre=n1)
        n3 = make_tarea(c, p, nombre='Nivel 3', tarea_padre=n2)
        n4 = make_tarea(c, p, nombre='Nivel 4', tarea_padre=n3)

        # Nivel 5 debería fallar clean()
        n5 = Tarea(
            company=c,
            proyecto=p,
            nombre='Nivel 5 inválido',
            tarea_padre=n4,
        )
        with pytest.raises(ValidationError) as exc_info:
            n5.clean()
        assert 'tarea_padre' in exc_info.value.message_dict

    def test_sin_padre_no_valida_nivel(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = Tarea(company=c, proyecto=p, nombre='Raíz')
        t.clean()  # No debe lanzar excepción


# ── Tests: Tarea — Properties ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestTareaProperties:

    def test_es_vencida_sin_fecha_limite(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.es_vencida is False

    def test_es_vencida_fecha_futura(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p, fecha_limite=date.today() + timedelta(days=5))
        assert t.es_vencida is False

    def test_es_vencida_fecha_pasada_en_progreso(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(
            c, p,
            fecha_limite=date.today() - timedelta(days=1),
            estado='in_progress'
        )
        assert t.es_vencida is True

    def test_es_vencida_completada_no_vencida(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(
            c, p,
            fecha_limite=date.today() - timedelta(days=1),
            estado='completed'
        )
        assert t.es_vencida is False

    def test_es_vencida_cancelada_no_vencida(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(
            c, p,
            fecha_limite=date.today() - timedelta(days=1),
            estado='cancelled'
        )
        assert t.es_vencida is False


# ── Tests: Tarea — Recurrencia ────────────────────────────────────────────────

@pytest.mark.django_db
class TestTareaRecurrencia:

    def test_recurrencia_default_false(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t = make_tarea(c, p)
        assert t.es_recurrente is False
        assert t.frecuencia_recurrencia is None

    def test_tarea_recurrente_semanal(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        prox = date.today() + timedelta(days=7)
        t = make_tarea(
            c, p,
            es_recurrente=True,
            frecuencia_recurrencia='semanal',
            proxima_generacion=prox,
        )
        assert t.es_recurrente is True
        assert t.frecuencia_recurrencia == 'semanal'
        assert t.proxima_generacion == prox


# ── Tests: Tarea — Ordering y Meta ───────────────────────────────────────────

@pytest.mark.django_db
class TestTareaOrdering:

    def test_ordering_por_prioridad_desc(self):
        c = make_company()
        g = make_user(c)
        p = make_proyecto(c, g)
        t_normal = make_tarea(c, p, nombre='Normal', prioridad=2)
        t_urgente = make_tarea(c, p, nombre='Urgente', prioridad=4)
        t_baja = make_tarea(c, p, nombre='Baja', prioridad=1)
        tareas = list(Tarea.all_objects.filter(proyecto=p))
        prioridades = [t.prioridad for t in tareas]
        assert prioridades == sorted(prioridades, reverse=True)

    def test_verbose_name(self):
        assert Tarea._meta.verbose_name == 'Tarea'
        assert Tarea._meta.verbose_name_plural == 'Tareas'

    def test_tareatag_verbose_name(self):
        assert TareaTag._meta.verbose_name == 'Etiqueta de Tarea'
