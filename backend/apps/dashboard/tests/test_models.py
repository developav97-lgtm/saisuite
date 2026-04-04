"""
SaiSuite -- Dashboard: Model Tests
Tests para modelos de dashboard: integridad, constraints, metodos.
"""
import logging
from datetime import timedelta

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.companies.models import Company
from apps.users.models import User
from apps.dashboard.models import (
    Dashboard,
    DashboardCard,
    DashboardShare,
    ModuleTrial,
)

logger = logging.getLogger(__name__)


class DashboardModelTest(TestCase):
    """Tests para el modelo Dashboard."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Dashboard', nit='900111222',
        )
        self.user = User.objects.create_user(
            email='test@empresa.com',
            password='testpass123',
            company=self.company,
        )

    def test_create_dashboard(self):
        """Un dashboard se crea correctamente."""
        dashboard = Dashboard.all_objects.create(
            user=self.user,
            company=self.company,
            titulo='Mi Dashboard',
            descripcion='Dashboard de prueba',
        )
        self.assertEqual(dashboard.titulo, 'Mi Dashboard')
        self.assertTrue(dashboard.es_privado)
        self.assertFalse(dashboard.es_favorito)
        self.assertFalse(dashboard.es_default)
        self.assertEqual(dashboard.orientacion, 'portrait')

    def test_str_representation(self):
        dashboard = Dashboard.all_objects.create(
            user=self.user,
            company=self.company,
            titulo='Dashboard Test',
        )
        self.assertIn('Dashboard Test', str(dashboard))
        self.assertIn(self.user.email, str(dashboard))


class DashboardCardModelTest(TestCase):
    """Tests para el modelo DashboardCard."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Cards', nit='900333444',
        )
        self.user = User.objects.create_user(
            email='cards@empresa.com',
            password='testpass123',
            company=self.company,
        )
        self.dashboard = Dashboard.all_objects.create(
            user=self.user,
            company=self.company,
            titulo='Dashboard Cards',
        )

    def test_create_card(self):
        """Una tarjeta se crea correctamente."""
        card = DashboardCard.objects.create(
            dashboard=self.dashboard,
            card_type_code='BALANCE_GENERAL',
            chart_type='bar',
            pos_x=0,
            pos_y=0,
            width=4,
            height=3,
        )
        self.assertEqual(card.card_type_code, 'BALANCE_GENERAL')
        self.assertEqual(card.chart_type, 'bar')

    def test_ordering(self):
        """Las tarjetas se ordenan por orden, pos_y, pos_x."""
        DashboardCard.objects.create(
            dashboard=self.dashboard,
            card_type_code='A',
            orden=2, pos_y=0, pos_x=0,
        )
        DashboardCard.objects.create(
            dashboard=self.dashboard,
            card_type_code='B',
            orden=1, pos_y=0, pos_x=0,
        )
        cards = list(DashboardCard.objects.filter(dashboard=self.dashboard))
        self.assertEqual(cards[0].card_type_code, 'B')  # orden=1
        self.assertEqual(cards[1].card_type_code, 'A')  # orden=2

    def test_cascade_delete(self):
        """Al eliminar un dashboard, se eliminan sus tarjetas."""
        DashboardCard.objects.create(
            dashboard=self.dashboard,
            card_type_code='BALANCE_GENERAL',
        )
        self.assertEqual(DashboardCard.objects.count(), 1)
        self.dashboard.delete()
        self.assertEqual(DashboardCard.objects.count(), 0)


class DashboardShareModelTest(TestCase):
    """Tests para el modelo DashboardShare."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Share', nit='900555666',
        )
        self.user_a = User.objects.create_user(
            email='usera@empresa.com',
            password='testpass123',
            company=self.company,
        )
        self.user_b = User.objects.create_user(
            email='userb@empresa.com',
            password='testpass123',
            company=self.company,
        )
        self.dashboard = Dashboard.all_objects.create(
            user=self.user_a,
            company=self.company,
            titulo='Dashboard Compartido',
        )

    def test_create_share(self):
        """Un share se crea correctamente."""
        share = DashboardShare.objects.create(
            dashboard=self.dashboard,
            compartido_con=self.user_b,
            compartido_por=self.user_a,
        )
        self.assertFalse(share.puede_editar)
        self.assertIsNotNone(share.creado_en)

    def test_unique_together(self):
        """No se puede compartir dos veces con el mismo usuario."""
        DashboardShare.objects.create(
            dashboard=self.dashboard,
            compartido_con=self.user_b,
            compartido_por=self.user_a,
        )
        with self.assertRaises(IntegrityError):
            DashboardShare.objects.create(
                dashboard=self.dashboard,
                compartido_con=self.user_b,
                compartido_por=self.user_a,
            )


class ModuleTrialModelTest(TestCase):
    """Tests para el modelo ModuleTrial."""

    def setUp(self):
        self.company = Company.objects.create(
            name='Empresa Trial', nit='900777888',
        )

    def test_create_trial(self):
        """Un trial se crea correctamente."""
        now = timezone.now()
        trial = ModuleTrial.objects.create(
            company=self.company,
            module_code='dashboard',
            expira_en=now + timedelta(days=14),
        )
        self.assertEqual(trial.module_code, 'dashboard')
        self.assertTrue(trial.esta_activo())
        self.assertEqual(trial.dias_restantes(), 13)  # 14 days minus partial day

    def test_expired_trial(self):
        """Un trial expirado no esta activo."""
        trial = ModuleTrial.objects.create(
            company=self.company,
            module_code='dashboard',
            expira_en=timezone.now() - timedelta(days=1),
        )
        self.assertFalse(trial.esta_activo())
        self.assertEqual(trial.dias_restantes(), 0)

    def test_unique_together(self):
        """Solo un trial por modulo/empresa."""
        ModuleTrial.objects.create(
            company=self.company,
            module_code='dashboard',
            expira_en=timezone.now() + timedelta(days=14),
        )
        with self.assertRaises(IntegrityError):
            ModuleTrial.objects.create(
                company=self.company,
                module_code='dashboard',
                expira_en=timezone.now() + timedelta(days=14),
            )
