"""SaiSuite — Settings para ejecución de tests (SQLite en memoria)."""
from .base import *  # noqa

DEBUG = True
SECRET_KEY = 'test-secret-key-only-for-testing'
ALLOWED_HOSTS = ['*']

# SQLite en memoria — sin dependencia de Docker/PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desactivar migraciones pesadas en tests (usa schema directo)
# Nota: dejar en False para que cree las tablas correctamente
# MIGRATION_MODULES = {app: None for app in INSTALLED_APPS}

# Passwords más simples en tests → más rápido
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
