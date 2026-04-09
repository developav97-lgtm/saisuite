"""SaiSuite — Settings para desarrollo local."""
from .base import *  # noqa

DEBUG = True
SECRET_KEY = env('SECRET_KEY', default='dev-secret-key-cambiar-en-produccion')
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'backend', 'saisuite-api']
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:4200'])
CORS_ALLOW_ALL_ORIGINS = True  # dev only — Vite proxy reescribe Origin
CORS_ALLOW_CREDENTIALS = True

# Email: usa SMTP si EMAIL_HOST_USER está configurado, sino consola
EMAIL_BACKEND   = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='SaiSuite <noreply@saisuite.com>')

# URL del frontend — se usa en emails de recuperación de contraseña
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:4200')
