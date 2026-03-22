"""
SaiSuite — Tests: Signals de Tarea
Verifica comportamientos automáticos al crear/modificar Tareas.
"""
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.proyectos.models import Tarea


@pytest.mark.django_db
class TestAutoFollowerAlCrear:

    def test_responsable_se_agrega_como_follower(self, proyecto, user):
        tarea = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Tarea con responsable',
            responsable=user,
        )
        assert user in tarea.followers.all()

    def test_sin_responsable_no_falla(self, proyecto):
        tarea = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Tarea sin responsable',
        )
        assert tarea.followers.count() == 0


@pytest.mark.django_db
class TestRecalcularAvancePadreSignal:

    def test_recalcula_al_cambiar_porcentaje_subtarea(self, tarea_con_subtareas):
        subtarea = tarea_con_subtareas.subtareas.first()
        subtarea.porcentaje_completado = 100
        subtarea.save()

        tarea_con_subtareas.refresh_from_db()
        # (100 + 0 + 0) / 3 = 33.33 → 33
        assert tarea_con_subtareas.porcentaje_completado == 33

    def test_recalcula_todas_al_100(self, tarea_con_subtareas):
        tarea_con_subtareas.subtareas.all().update(porcentaje_completado=100)
        # Disparar el signal con la última subtarea guardada individualmente
        ultima = tarea_con_subtareas.subtareas.last()
        ultima.porcentaje_completado = 100
        ultima.save()

        tarea_con_subtareas.refresh_from_db()
        assert tarea_con_subtareas.porcentaje_completado == 100

    def test_no_dispara_al_crear_raiz(self, proyecto):
        """Crear tarea sin padre no intenta recalcular."""
        # No debe lanzar excepción
        tarea = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Raíz sin padre',
        )
        assert tarea.id is not None


@pytest.mark.django_db
class TestGenerarTareaRecurrenteSignal:

    def test_genera_nueva_tarea_al_completar_recurrente(self, proyecto):
        hoy = timezone.now().date()
        tarea_original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Tarea recurrente',
            es_recurrente=True,
            frecuencia_recurrencia='diaria',
            fecha_limite=hoy,
            estado='por_hacer',
        )
        count_inicial = Tarea.objects.count()

        tarea_original.estado = 'completada'
        tarea_original.save()

        assert Tarea.objects.count() == count_inicial + 1

        nueva = Tarea.objects.exclude(id=tarea_original.id).filter(
            nombre='Tarea recurrente'
        ).last()
        assert nueva is not None
        assert nueva.fecha_limite == hoy + timedelta(days=1)
        assert nueva.es_recurrente is True

    def test_no_genera_si_no_es_recurrente(self, tarea_simple):
        count_inicial = Tarea.objects.count()

        tarea_simple.estado = 'completada'
        tarea_simple.save()

        assert Tarea.objects.count() == count_inicial

    def test_no_genera_al_crear_recurrente(self, proyecto):
        """Crear tarea recurrente NO debe generar una nueva instancia."""
        count_inicial = Tarea.objects.count()

        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Recurrente nueva',
            es_recurrente=True,
            frecuencia_recurrencia='semanal',
            estado='por_hacer',
        )

        # Solo debe existir la tarea recién creada, no una generada automáticamente
        assert Tarea.objects.count() == count_inicial + 1
