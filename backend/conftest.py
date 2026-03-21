"""
SaiSuite — Fixtures globales de pytest.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.companies.models import Company

User = get_user_model()


@pytest.fixture
def company():
    """Fixture: Empresa de prueba."""
    return Company.objects.create(
        name="Test Company",
        nit="900000000",
        plan="professional",
    )


@pytest.fixture
def company2():
    """Fixture: Segunda empresa (para tests de aislamiento multi-tenant)."""
    return Company.objects.create(
        name="Otra Company",
        nit="800000001",
        plan="starter",
    )


@pytest.fixture
def user(company):
    """Fixture: Usuario de prueba."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        company=company,
    )


@pytest.fixture
def authenticated_client(user):
    """Fixture: Cliente API autenticado con JWT."""
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client
