# INFORME FASE 1: Infraestructura Base — Sistema de Comunicaciones

**Fecha:** 2026-03-30
**Duración total:** ~20 minutos
**Estado:** COMPLETADO

---

## Resumen Ejecutivo

Se implementó la infraestructura base de comunicaciones en tiempo real para SaiSuite:
Django Channels + Upstash Redis + WebSocket con autenticación JWT.
Tanto el backend (ASGI/Daphne) como el frontend (Angular WebSocket service con signals)
están operativos y validados en navegador.

---

## Archivos Creados

| Archivo | Descripción |
|---|---|
| `backend/config/asgi.py` | ProtocolTypeRouter HTTP + WebSocket con JWTAuthMiddleware |
| `backend/apps/notifications/routing.py` | WebSocket URL routing: `ws/notifications/` |
| `backend/apps/notifications/middleware.py` | JWT auth middleware para WebSocket (query param `?token=`) |
| `backend/apps/notifications/consumers.py` | NotificationConsumer: connect/disconnect/notification_message/count_update/mark_read |
| `backend/apps/notifications/tests/test_websocket.py` | 5 tests unitarios con WebsocketCommunicator |
| `backend/config/settings/testing.py` | CHANNEL_LAYERS override con InMemoryChannelLayer |
| `frontend/src/app/core/services/notification-socket.service.ts` | WebSocket service con signals, exponential backoff, auth failure guard |

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `backend/requirements.txt` | +channels==4.1.0, +channels-redis==4.2.0, +daphne==4.1.0, +bleach==6.1.0, +pytest-asyncio==0.23.8 |
| `backend/config/settings/base.py` | +`daphne` en DJANGO_APPS (primero), +`channels` en THIRD_PARTY_APPS, +ASGI_APPLICATION, +CHANNEL_LAYERS |
| `backend/conftest.py` | Fix AppRegistryNotReady: lazy imports de modelos dentro de fixtures |
| `backend/.env` | Fix UPSTASH_REDIS_URL: `redis-cli --tls -u redis://...` -> `rediss://...` |
| `backend/.env.example` | Mismo fix de formato URL |
| `frontend/src/environments/environment.ts` | +`wsUrl: 'ws://localhost:8000'` |
| `frontend/src/environments/environment.production.ts` | +`wsUrl: 'wss://api.saicloud.com'` |

---

## Tests Ejecutados

### Backend — WebSocket Tests (pytest)

| Test | Resultado | Tiempo |
|---|---|---|
| `test_authenticated_connection` | PASSED | ~1.2s |
| `test_unauthenticated_connection_no_token` | PASSED | ~0.1s |
| `test_unauthenticated_connection_invalid_token` | PASSED | ~0.1s |
| `test_receive_notification_via_channel_layer` | PASSED | ~1.5s |
| `test_receive_count_update_via_channel_layer` | PASSED | ~1.5s |

**Total: 5 passed en 6.79s**

### Frontend — Angular Build

| Check | Resultado |
|---|---|
| `ng build --configuration development` | SUCCESS (0 errores, solo warnings pre-existentes) |
| TypeScript strict compliance | OK — sin `any`, signals correctos |

---

## Validacion en Navegador

### Test 1: Login + Dashboard
- Navegacion a `http://localhost:4200` -> redirect a `/auth/login`
- Login con `admin@andina.com` -> redirect exitoso a `/dashboard`
- 0 errores de consola post-login
- Screenshot: `reports/fase_1/01_login_page.png`, `reports/fase_1/02_dashboard_logged_in.png`

### Test 2: WebSocket Autenticado (JWT valido)
```json
{
  "connected": true,
  "messages": [{"type": "unread_count", "count": 1}],
  "error": null,
  "closeCode": null
}
```
- Conexion aceptada
- Mensaje inicial `unread_count` recibido correctamente
- Backend logs: `ws_connected` con user_id y group name

### Test 3: WebSocket Sin Token (rechazo)
```json
{
  "connected": false,
  "closeCode": 1006
}
```
- Conexion rechazada (403 server-side)
- Backend logs: `ws_connect_rejected_unauthenticated` + `WebSocket REJECT`
- Screenshot: `reports/fase_1/03_websocket_validated.png`

### Logs del Servidor (Daphne ASGI)
```
INFO  Starting ASGI/Daphne version 4.1.0 development server at http://0.0.0.0:8000/
INFO  WebSocket HANDSHAKING /ws/notifications/ [192.168.65.1:19786]
INFO  WebSocket CONNECT /ws/notifications/ [192.168.65.1:19786]
INFO  ws_connected
INFO  WebSocket DISCONNECT /ws/notifications/ [192.168.65.1:19786]
INFO  ws_disconnected
INFO  WebSocket HANDSHAKING /ws/notifications/ [192.168.65.1:40517]
WARN  ws_connect_rejected_unauthenticated
INFO  WebSocket REJECT /ws/notifications/ [192.168.65.1:40517]
```

---

## Issues Encontrados y Resueltos

### Issue 1: UPSTASH_REDIS_URL con formato invalido
- **Sintoma:** WebSocket retorna 500 — `ValueError: Redis URL must specify one of the following schemes (redis://, rediss://, unix://)`
- **Causa:** El `.env` contenia `redis-cli --tls -u redis://...` (comando CLI completo en vez de solo la URL)
- **Fix:** Cambiado a `rediss://default:...@...upstash.io:6379` (protocolo `rediss://` para TLS)
- **Archivos:** `.env`, `.env.example`

### Issue 2: conftest.py — AppRegistryNotReady
- **Sintoma:** Todos los tests fallaban al importar modelos en `conftest.py` a nivel de modulo
- **Causa:** Imports de `Company` y `User` a nivel de modulo se ejecutaban antes de `django.setup()`
- **Fix:** Mover imports dentro de las fixture functions (lazy imports)
- **Archivo:** `backend/conftest.py`

### Issue 3: Container sin dependencias
- **Sintoma:** Django crasheaba con `ModuleNotFoundError: No module named 'daphne'`
- **Causa:** settings.py modificado (volume mount) antes de instalar paquetes en el container
- **Fix:** `pip install` dentro del container + restart
- **Nota:** Para persistir, hacer `docker compose build` para reconstruir la imagen

---

## Criterios de Exito

| Criterio | Estado |
|---|---|
| WebSocket conecta con JWT valido | PASS |
| WebSocket rechaza sin JWT (code 4001/403) | PASS |
| Tests unitarios: 100% pasando (5/5) | PASS |
| Test de integracion en navegador | PASS |
| Angular compila sin errores | PASS |
| Validacion en navegador exitosa | PASS |

---

## Arquitectura Implementada

```
Browser (Angular)
    |
    | WebSocket: ws://localhost:8000/ws/notifications/?token=<JWT>
    v
Daphne (ASGI Server)
    |
    | ProtocolTypeRouter
    |--- HTTP --> Django ASGI App (normal REST API)
    |--- WebSocket --> JWTAuthMiddleware
                         |
                         | Valida AccessToken (simplejwt)
                         v
                    URLRouter
                         |
                    NotificationConsumer
                         |
                         |--- connect() --> group_add + send unread_count
                         |--- disconnect() --> group_discard
                         |--- notification_message() --> forward to client
                         |--- notification_count_update() --> query + send count
                         |--- receive_json(mark_read) --> mark + send count
                         |
                    Redis (Upstash)
                         |
                    Channel Layer (pub/sub)
```

## Protocolo WebSocket

**Server -> Client:**
- `{"type": "unread_count", "count": int}` — badge count
- `{"type": "notification", "data": {...}}` — new notification

**Client -> Server:**
- `{"type": "mark_read", "notification_id": "<uuid>"}` — mark as read

---

## Proximos Pasos (Fase 2)

1. Wiring: llamar `NotificationSocketService.connect()` despues del login en `AuthService`
2. Integrar `NotificacionService.crear()` con `channel_layer.group_send()` para push real-time
3. UI: toast con ngx-sonner al recibir `latestNotification` signal
4. Reconstruir imagen Docker: `docker compose build backend`

---

## Screenshots

- `reports/fase_1/01_login_page.png` — Pagina de login
- `reports/fase_1/02_dashboard_logged_in.png` — Dashboard post-login con badge de notificaciones
- `reports/fase_1/03_websocket_validated.png` — Dashboard tras validacion WebSocket exitosa
