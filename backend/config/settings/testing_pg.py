"""SaiSuite — Settings para tests que requieren PostgreSQL (pgvector, HNSW, etc.)."""
from .base import *  # noqa

DEBUG = True
SECRET_KEY = 'test-secret-key-only-for-testing-pg'
ALLOWED_HOSTS = ['*']

# PostgreSQL — usa la misma DB pero pytest crea una DB de test con prefijo test_
# Requiere que saisuite-db esté corriendo.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'saisuite_test',
        'USER': 'saisuite',
        'PASSWORD': 'saisuite_local',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# Passwords más simples en tests → más rápido
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Channel Layers — in-memory backend for tests (no Redis dependency)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
