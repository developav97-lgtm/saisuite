"""
SaiSuite — Tests: Signals de Task
Verifica comportamientos automáticos al crear/modificar Tareas.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.proyectos.models import Task


@pytest.mark.django_db
class TestAutoFollowerAlCrear:

    def test_responsable_se_agrega_como_follower(self, proyecto, fase, user):
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Task con responsable',
            responsable=user,
        )
        assert user in tarea.followers.all()

    def test_sin_responsable_no_falla(self, proyecto, fase):
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Task sin responsable',
        )
        assert tarea.followers.count() == 0


@pytest.mark.django_db
class TestRecalcularAvancePadreSignal:

    def test_recalcula_al_cambiar_porcentaje_subtarea(self, tarea_con_subtareas):
        subtarea = tarea_con_subtareas.subtasks.first()
        subtarea.porcentaje_completado = 100
        subtarea.save()

        tarea_con_subtareas.refresh_from_db()
        # (100 + 0 + 0) / 3 = 33.33 → 33
        assert tarea_con_subtareas.porcentaje_completado == 33

    def test_recalcula_todas_al_100(self, tarea_con_subtareas):
        tarea_con_subtareas.subtasks.all().update(porcentaje_completado=100)
        # Disparar el signal con la última subtarea guardada individualmente
        ultima = tarea_con_subtareas.subtasks.last()
        ultima.porcentaje_completado = 100
        ultima.save()

        tarea_con_subtareas.refresh_from_db()
        assert tarea_con_subtareas.porcentaje_completado == 100

    def test_no_dispara_al_crear_raiz(self, proyecto, fase):
        """Crear tarea sin padre no intenta recalcular."""
        # No debe lanzar excepción
        tarea = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Raíz sin padre',
        )
        assert tarea.id is not None


@pytest.mark.django_db
class TestGenerarTareaRecurrenteSignal:

    def test_genera_nueva_tarea_al_completar_recurrente(self, proyecto, fase):
        hoy = timezone.now().date()
        tarea_original = Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Task recurrente',
            es_recurrente=True,
            frecuencia_recurrencia='diaria',
            fecha_limite=hoy,
            estado='todo',
        )
        count_inicial = Task.objects.count()

        tarea_original.estado = 'completed'
        tarea_original.save()

        assert Task.objects.count() == count_inicial + 1

        nueva = Task.objects.exclude(id=tarea_original.id).filter(
            nombre='Task recurrente'
        ).last()
        assert nueva is not None
        assert nueva.fecha_limite == hoy + timedelta(days=1)
        assert nueva.es_recurrente is True

    def test_no_genera_si_no_es_recurrente(self, tarea_simple):
        count_inicial = Task.objects.count()

        tarea_simple.estado = 'completed'
        tarea_simple.save()

        assert Task.objects.count() == count_inicial

    def test_no_genera_al_crear_recurrente(self, proyecto, fase):
        """Crear tarea recurrente NO debe generar una nueva instancia."""
        count_inicial = Task.objects.count()

        Task.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            fase=fase,
            nombre='Recurrente nueva',
            es_recurrente=True,
            frecuencia_recurrencia='semanal',
            estado='todo',
        )

        # Solo debe existir la tarea recién creada, no una generada automáticamente
        assert Task.objects.count() == count_inicial + 1
