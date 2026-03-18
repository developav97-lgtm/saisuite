"""
Tests para la capa de autenticación (AuthService + views).
Objetivo: ≥80% de cobertura en services.py
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import User


def make_user(email="test@test.com", password="Test1234!", active=True) -> User:
    company = Company.objects.create(name="Test Co", nit="900000001")
    return User.objects.create_user(
        email=email,
        password=password,
        company=company,
        role=User.Role.COMPANY_ADMIN,
        first_name="Test",
        last_name="User",
        is_active=active,
    )


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url    = reverse("auth-login")
        self.user   = make_user()

    def test_login_success(self):
        res = self.client.post(self.url, {"email": self.user.email, "password": "Test1234!"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.data["user"]["email"], self.user.email)

    def test_login_wrong_password(self):
        res = self.client.post(self.url, {"email": self.user.email, "password": "Wrong999!"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_login_inactive_user(self):
        company  = Company.objects.create(name="Inactive Co", nit="900000002")
        inactive = User.objects.create_user(
            email="inactive@test.com", password="Test1234!",
            company=company, role=User.Role.VIEWER, is_active=False,
        )
        res = self.client.post(self.url, {"email": inactive.email, "password": "Test1234!"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_login_missing_fields(self):
        res = self.client.post(self.url, {"email": self.user.email}, format="json")
        self.assertEqual(res.status_code, 400)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url    = reverse("auth-logout")
        self.user   = make_user()
        self.refresh_token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.refresh_token.access_token}")

    def test_logout_success(self):
        res = self.client.post(self.url, {"refresh": str(self.refresh_token)}, format="json")
        self.assertEqual(res.status_code, 200)

    def test_logout_invalid_token(self):
        res = self.client.post(self.url, {"refresh": "notavalidtoken"}, format="json")
        self.assertEqual(res.status_code, 400)


class RefreshViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url    = reverse("auth-refresh")
        self.user   = make_user()
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_refresh_success(self):
        res = self.client.post(self.url, {"refresh": str(self.refresh_token)}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_refresh_invalid(self):
        res = self.client.post(self.url, {"refresh": "invalid.token.here"}, format="json")
        self.assertEqual(res.status_code, 401)


class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url    = reverse("auth-me")
        self.user   = make_user()
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def test_me_authenticated(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], self.user.email)

    def test_me_unauthenticated(self):
        self.client.credentials()  # clear auth
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)
