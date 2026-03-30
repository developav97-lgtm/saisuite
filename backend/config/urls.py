"""SaiSuite — URLs principales."""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        db_status = 'ok'
    except Exception:
        db_status = 'error'
    return JsonResponse({'status': 'ok', 'db': db_status})


urlpatterns = [
    path('health/', health_check),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/admin/tenants/', include('apps.companies.admin_urls')),
    path('api/v1/sync/', include('apps.sync_agent.urls')),
    path('api/v1/integrations/', include('apps.integrations.urls')),
    path('api/v1/core/', include('apps.core.urls')),
    path('api/v1/projects/', include('apps.proyectos.urls')),
    path('api/v1/terceros/', include('apps.terceros.urls')),
    path('api/v1/notificaciones/', include('apps.notifications.urls')),
    path('api/v1/chat/', include('apps.chat.urls')),
]