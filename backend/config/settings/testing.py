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

# Desactivar migraciones en tests — Django crea el schema desde el estado actual
# del modelo, evitando el bug de SQLite donde RenameModel no actualiza FK
# constraints en tablas relacionadas (ej: proyectos_taskdependency → proyectos_tarea).
# En PostgreSQL (producción) las migraciones se ejecutan normalmente.
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Excluir apps incompatibles con SQLite de tests:
# - apps.ai: pgvector HnswIndex incompatible con SQLite
# - apps.dashboard: importa 'requests' que puede no estar en venv de test
# - django.contrib.postgres: requiere psycopg2, incompatible con SQLite
INSTALLED_APPS = [
    app for app in INSTALLED_APPS
    if app not in ('apps.ai', 'apps.dashboard', 'django.contrib.postgres')
]

# Passwords más simples en tests → más rápido
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Channel Layers — in-memory backend for tests (no Redis dependency)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
