"""
SaiSuite — Proyectos: Tests de Serializers
"""
from decimal import Decimal
from django.test import TestCase
from apps.proyectos.serializers import (
    FaseCreateUpdateSerializer,
    ProyectoCreateUpdateSerializer,
    CambiarEstadoSerializer,
)


class FaseCreateUpdateSerializerTest(TestCase):

    def _base_data(self, **kwargs):
        defaults = {
            'nombre': 'Fase Test',
            'orden': 1,
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-06-30',
        }
        defaults.update(kwargs)
        return defaults

    def test_valido(self):
        s = FaseCreateUpdateSerializer(data=self._base_data())
        self.assertTrue(s.is_valid(), s.errors)

    def test_fecha_fin_menor_inicio(self):
        s = FaseCreateUpdateSerializer(data=self._base_data(
            fecha_inicio_planificada='2026-06-30',
            fecha_fin_planificada='2026-04-01',
        ))
        self.assertFalse(s.is_valid())
        self.assertIn('fecha_fin_planificada', s.errors)

    def test_porcentaje_avance_fuera_rango(self):
        s = FaseCreateUpdateSerializer(data=self._base_data(porcentaje_avance='150'))
        self.assertFalse(s.is_valid())
        self.assertIn('porcentaje_avance', s.errors)

    def test_porcentaje_avance_negativo(self):
        s = FaseCreateUpdateSerializer(data=self._base_data(porcentaje_avance='-1'))
        self.assertFalse(s.is_valid())
        self.assertIn('porcentaje_avance', s.errors)


class ProyectoCreateUpdateSerializerTest(TestCase):

    def _base_data(self, gerente_id, **kwargs):
        defaults = {
            'nombre': 'Proyecto Test',
            'tipo': 'obra_civil',
            'cliente_id': '900111',
            'cliente_nombre': 'Cliente',
            'fecha_inicio_planificada': '2026-04-01',
            'fecha_fin_planificada': '2026-12-31',
            'presupuesto_total': '500000.00',
            'gerente': str(gerente_id),
        }
        defaults.update(kwargs)
        return defaults

    def setUp(self):
        import uuid
        self.gerente_id = uuid.uuid4()

    def test_valido(self):
        s = ProyectoCreateUpdateSerializer(data=self._base_data(self.gerente_id))
        self.assertTrue(s.is_valid(), s.errors)

    def test_fecha_fin_menor_inicio(self):
        s = ProyectoCreateUpdateSerializer(data=self._base_data(
            self.gerente_id,
            fecha_inicio_planificada='2026-12-31',
            fecha_fin_planificada='2026-01-01',
        ))
        self.assertFalse(s.is_valid())
        self.assertIn('fecha_fin_planificada', s.errors)

    def test_presupuesto_negativo(self):
        s = ProyectoCreateUpdateSerializer(data=self._base_data(
            self.gerente_id, presupuesto_total='-100'
        ))
        self.assertFalse(s.is_valid())
        self.assertIn('presupuesto_total', s.errors)


class CambiarEstadoSerializerTest(TestCase):

    def test_estado_valido(self):
        s = CambiarEstadoSerializer(data={'nuevo_estado': 'planificado'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_estado_invalido(self):
        s = CambiarEstadoSerializer(data={'nuevo_estado': 'inexistente'})
        self.assertFalse(s.is_valid())

    def test_forzar_default_false(self):
        s = CambiarEstadoSerializer(data={'nuevo_estado': 'planificado'})
        s.is_valid()
        self.assertFalse(s.validated_data.get('forzar', False))
