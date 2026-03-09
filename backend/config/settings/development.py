"""SaiSuite — Settings para desarrollo local."""
from .base import *  # noqa

DEBUG = True
SECRET_KEY = env('SECRET_KEY', default='dev-secret-key-cambiar-en-produccion')
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:4200'])
CORS_ALLOW_CREDENTIALS = True
