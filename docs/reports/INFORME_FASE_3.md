# INFORME FASE 3: Chat Backend — Modelos + API REST + WebSocket Events

**Fecha:** 2026-03-30
**Estado:** COMPLETADO

---

## Resumen Ejecutivo

Se implemento el backend completo del chat interno 1-a-1:
- **Modelos:** `Conversacion` (1-to-1 entre dos usuarios) + `Mensaje` (texto, HTML procesado, imagenes, respuestas)
- **Services:** `ChatService` con 8 metodos — conversaciones, mensajes, procesamiento de enlaces/menciones, notificaciones
- **API REST:** 6 endpoints bajo `/api/v1/chat/` con autenticacion JWT
- **WebSocket:** `ChatConsumer` con 7 eventos (mensajes en tiempo real, typing indicators, read receipts)
- **Tests:** 69/69 pasando (62 chat + 7 notifications sin regresion)

---

## Archivos Creados

| Archivo | Descripcion |
|---|---|
| `apps/chat/__init__.py` | App init |
| `apps/chat/apps.py` | ChatConfig |
| `apps/chat/admin.py` | Admin registrations para Conversacion y Mensaje |
| `apps/chat/models.py` | Modelos Conversacion + Mensaje (heredan BaseModel) |
| `apps/chat/services.py` | ChatService — toda la logica de negocio |
| `apps/chat/serializers.py` | 6 serializers (lectura + escritura + autocomplete) |
| `apps/chat/views.py` | 6 views (solo orquestan) |
| `apps/chat/urls.py` | 6 URL patterns bajo `/api/v1/chat/` |
| `apps/chat/consumers.py` | ChatConsumer WebSocket (AsyncJsonWebsocketConsumer) |
| `apps/chat/routing.py` | WebSocket URL: `ws/chat/` |
| `apps/chat/migrations/0001_initial.py` | Migracion autogenerada |
| `apps/chat/tests/__init__.py` | Tests init |
| `apps/chat/tests/test_models.py` | 5 tests de modelos |
| `apps/chat/tests/test_services.py` | 25 tests de servicios |
| `apps/chat/tests/test_views.py` | 21 tests de API REST |
| `apps/chat/tests/test_websocket_chat.py` | 11 tests de WebSocket |

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `config/settings/base.py` | +`'apps.chat'` en INSTALLED_APPS |
| `config/urls.py` | +`path('api/v1/chat/', include('apps.chat.urls'))` |
| `config/asgi.py` | +import chat_ws, URLRouter combina notification_ws + chat_ws |

---

## Detalle de Cambios

### 1. Modelos (`models.py`)

#### Conversacion
```python
class Conversacion(BaseModel):
    participante_1 = FK(User, related_name='conversaciones_iniciadas')
    participante_2 = FK(User, related_name='conversaciones_recibidas')
    ultimo_mensaje = FK('Mensaje', null=True, on_delete=SET_NULL)
    ultimo_mensaje_at = DateTimeField(null=True)

    Meta:
        unique_together = [('company', 'participante_1', 'participante_2')]
        indexes = [Index(fields=['company', '-ultimo_mensaje_at'])]
        ordering = ['-ultimo_mensaje_at']
```

#### Mensaje
```python
class Mensaje(BaseModel):
    conversacion = FK(Conversacion, related_name='mensajes')
    remitente = FK(User, related_name='mensajes_enviados')
    contenido = TextField(blank=True)           # Original del usuario
    contenido_html = TextField(blank=True)      # Procesado con links/menciones
    imagen_url = CharField(max_length=500)      # Cloudflare R2 URL
    responde_a = FK(self, null=True)            # Reply threading
    leido_por_destinatario = BooleanField(default=False)
    leido_at = DateTimeField(null=True)

    Meta:
        ordering = ['created_at']  # Cronologico (override BaseModel)
        indexes = [Index(fields=['conversacion', 'created_at'])]
```

**Decisiones clave:**
- Ambos heredan de `BaseModel` (UUID pk, company FK, timestamps)
- UUID normalization en `obtener_o_crear_conversacion()` — UUID menor siempre es participante_1
- `ordering = ['created_at']` en Mensaje override el `-created_at` de BaseModel
- `ultimo_mensaje` FK permite mostrar preview en listado sin query adicional

### 2. ChatService (`services.py`) — 8 metodos

| Metodo | Descripcion |
|---|---|
| `obtener_o_crear_conversacion()` | Get/create con UUID normalization |
| `listar_conversaciones()` | Conversaciones del usuario, ordered by ultimo_mensaje_at |
| `enviar_mensaje()` | Crea mensaje + procesa HTML + WS push + notificacion |
| `listar_mensajes()` | Mensajes paginados con validacion de participante |
| `marcar_leido()` | Update + WS read receipt |
| `procesar_contenido()` | Orquesta enlaces + menciones + bleach sanitization |
| `procesar_enlaces()` | `[PRY-001]` → `<a href="/proyectos/{id}">` |
| `procesar_menciones()` | `@Usuario` → `<span class="chat-mention">` |

**Procesamiento de contenido:**
```
Input:  "Revisa [PRY-001] y habla con @Juan"
         ↓ procesar_enlaces() → regex \[([A-Z]{3})-(\d{3,})\]
         ↓ procesar_menciones() → regex @([\w.\s]+?)
         ↓ bleach.clean() → whitelist: a, span
Output: "Revisa <a href="/proyectos/{id}" class="chat-entity-link">[PRY-001]</a>
         y habla con <span class="chat-mention" data-user-id="{id}">@Juan Perez</span>"
```

**Entidades soportadas:**
- `PRY` → Project (campo `codigo`)
- `TAR` → Task (campo `codigo`)
- Phase excluida (no tiene campo `codigo`)

### 3. API REST — 6 endpoints

| Metodo | URL | Descripcion |
|---|---|---|
| GET | `/api/v1/chat/conversaciones/` | Listar conversaciones del usuario |
| POST | `/api/v1/chat/conversaciones/` | Crear/obtener conversacion `{destinatario_id}` |
| GET | `/api/v1/chat/conversaciones/{id}/mensajes/` | Listar mensajes (paginado, 50/page) |
| POST | `/api/v1/chat/conversaciones/{id}/mensajes/enviar/` | Enviar mensaje `{contenido, imagen_url?, responde_a_id?}` |
| POST | `/api/v1/chat/mensajes/{id}/marcar-leido/` | Marcar mensaje como leido |
| GET | `/api/v1/chat/autocomplete/entidades/?query=PRY&tipo=proyecto` | Autocomplete entidades |
| GET | `/api/v1/chat/autocomplete/usuarios/?query=Juan` | Autocomplete usuarios |

**Paginacion:** `PageNumberPagination` con `page_size=50`, max 100.

**Validaciones:**
- Solo usuarios autenticados (JWT via interceptor)
- Solo participantes pueden ver/enviar mensajes (403)
- No puedes crear conversacion contigo mismo (400)
- Destinatario debe existir en el mismo tenant (404)
- Mensaje requiere contenido o imagen (400)
- Solo el destinatario puede marcar como leido (403)

### 4. WebSocket Consumer (`consumers.py`)

**Ruta:** `ws/chat/` (autenticacion JWT via query string `?token=`)

#### Eventos Client → Server

| Type | Payload | Accion |
|---|---|---|
| `chat.send_message` | `{conversacion_id, contenido, imagen_url?, responde_a_id?}` | Crea mensaje via ChatService |
| `chat.typing` | `{conversacion_id}` | Broadcast typing indicator |
| `chat.mark_read` | `{mensaje_id}` | Marca leido via ChatService |
| `chat.join_conversation` | `{conversacion_id}` | Join dinamico a grupo |

#### Eventos Server → Client

| Type | Payload | Trigger |
|---|---|---|
| `new_message` | `{...mensaje serializado}` | ChatService.enviar_mensaje() |
| `message_read` | `{mensaje_id, leido_at, leido_por}` | ChatService.marcar_leido() |
| `typing` | `{conversacion_id, user_id, user_name}` | _handle_typing() |
| `new_conversation` | `{conversacion_id, data}` | Creacion de conversacion |
| `error` | `{message}` | Validacion fallida |

**Arquitectura de grupos:**
```
connect() →
  ├── chat_{conv_1_id}  ← grupo por cada conversacion existente
  ├── chat_{conv_2_id}
  ├── ...
  └── chat_user_{user_id}  ← grupo personal para nuevas conversaciones
```

**Typing indicator:** No se reenvia al usuario que escribe (filtro por user_id).

### 5. ASGI Config (`asgi.py`)

```python
from apps.notifications.routing import websocket_urlpatterns as notification_ws
from apps.chat.routing import websocket_urlpatterns as chat_ws

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(
        URLRouter(notification_ws + chat_ws)  # Combinados
    ),
})
```

---

## Tests Ejecutados

### Modelos (5/5)

| Test | Resultado |
|---|---|
| `test_create_conversacion` | PASSED |
| `test_unique_together` | PASSED |
| `test_create_mensaje` | PASSED |
| `test_mensaje_ordering_chronological` | PASSED |
| `test_reply_to_message` | PASSED |

### Services (25/25)

| Test | Resultado |
|---|---|
| `test_crea_nueva_conversacion` | PASSED |
| `test_obtiene_conversacion_existente` | PASSED |
| `test_obtiene_existente_orden_invertido` | PASSED |
| `test_normaliza_uuid_orden` | PASSED |
| `test_envia_mensaje_exitosamente` | PASSED |
| `test_actualiza_ultimo_mensaje` | PASSED |
| `test_no_participante_lanza_permission_error` | PASSED |
| `test_responder_a_mensaje` | PASSED |
| `test_mensaje_con_imagen` | PASSED |
| `test_push_websocket_en_envio` | PASSED |
| `test_procesar_enlaces_proyecto_existente` | PASSED |
| `test_procesar_enlaces_no_encontrado` | PASSED |
| `test_procesar_enlaces_prefijo_desconocido` | PASSED |
| `test_procesar_menciones_usuario_existente` | PASSED |
| `test_procesar_menciones_usuario_no_encontrado` | PASSED |
| `test_sanitizacion_html` | PASSED |
| `test_sanitizacion_permite_tags_validos` | PASSED |
| `test_marca_leido_correctamente` | PASSED |
| `test_marcar_leido_idempotente` | PASSED |
| `test_remitente_no_puede_marcar_leido` | PASSED |
| `test_tercero_no_puede_marcar_leido` | PASSED |
| `test_listar_mensajes_participante` | PASSED |
| `test_listar_mensajes_no_participante` | PASSED |
| `test_lista_conversaciones_del_usuario` | PASSED |
| `test_no_lista_conversaciones_ajenas` | PASSED |

### Views/API REST (21/21)

| Test | Resultado |
|---|---|
| `test_list_conversaciones_authenticated` | PASSED |
| `test_create_conversacion` | PASSED |
| `test_create_conversacion_self` | PASSED |
| `test_create_conversacion_usuario_inexistente` | PASSED |
| `test_create_conversacion_idempotente` | PASSED |
| `test_list_mensajes` | PASSED |
| `test_enviar_mensaje` | PASSED |
| `test_enviar_mensaje_con_imagen` | PASSED |
| `test_enviar_mensaje_vacio_falla` | PASSED |
| `test_marcar_leido` | PASSED |
| `test_marcar_leido_remitente_falla` | PASSED |
| `test_autocomplete_entidades` | PASSED |
| `test_autocomplete_entidades_query_corta` | PASSED |
| `test_autocomplete_usuarios` | PASSED |
| `test_autocomplete_usuarios_excluye_self` | PASSED |
| `test_autocomplete_usuarios_query_corta` | PASSED |
| `test_conversaciones_requiere_auth` | PASSED |
| `test_enviar_mensaje_requiere_auth` | PASSED |
| `test_marcar_leido_requiere_auth` | PASSED |
| `test_autocomplete_entidades_requiere_auth` | PASSED |
| `test_autocomplete_usuarios_requiere_auth` | PASSED |

### WebSocket (11/11)

| Test | Resultado |
|---|---|
| `test_chat_ws_connect_authenticated` | PASSED |
| `test_chat_ws_unauthenticated_no_token` | PASSED |
| `test_chat_ws_unauthenticated_invalid_token` | PASSED |
| `test_chat_ws_joins_conversation_groups` | PASSED |
| `test_chat_ws_typing_indicator` | PASSED |
| `test_chat_ws_new_message_via_channel_layer` | PASSED |
| `test_chat_ws_read_receipt_via_channel_layer` | PASSED |
| `test_chat_ws_new_conversation_notification` | PASSED |
| `test_chat_ws_send_message_missing_fields` | PASSED |
| `test_chat_ws_disconnect_cleans_up` | PASSED |
| `test_chat_ws_join_conversation` | PASSED |

### Regresion Notifications (7/7)

| Test | Resultado |
|---|---|
| `test_authenticated_connection` | PASSED |
| `test_unauthenticated_connection_no_token` | PASSED |
| `test_unauthenticated_connection_invalid_token` | PASSED |
| `test_receive_notification_via_channel_layer` | PASSED |
| `test_receive_count_update_via_channel_layer` | PASSED |
| `test_crear_pushes_via_websocket` | PASSED |
| `test_crear_without_ws_client_does_not_fail` | PASSED |

**Total: 69 passed, 0 failed**

---

## Flujo Completo Implementado

### Enviar Mensaje (REST + WS)
```
1. Cliente POST /api/v1/chat/conversaciones/{id}/mensajes/enviar/
   body: { contenido: "Revisa [PRY-001] y habla con @Juan" }
   ↓
2. enviar_mensaje_view() → valida input
   ↓
3. ChatService.enviar_mensaje()
   ↓
4. procesar_contenido()
   ├── procesar_enlaces() → [PRY-001] → <a href="...">
   ├── procesar_menciones() → @Juan → <span class="chat-mention">
   └── bleach.clean() → sanitiza HTML
   ↓
5. Mensaje.create() → PostgreSQL
   ↓
6. Conversacion.save() → update ultimo_mensaje + ultimo_mensaje_at
   ↓
7. channel_layer.group_send('chat_{conv_id}', {
       type: 'chat.new_message',
       data: { ...serialized message... }
   })
   ↓
8. ChatConsumer.chat_new_message() → send_json a ambos participantes
   ↓
9. _notificar_destinatario() → NotificacionService.crear(tipo='chat')
   ↓
10. _notificar_menciones() → NotificacionService.crear(tipo='mencion')
```

### Enviar Mensaje (WS directo)
```
1. Cliente WS: { type: "chat.send_message", conversacion_id, contenido }
   ↓
2. ChatConsumer.receive_json() → dispatch
   ↓
3. _handle_send_message() → _create_message() (database_sync_to_async)
   ↓
4. ChatService.enviar_mensaje() → mismo flujo que REST
```

### Typing Indicator
```
1. Cliente WS: { type: "chat.typing", conversacion_id }
   ↓
2. channel_layer.group_send('chat_{conv_id}', { type: 'chat.typing' })
   ↓
3. ChatConsumer.chat_typing() → filtra (no reenvia al que escribe)
   ↓
4. Otro participante recibe: { type: "typing", data: { user_id, user_name } }
```

### Read Receipt
```
1. Cliente POST /api/v1/chat/mensajes/{id}/marcar-leido/
   o WS: { type: "chat.mark_read", mensaje_id }
   ↓
2. ChatService.marcar_leido() → update BD + WS push
   ↓
3. channel_layer.group_send('chat_{conv_id}', {
       type: 'chat.message_read',
       data: { mensaje_id, leido_at, leido_por }
   })
   ↓
4. Remitente recibe: { type: "message_read", data: {...} }
```

---

## Seguridad

| Control | Implementacion |
|---|---|
| Autenticacion | JWT validado por interceptor (REST) y JWTAuthMiddleware (WS) |
| Multi-tenancy | BaseModel + CompanyManager filtra por company automaticamente |
| Autorizacion | Solo participantes pueden ver/enviar mensajes (403) |
| XSS Prevention | bleach.clean() con whitelist: `<a>`, `<span>` |
| Permission validation | procesar_enlaces() valida que la entidad pertenezca al tenant |
| WS Auth | JWT en query string, close(4001) si invalido |
| Self-chat prevention | 400 si destinatario_id == request.user.id |

---

## Criterios de Exito

| Criterio | Estado |
|---|---|
| Modelos Conversacion + Mensaje creados | PASS |
| Migraciones aplicadas sin errores | PASS |
| ChatService con 8 metodos funcionando | PASS |
| API REST: 6 endpoints funcionando | PASS |
| Autocomplete entidades filtra por tenant | PASS |
| Procesamiento de enlaces [PRY-001] funciona | PASS |
| Procesamiento de menciones @Usuario funciona | PASS |
| Sanitizacion HTML con bleach | PASS |
| ChatConsumer implementado con 7 eventos | PASS |
| Tests unitarios: 100% pasando (62/62) | PASS |
| Tests WebSocket: PASS (11/11) | PASS |
| Sin regresion en notifications (7/7) | PASS |

---

## Proximos Pasos (Fase 4 — Frontend Chat)

1. Componente Angular de chat (lista conversaciones + ventana mensajes)
2. Servicio Angular `ChatSocketService` para WebSocket `ws/chat/`
3. Componente de autocomplete para `[PRY-001]` y `@Usuario`
4. Upload de imagenes a Cloudflare R2
5. Indicador de typing en UI
6. Double-check (read receipts) en mensajes
7. Integracion con NotificationBellComponent (badge chat)
