"""
SaiSuite — Tests: TareaService
Cobertura objetivo: >= 85% de apps.proyectos.tarea_services
"""
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.proyectos.models import Tarea
from apps.proyectos.tarea_services import TareaService


@pytest.mark.django_db
class TestCrearTareaConValidaciones:

    def test_crear_tarea_ok(self, proyecto, user):
        tarea = TareaService.crear_tarea_con_validaciones(
            proyecto=proyecto,
            nombre='Tarea de prueba',
            responsable=user,
        )
        assert tarea.id is not None
        assert tarea.nombre == 'Tarea de prueba'
        assert tarea.proyecto == proyecto
        assert tarea.codigo.startswith('TASK-')

    def test_crear_tarea_proyecto_borrador_falla(self, proyecto, user):
        proyecto.estado = 'borrador'
        proyecto.save()

        with pytest.raises(ValidationError) as exc:
            TareaService.crear_tarea_con_validaciones(
                proyecto=proyecto,
                nombre='Tarea inválida',
            )
        assert 'proyecto' in exc.value.message_dict

    def test_crear_tarea_proyecto_cerrado_falla(self, proyecto):
        proyecto.estado = 'cerrado'
        proyecto.save()

        with pytest.raises(ValidationError) as exc:
            TareaService.crear_tarea_con_validaciones(
                proyecto=proyecto,
                nombre='Tarea inválida',
            )
        assert 'proyecto' in exc.value.message_dict

    def test_crear_subtarea_con_padre_valido(self, proyecto, tarea_simple):
        subtarea = TareaService.crear_tarea_con_validaciones(
            proyecto=proyecto,
            nombre='Subtarea',
            tarea_padre=tarea_simple,
        )
        assert subtarea.tarea_padre == tarea_simple
        assert subtarea.nivel_jerarquia == 1

    def test_crear_subtarea_padre_otro_proyecto_falla(self, proyecto, user):
        from decimal import Decimal
        from datetime import date
        otro_proyecto = type(proyecto).all_objects.create(
            company=proyecto.company,
            gerente=user,
            codigo='PRY-OTRO-001',
            nombre='Otro Proyecto',
            tipo='obra_civil',
            estado='en_ejecucion',
            cliente_id='222',
            cliente_nombre='Otro Cliente',
            fecha_inicio_planificada=date.today(),
            fecha_fin_planificada=date.today() + timedelta(days=90),
            presupuesto_total=Decimal('5000000.00'),
        )
        tarea_otro = Tarea.objects.create(
            company=proyecto.company,
            proyecto=otro_proyecto,
            nombre='Tarea en otro proyecto',
        )

        with pytest.raises(ValidationError) as exc:
            TareaService.crear_tarea_con_validaciones(
                proyecto=proyecto,
                nombre='Subtarea inválida',
                tarea_padre=tarea_otro,
            )
        assert 'tarea_padre' in exc.value.message_dict

    def test_crear_subtarea_nivel_maximo_falla(self, proyecto):
        """No se puede crear subtarea si la padre está en nivel 4."""
        def crear(nombre, padre=None):
            kwargs = {'nombre': nombre}
            if padre:
                kwargs['tarea_padre'] = padre
            return Tarea.objects.create(
                company=proyecto.company, proyecto=proyecto, **kwargs
            )

        n0 = crear('N0')
        n1 = crear('N1', n0)
        n2 = crear('N2', n1)
        n3 = crear('N3', n2)
        n4 = crear('N4', n3)  # nivel_jerarquia == 4

        with pytest.raises(ValidationError) as exc:
            TareaService.crear_tarea_con_validaciones(
                proyecto=proyecto,
                nombre='N5 inválido',
                tarea_padre=n4,
            )
        assert 'tarea_padre' in exc.value.message_dict


@pytest.mark.django_db
class TestValidarPuedeCompletar:

    def test_sin_subtareas_puede_completar(self, tarea_simple):
        puede, mensaje = TareaService.validar_puede_completar(tarea_simple)
        assert puede is True
        assert mensaje is None

    def test_con_subtareas_pendientes_no_puede(self, tarea_con_subtareas):
        puede, mensaje = TareaService.validar_puede_completar(tarea_con_subtareas)
        assert puede is False
        assert 'pendiente' in mensaje.lower()

    def test_con_subtareas_completadas_puede(self, tarea_con_subtareas):
        tarea_con_subtareas.subtareas.update(estado='completada')
        puede, mensaje = TareaService.validar_puede_completar(tarea_con_subtareas)
        assert puede is True

    def test_con_subtareas_canceladas_puede(self, tarea_con_subtareas):
        tarea_con_subtareas.subtareas.update(estado='cancelada')
        puede, mensaje = TareaService.validar_puede_completar(tarea_con_subtareas)
        assert puede is True


@pytest.mark.django_db
class TestCambiarEstado:

    def test_cambiar_a_en_progreso(self, tarea_simple):
        tarea = TareaService.cambiar_estado(tarea_simple, 'en_progreso')
        assert tarea.estado == 'en_progreso'

    def test_cambiar_a_completada_sets_porcentaje_100(self, tarea_simple):
        tarea = TareaService.cambiar_estado(tarea_simple, 'completada')
        assert tarea.estado == 'completada'
        assert tarea.porcentaje_completado == 100

    def test_cambiar_a_completada_con_subtareas_pendientes_falla(self, tarea_con_subtareas):
        with pytest.raises(ValidationError) as exc:
            TareaService.cambiar_estado(tarea_con_subtareas, 'completada')
        assert 'estado' in exc.value.message_dict

    def test_cambiar_estado_invalido_falla(self, tarea_simple):
        with pytest.raises(ValidationError) as exc:
            TareaService.cambiar_estado(tarea_simple, 'estado_inexistente')
        assert 'estado' in exc.value.message_dict

    def test_cambiar_a_cancelada(self, tarea_simple):
        tarea = TareaService.cambiar_estado(tarea_simple, 'cancelada')
        assert tarea.estado == 'cancelada'


@pytest.mark.django_db
class TestRecalcularAvanceTareaPadre:

    def test_recalcula_promedio_correcto(self, tarea_con_subtareas):
        subtareas = list(tarea_con_subtareas.subtareas.all())
        subtareas[0].porcentaje_completado = 50
        subtareas[0].save()
        subtareas[1].porcentaje_completado = 50
        subtareas[1].save()
        subtareas[2].porcentaje_completado = 100
        subtareas[2].save()

        TareaService.recalcular_avance_tarea_padre(tarea_con_subtareas)

        tarea_con_subtareas.refresh_from_db()
        # (50 + 50 + 100) / 3 = 66.66 → 66
        assert tarea_con_subtareas.porcentaje_completado == 66

    def test_sin_subtareas_no_cambia(self, tarea_simple):
        tarea_simple.porcentaje_completado = 25
        tarea_simple.save()

        TareaService.recalcular_avance_tarea_padre(tarea_simple)

        tarea_simple.refresh_from_db()
        assert tarea_simple.porcentaje_completado == 25

    def test_todas_completadas_da_100(self, tarea_con_subtareas):
        tarea_con_subtareas.subtareas.update(porcentaje_completado=100)
        TareaService.recalcular_avance_tarea_padre(tarea_con_subtareas)
        tarea_con_subtareas.refresh_from_db()
        assert tarea_con_subtareas.porcentaje_completado == 100


@pytest.mark.django_db
class TestEliminarTareaConSubtareas:

    def test_cascada_elimina_padre_y_subtareas(self, tarea_con_subtareas):
        subtareas_ids = list(tarea_con_subtareas.subtareas.values_list('id', flat=True))
        padre_id = tarea_con_subtareas.id

        resultado = TareaService.eliminar_tarea_con_subtareas(
            tarea_con_subtareas, accion_subtareas='cascada'
        )

        assert resultado['success'] is True
        assert resultado['subtareas_eliminadas'] == 3
        assert resultado['subtareas_promovidas'] == 0
        assert not Tarea.objects.filter(id=padre_id).exists()
        # Con cascada, las subtareas también se eliminan (on_delete=CASCADE)
        for sid in subtareas_ids:
            assert not Tarea.objects.filter(id=sid).exists()

    def test_promover_sube_subtareas_al_nivel_del_padre(self, tarea_con_subtareas):
        subtareas_ids = list(tarea_con_subtareas.subtareas.values_list('id', flat=True))
        padre_id = tarea_con_subtareas.id
        abuelo = tarea_con_subtareas.tarea_padre  # None en este caso

        resultado = TareaService.eliminar_tarea_con_subtareas(
            tarea_con_subtareas, accion_subtareas='promover'
        )

        assert resultado['success'] is True
        assert resultado['subtareas_promovidas'] == 3
        assert resultado['subtareas_eliminadas'] == 0
        assert not Tarea.objects.filter(id=padre_id).exists()
        for sid in subtareas_ids:
            sub = Tarea.objects.get(id=sid)
            assert sub.tarea_padre == abuelo  # subieron al nivel del padre (None)

    def test_accion_invalida_falla(self, tarea_simple):
        with pytest.raises(ValidationError) as exc:
            TareaService.eliminar_tarea_con_subtareas(tarea_simple, 'borrar_todo')
        assert 'accion_subtareas' in exc.value.message_dict

    def test_cascada_sin_subtareas(self, tarea_simple):
        resultado = TareaService.eliminar_tarea_con_subtareas(
            tarea_simple, accion_subtareas='cascada'
        )
        assert resultado['success'] is True
        assert resultado['subtareas_eliminadas'] == 0


@pytest.mark.django_db
class TestObtenerTareasVencidas:

    def test_retorna_tareas_vencidas(self, proyecto):
        vencida = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Vencida',
            fecha_limite=timezone.now().date() - timedelta(days=1),
            estado='por_hacer',
        )
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='No vencida',
            fecha_limite=timezone.now().date() + timedelta(days=5),
            estado='por_hacer',
        )

        tareas = TareaService.obtener_tareas_vencidas(proyecto)

        assert len(tareas) == 1
        assert tareas[0].id == vencida.id

    def test_excluye_completadas_y_canceladas(self, proyecto):
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Completada vencida',
            fecha_limite=timezone.now().date() - timedelta(days=1),
            estado='completada',
        )
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Cancelada vencida',
            fecha_limite=timezone.now().date() - timedelta(days=1),
            estado='cancelada',
        )

        tareas = TareaService.obtener_tareas_vencidas(proyecto)
        assert len(tareas) == 0

    def test_sin_proyecto_retorna_todas(self, proyecto):
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Vencida global',
            fecha_limite=timezone.now().date() - timedelta(days=2),
            estado='en_progreso',
        )
        tareas = TareaService.obtener_tareas_vencidas()
        assert any(t.nombre == 'Vencida global' for t in tareas)


@pytest.mark.django_db
class TestObtenerTareasProximasVencer:

    def test_retorna_tarea_que_vence_manana(self, proyecto):
        manana = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Vence mañana',
            fecha_limite=timezone.now().date() + timedelta(days=1),
            estado='por_hacer',
        )
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Vence en 5 días',
            fecha_limite=timezone.now().date() + timedelta(days=5),
            estado='por_hacer',
        )

        tareas = TareaService.obtener_tareas_proximas_vencer(dias=1, proyecto=proyecto)

        assert len(tareas) == 1
        assert tareas[0].id == manana.id

    def test_excluye_completadas(self, proyecto):
        Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Completada próxima',
            fecha_limite=timezone.now().date() + timedelta(days=1),
            estado='completada',
        )

        tareas = TareaService.obtener_tareas_proximas_vencer(dias=1, proyecto=proyecto)
        assert len(tareas) == 0

    def test_incluye_hoy(self, proyecto):
        hoy = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Vence hoy',
            fecha_limite=timezone.now().date(),
            estado='por_hacer',
        )

        tareas = TareaService.obtener_tareas_proximas_vencer(dias=0, proyecto=proyecto)
        assert any(t.id == hoy.id for t in tareas)


@pytest.mark.django_db
class TestGenerarTareaRecurrente:

    def test_genera_tarea_semanal(self, proyecto):
        hoy = timezone.now().date()
        original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Revisión semanal',
            es_recurrente=True,
            frecuencia_recurrencia='semanal',
            fecha_limite=hoy,
            estado='completada',
        )

        nueva = TareaService.generar_tarea_recurrente(original)

        assert nueva is not None
        assert nueva.nombre == original.nombre
        assert nueva.fecha_limite == hoy + timedelta(weeks=1)
        assert nueva.estado == 'por_hacer'
        assert nueva.es_recurrente is True

    def test_genera_tarea_diaria(self, proyecto):
        hoy = timezone.now().date()
        original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Tarea diaria',
            es_recurrente=True,
            frecuencia_recurrencia='diaria',
            fecha_limite=hoy,
        )

        nueva = TareaService.generar_tarea_recurrente(original)

        assert nueva.fecha_limite == hoy + timedelta(days=1)

    def test_genera_tarea_mensual(self, proyecto):
        hoy = timezone.now().date()
        original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Tarea mensual',
            es_recurrente=True,
            frecuencia_recurrencia='mensual',
            fecha_limite=hoy,
        )

        nueva = TareaService.generar_tarea_recurrente(original)

        assert nueva.fecha_limite == hoy + timedelta(days=30)

    def test_no_recurrente_retorna_none(self, tarea_simple):
        resultado = TareaService.generar_tarea_recurrente(tarea_simple)
        assert resultado is None

    def test_recurrente_sin_frecuencia_retorna_none(self, proyecto):
        original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Sin frecuencia',
            es_recurrente=True,
            frecuencia_recurrencia=None,
        )
        resultado = TareaService.generar_tarea_recurrente(original)
        assert resultado is None

    def test_copia_tags_y_followers(self, proyecto, user):
        from apps.proyectos.models import TareaTag
        tag = TareaTag.objects.create(company=proyecto.company, nombre='urgente', color='red')
        hoy = timezone.now().date()
        original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Con tags',
            es_recurrente=True,
            frecuencia_recurrencia='semanal',
            fecha_limite=hoy,
        )
        original.tags.add(tag)
        original.followers.add(user)

        nueva = TareaService.generar_tarea_recurrente(original)

        assert tag in nueva.tags.all()
        assert user in nueva.followers.all()

    def test_actualiza_proxima_generacion_en_original(self, proyecto):
        hoy = timezone.now().date()
        original = Tarea.objects.create(
            company=proyecto.company,
            proyecto=proyecto,
            nombre='Con próxima',
            es_recurrente=True,
            frecuencia_recurrencia='semanal',
            fecha_limite=hoy,
        )

        TareaService.generar_tarea_recurrente(original)

        original.refresh_from_db()
        assert original.proxima_generacion == hoy + timedelta(weeks=1)
