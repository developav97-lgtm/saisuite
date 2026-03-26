"""
SaiSuite — Tests: Feature Dependencias entre Tareas
Cubre: modelo TareaDependencia, DependenciaService (ciclos, CPM, cascada)
       y los endpoints crear-dependencia, eliminar-dependencia, camino-critico.

Cobertura objetivo: >= 85%
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, Tarea, TareaDependencia
from apps.proyectos.tarea_services import DependenciaService

User = get_user_model()

# ── Counter helpers ───────────────────────────────────────────────────────────

_NIT = [850_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'dep_test_{_EMAIL[0]}@test.com'


# ── Setup helpers ─────────────────────────────────────────────────────────────

def make_company():
    c = Company.objects.create(name=f'Dep Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role=role
    )


def make_proyecto(company, gerente):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'PRY-{_nit()}',
        nombre='Proyecto Dep Test',
        tipo='civil_works',
        estado='in_progress',
        cliente_id='999', cliente_nombre='Cliente Dep',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=120),
        presupuesto_total=Decimal('5000000'),
    )


def make_fase(company, proyecto, orden=1):
    return Fase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('500000'),
    )


def make_tarea(company, proyecto, fase, nombre='Tarea', **kwargs):
    return Tarea.objects.create(
        company=company, proyecto=proyecto, fase=fase,
        nombre=nombre, estado='todo', **kwargs
    )


# ── Modelo TareaDependencia ───────────────────────────────────────────────────

class TestTareaDependenciaModelo(TestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.t1 = make_tarea(self.company, self.proyecto, self.fase, 'T1')
        self.t2 = make_tarea(self.company, self.proyecto, self.fase, 'T2')

    def test_crear_dependencia_valida(self):
        dep = TareaDependencia.objects.create(
            company=self.company,
            tarea_predecesora=self.t1,
            tarea_sucesora=self.t2,
            tipo_dependencia='FS',
            retraso_dias=0,
        )
        self.assertEqual(dep.tipo_dependencia, 'FS')
        self.assertIn('→', str(dep))

    def test_unique_together_previene_duplicados(self):
        TareaDependencia.objects.create(
            company=self.company,
            tarea_predecesora=self.t1,
            tarea_sucesora=self.t2,
            tipo_dependencia='FS',
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            TareaDependencia.objects.create(
                company=self.company,
                tarea_predecesora=self.t1,
                tarea_sucesora=self.t2,
                tipo_dependencia='SS',
            )

    def test_clean_rechaza_autoreferencia(self):
        dep = TareaDependencia(
            company=self.company,
            tarea_predecesora=self.t1,
            tarea_sucesora=self.t1,
        )
        with self.assertRaises(ValidationError):
            dep.clean()

    def test_clean_acepta_tareas_diferentes(self):
        dep = TareaDependencia(
            company=self.company,
            tarea_predecesora=self.t1,
            tarea_sucesora=self.t2,
        )
        dep.clean()  # no debe lanzar


# ── DependenciaService ────────────────────────────────────────────────────────

class TestDependenciaServiceCrear(TestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.ta = make_tarea(self.company, self.proyecto, self.fase, 'A')
        self.tb = make_tarea(self.company, self.proyecto, self.fase, 'B')
        self.tc = make_tarea(self.company, self.proyecto, self.fase, 'C')

    def test_crear_dependencia_fs(self):
        dep = DependenciaService.crear_dependencia(
            predecesora_id=str(self.ta.id),
            sucesora_id=str(self.tb.id),
            company=self.company,
            tipo='FS',
            retraso_dias=0,
        )
        self.assertEqual(dep.tipo_dependencia, 'FS')
        self.assertEqual(dep.tarea_predecesora_id, self.ta.id)
        self.assertEqual(dep.tarea_sucesora_id, self.tb.id)

    def test_crear_dependencia_ss(self):
        dep = DependenciaService.crear_dependencia(
            predecesora_id=str(self.ta.id),
            sucesora_id=str(self.tb.id),
            company=self.company,
            tipo='SS',
        )
        self.assertEqual(dep.tipo_dependencia, 'SS')

    def test_crear_dependencia_ff(self):
        dep = DependenciaService.crear_dependencia(
            predecesora_id=str(self.ta.id),
            sucesora_id=str(self.tb.id),
            company=self.company,
            tipo='FF',
        )
        self.assertEqual(dep.tipo_dependencia, 'FF')

    def test_crear_dependencia_autoreferencia_lanza_error(self):
        with self.assertRaises(ValidationError):
            DependenciaService.crear_dependencia(
                predecesora_id=str(self.ta.id),
                sucesora_id=str(self.ta.id),
                company=self.company,
            )

    def test_crear_dependencia_tarea_no_existe_lanza_error(self):
        import uuid
        with self.assertRaises(ValidationError):
            DependenciaService.crear_dependencia(
                predecesora_id=str(uuid.uuid4()),
                sucesora_id=str(self.tb.id),
                company=self.company,
            )

    def test_crear_dependencia_ya_existe_lanza_error(self):
        DependenciaService.crear_dependencia(
            predecesora_id=str(self.ta.id),
            sucesora_id=str(self.tb.id),
            company=self.company,
        )
        with self.assertRaises(ValidationError):
            DependenciaService.crear_dependencia(
                predecesora_id=str(self.ta.id),
                sucesora_id=str(self.tb.id),
                company=self.company,
            )

    def test_crear_dependencia_proyectos_distintos_lanza_error(self):
        proyecto2 = make_proyecto(self.company, self.user)
        fase2     = make_fase(self.company, proyecto2, 1)
        tx        = make_tarea(self.company, proyecto2, fase2, 'TX')
        with self.assertRaises(ValidationError):
            DependenciaService.crear_dependencia(
                predecesora_id=str(self.ta.id),
                sucesora_id=str(tx.id),
                company=self.company,
            )


class TestDependenciaServiceCiclos(TestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.ta = make_tarea(self.company, self.proyecto, self.fase, 'A')
        self.tb = make_tarea(self.company, self.proyecto, self.fase, 'B')
        self.tc = make_tarea(self.company, self.proyecto, self.fase, 'C')

    def test_detectar_ciclo_directo(self):
        # A → B (existe)
        DependenciaService.crear_dependencia(
            str(self.ta.id), str(self.tb.id), self.company
        )
        # Intentar B → A debe detectar ciclo
        ciclo = DependenciaService._detectar_ciclo(
            str(self.tb.id), str(self.ta.id), self.company
        )
        self.assertTrue(ciclo)

    def test_detectar_ciclo_indirecto(self):
        # A → B → C
        DependenciaService.crear_dependencia(str(self.ta.id), str(self.tb.id), self.company)
        DependenciaService.crear_dependencia(str(self.tb.id), str(self.tc.id), self.company)
        # Intentar C → A: ciclo A→B→C→A
        ciclo = DependenciaService._detectar_ciclo(
            str(self.tc.id), str(self.ta.id), self.company
        )
        self.assertTrue(ciclo)

    def test_no_ciclo_arista_valida(self):
        # A → B (existe). A → C es válido, no hay ciclo
        DependenciaService.crear_dependencia(str(self.ta.id), str(self.tb.id), self.company)
        ciclo = DependenciaService._detectar_ciclo(
            str(self.ta.id), str(self.tc.id), self.company
        )
        self.assertFalse(ciclo)

    def test_crear_dependencia_con_ciclo_lanza_error(self):
        DependenciaService.crear_dependencia(str(self.ta.id), str(self.tb.id), self.company)
        DependenciaService.crear_dependencia(str(self.tb.id), str(self.tc.id), self.company)
        with self.assertRaises(ValidationError) as ctx:
            DependenciaService.crear_dependencia(
                str(self.tc.id), str(self.ta.id), self.company
            )
        self.assertIn('ciclo', str(ctx.exception).lower())


class TestDependenciaServiceCPM(TestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        hoy = date.today()
        # A (5 días) → B (3 días) → D (2 días)   ← camino más largo = 10
        # A (5 días) → C (2 días) → D (2 días)   ← camino = 9
        self.ta = make_tarea(
            self.company, self.proyecto, self.fase, 'A',
            fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=5),
        )
        self.tb = make_tarea(
            self.company, self.proyecto, self.fase, 'B',
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=8),
        )
        self.tc = make_tarea(
            self.company, self.proyecto, self.fase, 'C',
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=7),
        )
        self.td = make_tarea(
            self.company, self.proyecto, self.fase, 'D',
            fecha_inicio=hoy + timedelta(days=8),
            fecha_fin=hoy + timedelta(days=10),
        )
        # Crear dependencias: A→B, A→C, B→D, C→D
        DependenciaService.crear_dependencia(str(self.ta.id), str(self.tb.id), self.company)
        DependenciaService.crear_dependencia(str(self.ta.id), str(self.tc.id), self.company)
        DependenciaService.crear_dependencia(str(self.tb.id), str(self.td.id), self.company)
        DependenciaService.crear_dependencia(str(self.tc.id), str(self.td.id), self.company)

    def test_camino_critico_contiene_tareas_esperadas(self):
        criticas = DependenciaService.calcular_camino_critico(
            str(self.proyecto.id), self.company
        )
        criticas_set = set(criticas)
        # A, B y D deben estar (camino A→B→D = 10 días)
        self.assertIn(str(self.ta.id), criticas_set)
        self.assertIn(str(self.tb.id), criticas_set)
        self.assertIn(str(self.td.id), criticas_set)

    def test_camino_critico_proyecto_sin_tareas(self):
        proyecto_vacio = make_proyecto(self.company, self.user)
        criticas = DependenciaService.calcular_camino_critico(
            str(proyecto_vacio.id), self.company
        )
        self.assertEqual(criticas, [])

    def test_camino_critico_proyecto_sin_dependencias(self):
        proyecto_nuevo = make_proyecto(self.company, self.user)
        fase_nueva = make_fase(self.company, proyecto_nuevo, 1)
        hoy = date.today()
        make_tarea(
            self.company, proyecto_nuevo, fase_nueva, 'Solo',
            fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=3),
        )
        criticas = DependenciaService.calcular_camino_critico(
            str(proyecto_nuevo.id), self.company
        )
        self.assertEqual(len(criticas), 1)


class TestDependenciaServiceReprogramacion(TestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        hoy = date.today()
        self.pred = make_tarea(
            self.company, self.proyecto, self.fase, 'Pred',
            fecha_inicio=hoy,
            fecha_fin=hoy + timedelta(days=5),
        )
        self.suc = make_tarea(
            self.company, self.proyecto, self.fase, 'Suc',
            fecha_inicio=hoy + timedelta(days=5),
            fecha_fin=hoy + timedelta(days=8),
        )
        DependenciaService.crear_dependencia(
            str(self.pred.id), str(self.suc.id), self.company, tipo='FS', retraso_dias=0
        )

    def test_reprogramacion_automatica_ajusta_sucesora(self):
        # Cambiar fecha_fin de predecesora a +10 días
        hoy = date.today()
        self.pred.fecha_fin = hoy + timedelta(days=10)
        self.pred.save()

        DependenciaService.reprogramar_en_cascada(str(self.pred.id), self.company)

        self.suc.refresh_from_db()
        # Sucesora debe iniciar el día después de la nueva fecha_fin de predecesora
        self.assertEqual(self.suc.fecha_inicio, hoy + timedelta(days=10))

    def test_reprogramacion_no_ajusta_si_nueva_fecha_es_anterior(self):
        # La fecha de la sucesora ya es posterior; si la predecesora termina antes
        # no debe ajustarse (no se adelanta, solo se retrasa)
        hoy = date.today()
        original_inicio = self.suc.fecha_inicio

        # Adelantar fecha_fin de predecesora (termina antes)
        self.pred.fecha_fin = hoy + timedelta(days=2)
        self.pred.save()

        DependenciaService.reprogramar_en_cascada(str(self.pred.id), self.company)

        self.suc.refresh_from_db()
        # fecha_inicio NO debe cambiar
        self.assertEqual(self.suc.fecha_inicio, original_inicio)

    def test_reprogramacion_cascada_recursiva(self):
        hoy = date.today()
        suc2 = make_tarea(
            self.company, self.proyecto, self.fase, 'Suc2',
            fecha_inicio=hoy + timedelta(days=8),
            fecha_fin=hoy + timedelta(days=11),
        )
        DependenciaService.crear_dependencia(
            str(self.suc.id), str(suc2.id), self.company, tipo='FS'
        )

        # Mover predecesora original al día +10
        self.pred.fecha_fin = hoy + timedelta(days=10)
        self.pred.save()

        DependenciaService.reprogramar_en_cascada(str(self.pred.id), self.company)

        suc2.refresh_from_db()
        # suc2 debe haberse reprogramado también
        self.suc.refresh_from_db()
        self.assertGreaterEqual(suc2.fecha_inicio, self.suc.fecha_inicio)

    def test_reprogramacion_tarea_sin_fecha_fin_no_falla(self):
        # Tarea sin fecha_fin no debe lanzar error
        self.pred.fecha_fin = None
        self.pred.save()
        # No debe levantar excepciones
        DependenciaService.reprogramar_en_cascada(str(self.pred.id), self.company)

    def test_reprogramacion_tarea_no_existe_no_falla(self):
        import uuid
        # ID inválido no debe lanzar error
        DependenciaService.reprogramar_en_cascada(str(uuid.uuid4()), self.company)


# ── API: TareaViewSet acciones de dependencia ─────────────────────────────────

class DependenciaBaseTest(APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        hoy = date.today()
        self.ta = make_tarea(
            self.company, self.proyecto, self.fase, 'A',
            fecha_inicio=hoy, fecha_fin=hoy + timedelta(days=3),
        )
        self.tb = make_tarea(
            self.company, self.proyecto, self.fase, 'B',
            fecha_inicio=hoy + timedelta(days=3), fecha_fin=hoy + timedelta(days=6),
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def _url_dep(self, tarea_id, action):
        return f'/api/v1/projects/tasks/{tarea_id}/{action}/'


class TestCrearDependenciaEndpoint(DependenciaBaseTest):

    def test_crear_dependencia_retorna_201(self):
        resp = self.client.post(
            self._url_dep(self.tb.id, 'crear-dependencia'),
            {'predecesora_id': str(self.ta.id), 'tipo': 'FS', 'retraso_dias': 0},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['tipo_dependencia'], 'FS')

    def test_crear_dependencia_con_ciclo_retorna_400(self):
        # A → B
        self.client.post(
            self._url_dep(self.tb.id, 'crear-dependencia'),
            {'predecesora_id': str(self.ta.id)},
        )
        # B → A crea ciclo
        resp = self.client.post(
            self._url_dep(self.ta.id, 'crear-dependencia'),
            {'predecesora_id': str(self.tb.id)},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_dependencia_sin_predecesora_id_retorna_400(self):
        resp = self.client.post(
            self._url_dep(self.tb.id, 'crear-dependencia'),
            {},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_crear_dependencia_autoreferencia_retorna_400(self):
        resp = self.client.post(
            self._url_dep(self.ta.id, 'crear-dependencia'),
            {'predecesora_id': str(self.ta.id)},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TestEliminarDependenciaEndpoint(DependenciaBaseTest):

    def setUp(self):
        super().setUp()
        self.dep = TareaDependencia.objects.create(
            company=self.company,
            tarea_predecesora=self.ta,
            tarea_sucesora=self.tb,
            tipo_dependencia='FS',
        )

    def test_eliminar_dependencia_retorna_204(self):
        resp = self.client.delete(
            self._url_dep(self.tb.id, 'eliminar-dependencia'),
            data={'dependencia_id': str(self.dep.id)},
            QUERY_STRING=f'dependencia_id={self.dep.id}',
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TareaDependencia.objects.filter(id=self.dep.id).exists())

    def test_eliminar_dependencia_sin_id_retorna_400(self):
        resp = self.client.delete(
            self._url_dep(self.tb.id, 'eliminar-dependencia'),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_eliminar_dependencia_no_encontrada_retorna_404(self):
        import uuid
        resp = self.client.delete(
            self._url_dep(self.tb.id, 'eliminar-dependencia'),
            QUERY_STRING=f'dependencia_id={uuid.uuid4()}',
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class TestCaminoCriticoEndpoint(DependenciaBaseTest):

    def test_camino_critico_retorna_lista(self):
        # Crear dependencia A → B
        DependenciaService.crear_dependencia(
            str(self.ta.id), str(self.tb.id), self.company
        )
        resp = self.client.get(
            f'/api/v1/projects/{self.proyecto.id}/camino-critico/'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('tareas_criticas', resp.data)
        self.assertIsInstance(resp.data['tareas_criticas'], list)

    def test_camino_critico_proyecto_vacio_retorna_lista_vacia(self):
        proyecto_vacio = make_proyecto(self.company, self.user)
        resp = self.client.get(
            f'/api/v1/projects/{proyecto_vacio.id}/camino-critico/'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['tareas_criticas'], [])


class TestTareaSerializerDependencias(DependenciaBaseTest):
    """Verifica que el TareaSerializer incluya predecesoras_detail y es_camino_critico."""

    def test_tarea_detail_incluye_predecesoras(self):
        DependenciaService.crear_dependencia(
            str(self.ta.id), str(self.tb.id), self.company
        )
        resp = self.client.get(f'/api/v1/projects/tasks/{self.tb.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('predecesoras_detail', resp.data)
        self.assertEqual(len(resp.data['predecesoras_detail']), 1)

    def test_tarea_detail_incluye_sucesoras(self):
        DependenciaService.crear_dependencia(
            str(self.ta.id), str(self.tb.id), self.company
        )
        resp = self.client.get(f'/api/v1/projects/tasks/{self.ta.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('sucesoras_detail', resp.data)
        self.assertEqual(len(resp.data['sucesoras_detail']), 1)

    def test_tarea_detail_incluye_es_camino_critico(self):
        resp = self.client.get(f'/api/v1/projects/tasks/{self.ta.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('es_camino_critico', resp.data)
        self.assertIsInstance(resp.data['es_camino_critico'], bool)
