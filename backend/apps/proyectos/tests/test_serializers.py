"""
SaiSuite — Proyectos: Tests de Serializers
"""
import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company, CompanyModule
from apps.proyectos.serializers import (
    FaseCreateUpdateSerializer,
    ProyectoCreateUpdateSerializer,
    CambiarEstadoSerializer,
    TerceroProyectoCreateSerializer,
    HitoCreateSerializer,
    GenerarFacturaSerializer,
)
from apps.proyectos.models import Proyecto, Fase

User = get_user_model()


def _crear_empresa(nit='900000001'):
    company = Company.objects.create(name='Test', nit=nit)
    CompanyModule.objects.create(company=company, module='proyectos', is_active=True)
    return company


def _crear_user(company, email='u@test.com'):
    return User.objects.create_user(email=email, password='x', company=company, role='company_admin')


def _crear_proyecto(company, gerente, codigo='PRY-001'):
    return Proyecto.all_objects.create(
        company=company, gerente=gerente,
        codigo=codigo, nombre='P', tipo='servicios',
        cliente_id='1', cliente_nombre='C',
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-12-31',
        presupuesto_total=Decimal('1000000'),
    )


def _crear_fase(company, proyecto, orden=1):
    return Fase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre=f'Fase {orden}', orden=orden,
        fecha_inicio_planificada='2026-04-01',
        fecha_fin_planificada='2026-06-30',
        presupuesto_mano_obra=Decimal('200000'),
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


# ══════════════════════════════════════════════
# Fase B — TerceroProyectoCreateSerializer
# ══════════════════════════════════════════════

class TerceroProyectoCreateSerializerTest(TestCase):

    def setUp(self):
        self.company  = _crear_empresa()
        self.user     = _crear_user(self.company)
        self.proyecto = _crear_proyecto(self.company, self.user)
        self.fase     = _crear_fase(self.company, self.proyecto)

    def _base_data(self, **kwargs):
        defaults = {
            'tercero_id': '900111',
            'tercero_nombre': 'Subcontratista SA',
            'rol': 'subcontratista',
        }
        defaults.update(kwargs)
        return defaults

    def test_valido_sin_fase(self):
        s = TerceroProyectoCreateSerializer(
            data=self._base_data(), context={'proyecto': self.proyecto}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_valido_con_fase_del_mismo_proyecto(self):
        s = TerceroProyectoCreateSerializer(
            data=self._base_data(fase=str(self.fase.id)),
            context={'proyecto': self.proyecto},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_fase_de_otro_proyecto_falla(self):
        otro_user     = _crear_user(self.company, 'otro@test.com')
        otro_proyecto = _crear_proyecto(self.company, otro_user, codigo='PRY-002')
        fase_ajena = _crear_fase(self.company, otro_proyecto, orden=2)
        s = TerceroProyectoCreateSerializer(
            data=self._base_data(fase=str(fase_ajena.id)),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('fase', s.errors)

    def test_rol_invalido_falla(self):
        s = TerceroProyectoCreateSerializer(
            data=self._base_data(rol='rol_inexistente'),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('rol', s.errors)

    def test_sin_tercero_id_falla(self):
        data = self._base_data()
        del data['tercero_id']
        s = TerceroProyectoCreateSerializer(data=data, context={'proyecto': self.proyecto})
        self.assertFalse(s.is_valid())
        self.assertIn('tercero_id', s.errors)

    def test_sin_rol_falla(self):
        data = self._base_data()
        del data['rol']
        s = TerceroProyectoCreateSerializer(data=data, context={'proyecto': self.proyecto})
        self.assertFalse(s.is_valid())
        self.assertIn('rol', s.errors)


# ══════════════════════════════════════════════
# Fase B — HitoCreateSerializer
# ══════════════════════════════════════════════

class HitoCreateSerializerTest(TestCase):

    def setUp(self):
        self.company  = _crear_empresa('900000099')
        self.user     = _crear_user(self.company, 'hito@test.com')
        self.proyecto = _crear_proyecto(self.company, self.user)
        self.fase     = _crear_fase(self.company, self.proyecto)

    def _base_data(self, **kwargs):
        defaults = {
            'nombre': 'Hito Test',
            'porcentaje_proyecto': '25.00',
            'valor_facturar': '250000.00',
            'facturable': True,
        }
        defaults.update(kwargs)
        return defaults

    def test_valido(self):
        s = HitoCreateSerializer(
            data=self._base_data(), context={'proyecto': self.proyecto}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_porcentaje_cero_falla(self):
        s = HitoCreateSerializer(
            data=self._base_data(porcentaje_proyecto='0'),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('porcentaje_proyecto', s.errors)

    def test_porcentaje_mayor_100_falla(self):
        s = HitoCreateSerializer(
            data=self._base_data(porcentaje_proyecto='101'),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('porcentaje_proyecto', s.errors)

    def test_valor_cero_falla(self):
        s = HitoCreateSerializer(
            data=self._base_data(valor_facturar='0'),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('valor_facturar', s.errors)

    def test_valor_negativo_falla(self):
        s = HitoCreateSerializer(
            data=self._base_data(valor_facturar='-1000'),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('valor_facturar', s.errors)

    def test_valido_con_fase_mismo_proyecto(self):
        s = HitoCreateSerializer(
            data=self._base_data(fase=str(self.fase.id)),
            context={'proyecto': self.proyecto},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_fase_otro_proyecto_falla(self):
        otro_user = _crear_user(self.company, 'otro_hito@test.com')
        otro_proyecto = _crear_proyecto(self.company, otro_user, codigo='PRY-099')
        fase_ajena = _crear_fase(self.company, otro_proyecto, orden=2)
        s = HitoCreateSerializer(
            data=self._base_data(fase=str(fase_ajena.id)),
            context={'proyecto': self.proyecto},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('fase', s.errors)

    def test_porcentaje_exactamente_100_valido(self):
        s = HitoCreateSerializer(
            data=self._base_data(porcentaje_proyecto='100.00'),
            context={'proyecto': self.proyecto},
        )
        self.assertTrue(s.is_valid(), s.errors)


# ══════════════════════════════════════════════
# Fase B — GenerarFacturaSerializer
# ══════════════════════════════════════════════

class GenerarFacturaSerializerTest(TestCase):

    def test_confirmar_true_valido(self):
        s = GenerarFacturaSerializer(data={'confirmar': True})
        self.assertTrue(s.is_valid(), s.errors)

    def test_confirmar_false_falla(self):
        s = GenerarFacturaSerializer(data={'confirmar': False})
        self.assertFalse(s.is_valid())
        self.assertIn('confirmar', s.errors)

    def test_sin_confirmar_falla(self):
        s = GenerarFacturaSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('confirmar', s.errors)
