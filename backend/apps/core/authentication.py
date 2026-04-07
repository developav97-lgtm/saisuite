"""
Autenticación por AgentToken para el agente Go de sync.
El agente envía: Authorization: Agent <token>
"""
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AgentTokenAuthentication(BaseAuthentication):
    """
    Autentica requests del agente Go usando un AgentToken estático.
    Header esperado: Authorization: Agent <token>
    Retorna el usuario del company como request.user y la company como request.auth.
    """
    keyword = 'Agent'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith(f'{self.keyword} '):
            return None  # No es este esquema — dejar pasar a otros authenticators

        token_value = auth_header[len(self.keyword) + 1:].strip()
        if not token_value:
            return None

        # Import aquí para evitar circular imports
        from apps.companies.models import AgentToken

        try:
            agent_token = AgentToken.objects.select_related('company').get(
                token=token_value,
                is_active=True,
            )
        except AgentToken.DoesNotExist:
            raise AuthenticationFailed('Token de agente inválido o revocado.')

        # Actualizar last_used sin disparar signals
        AgentToken.objects.filter(pk=agent_token.pk).update(last_used=timezone.now())

        # Devolvemos un pseudo-user con company para que las views funcionen igual
        company = agent_token.company
        user = _AgentUser(company)
        return (user, agent_token)

    def authenticate_header(self, request):
        return self.keyword


class _AgentUser:
    """
    Objeto mínimo que actúa como request.user para los endpoints de sync.
    No es un User de Django — solo expone lo que las views de contabilidad necesitan.
    """
    def __init__(self, company):
        self.company = company
        self.effective_company = company
        self.is_authenticated = True
        self.is_active = True

    def __str__(self):
        return f'AgentUser({self.company.name})'
