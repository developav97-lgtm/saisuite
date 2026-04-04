"""
SaiSuite — Tests: Notificaciones automáticas en Tareas
Verifica que el signal tarea_post_save genera notificaciones correctas
al crear una tarea o al modificar responsable, estado, prioridad y fechas.
"""
from datetime import date, timedelta

import pytest

from apps.notifications.models import Notificacion
from apps.proyectos.models import Task


# ─────────────────────────────────────────────────────────────────────────────
# Fixture auxiliar: segundo usuario de la misma empresa
# ─────────────────────────────────────────────────────────────────────────────

_OTRO_EMAIL = [0]


def _otro_email():
    _OTRO_EMAIL[0] += 1
    return f'otro_user_{_OTRO_EMAIL[0]}@test.com'


@pytest.fixture
def otro_usuario(company):
    """Usuario alternativo de la misma empresa para tests de reasignación."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email=_otro_email(),
        password='Pass1234!',
        company=company,
        role='company_admin',
        is_active=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Creación de tarea
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionCreacionTarea:

    def test_crea_notificacion_asignacion_al_crear_con_responsable(self, proyecto, fase, user):
        """Crear tarea con responsable genera una notificación de tipo 'asignacion'."""
        count_antes = Notificacion.objects.filter(usuario=user, tipo='asignacion').count()

        Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea nueva con responsable',
            responsable=user,
        )

        assert Notificacion.objects.filter(usuario=user, tipo='asignacion').count() == count_antes + 1

    def test_notificacion_contiene_nombre_tarea(self, proyecto, fase, user):
        """La notificación menciona el nombre de la tarea en título y mensaje."""
        Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea Alpha',
            responsable=user,
        )

        notif = Notificacion.objects.filter(usuario=user, tipo='asignacion').order_by('-created_at').first()
        assert notif is not None
        assert 'Tarea Alpha' in notif.titulo or 'Tarea Alpha' in notif.mensaje

    def test_no_crea_notificacion_si_sin_responsable(self, proyecto, fase):
        """Crear tarea sin responsable no genera ninguna notificación."""
        count_antes = Notificacion.objects.filter(tipo='asignacion').count()

        Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea sin responsable',
        )

        assert Notificacion.objects.filter(tipo='asignacion').count() == count_antes

    def test_notificacion_url_accion_apunta_a_tarea(self, proyecto, fase, user):
        """La url_accion de la notificación apunta al endpoint de la tarea."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea URL test',
            responsable=user,
        )

        notif = Notificacion.objects.filter(usuario=user, tipo='asignacion').order_by('-created_at').first()
        assert notif is not None
        assert str(tarea.pk) in notif.url_accion


# ─────────────────────────────────────────────────────────────────────────────
# 2. Reasignación de responsable
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionReasignacionTarea:

    def test_nuevo_responsable_recibe_notificacion(self, proyecto, fase, user, otro_usuario):
        """Al reasignar la tarea, el nuevo responsable recibe una notificación de asignacion."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea a reasignar',
            responsable=user,
        )
        # Limpiar notificaciones de la creación
        Notificacion.objects.all().delete()

        tarea.responsable = otro_usuario
        tarea.save()

        assert Notificacion.objects.filter(usuario=otro_usuario, tipo='asignacion').exists()

    def test_responsable_anterior_recibe_notificacion_de_remocion(self, proyecto, fase, user, otro_usuario):
        """Al reasignar la tarea, el responsable anterior recibe notificación."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea remocion',
            responsable=user,
        )
        Notificacion.objects.all().delete()

        tarea.responsable = otro_usuario
        tarea.save()

        notif_anterior = Notificacion.objects.filter(usuario=user, tipo='asignacion').first()
        assert notif_anterior is not None
        # El mensaje debe indicar remoción del responsable
        assert 'removido' in notif_anterior.mensaje.lower() or 'Ya no eres' in notif_anterior.titulo

    def test_asignar_responsable_a_tarea_sin_responsable(self, proyecto, fase, user):
        """Asignar responsable a tarea que no tenía genera notificación para el nuevo."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea sin responsable inicial',
        )
        Notificacion.objects.all().delete()

        tarea.responsable = user
        tarea.save()

        assert Notificacion.objects.filter(usuario=user, tipo='asignacion').exists()

    def test_quitar_responsable_no_falla(self, proyecto, fase, user):
        """Quitar el responsable de una tarea no genera error."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea quitar responsable',
            responsable=user,
        )
        Notificacion.objects.all().delete()

        tarea.responsable = None
        tarea.save()  # No debe lanzar excepción

        # El responsable anterior (user) debe recibir notificación de remoción
        assert Notificacion.objects.filter(usuario=user, tipo='asignacion').exists()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Cambio de estado
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionCambioEstadoTarea:

    def test_cambio_estado_genera_notificacion(self, proyecto, fase, user):
        """Cambiar el estado de una tarea genera notificación de cambio_estado al responsable."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea cambio estado',
            responsable=user,
            estado='todo',
        )
        Notificacion.objects.all().delete()

        tarea.estado = 'in_progress'
        tarea.save()

        assert Notificacion.objects.filter(usuario=user, tipo='cambio_estado').exists()

    def test_notificacion_estado_menciona_nuevo_estado(self, proyecto, fase, user):
        """La notificación de cambio de estado incluye el estado destino."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea estado display',
            responsable=user,
            estado='todo',
        )
        Notificacion.objects.all().delete()

        tarea.estado = 'in_review'
        tarea.save()

        notif = Notificacion.objects.filter(usuario=user, tipo='cambio_estado').order_by('-created_at').first()
        assert notif is not None
        # metadata debe contener el nuevo estado
        assert notif.metadata.get('estado_nuevo') == 'in_review'

    def test_sin_responsable_no_genera_notificacion_estado(self, proyecto, fase):
        """Cambio de estado en tarea sin responsable no genera notificación."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea sin resp estado',
            estado='todo',
        )
        Notificacion.objects.all().delete()

        tarea.estado = 'in_progress'
        tarea.save()

        assert not Notificacion.objects.filter(tipo='cambio_estado').exists()

    def test_mismo_estado_no_genera_notificacion(self, proyecto, fase, user):
        """Guardar sin cambiar el estado no genera notificación de estado."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea estado igual',
            responsable=user,
            estado='todo',
        )
        Notificacion.objects.all().delete()

        tarea.nombre = 'Tarea estado igual (editada)'
        tarea.save()  # estado sigue siendo 'todo'

        assert not Notificacion.objects.filter(tipo='cambio_estado').exists()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Cambio de prioridad
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionCambioPrioridadTarea:

    def test_cambio_prioridad_genera_notificacion(self, proyecto, fase, user):
        """Cambiar la prioridad genera notificación de cambio_estado al responsable."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea prioridad',
            responsable=user,
            prioridad=2,  # Normal
        )
        Notificacion.objects.all().delete()

        tarea.prioridad = 4  # Urgente
        tarea.save()

        notif = Notificacion.objects.filter(usuario=user, tipo='cambio_estado').order_by('-created_at').first()
        assert notif is not None
        assert notif.metadata.get('prioridad_nueva') == 4

    def test_misma_prioridad_no_genera_notificacion(self, proyecto, fase, user):
        """Guardar sin cambiar la prioridad no genera notificación."""
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea prioridad igual',
            responsable=user,
            prioridad=2,
        )
        Notificacion.objects.all().delete()

        tarea.nombre = 'Tarea prioridad igual (editada)'
        tarea.save()

        assert not Notificacion.objects.filter(tipo='cambio_estado').exists()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Cambio de fechas
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionCambioFechasTarea:

    def test_cambio_fecha_limite_genera_notificacion(self, proyecto, fase, user):
        """Cambiar la fecha límite genera notificación de cambio_estado al responsable."""
        hoy = date.today()
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea fecha limite',
            responsable=user,
            fecha_limite=hoy,
        )
        Notificacion.objects.all().delete()

        tarea.fecha_limite = hoy + timedelta(days=7)
        tarea.save()

        assert Notificacion.objects.filter(usuario=user, tipo='cambio_estado').exists()

    def test_cambio_fecha_inicio_genera_notificacion(self, proyecto, fase, user):
        """Cambiar la fecha de inicio genera notificación."""
        hoy = date.today()
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea fecha inicio',
            responsable=user,
            fecha_inicio=hoy,
        )
        Notificacion.objects.all().delete()

        tarea.fecha_inicio = hoy + timedelta(days=3)
        tarea.save()

        assert Notificacion.objects.filter(usuario=user, tipo='cambio_estado').exists()

    def test_cambio_fecha_fin_genera_notificacion(self, proyecto, fase, user):
        """Cambiar la fecha fin genera notificación."""
        hoy = date.today()
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea fecha fin',
            responsable=user,
            fecha_fin=hoy + timedelta(days=10),
        )
        Notificacion.objects.all().delete()

        tarea.fecha_fin = hoy + timedelta(days=15)
        tarea.save()

        assert Notificacion.objects.filter(usuario=user, tipo='cambio_estado').exists()

    def test_metadata_incluye_fechas_actualizadas(self, proyecto, fase, user):
        """La metadata de la notificación incluye las nuevas fechas."""
        hoy = date.today()
        nueva_fecha = hoy + timedelta(days=5)
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea metadata fechas',
            responsable=user,
            fecha_limite=hoy,
        )
        Notificacion.objects.all().delete()

        tarea.fecha_limite = nueva_fecha
        tarea.save()

        notif = Notificacion.objects.filter(usuario=user, tipo='cambio_estado').order_by('-created_at').first()
        assert notif is not None
        assert notif.metadata.get('fecha_limite') == str(nueva_fecha)

    def test_sin_responsable_no_genera_notificacion_fechas(self, proyecto, fase):
        """Cambio de fechas en tarea sin responsable no genera notificación."""
        hoy = date.today()
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Tarea sin resp fechas',
            fecha_limite=hoy,
        )
        Notificacion.objects.all().delete()

        tarea.fecha_limite = hoy + timedelta(days=7)
        tarea.save()

        assert not Notificacion.objects.filter(tipo='cambio_estado').exists()
