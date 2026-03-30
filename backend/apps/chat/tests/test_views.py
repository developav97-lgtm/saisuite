"""
SaiSuite — Chat: Tests para Views (API REST).
Verifica endpoints, permisos y respuestas HTTP.
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.chat.models import Conversacion, Mensaje
from apps.chat.services import ChatService
from apps.companies.models import Company
from apps.users.models import User


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def company(db):
    return Company.objects.create(name='Chat API Test Co', nit='900200300')


@pytest.fixture
def user_a(company):
    return User.objects.create_user(
        email='api_alice@test.com',
        password='TestPass123!',
        first_name='Alice',
        last_name='API',
        company=company,
    )


@pytest.fixture
def user_b(company):
    return User.objects.create_user(
        email='api_bob@test.com',
        password='TestPass123!',
        first_name='Bob',
        last_name='API',
        company=company,
    )


@pytest.fixture
def client_a(user_a):
    """Cliente API autenticado como user_a."""
    client = APIClient()
    refresh = RefreshToken.for_user(user_a)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def client_b(user_b):
    """Cliente API autenticado como user_b."""
    client = APIClient()
    refresh = RefreshToken.for_user(user_b)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def client_anonimo():
    """Cliente API sin autenticar."""
    return APIClient()


@pytest.fixture
def conversacion(company, user_a, user_b):
    return ChatService.obtener_o_crear_conversacion(user_a, user_b, company)


@pytest.fixture
def mensaje(conversacion, user_a):
    return ChatService.enviar_mensaje(
        conversacion_id=conversacion.id,
        remitente=user_a,
        contenido='Mensaje de prueba API',
    )


# ── Tests: Conversaciones ──────────────────────────────────────────


@pytest.mark.django_db
class TestConversacionesView:

    def test_list_conversaciones_authenticated(self, client_a, conversacion, user_a):
        # Enviar mensaje para tener ultimo_mensaje_at
        ChatService.enviar_mensaje(conversacion.id, user_a, 'Hola')

        response = client_a.get('/api/v1/chat/conversaciones/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert 'participante_1_nombre' in response.data[0]
        assert 'participante_2_nombre' in response.data[0]
        assert 'mensajes_sin_leer' in response.data[0]

    def test_create_conversacion(self, client_a, user_b):
        response = client_a.post(
            '/api/v1/chat/conversaciones/',
            {'destinatario_id': str(user_b.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['participante_1'] is not None
        assert response.data['participante_2'] is not None

    def test_create_conversacion_self(self, client_a, user_a):
        """No se puede crear conversacion con uno mismo."""
        response = client_a.post(
            '/api/v1/chat/conversaciones/',
            {'destinatario_id': str(user_a.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'contigo mismo' in response.data['error']

    def test_create_conversacion_usuario_inexistente(self, client_a):
        import uuid
        response = client_a.post(
            '/api/v1/chat/conversaciones/',
            {'destinatario_id': str(uuid.uuid4())},
            format='json',
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_conversacion_idempotente(self, client_a, user_b):
        """Crear la misma conversacion dos veces retorna la misma."""
        resp1 = client_a.post(
            '/api/v1/chat/conversaciones/',
            {'destinatario_id': str(user_b.id)},
            format='json',
        )
        resp2 = client_a.post(
            '/api/v1/chat/conversaciones/',
            {'destinatario_id': str(user_b.id)},
            format='json',
        )

        assert resp1.data['id'] == resp2.data['id']


# ── Tests: Mensajes ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestMensajesView:

    def test_list_mensajes(self, client_a, conversacion, user_a):
        ChatService.enviar_mensaje(conversacion.id, user_a, 'Msg 1')
        ChatService.enviar_mensaje(conversacion.id, user_a, 'Msg 2')

        response = client_a.get(
            f'/api/v1/chat/conversaciones/{conversacion.id}/mensajes/',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_enviar_mensaje(self, client_a, conversacion):
        response = client_a.post(
            f'/api/v1/chat/conversaciones/{conversacion.id}/mensajes/enviar/',
            {'contenido': 'Mensaje via API'},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['contenido'] == 'Mensaje via API'
        assert 'remitente_nombre' in response.data

    def test_enviar_mensaje_con_imagen(self, client_a, conversacion):
        response = client_a.post(
            f'/api/v1/chat/conversaciones/{conversacion.id}/mensajes/enviar/',
            {'imagen_url': 'https://cdn.example.com/img.png'},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['imagen_url'] == 'https://cdn.example.com/img.png'

    def test_enviar_mensaje_vacio_falla(self, client_a, conversacion):
        """Un mensaje sin contenido ni imagen debe fallar validacion."""
        response = client_a.post(
            f'/api/v1/chat/conversaciones/{conversacion.id}/mensajes/enviar/',
            {'contenido': '', 'imagen_url': ''},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Tests: Marcar leido ─────────────────────────────────────────────


@pytest.mark.django_db
class TestMarcarLeidoView:

    def test_marcar_leido(self, client_b, mensaje):
        """user_b es el destinatario, debe poder marcar como leido."""
        response = client_b.post(
            f'/api/v1/chat/mensajes/{mensaje.id}/marcar-leido/',
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ok'
        assert response.data['leido_at'] is not None

    def test_marcar_leido_remitente_falla(self, client_a, mensaje):
        """user_a envio el mensaje, no puede marcarlo como leido."""
        response = client_a.post(
            f'/api/v1/chat/mensajes/{mensaje.id}/marcar-leido/',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Tests: Autocomplete ─────────────────────────────────────────────


@pytest.mark.django_db
class TestAutocompleteView:

    def test_autocomplete_entidades(self, client_a, company, user_a):
        from apps.proyectos.models import Project
        from datetime import date, timedelta

        Project.all_objects.create(
            company=company,
            codigo='PRY-100',
            nombre='Proyecto Autocomplete',
            tipo='civil_works',
            estado='draft',
            gerente=user_a,
            cliente_id='300',
            cliente_nombre='Cliente AC',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=30),
        )

        response = client_a.get(
            '/api/v1/chat/autocomplete/entidades/',
            {'query': 'PRY-100'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['codigo'] == 'PRY-100'
        assert response.data[0]['tipo'] == 'proyecto'

    def test_autocomplete_entidades_query_corta(self, client_a):
        """Query menor a 2 caracteres debe retornar lista vacia."""
        response = client_a.get(
            '/api/v1/chat/autocomplete/entidades/',
            {'query': 'P'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_autocomplete_usuarios(self, client_a, user_b):
        response = client_a.get(
            '/api/v1/chat/autocomplete/usuarios/',
            {'query': 'Bob'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['nombre'] == 'Bob API'

    def test_autocomplete_usuarios_excluye_self(self, client_a, user_a):
        """El autocomplete no debe incluir al usuario que hace la busqueda."""
        response = client_a.get(
            '/api/v1/chat/autocomplete/usuarios/',
            {'query': 'Alice'},
        )

        assert response.status_code == status.HTTP_200_OK
        user_ids = [str(u['id']) for u in response.data]
        assert str(user_a.id) not in user_ids

    def test_autocomplete_usuarios_query_corta(self, client_a):
        response = client_a.get(
            '/api/v1/chat/autocomplete/usuarios/',
            {'query': 'B'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


# ── Tests: Acceso no autenticado ────────────────────────────────────


@pytest.mark.django_db
class TestUnauthenticatedAccess:

    def test_conversaciones_requiere_auth(self, client_anonimo):
        response = client_anonimo.get('/api/v1/chat/conversaciones/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_enviar_mensaje_requiere_auth(self, client_anonimo):
        import uuid
        response = client_anonimo.post(
            f'/api/v1/chat/conversaciones/{uuid.uuid4()}/mensajes/enviar/',
            {'contenido': 'Intento no autenticado'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_marcar_leido_requiere_auth(self, client_anonimo):
        import uuid
        response = client_anonimo.post(
            f'/api/v1/chat/mensajes/{uuid.uuid4()}/marcar-leido/',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_autocomplete_entidades_requiere_auth(self, client_anonimo):
        response = client_anonimo.get(
            '/api/v1/chat/autocomplete/entidades/',
            {'query': 'PRY'},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_autocomplete_usuarios_requiere_auth(self, client_anonimo):
        response = client_anonimo.get(
            '/api/v1/chat/autocomplete/usuarios/',
            {'query': 'test'},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
