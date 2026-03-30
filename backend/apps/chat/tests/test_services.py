"""
SaiSuite — Chat: Tests para ChatService.
Cobertura de toda la logica de negocio del modulo de chat.
"""
import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone

from apps.chat.models import Conversacion, Mensaje
from apps.chat.services import ChatService
from apps.companies.models import Company
from apps.users.models import User


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def company(db):
    return Company.objects.create(name='Chat Test Co', nit='900100200')


@pytest.fixture
def user_a(company):
    return User.objects.create_user(
        email='alice@test.com',
        password='TestPass123!',
        first_name='Alice',
        last_name='Smith',
        company=company,
    )


@pytest.fixture
def user_b(company):
    return User.objects.create_user(
        email='bob@test.com',
        password='TestPass123!',
        first_name='Bob',
        last_name='Jones',
        company=company,
    )


@pytest.fixture
def user_c(company):
    """Tercer usuario para tests de aislamiento."""
    return User.objects.create_user(
        email='carol@test.com',
        password='TestPass123!',
        first_name='Carol',
        last_name='Williams',
        company=company,
    )


@pytest.fixture
def conversacion(company, user_a, user_b):
    """Conversacion pre-creada entre user_a y user_b."""
    return ChatService.obtener_o_crear_conversacion(user_a, user_b, company)


@pytest.fixture
def mensaje(conversacion, user_a):
    """Mensaje enviado por user_a en la conversacion."""
    return ChatService.enviar_mensaje(
        conversacion_id=conversacion.id,
        remitente=user_a,
        contenido='Hola Bob',
    )


# ── Tests: obtener_o_crear_conversacion ─────────────────────────────


@pytest.mark.django_db
class TestObtenerOCrearConversacion:

    def test_crea_nueva_conversacion(self, company, user_a, user_b):
        conv = ChatService.obtener_o_crear_conversacion(user_a, user_b, company)

        assert conv is not None
        assert conv.company == company
        assert conv.participante_1 is not None
        assert conv.participante_2 is not None
        # Debe haber exactamente 1 conversacion
        assert Conversacion.all_objects.filter(company=company).count() == 1

    def test_obtiene_conversacion_existente(self, company, user_a, user_b):
        conv1 = ChatService.obtener_o_crear_conversacion(user_a, user_b, company)
        conv2 = ChatService.obtener_o_crear_conversacion(user_a, user_b, company)

        assert conv1.id == conv2.id
        assert Conversacion.all_objects.filter(company=company).count() == 1

    def test_obtiene_existente_orden_invertido(self, company, user_a, user_b):
        """Obtener con usuarios en orden invertido debe retornar la misma conversacion."""
        conv1 = ChatService.obtener_o_crear_conversacion(user_a, user_b, company)
        conv2 = ChatService.obtener_o_crear_conversacion(user_b, user_a, company)

        assert conv1.id == conv2.id
        assert Conversacion.all_objects.filter(company=company).count() == 1

    def test_normaliza_uuid_orden(self, company, user_a, user_b):
        """Siempre almacena el UUID menor como participante_1."""
        conv = ChatService.obtener_o_crear_conversacion(user_a, user_b, company)

        # El participante_1 debe tener el UUID menor
        assert str(conv.participante_1_id) < str(conv.participante_2_id)


# ── Tests: enviar_mensaje ───────────────────────────────────────────


@pytest.mark.django_db
class TestEnviarMensaje:

    def test_envia_mensaje_exitosamente(self, conversacion, user_a):
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Hola!',
        )

        assert msg.id is not None
        assert msg.contenido == 'Hola!'
        assert msg.remitente == user_a
        assert msg.conversacion == conversacion
        assert msg.leido_por_destinatario is False

    def test_actualiza_ultimo_mensaje(self, conversacion, user_a):
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Mensaje test',
        )

        conversacion.refresh_from_db()
        assert conversacion.ultimo_mensaje_id == msg.id
        assert conversacion.ultimo_mensaje_at is not None

    def test_no_participante_lanza_permission_error(self, conversacion, user_c):
        with pytest.raises(PermissionError, match='no es participante'):
            ChatService.enviar_mensaje(
                conversacion_id=conversacion.id,
                remitente=user_c,
                contenido='Intruso!',
            )

    def test_responder_a_mensaje(self, conversacion, user_a, user_b):
        msg1 = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Mensaje original',
        )

        msg2 = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_b,
            contenido='Respuesta',
            responde_a_id=msg1.id,
        )

        assert msg2.responde_a_id == msg1.id

    def test_mensaje_con_imagen(self, conversacion, user_a):
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='',
            imagen_url='https://cdn.example.com/img.png',
        )

        assert msg.imagen_url == 'https://cdn.example.com/img.png'

    @patch('apps.chat.services.get_channel_layer')
    def test_push_websocket_en_envio(self, mock_get_layer, conversacion, user_a):
        """Verifica que se intenta push via WebSocket al enviar mensaje."""
        mock_layer = MagicMock()
        mock_get_layer.return_value = mock_layer

        ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Test WS push',
        )

        mock_layer.group_send.assert_called()


# ── Tests: procesar_contenido ───────────────────────────────────────


@pytest.mark.django_db
class TestProcesarContenido:

    def test_procesar_enlaces_proyecto_existente(self, company, user_a):
        """[PRY-001] debe convertirse en link HTML si el proyecto existe."""
        from apps.proyectos.models import Project
        from datetime import date, timedelta

        project = Project.all_objects.create(
            company=company,
            codigo='PRY-001',
            nombre='Proyecto Test',
            tipo='civil_works',
            estado='in_progress',
            gerente=user_a,
            cliente_id='100',
            cliente_nombre='Cliente Test',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=30),
        )

        result = ChatService.procesar_enlaces('[PRY-001] esta listo', company)

        assert 'chat-entity-link' in result
        assert str(project.id) in result
        assert 'data-type="proyecto"' in result

    def test_procesar_enlaces_no_encontrado(self, company):
        """[PRY-999] debe quedar como texto plano si no existe."""
        result = ChatService.procesar_enlaces('[PRY-999] no existe', company)

        assert result == '[PRY-999] no existe'
        assert 'chat-entity-link' not in result

    def test_procesar_enlaces_prefijo_desconocido(self, company):
        """[XYZ-001] debe quedar como texto plano."""
        result = ChatService.procesar_enlaces('[XYZ-001] desconocido', company)

        assert result == '[XYZ-001] desconocido'

    def test_procesar_menciones_usuario_existente(self, company, user_a):
        """@Alice debe convertirse en span HTML."""
        result = ChatService.procesar_menciones('@Alice', company)

        assert 'chat-mention' in result
        assert str(user_a.id) in result
        assert 'Alice Smith' in result

    def test_procesar_menciones_usuario_no_encontrado(self, company):
        """@UsuarioInexistente debe quedar como texto plano."""
        result = ChatService.procesar_menciones('@UsuarioInexistente', company)

        assert result == '@UsuarioInexistente'
        assert 'chat-mention' not in result

    def test_sanitizacion_html(self, company):
        """Bleach debe escapar tags no permitidos."""
        contenido = '<script>alert("xss")</script>Hola <b>mundo</b>'
        result = ChatService.procesar_contenido(contenido, company)

        # Tags no permitidos deben estar escapados, no en raw
        assert '<script>' not in result
        assert '<b>' not in result
        # El contenido de texto se preserva (escapado)
        assert 'Hola' in result
        assert 'mundo' in result

    def test_sanitizacion_permite_tags_validos(self, company, user_a):
        """Los tags permitidos (a, span) deben sobrevivir a la sanitizacion."""
        from apps.proyectos.models import Project
        from datetime import date, timedelta

        Project.all_objects.create(
            company=company,
            codigo='PRY-002',
            nombre='Proyecto Link Test',
            tipo='consulting',
            estado='draft',
            gerente=user_a,
            cliente_id='200',
            cliente_nombre='Cliente Link',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=30),
        )

        result = ChatService.procesar_contenido('[PRY-002] enlace', company)

        assert '<a href=' in result
        assert 'chat-entity-link' in result


# ── Tests: marcar_leido ─────────────────────────────────────────────


@pytest.mark.django_db
class TestMarcarLeido:

    def test_marca_leido_correctamente(self, conversacion, user_a, user_b):
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Leeme',
        )

        # user_b es el destinatario
        result = ChatService.marcar_leido(msg.id, user_b)

        assert result.leido_por_destinatario is True
        assert result.leido_at is not None

    def test_marcar_leido_idempotente(self, conversacion, user_a, user_b):
        """Marcar como leido dos veces no debe fallar."""
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Leeme dos veces',
        )

        ChatService.marcar_leido(msg.id, user_b)
        result = ChatService.marcar_leido(msg.id, user_b)

        assert result.leido_por_destinatario is True

    def test_remitente_no_puede_marcar_leido(self, conversacion, user_a):
        """El remitente no puede marcar su propio mensaje como leido."""
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Mi propio mensaje',
        )

        with pytest.raises(PermissionError, match='Solo el destinatario'):
            ChatService.marcar_leido(msg.id, user_a)

    def test_tercero_no_puede_marcar_leido(self, conversacion, user_a, user_c):
        """Un usuario que no es participante no puede marcar como leido."""
        msg = ChatService.enviar_mensaje(
            conversacion_id=conversacion.id,
            remitente=user_a,
            contenido='Mensaje privado',
        )

        with pytest.raises(PermissionError, match='Solo el destinatario'):
            ChatService.marcar_leido(msg.id, user_c)


# ── Tests: listar_mensajes ──────────────────────────────────────────


@pytest.mark.django_db
class TestListarMensajes:

    def test_listar_mensajes_participante(self, conversacion, user_a, user_b):
        ChatService.enviar_mensaje(conversacion.id, user_a, 'Msg 1')
        ChatService.enviar_mensaje(conversacion.id, user_b, 'Msg 2')
        ChatService.enviar_mensaje(conversacion.id, user_a, 'Msg 3')

        mensajes = ChatService.listar_mensajes(conversacion.id, user_a)

        assert mensajes.count() == 3

    def test_listar_mensajes_no_participante(self, conversacion, user_c):
        with pytest.raises(PermissionError, match='no es participante'):
            ChatService.listar_mensajes(conversacion.id, user_c)


# ── Tests: listar_conversaciones ────────────────────────────────────


@pytest.mark.django_db
class TestListarConversaciones:

    def test_lista_conversaciones_del_usuario(self, company, user_a, user_b, user_c):
        conv1 = ChatService.obtener_o_crear_conversacion(user_a, user_b, company)
        conv2 = ChatService.obtener_o_crear_conversacion(user_a, user_c, company)

        # Enviar mensajes para que ultimo_mensaje_at tenga valor
        ChatService.enviar_mensaje(conv1.id, user_a, 'Hola B')
        ChatService.enviar_mensaje(conv2.id, user_a, 'Hola C')

        convs = ChatService.listar_conversaciones(user_a)

        assert convs.count() == 2

    def test_no_lista_conversaciones_ajenas(self, company, user_a, user_b, user_c):
        ChatService.obtener_o_crear_conversacion(user_a, user_b, company)

        convs = ChatService.listar_conversaciones(user_c)

        assert convs.count() == 0
