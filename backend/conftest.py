"""
SaiSuite — Fixtures globales de pytest.
"""
import pytest


@pytest.fixture
def company():
    """Fixture: Empresa de prueba."""
    from apps.companies.models import Company
    return Company.objects.create(
        name="Test Company",
        nit="900000000",
        plan="professional",
    )


@pytest.fixture
def company2():
    """Fixture: Segunda empresa (para tests de aislamiento multi-tenant)."""
    from apps.companies.models import Company
    return Company.objects.create(
        name="Otra Company",
        nit="800000001",
        plan="starter",
    )


@pytest.fixture
def user(company):
    """Fixture: Usuario de prueba."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
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
