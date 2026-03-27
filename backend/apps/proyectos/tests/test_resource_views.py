"""
SaiSuite — Tests: Feature #4 Resource Management — Views
BK-28

Cubre:
- ResourceAssignmentViewSet:   list, create, retrieve, destroy, check_overallocation
- ResourceCapacityViewSet:     list, create, retrieve, partial_update, destroy
- ResourceAvailabilityViewSet: list, create, retrieve, destroy, approve
- WorkloadView:                ok + parámetros faltantes
- TeamAvailabilityView:        ok + sin asignaciones
- UserCalendarView:            ok + parámetros faltantes
- Aislamiento multi-tenant:    usuarios de otra empresa no pueden acceder a datos ajenos
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import (
    Project, Phase, Task,
    ResourceAssignment, ResourceCapacity, ResourceAvailability,
    AvailabilityType,
)

User = get_user_model()

# ── Counters ──────────────────────────────────────────────────────────────────

_NIT   = [500_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'rv_{_EMAIL[0]}@test.com'


# ── Factories ─────────────────────────────────────────────────────────────────

def make_company():
    c = Company.objects.create(name=f'RV Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role=role,
    )


def make_proyecto(company, gerente, estado='in_progress'):
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'RV-{_nit()}',
        nombre='Project RV Test',
        tipo='services',
        estado=estado,
        cliente_id='001',
        cliente_nombre='Cliente RV',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('5000000.00'),
    )


def make_fase(company, proyecto):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre='Fase RV', orden=1,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
    )


def make_tarea(company, proyecto, fase, responsable, estado='todo'):
    return Task.objects.create(
        company=company, proyecto=proyecto, fase=fase,
        nombre='Tarea RV', responsable=responsable, estado=estado,
    )


def make_assignment(company, tarea, usuario, porcentaje='50.00'):
    return ResourceAssignment.objects.create(
        company=company, tarea=tarea, usuario=usuario,
        porcentaje_asignacion=Decimal(porcentaje),
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=30),
        activo=True,
    )


def make_capacity(company, user, horas='40.00'):
    return ResourceCapacity.objects.create(
        company=company, usuario=user,
        horas_por_semana=Decimal(horas),
        fecha_inicio=date(2020, 1, 1),
        activo=True,
    )


def make_availability(company, user, tipo=AvailabilityType.VACATION, aprobado=False):
    return ResourceAvailability.objects.create(
        company=company, usuario=user,
        tipo=tipo,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        aprobado=aprobado,
        activo=True,
    )


TODAY   = date.today().isoformat()
IN_30   = (date.today() + timedelta(days=30)).isoformat()


# ── Mixin de autenticación ────────────────────────────────────────────────────

class AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceAssignmentViewSet
# ═══════════════════════════════════════════════════════════════════════════════

class TestResourceAssignmentViewSet(AuthMixin, APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.admin    = make_user(self.company)
        self.user2    = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.admin)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.admin)
        self._auth(self.admin)
        self.base = f'/api/v1/projects/tasks/{self.tarea.id}/assignments/'

    # ── list ──────────────────────────────────────────────────────────────────

    def test_list_retorna_200(self):
        make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.get(self.base)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_list_tarea_inexistente_retorna_404(self):
        import uuid
        resp = self.client.get(f'/api/v1/projects/tasks/{uuid.uuid4()}/assignments/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # ── create ────────────────────────────────────────────────────────────────

    def test_create_retorna_201(self):
        resp = self.client.post(self.base, {
            'usuario_id':            str(self.admin.id),
            'porcentaje_asignacion': '50.00',
            'fecha_inicio':          TODAY,
            'fecha_fin':             IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['activo'], True)

    def test_create_porcentaje_cero_retorna_400(self):
        resp = self.client.post(self.base, {
            'usuario_id':            str(self.admin.id),
            'porcentaje_asignacion': '0',
            'fecha_inicio':          TODAY,
            'fecha_fin':             IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_usuario_otra_empresa_retorna_400(self):
        otra      = make_company()
        otro_user = make_user(otra)
        resp = self.client.post(self.base, {
            'usuario_id':            str(otro_user.id),
            'porcentaje_asignacion': '50.00',
            'fecha_inicio':          TODAY,
            'fecha_fin':             IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_doble_asignacion_mismo_usuario_retorna_400(self):
        make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.post(self.base, {
            'usuario_id':            str(self.admin.id),
            'porcentaje_asignacion': '30.00',
            'fecha_inicio':          TODAY,
            'fecha_fin':             IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── retrieve ──────────────────────────────────────────────────────────────

    def test_retrieve_retorna_200(self):
        a = make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.get(f'{self.base}{a.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ── destroy (soft delete) ─────────────────────────────────────────────────

    def test_destroy_retorna_204(self):
        a = make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.delete(f'{self.base}{a.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        a.refresh_from_db()
        self.assertFalse(a.activo)

    def test_destroy_preserva_registro_en_bd(self):
        a = make_assignment(self.company, self.tarea, self.admin)
        pk = a.id
        self.client.delete(f'{self.base}{a.id}/')
        self.assertTrue(ResourceAssignment.objects.filter(id=pk).exists())

    # ── check-overallocation ──────────────────────────────────────────────────

    def test_check_overallocation_sin_conflictos(self):
        make_assignment(self.company, self.tarea, self.admin, '80.00')
        resp = self.client.get(
            f'{self.base}check-overallocation/',
            {'usuario_id': str(self.admin.id), 'start_date': TODAY, 'end_date': IN_30},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total'], 0)

    def test_check_overallocation_con_conflictos(self):
        tarea2 = Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Tarea 2 RV', estado='todo',
        )
        make_assignment(self.company, self.tarea, self.admin, '70.00')
        make_assignment(self.company, tarea2, self.admin, '60.00')
        resp = self.client.get(
            f'{self.base}check-overallocation/',
            {'usuario_id': str(self.admin.id), 'start_date': TODAY, 'end_date': IN_30},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(resp.data['total'], 0)

    def test_check_overallocation_sin_params_retorna_400(self):
        resp = self.client.get(f'{self.base}check-overallocation/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── aislamiento multi-tenant ──────────────────────────────────────────────

    def test_no_accede_tarea_otra_empresa(self):
        otra      = make_company()
        otro_user = make_user(otra)
        self._auth(otro_user)
        resp = self.client.get(self.base)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceCapacityViewSet
# ═══════════════════════════════════════════════════════════════════════════════

class TestResourceCapacityViewSet(AuthMixin, APITestCase):

    def setUp(self):
        self.company = make_company()
        self.admin   = make_user(self.company)
        self._auth(self.admin)
        self.base = '/api/v1/projects/resources/capacity/'

    def test_list_retorna_200(self):
        make_capacity(self.company, self.admin)
        resp = self.client.get(self.base)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_list_filtra_por_usuario_id(self):
        user2 = make_user(self.company)
        make_capacity(self.company, self.admin)
        make_capacity(self.company, user2)
        resp = self.client.get(self.base, {'usuario_id': str(self.admin.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data:
            self.assertEqual(str(item['usuario']), str(self.admin.id))

    def test_create_retorna_201(self):
        resp = self.client.post(self.base, {
            'usuario':         str(self.admin.id),
            'horas_por_semana': '40.00',
            'fecha_inicio':    '2025-01-01',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(resp.data['horas_por_semana']), Decimal('40.00'))

    def test_create_horas_cero_retorna_400(self):
        resp = self.client.post(self.base, {
            'usuario':         str(self.admin.id),
            'horas_por_semana': '0',
            'fecha_inicio':    '2025-01-01',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_retorna_200(self):
        cap = make_capacity(self.company, self.admin)
        resp = self.client.get(f'{self.base}{cap.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_inexistente_retorna_404(self):
        import uuid
        resp = self.client.get(f'{self.base}{uuid.uuid4()}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_retorna_200(self):
        cap = make_capacity(self.company, self.admin)
        resp = self.client.patch(f'{self.base}{cap.id}/', {
            'usuario':         str(self.admin.id),
            'horas_por_semana': '32.00',
            'fecha_inicio':    '2020-01-01',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data['horas_por_semana']), Decimal('32.00'))

    def test_destroy_retorna_204(self):
        cap = make_capacity(self.company, self.admin)
        resp = self.client.delete(f'{self.base}{cap.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        cap.refresh_from_db()
        self.assertFalse(cap.activo)

    def test_destroy_inexistente_retorna_404(self):
        import uuid
        resp = self.client.delete(f'{self.base}{uuid.uuid4()}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_ve_capacidades_otra_empresa(self):
        otra      = make_company()
        otro_user = make_user(otra)
        make_capacity(otra, otro_user)
        resp = self.client.get(self.base)
        ids_empresa = {str(item['usuario']) for item in resp.data}
        self.assertNotIn(str(otro_user.id), ids_empresa)


# ═══════════════════════════════════════════════════════════════════════════════
# ResourceAvailabilityViewSet
# ═══════════════════════════════════════════════════════════════════════════════

class TestResourceAvailabilityViewSet(AuthMixin, APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.admin    = make_user(self.company)
        self.empleado = make_user(self.company)
        self._auth(self.admin)
        self.base = '/api/v1/projects/resources/availability/'

    def test_list_retorna_200(self):
        make_availability(self.company, self.empleado)
        resp = self.client.get(self.base)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_list_filtra_por_aprobado(self):
        make_availability(self.company, self.empleado, aprobado=False)
        make_availability(self.company, self.admin,    tipo=AvailabilityType.SICK_LEAVE, aprobado=True)
        resp = self.client.get(self.base, {'aprobado': 'true'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data:
            self.assertTrue(item['aprobado'])

    def test_list_filtra_por_tipo(self):
        make_availability(self.company, self.empleado, tipo=AvailabilityType.VACATION)
        make_availability(self.company, self.admin, tipo=AvailabilityType.SICK_LEAVE)
        resp = self.client.get(self.base, {'tipo': 'vacation'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for item in resp.data:
            self.assertEqual(item['tipo'], 'vacation')

    def test_create_retorna_201(self):
        resp = self.client.post(self.base, {
            'usuario_id':   str(self.empleado.id),
            'tipo':         'vacation',
            'fecha_inicio': TODAY,
            'fecha_fin':    IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resp.data['aprobado'])

    def test_create_tipo_invalido_retorna_400(self):
        resp = self.client.post(self.base, {
            'usuario_id':   str(self.empleado.id),
            'tipo':         'invalid_type',
            'fecha_inicio': TODAY,
            'fecha_fin':    IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_solapamiento_mismo_tipo_retorna_400(self):
        make_availability(self.company, self.empleado, tipo=AvailabilityType.VACATION)
        resp = self.client.post(self.base, {
            'usuario_id':   str(self.empleado.id),
            'tipo':         'vacation',
            'fecha_inicio': TODAY,
            'fecha_fin':    IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_retorna_200(self):
        av = make_availability(self.company, self.empleado)
        resp = self.client.get(f'{self.base}{av.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_destroy_retorna_204_soft_delete(self):
        av = make_availability(self.company, self.empleado)
        resp = self.client.delete(f'{self.base}{av.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        av.refresh_from_db()
        self.assertFalse(av.activo)

    # ── approve action ────────────────────────────────────────────────────────

    def test_approve_retorna_200_con_aprobado_true(self):
        av = make_availability(self.company, self.empleado)
        resp = self.client.post(f'{self.base}{av.id}/approve/', {'aprobar': True})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['aprobado'])
        self.assertIsNotNone(resp.data['fecha_aprobacion'])

    def test_approve_false_limpia_datos(self):
        av = make_availability(self.company, self.empleado, aprobado=True)
        resp = self.client.post(f'{self.base}{av.id}/approve/', {'aprobar': False})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['aprobado'])
        self.assertIsNone(resp.data['aprobado_por'])

    def test_approve_inexistente_retorna_400(self):
        import uuid
        resp = self.client.post(f'{self.base}{uuid.uuid4()}/approve/', {'aprobar': True})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_ve_ausencias_otra_empresa(self):
        otra      = make_company()
        otro_user = make_user(otra)
        make_availability(otra, otro_user)
        resp = self.client.get(self.base)
        self.assertEqual(len(resp.data), 0)


# ═══════════════════════════════════════════════════════════════════════════════
# WorkloadView
# ═══════════════════════════════════════════════════════════════════════════════

class TestWorkloadView(AuthMixin, APITestCase):

    def setUp(self):
        self.company = make_company()
        self.admin   = make_user(self.company)
        self._auth(self.admin)
        self.base = '/api/v1/projects/resources/workload/'
        make_capacity(self.company, self.admin)

    def test_retorna_200_con_params_correctos(self):
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': '2026-03-01',
            'end_date':   '2026-03-31',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('horas_capacidad', resp.data)
        self.assertIn('horas_asignadas', resp.data)
        self.assertIn('horas_registradas', resp.data)
        self.assertIn('porcentaje_utilizacion', resp.data)
        self.assertIn('conflictos', resp.data)

    def test_retorna_400_sin_usuario_id(self):
        resp = self.client.get(self.base, {
            'start_date': '2026-03-01',
            'end_date':   '2026-03-31',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retorna_400_sin_fechas(self):
        resp = self.client.get(self.base, {'usuario_id': str(self.admin.id)})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retorna_400_fecha_invalida(self):
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': 'not-a-date',
            'end_date':   '2026-03-31',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_horas_capacidad_calculadas_correctamente(self):
        # Semana completa (lunes–viernes) con 40h/semana → 40h
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': '2026-03-23',  # Lunes
            'end_date':   '2026-03-27',  # Viernes
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(resp.data['horas_capacidad']), Decimal('40.00'))

    def test_sin_autenticacion_retorna_401(self):
        self.client.credentials()
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': '2026-03-01',
            'end_date':   '2026-03-31',
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ═══════════════════════════════════════════════════════════════════════════════
# TeamAvailabilityView
# ═══════════════════════════════════════════════════════════════════════════════

class TestTeamAvailabilityView(AuthMixin, APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.admin    = make_user(self.company)
        self.user2    = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.admin)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.admin)
        self._auth(self.admin)
        self.base = f'/api/v1/projects/{self.proyecto.id}/team-availability/'

    def test_sin_asignaciones_retorna_lista_vacia(self):
        resp = self.client.get(self.base, {
            'start_date': TODAY, 'end_date': IN_30
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_con_asignacion_retorna_usuario(self):
        make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.get(self.base, {
            'start_date': TODAY, 'end_date': IN_30
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['usuario_id'], str(self.admin.id))

    def test_retorna_400_sin_fechas(self):
        resp = self.client.get(self.base)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_incluye_usuarios_sin_asignacion_activa(self):
        # user2 no tiene asignaciones → no aparece
        make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.get(self.base, {
            'start_date': TODAY, 'end_date': IN_30
        })
        ids_respuesta = {item['usuario_id'] for item in resp.data}
        self.assertNotIn(str(self.user2.id), ids_respuesta)


# ═══════════════════════════════════════════════════════════════════════════════
# UserCalendarView
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserCalendarView(AuthMixin, APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.admin    = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.admin)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase, self.admin)
        self._auth(self.admin)
        self.base = '/api/v1/projects/resources/calendar/'

    def test_retorna_200_con_params_correctos(self):
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': TODAY,
            'end_date':   IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('asignaciones', resp.data)
        self.assertIn('ausencias', resp.data)

    def test_asignaciones_incluidas_en_rango(self):
        make_assignment(self.company, self.tarea, self.admin)
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': TODAY,
            'end_date':   IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['asignaciones']), 1)
        self.assertIn('tarea_codigo', resp.data['asignaciones'][0])
        self.assertIn('proyecto_codigo', resp.data['asignaciones'][0])

    def test_ausencias_aprobadas_incluidas(self):
        make_availability(self.company, self.admin, aprobado=True)
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': TODAY,
            'end_date':   IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['ausencias']), 1)

    def test_ausencias_no_aprobadas_excluidas(self):
        make_availability(self.company, self.admin, aprobado=False)
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': TODAY,
            'end_date':   IN_30,
        })
        self.assertEqual(len(resp.data['ausencias']), 0)

    def test_retorna_400_sin_params(self):
        resp = self.client.get(self.base)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retorna_400_fecha_invalida(self):
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': 'bad-date',
            'end_date':   IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_autenticacion_retorna_401(self):
        self.client.credentials()
        resp = self.client.get(self.base, {
            'usuario_id': str(self.admin.id),
            'start_date': TODAY,
            'end_date':   IN_30,
        })
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
