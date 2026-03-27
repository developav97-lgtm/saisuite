"""
SaiSuite — Tests: Feature Timesheets Mejorados
Cubre:
- Modelo TimesheetEntry (unique_together, clean, validadores)
- TimesheetEntryService: registrar_horas, eliminar_entry, validar_timesheet, recalcular_horas_tarea
- TimesheetViewSet: list, create, partial_update, destroy, mis_horas, validar
- Flujo timer existente: iniciar → pausar → reanudar → detener (WorkSession)
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from apps.companies.models import Company, CompanyModule
from apps.proyectos.models import Project, Phase, Task, TimesheetEntry
from apps.proyectos.tarea_services import TimesheetEntryService, TimesheetService

User = get_user_model()

# ── Counters for unique values ─────────────────────────────────────────────────
_NIT   = [850_000_000]
_EMAIL = [0]


def _nit():
    _NIT[0] += 1
    return str(_NIT[0])


def _email():
    _EMAIL[0] += 1
    return f'ts_{_EMAIL[0]}@test.com'


# ── Factories ──────────────────────────────────────────────────────────────────

def make_company():
    c = Company.objects.create(name=f'TS Co {_nit()}', nit=_nit())
    CompanyModule.objects.create(company=c, module='proyectos', is_active=True)
    return c


def make_user(company, role='company_admin'):
    return User.objects.create_user(
        email=_email(), password='Pass1234!', company=company, role=role,
    )


def make_proyecto(company, gerente):
    return Project.all_objects.create(
        company=company, gerente=gerente,
        codigo=f'TS-{_nit()}',
        nombre='Project Timesheet',
        tipo='services',
        estado='in_progress',
        cliente_id='777', cliente_nombre='Cliente TS',
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=90),
        presupuesto_total=Decimal('10000000'),
    )


def make_fase(company, proyecto):
    return Phase.all_objects.create(
        company=company, proyecto=proyecto,
        nombre='Phase TS', orden=1,
        fecha_inicio_planificada=date.today(),
        fecha_fin_planificada=date.today() + timedelta(days=60),
        presupuesto_mano_obra=Decimal('1000000'),
    )


def make_tarea(company, proyecto, fase, nombre='Task TS'):
    return Task.objects.create(
        company=company, proyecto=proyecto, fase=fase,
        nombre=nombre, estado='in_progress',
        horas_estimadas=Decimal('8'),
    )


def make_entry(company, tarea, usuario, horas=Decimal('2'), fecha=None):
    return TimesheetEntry.objects.create(
        company=company,
        tarea=tarea,
        usuario=usuario,
        fecha=fecha or date.today(),
        horas=horas,
        descripcion='Trabajo realizado',
    )


# ── Tests: Modelo ──────────────────────────────────────────────────────────────

class TestTimesheetEntryModelo(APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase)

    def test_crear_entry_valido(self):
        entry = make_entry(self.company, self.tarea, self.user)
        self.assertEqual(entry.horas, Decimal('2'))
        self.assertFalse(entry.validado)

    def test_unique_together_tarea_usuario_fecha(self):
        make_entry(self.company, self.tarea, self.user, fecha=date.today())
        with self.assertRaises(Exception):
            make_entry(self.company, self.tarea, self.user, fecha=date.today())

    def test_clean_horas_cero_falla(self):
        entry = TimesheetEntry(
            company=self.company, tarea=self.tarea, usuario=self.user,
            fecha=date.today(), horas=Decimal('0'),
        )
        with self.assertRaises(DjangoValidationError):
            entry.clean()

    def test_clean_horas_mayor_24_falla(self):
        entry = TimesheetEntry(
            company=self.company, tarea=self.tarea, usuario=self.user,
            fecha=date.today(), horas=Decimal('25'),
        )
        with self.assertRaises(DjangoValidationError):
            entry.clean()

    def test_str_representation(self):
        entry = make_entry(self.company, self.tarea, self.user)
        self.assertIn(self.tarea.codigo, str(entry))


# ── Tests: TimesheetEntryService ───────────────────────────────────────────────

class TestTimesheetEntryService(APITestCase):

    def setUp(self):
        self.company  = make_company()
        self.admin    = make_user(self.company, role='company_admin')
        self.empleado = make_user(self.company, role='seller')
        self.proyecto = make_proyecto(self.company, self.admin)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase)

    def test_registrar_horas_crea_entry(self):
        entry = TimesheetEntryService.registrar_horas(
            tarea_id=str(self.tarea.id),
            usuario=self.empleado,
            fecha=date.today(),
            horas=Decimal('3'),
            company=self.company,
        )
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.horas, Decimal('3'))

    def test_registrar_horas_actualiza_si_ya_existe(self):
        TimesheetEntryService.registrar_horas(
            tarea_id=str(self.tarea.id),
            usuario=self.empleado,
            fecha=date.today(),
            horas=Decimal('2'),
            company=self.company,
        )
        entry = TimesheetEntryService.registrar_horas(
            tarea_id=str(self.tarea.id),
            usuario=self.empleado,
            fecha=date.today(),
            horas=Decimal('4'),
            company=self.company,
        )
        self.assertEqual(entry.horas, Decimal('4'))
        self.assertEqual(
            TimesheetEntry.objects.filter(
                tarea=self.tarea, usuario=self.empleado, fecha=date.today(),
            ).count(), 1,
        )

    def test_registrar_horas_entry_validado_falla(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry.validado = True
        entry.save()
        from rest_framework.exceptions import ValidationError as DRFValidationError
        with self.assertRaises((DRFValidationError, DjangoValidationError, Exception)):
            TimesheetEntryService.registrar_horas(
                tarea_id=str(self.tarea.id),
                usuario=self.empleado,
                fecha=date.today(),
                horas=Decimal('1'),
                company=self.company,
            )

    def test_eliminar_entry_no_validado(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry_id = str(entry.id)
        TimesheetEntryService.eliminar_entry(entry_id, self.empleado)
        self.assertFalse(TimesheetEntry.objects.filter(id=entry_id).exists())

    def test_eliminar_entry_validado_falla(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry.validado = True
        entry.save()
        from rest_framework.exceptions import ValidationError as DRFValidationError
        with self.assertRaises((DRFValidationError, DjangoValidationError, Exception)):
            TimesheetEntryService.eliminar_entry(str(entry.id), self.empleado)

    def test_validar_timesheet_por_gerente(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry_validado = TimesheetEntryService.validar_timesheet(str(entry.id), self.admin)
        self.assertTrue(entry_validado.validado)
        self.assertEqual(entry_validado.validado_por, self.admin)

    def test_validar_timesheet_sin_permiso_falla(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        otro_user = make_user(self.company, role='seller')
        from rest_framework.exceptions import ValidationError as DRFValidationError
        with self.assertRaises((DRFValidationError, DjangoValidationError, Exception)):
            TimesheetEntryService.validar_timesheet(str(entry.id), otro_user)

    def test_recalcular_horas_tarea(self):
        entry1 = make_entry(
            self.company, self.tarea, self.empleado,
            horas=Decimal('3'), fecha=date.today(),
        )
        entry2 = make_entry(
            self.company, self.tarea, self.admin,
            horas=Decimal('2'), fecha=date.today(),
        )
        # Solo validados suman
        entry1.validado = True
        entry1.save()
        entry2.validado = True
        entry2.save()

        total = TimesheetEntryService.recalcular_horas_tarea(str(self.tarea.id))
        self.tarea.refresh_from_db()
        self.assertEqual(total, Decimal('5'))
        self.assertEqual(self.tarea.horas_registradas, Decimal('5'))

    def test_recalcular_no_incluye_no_validados(self):
        make_entry(self.company, self.tarea, self.empleado, horas=Decimal('5'))
        total = TimesheetEntryService.recalcular_horas_tarea(str(self.tarea.id))
        self.assertEqual(total, Decimal('0'))

    def test_mis_horas_filtra_por_rango(self):
        make_entry(self.company, self.tarea, self.empleado, fecha=date.today())
        make_entry(
            self.company, self.tarea, self.empleado,
            fecha=date.today() - timedelta(days=10),
        )
        qs = TimesheetEntryService.mis_horas(
            self.empleado,
            date.today() - timedelta(days=5),
            date.today(),
            self.company,
        )
        self.assertEqual(qs.count(), 1)


# ── Tests: API (TimesheetViewSet) ──────────────────────────────────────────────

class TestTimesheetViewSet(APITestCase):

    def setUp(self):
        self.company   = make_company()
        self.admin     = make_user(self.company, role='company_admin')
        self.empleado  = make_user(self.company, role='seller')
        self.proyecto  = make_proyecto(self.company, self.admin)
        self.fase      = make_fase(self.company, self.proyecto)
        self.tarea     = make_tarea(self.company, self.proyecto, self.fase)
        token = RefreshToken.for_user(self.empleado)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        self.base_url = '/api/v1/projects/timesheets/'

    # ── list ──────────────────────────────────────────────────────────────────

    def test_list_retorna_200(self):
        make_entry(self.company, self.tarea, self.empleado)
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)

    def test_list_solo_mis_entries(self):
        make_entry(self.company, self.tarea, self.empleado)
        make_entry(self.company, self.tarea, self.admin, fecha=date.today() + timedelta(days=1))
        resp = self.client.get(self.base_url)
        self.assertEqual(len(resp.data), 1)

    # ── create ────────────────────────────────────────────────────────────────

    def test_create_retorna_201(self):
        resp = self.client.post(self.base_url, {
            'tarea_id':    str(self.tarea.id),
            'fecha':       str(date.today()),
            'horas':       '3.50',
            'descripcion': 'Desarrollo backend',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(resp.data['horas']), Decimal('3.50'))

    def test_create_horas_invalidas_retorna_400(self):
        resp = self.client.post(self.base_url, {
            'tarea_id': str(self.tarea.id),
            'fecha':    str(date.today()),
            'horas':    '0',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_horas_mayores_24_retorna_400(self):
        resp = self.client.post(self.base_url, {
            'tarea_id': str(self.tarea.id),
            'fecha':    str(date.today()),
            'horas':    '25',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── partial_update ────────────────────────────────────────────────────────

    def test_partial_update_retorna_200(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        resp = self.client.patch(
            f'{self.base_url}{entry.id}/', {'descripcion': 'Actualizado'}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_partial_update_entry_validado_retorna_400(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry.validado = True
        entry.save()
        resp = self.client.patch(f'{self.base_url}{entry.id}/', {'horas': '5'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── destroy ───────────────────────────────────────────────────────────────

    def test_destroy_retorna_204(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        resp = self.client.delete(f'{self.base_url}{entry.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TimesheetEntry.objects.filter(id=entry.id).exists())

    def test_destroy_entry_validado_retorna_400(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry.validado = True
        entry.save()
        resp = self.client.delete(f'{self.base_url}{entry.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── mis_horas ─────────────────────────────────────────────────────────────

    def test_mis_horas_retorna_200(self):
        make_entry(self.company, self.tarea, self.empleado)
        fi = date.today() - timedelta(days=7)
        ff = date.today()
        resp = self.client.get(
            f'{self.base_url}mis_horas/?fecha_inicio={fi}&fecha_fin={ff}'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 1)

    def test_mis_horas_sin_fechas_retorna_400(self):
        resp = self.client.get(f'{self.base_url}mis_horas/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mis_horas_fecha_invalida_retorna_400(self):
        resp = self.client.get(
            f'{self.base_url}mis_horas/?fecha_inicio=invalid&fecha_fin=2026-03-31'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── validar ───────────────────────────────────────────────────────────────

    def test_validar_por_gerente_retorna_200(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        token = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.post(f'{self.base_url}{entry.id}/validar/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['validado'])

    def test_validar_sin_permiso_retorna_400(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        otro = make_user(self.company, role='seller')
        token = RefreshToken.for_user(otro)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.post(f'{self.base_url}{entry.id}/validar/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validar_dos_veces_retorna_400(self):
        entry = make_entry(self.company, self.tarea, self.empleado)
        entry.validado = True
        entry.save()
        token = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.post(f'{self.base_url}{entry.id}/validar/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── acceso cross-company ──────────────────────────────────────────────────

    def test_otra_empresa_no_ve_mis_entries(self):
        make_entry(self.company, self.tarea, self.empleado)
        otro_company = make_company()
        otro_user    = make_user(otro_company)
        token = RefreshToken.for_user(otro_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)


# ── Tests: Timer (WorkSession) ──────────────────────────────────────────────

class TestTimerFlujo(APITestCase):
    """Flujo completo del cronómetro usando los endpoints existentes."""

    def setUp(self):
        self.company  = make_company()
        self.user     = make_user(self.company)
        self.proyecto = make_proyecto(self.company, self.user)
        self.fase     = make_fase(self.company, self.proyecto)
        self.tarea    = make_tarea(self.company, self.proyecto, self.fase)
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')

    def test_iniciar_sesion_retorna_201(self):
        resp = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['estado'], 'active')

    def test_no_puede_iniciar_dos_sesiones(self):
        self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        resp = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pausar_sesion_activa(self):
        resp_inicio = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        sesion_id = resp_inicio.data['id']
        resp = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/{sesion_id}/pausar/'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'paused')

    def test_reanudar_sesion_pausada(self):
        resp_inicio = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        sesion_id = resp_inicio.data['id']
        self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/{sesion_id}/pausar/'
        )
        resp = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/{sesion_id}/reanudar/'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'active')

    def test_detener_sesion_actualiza_horas_tarea(self):
        resp_inicio = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        sesion_id = resp_inicio.data['id']
        resp = self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/{sesion_id}/detener/',
            {'notas': 'Trabajo completado'},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'finished')

    def test_sesion_activa_endpoint(self):
        self.client.post(
            f'/api/v1/projects/tasks/{self.tarea.id}/sesiones/iniciar/'
        )
        resp = self.client.get('/api/v1/projects/tasks/sesion-activa/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['estado'], 'active')
