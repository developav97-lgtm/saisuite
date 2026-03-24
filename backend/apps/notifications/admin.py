"""
SaiSuite — Notifications: Admin
"""
from django.contrib import admin
from .models import Notificacion, Comentario, PreferenciaNotificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display   = ('titulo', 'tipo', 'usuario', 'leida', 'created_at')
    list_filter    = ('tipo', 'leida', 'company')
    search_fields  = ('titulo', 'mensaje', 'usuario__email')
    date_hierarchy = 'created_at'
    ordering       = ('-created_at',)
    readonly_fields = ('content_type', 'object_id', 'leida_en', 'created_at', 'updated_at')


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display   = ('autor', 'texto_corto', 'content_type', 'editado', 'created_at')
    list_filter    = ('editado', 'company')
    search_fields  = ('texto', 'autor__email')
    date_hierarchy = 'created_at'
    ordering       = ('-created_at',)
    readonly_fields = ('content_type', 'object_id', 'editado_en', 'created_at', 'updated_at')

    @admin.display(description='Texto')
    def texto_corto(self, obj):
        return obj.texto[:60]


@admin.register(PreferenciaNotificacion)
class PreferenciaNotificacionAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'tipo', 'habilitado_app', 'habilitado_email')
    list_filter   = ('tipo', 'habilitado_app', 'company')
    search_fields = ('usuario__email',)
