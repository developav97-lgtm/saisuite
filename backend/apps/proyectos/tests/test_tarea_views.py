"""
SaiSuite — Tests: TareaViewSet + TareaTagViewSet
Cubre: GET/POST/PATCH/DELETE /api/v1/projects/tasks/
       GET/POST/PATCH/DELETE /api/v1/projects/tags/
       POST /api/v1/projects/tasks/{id}/agregar-follower/
       DELETE /api/v1/projects/tasks/{id}/quitar-follower/{user_id}/
       POST /api/v1/projects/tasks/{id}/cambiar-estado/
"""
from decimal import Decimal
from datetime import date, timedelta

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Proyecto, Fase, Tarea, TareaTag

User = get_user_model()

# ── Counter helpers for unique NITs/emails ──────────────────────────────────

_NIT = [920_000_000]
_EMAIL = [0]


def nit():
    _NIT[0] += 1
    return str(_NIT[0])


def email(prefix='tv'):
    _EMAIL[0] += 1
    return f'{prefix}_{_EMAIL[0]}@test.com'


# ── Pagination helper ─────────────────────────────────────────────────────────

def get_results(resp):
    """Return results list from paginated or plain response."""
    if isinstance(resp.data, dict) and 'results' in resp.data:
        return resp.data['results']
    return resp.data


# ── DB setup helpers ─────────────────────────────────────────────────────────

def make_company(name='TV Co'):
    c = Company.objects.create(name=name, nit=nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    return User.objects.create_user(
        email=email(), password='Pass1234!', company=company, role=role
    )


def make_proyecto(company, gerente):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'PRY-{nit()}',
        nombre='Proyecto Test Views',
        tipo='civil_works',
        cliente_id='123', cliente_nombre='Cliente',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('1000000'),
    )


def make_fase(company, proyecto, orden=1):
    return Fase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('500000'),
    )


def make_tarea(company, proyecto, fase=None, **kwargs):
    defaults = dict(nombre='Tarea Test', estado='todo')
    defaults.update(kwargs)
    if fase is not None:
        defaults['fase'] = fase
    return Tarea.all_objects.create(company=company, proyecto=proyecto, **defaults)


def make_tag(company, nombre='bug', color='red'):
    return TareaTag.all_objects.create(company=company, nombre=nombre, color=color)


# ── Base test case ────────────────────────────────────────────────────────────

class TareaBaseTest(APITestCase):
    """Configura empresa, usuario, proyecto, fase y JWT."""

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company, role='company_admin')
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')


# ── TareaTag ViewSet ──────────────────────────────────────────────────────────

class TestTareaTagList(TareaBaseTest):

    def test_listar_tags_vacio(self):
        resp = self.client.get('/api/v1/projects/tags/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_results(resp)), 0)

    def test_crear_tag(self):
        resp = self.client.post('/api/v1/projects/tags/', {'nombre': 'frontend', 'color': 'blue'})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['nombre'], 'frontend')
        self.assertEqual(resp.data['color'], 'blue')

    def test_crear_tag_color_invalido(self):
        resp = self.client.post('/api/v1/projects/tags/', {'nombre': 'x', 'color': 'rainbow'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_solo_tags_de_empresa(self):
        make_tag(self.company, nombre='mi-tag')
        otra = make_company('Otra Co')
        make_tag(otra, nombre='otro-tag')

        resp = self.client.get('/api/v1/projects/tags/')
        nombres = [t['nombre'] for t in get_results(resp)]
        self.assertIn('mi-tag', nombres)
        self.assertNotIn('otro-tag', nombres)

    def test_eliminar_tag(self):
        tag = make_tag(self.company, nombre='del-tag')
        resp = self.client.delete(f'/api/v1/projects/tags/{tag.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_actualizar_tag(self):
        tag = make_tag(self.company, nombre='viejo')
        resp = self.client.patch(f'/api/v1/projects/tags/{tag.id}/', {'color': 'green'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['color'], 'green')


# ── Tarea List / Create ───────────────────────────────────────────────────────

class TestTareaListCreate(TareaBaseTest):

    def test_listar_tareas_vacio(self):
        resp = self.client.get('/api/v1/projects/tasks/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_results(resp)), 0)

    def test_crear_tarea_minima(self):
        data = {'nombre': 'Nueva Tarea', 'fase': str(self.fase.id)}
        resp = self.client.post('/api/v1/projects/tasks/', data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['nombre'], 'Nueva Tarea')
        self.assertTrue(resp.data['codigo'].startswith('TASK-'))

    def test_crear_tarea_auto_agrega_creador_como_follower(self):
        data = {'nombre': 'Tarea Follower', 'fase': str(self.fase.id)}
        resp = self.client.post('/api/v1/projects/tasks/', data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        follower_ids = [f['id'] for f in resp.data['followers_detail']]
        self.assertIn(str(self.user.id), follower_ids)

    def test_crear_tarea_con_fase(self):
        data = {
            'nombre': 'Con Fase',
            'fase': str(self.fase.id),
        }
        resp = self.client.post('/api/v1/projects/tasks/', data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(resp.data['fase']), str(self.fase.id))

    def test_crear_tarea_con_responsable_lo_agrega_como_follower(self):
        responsable = make_user(self.company)
        data = {
            'nombre': 'Con Responsable',
            'fase': str(self.fase.id),
            'responsable': str(responsable.id),
        }
        resp = self.client.post('/api/v1/projects/tasks/', data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        follower_ids = [f['id'] for f in resp.data['followers_detail']]
        self.assertIn(str(responsable.id), follower_ids)

    def test_crear_tarea_valida_fecha_fin_anterior_inicio(self):
        data = {
            'nombre': 'Fechas Inválidas',
            'fase': str(self.fase.id),
            'fecha_inicio': str(date.today()),
            'fecha_fin': str(date.today() - timedelta(days=1)),
        }
        resp = self.client.post('/api/v1/projects/tasks/', data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_fin', resp.data)

    def test_listar_solo_tareas_de_empresa(self):
        make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Mi Tarea')
        otra_empresa  = make_company('Otra Co 2')
        otro_gerente  = make_user(otra_empresa)
        otro_proyecto = make_proyecto(otra_empresa, otro_gerente)
        otra_fase     = make_fase(otra_empresa, otro_proyecto)
        make_tarea(otra_empresa, otro_proyecto, fase=otra_fase, nombre='Tarea Ajena')

        resp = self.client.get('/api/v1/projects/tasks/')
        nombres = [t['nombre'] for t in get_results(resp)]
        self.assertIn('Mi Tarea', nombres)
        self.assertNotIn('Tarea Ajena', nombres)

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        resp = self.client.get('/api/v1/projects/tasks/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ── Tarea Retrieve / Update / Delete ─────────────────────────────────────────

class TestTareaDetail(TareaBaseTest):

    def setUp(self):
        super().setUp()
        self.tarea = make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Tarea Detalle')

    def test_retrieve_tarea(self):
        resp = self.client.get(f'/api/v1/projects/tasks/{self.tarea.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Tarea Detalle')
        self.assertIn('proyecto_detail', resp.data)
        self.assertIn('subtareas_detail', resp.data)

    def test_retrieve_incluye_computed_fields(self):
        resp = self.client.get(f'/api/v1/projects/tasks/{self.tarea.id}/')
        self.assertIn('es_vencida', resp.data)
        self.assertIn('tiene_subtareas', resp.data)
        self.assertIn('nivel_jerarquia', resp.data)

    def test_patch_nombre(self):
        resp = self.client.patch(f'/api/v1/projects/tasks/{self.tarea.id}/', {'nombre': 'Actualizado'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['nombre'], 'Actualizado')

    def test_patch_estado(self):
        resp = self.client.patch(f'/api/v1/projects/tasks/{self.tarea.id}/', {'estado': 'in_progress'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'in_progress')

    def test_patch_porcentaje_completado(self):
        resp = self.client.patch(f'/api/v1/projects/tasks/{self.tarea.id}/', {'porcentaje_completado': 50})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['porcentaje_completado'], 50)

    def test_delete_tarea(self):
        resp = self.client.delete(f'/api/v1/projects/tasks/{self.tarea.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tarea.all_objects.filter(id=self.tarea.id).exists())

    def test_viewer_no_puede_delete(self):
        viewer = make_user(self.company, role='viewer')
        token = RefreshToken.for_user(viewer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.delete(f'/api/v1/projects/tasks/{self.tarea.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_puede_listar(self):
        viewer = make_user(self.company, role='viewer')
        token = RefreshToken.for_user(viewer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.get('/api/v1/projects/tasks/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ── Acción: agregar-follower ──────────────────────────────────────────────────

class TestAgregarFollower(TareaBaseTest):

    def setUp(self):
        super().setUp()
        self.tarea = make_tarea(self.company, self.proyecto, fase=self.fase)

    def test_agregar_follower_ok(self):
        nuevo = make_user(self.company)
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/agregar-follower/'
        resp = self.client.post(url, {'user_id': str(nuevo.id)})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('followers_count', resp.data)
        self.assertIn(str(nuevo.id), [
            str(f.id) for f in self.tarea.followers.all()
        ])

    def test_agregar_follower_sin_user_id(self):
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/agregar-follower/'
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agregar_follower_user_inexistente(self):
        import uuid
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/agregar-follower/'
        resp = self.client.post(url, {'user_id': str(uuid.uuid4())})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ── Acción: quitar-follower ───────────────────────────────────────────────────

class TestQuitarFollower(TareaBaseTest):

    def setUp(self):
        super().setUp()
        self.tarea    = make_tarea(self.company, self.proyecto, fase=self.fase)
        self.follower = make_user(self.company)
        self.tarea.followers.add(self.follower)

    def test_quitar_follower_ok(self):
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/quitar-follower/{self.follower.id}/'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.follower, self.tarea.followers.all())

    def test_quitar_follower_user_inexistente(self):
        import uuid
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/quitar-follower/{uuid.uuid4()}/'
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ── Acción: cambiar-estado ────────────────────────────────────────────────────

class TestCambiarEstado(TareaBaseTest):

    def setUp(self):
        super().setUp()
        self.tarea = make_tarea(self.company, self.proyecto, fase=self.fase)

    def test_cambiar_estado_ok(self):
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/cambiar-estado/'
        resp = self.client.post(url, {'estado': 'in_progress'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'in_progress')

    def test_cambiar_estado_sin_estado(self):
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/cambiar-estado/'
        resp = self.client.post(url, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambiar_estado_invalido(self):
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/cambiar-estado/'
        resp = self.client.post(url, {'estado': 'volando'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_completar_con_subtareas_pendientes(self):
        make_tarea(self.company, self.proyecto, fase=self.fase,
                   nombre='Subtarea Pendiente', tarea_padre=self.tarea,
                   estado='todo')
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/cambiar-estado/'
        resp = self.client.post(url, {'estado': 'completed'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('subtareas pendientes', resp.data['error'])

    def test_completar_cuando_subtareas_completas(self):
        make_tarea(self.company, self.proyecto, fase=self.fase,
                   nombre='Subtarea OK', tarea_padre=self.tarea,
                   estado='completed')
        url  = f'/api/v1/projects/tasks/{self.tarea.id}/cambiar-estado/'
        resp = self.client.post(url, {'estado': 'completed'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_todos_los_estados_validos(self):
        for est in ['todo', 'in_progress', 'in_review', 'blocked', 'cancelled']:
            url  = f'/api/v1/projects/tasks/{self.tarea.id}/cambiar-estado/'
            resp = self.client.post(url, {'estado': est})
            self.assertEqual(resp.status_code, status.HTTP_200_OK, f'Falló con estado: {est}')


# ── Filtros ───────────────────────────────────────────────────────────────────

class TestTareaFiltros(TareaBaseTest):

    def setUp(self):
        super().setUp()
        self.responsable = make_user(self.company)
        self.t1 = make_tarea(self.company, self.proyecto, fase=self.fase,
                             nombre='Tarea Alta', prioridad=3, estado='in_progress',
                             responsable=self.responsable)
        self.t2 = make_tarea(self.company, self.proyecto, fase=self.fase,
                             nombre='Tarea Baja', prioridad=1, estado='todo')
        self.t3 = make_tarea(self.company, self.proyecto, fase=self.fase,
                             nombre='Tarea Vencida', estado='in_progress',
                             fecha_limite=date.today() - timedelta(days=1))

    def test_filtro_estado(self):
        resp = self.client.get('/api/v1/projects/tasks/?estado=in_progress')
        for t in get_results(resp):
            self.assertEqual(t['estado'], 'in_progress')

    def test_filtro_prioridad(self):
        resp = self.client.get('/api/v1/projects/tasks/?prioridad=3')
        resultados = get_results(resp)
        self.assertGreater(len(resultados), 0)
        for t in resultados:
            self.assertEqual(t['prioridad'], 3)

    def test_filtro_responsable(self):
        resp = self.client.get(f'/api/v1/projects/tasks/?responsable={self.responsable.id}')
        for t in get_results(resp):
            self.assertIsNotNone(t['responsable'])

    def test_filtro_vencidas(self):
        resp = self.client.get('/api/v1/projects/tasks/?vencidas=true')
        resultados = get_results(resp)
        self.assertGreater(len(resultados), 0)
        for t in resultados:
            self.assertNotIn(t['estado'], ['completed', 'cancelled'])

    def test_filtro_search_nombre(self):
        resp = self.client.get('/api/v1/projects/tasks/?search=Alta')
        nombres = [t['nombre'] for t in get_results(resp)]
        self.assertIn('Tarea Alta', nombres)
        self.assertNotIn('Tarea Baja', nombres)

    def test_filtro_solo_raiz(self):
        make_tarea(self.company, self.proyecto, fase=self.fase,
                   nombre='Subtarea', tarea_padre=self.t1)
        resp = self.client.get('/api/v1/projects/tasks/?solo_raiz=true')
        for t in get_results(resp):
            self.assertIsNone(t['tarea_padre'])

    def test_todas_tareas_tienen_fase(self):
        """Fase es requerida: todas las tareas deben tener fase asignada."""
        resp = self.client.get('/api/v1/projects/tasks/')
        for t in get_results(resp):
            self.assertIsNotNone(t['fase'])

    def test_filtro_proyecto_id(self):
        resp = self.client.get(f'/api/v1/projects/tasks/?proyecto_id={self.proyecto.id}')
        for t in get_results(resp):
            self.assertEqual(str(t['proyecto']), str(self.proyecto.id))


# ── Serializer: campos nested ─────────────────────────────────────────────────

class TestTareaSerializerNested(TareaBaseTest):

    def test_subtareas_detail_incluidas(self):
        padre = make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Padre')
        make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Hijo', tarea_padre=padre)
        resp = self.client.get(f'/api/v1/projects/tasks/{padre.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['subtareas_detail']), 1)
        self.assertEqual(resp.data['subtareas_detail'][0]['nombre'], 'Hijo')

    def test_subtareas_detail_vacio_nivel_2(self):
        """En nivel >= 2 el serializer retorna [] para evitar N+1 queries."""
        abuelo = make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Abuelo')
        padre  = make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Padre', tarea_padre=abuelo)
        make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Nieto', tarea_padre=padre)
        # padre está en nivel 1, nieto en nivel 2
        resp = self.client.get(f'/api/v1/projects/tasks/{padre.id}/')
        self.assertEqual(len(resp.data['subtareas_detail']), 1)
        nieto_data = resp.data['subtareas_detail'][0]
        self.assertEqual(nieto_data['subtareas_detail'], [])

    def test_tags_detail_incluidos(self):
        tarea = make_tarea(self.company, self.proyecto, fase=self.fase, nombre='Con Tags')
        tag   = make_tag(self.company, nombre='importante')
        tarea.tags.add(tag)
        resp = self.client.get(f'/api/v1/projects/tasks/{tarea.id}/')
        tag_nombres = [t['nombre'] for t in resp.data['tags_detail']]
        self.assertIn('importante', tag_nombres)

    def test_proyecto_detail_incluido(self):
        tarea = make_tarea(self.company, self.proyecto, fase=self.fase)
        resp = self.client.get(f'/api/v1/projects/tasks/{tarea.id}/')
        self.assertIn('codigo', resp.data['proyecto_detail'])
        self.assertEqual(resp.data['proyecto_detail']['id'], str(self.proyecto.id))
