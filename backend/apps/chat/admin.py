from django.contrib import admin
from .models import Conversacion, Mensaje


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'participante_1', 'participante_2', 'ultimo_mensaje_at')
    list_filter = ('company',)
    search_fields = ('participante_1__email', 'participante_2__email')


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversacion', 'remitente', 'created_at', 'leido_por_destinatario')
    list_filter = ('leido_por_destinatario', 'created_at')
    search_fields = ('contenido',)
