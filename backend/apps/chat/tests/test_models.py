import pytest
from apps.chat.models import Conversacion, Mensaje
from apps.users.models import User
from apps.companies.models import Company


@pytest.fixture
def company(db):
    return Company.objects.create(name='Test Co', nit='123456789')


@pytest.fixture
def user_a(db, company):
    return User.objects.create_user(
        email='usera@test.com',
        password='TestPass123!',
        company=company,
    )


@pytest.fixture
def user_b(db, company):
    return User.objects.create_user(
        email='userb@test.com',
        password='TestPass123!',
        company=company,
    )


@pytest.mark.django_db
class TestConversacion:
    def test_create_conversacion(self, company, user_a, user_b):
        conv = Conversacion.objects.create(
            company=company,
            participante_1=user_a,
            participante_2=user_b,
        )
        assert conv.id is not None
        assert conv.participante_1 == user_a
        assert conv.participante_2 == user_b
        assert conv.ultimo_mensaje is None

    def test_unique_together(self, company, user_a, user_b):
        Conversacion.objects.create(
            company=company,
            participante_1=user_a,
            participante_2=user_b,
        )
        with pytest.raises(Exception):
            Conversacion.objects.create(
                company=company,
                participante_1=user_a,
                participante_2=user_b,
            )


@pytest.mark.django_db
class TestMensaje:
    def test_create_mensaje(self, company, user_a, user_b):
        conv = Conversacion.objects.create(
            company=company,
            participante_1=user_a,
            participante_2=user_b,
        )
        msg = Mensaje.objects.create(
            company=company,
            conversacion=conv,
            remitente=user_a,
            contenido='Hola, \u00bfc\u00f3mo est\u00e1s?',
        )
        assert msg.id is not None
        assert msg.contenido == 'Hola, \u00bfc\u00f3mo est\u00e1s?'
        assert msg.leido_por_destinatario is False
        assert msg.leido_at is None

    def test_mensaje_ordering_chronological(self, company, user_a, user_b):
        conv = Conversacion.objects.create(
            company=company,
            participante_1=user_a,
            participante_2=user_b,
        )
        msg1 = Mensaje.objects.create(company=company, conversacion=conv, remitente=user_a, contenido='Primero')
        msg2 = Mensaje.objects.create(company=company, conversacion=conv, remitente=user_b, contenido='Segundo')
        msgs = list(conv.mensajes.all())
        assert msgs[0].id == msg1.id
        assert msgs[1].id == msg2.id

    def test_reply_to_message(self, company, user_a, user_b):
        conv = Conversacion.objects.create(
            company=company,
            participante_1=user_a,
            participante_2=user_b,
        )
        msg1 = Mensaje.objects.create(company=company, conversacion=conv, remitente=user_a, contenido='Original')
        reply = Mensaje.objects.create(
            company=company,
            conversacion=conv,
            remitente=user_b,
            contenido='Respuesta',
            responde_a=msg1,
        )
        assert reply.responde_a == msg1
        assert msg1.respuestas.first() == reply
