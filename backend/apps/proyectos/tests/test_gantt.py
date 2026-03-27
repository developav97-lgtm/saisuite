"""
SaiSuite — Tests: Endpoint gantt-data
GET /api/v1/projects/{id}/gantt-data/

Cubre:
- Retorna 200 con formato correcto
- Solo incluye tareas con fecha_inicio y fecha_fin
- Tareas ordenadas por fecha_inicio
- custom_class se genera con el estado
- Project vacío retorna lista vacía
"""
from datetime import date, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Phase, Task

User = get_user_model()

# ── Helpers ───────────────────────────────────────────────────────────────────

_NIT = [780_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'gantt_{_EMAIL[0]}@test.com'


def make_company():
    c = Company.objects.create(name=f'Gantt Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company):
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role='company_admin'
    )


def make_proyecto(company, gerente):
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'PRY-{_nit()}',
        nombre='Project Gantt Test',
        tipo='civil_works',
        estado='in_progress',
        cliente_id='888', cliente_nombre='Cliente Gantt',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('5000000'),
    )


def make_fase(company, proyecto):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre='Phase Gantt', orden=1,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('500000'),
    )


def make_tarea(company, proyecto, fase, nombre, fi, ff, estado='todo', progreso=0):
    return Task.objects.create(
        company=company, proyecto=proyecto, fase=fase,
        nombre=nombre, estado=estado,
        fecha_inicio=fi, fecha_fin=ff,
        porcentaje_completado=progreso,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestGanttDataEndpoint(APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        self.url = f'/api/v1/projects/{self.proyecto.id}/gantt-data/'
        hoy = date.today()
        self.t1 = make_tarea(
            self.company, self.proyecto, self.fase, 'Task A',
            fi=hoy, ff=hoy + timedelta(days=5),
            estado='in_progress', progreso=40,
        )
        self.t2 = make_tarea(
            self.company, self.proyecto, self.fase, 'Task B',
            fi=hoy + timedelta(days=5), ff=hoy + timedelta(days=10),
            estado='todo', progreso=0,
        )
        self.t3 = make_tarea(
            self.company, self.proyecto, self.fase, 'Task C',
            fi=hoy + timedelta(days=2), ff=hoy + timedelta(days=7),
            estado='completed', progreso=100,
        )

    def test_retorna_200(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_estructura_json_correcta(self):
        resp = self.client.get(self.url)
        self.assertIn('tasks', resp.data)
        self.assertIsInstance(resp.data['tasks'], list)

    def test_formato_de_cada_tarea(self):
        resp = self.client.get(self.url)
        task = resp.data['tasks'][0]
        self.assertIn('id', task)
        self.assertIn('name', task)
        self.assertIn('start', task)
        self.assertIn('end', task)
        self.assertIn('progress', task)
        self.assertIn('custom_class', task)

    def test_custom_class_contiene_estado(self):
        resp = self.client.get(self.url)
        tasks = {t['id']: t for t in resp.data['tasks']}
        self.assertEqual(tasks[str(self.t1.id)]['custom_class'], 'estado-in_progress')
        self.assertEqual(tasks[str(self.t2.id)]['custom_class'], 'estado-todo')
        self.assertEqual(tasks[str(self.t3.id)]['custom_class'], 'estado-completed')

    def test_progress_es_porcentaje_completado(self):
        resp = self.client.get(self.url)
        tasks = {t['id']: t for t in resp.data['tasks']}
        self.assertEqual(tasks[str(self.t1.id)]['progress'], 40)
        self.assertEqual(tasks[str(self.t3.id)]['progress'], 100)

    def test_tareas_ordenadas_por_fecha_inicio(self):
        resp = self.client.get(self.url)
        fechas = [t['start'] for t in resp.data['tasks']]
        self.assertEqual(fechas, sorted(fechas))

    def test_excluye_tareas_sin_fechas(self):
        # Crear tarea sin fecha_inicio ni fecha_fin
        Task.objects.create(
            company=self.company, proyecto=self.proyecto, fase=self.fase,
            nombre='Sin fechas', estado='todo',
        )
        resp = self.client.get(self.url)
        names = [t['name'] for t in resp.data['tasks']]
        self.assertNotIn('Sin fechas', names)

    def test_proyecto_sin_tareas_retorna_lista_vacia(self):
        proyecto_vacio = make_proyecto(self.company, self.user)
        resp = self.client.get(
            f'/api/v1/projects/{proyecto_vacio.id}/gantt-data/'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['tasks'], [])

    def test_usuario_otra_empresa_recibe_403_o_404(self):
        other_company = make_company()
        other_user    = make_user(other_company)
        token = RefreshToken.for_user(other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.get(self.url)
        self.assertIn(resp.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])

    def test_start_end_son_iso_date(self):
        resp = self.client.get(self.url)
        task = resp.data['tasks'][0]
        # Debe parsear como fecha ISO sin error
        from datetime import date as dt
        dt.fromisoformat(task['start'])
        dt.fromisoformat(task['end'])
