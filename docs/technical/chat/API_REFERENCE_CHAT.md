# API Reference — Sistema de Chat

**Versión:** 1.0  
**Fecha:** 30 Marzo 2026  
**Base URL:** `http://localhost:8000/api/v1/chat/` (dev) | `https://api.saicloud.com/api/v1/chat/` (prod)

---

## 📋 Tabla de Contenidos

1. [Autenticación](#autenticación)
2. [Endpoints REST](#endpoints-rest)
3. [WebSocket Events](#websocket-events)
4. [Modelos de Datos](#modelos-de-datos)
5. [Códigos de Error](#códigos-de-error)
6. [Rate Limits](#rate-limits)

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación JWT.

### Obtener Token

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "usuario@example.com",
  "password": "password123"
}
```

**Response 200:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "uuid",
    "email": "usuario@example.com",
    "nombre": "Juan Pérez"
  }
}
```

### Usar Token

```http
GET /api/v1/chat/conversaciones/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 📡 Endpoints REST

### 1. Listar Conversaciones

```http
GET /conversaciones/
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (int, opcional): Número de página (default: 1)
- `page_size` (int, opcional): Resultados por página (default: 20, max: 100)

**Response 200:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "participante_1": {
        "id": "uuid",
        "nombre": "Juan Pérez",
        "email": "juan@example.com"
      },
      "participante_2": {
        "id": "uuid",
        "nombre": "María García",
        "email": "maria@example.com"
      },
      "ultimo_mensaje": {
        "id": "uuid",
        "contenido": "Hola, ¿cómo estás?",
        "created_at": "2026-03-30T12:00:00Z"
      },
      "ultimo_mensaje_at": "2026-03-30T12:00:00Z",
      "unread_count": 3
    }
  ]
}
```

---

### 2. Crear/Obtener Conversación

```http
POST /conversaciones/
Authorization: Bearer {token}
Content-Type: application/json

{
  "destinatario_id": "uuid-del-usuario-b"
}
```

**Response 200 (si existe):**
```json
{
  "id": "uuid",
  "participante_1": {...},
  "participante_2": {...},
  "ultimo_mensaje": null,
  "ultimo_mensaje_at": null,
  "unread_count": 0
}
```

**Response 201 (si se crea):**
```json
{
  "id": "uuid-nuevo",
  "participante_1": {...},
  "participante_2": {...},
  "ultimo_mensaje": null,
  "ultimo_mensaje_at": null,
  "unread_count": 0
}
```

**Response 400:**
```json
{
  "error": "El destinatario no existe o no pertenece al mismo tenant"
}
```

---

### 3. Listar Mensajes

```http
GET /conversaciones/{conversacion_id}/mensajes/
Authorization: Bearer {token}
```

**Query Parameters:**
- `page` (int, opcional): Número de página (default: 1)
- `page_size` (int, opcional): Mensajes por página (default: 50, max: 100)

**Response 200:**
```json
{
  "count": 120,
  "next": "http://.../mensajes/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "conversacion_id": "uuid",
      "remitente": {
        "id": "uuid",
        "nombre": "Juan Pérez"
      },
      "contenido": "Hola, revisa [PRY-001] por favor",
      "contenido_html": "Hola, revisa <a href=\"/proyectos/uuid\">PRY-001</a> por favor",
      "imagen_url": null,
      "thumbnail_url": null,
      "archivo_url": null,
      "archivo_nombre": null,
      "archivo_tamanio": null,
      "responde_a": null,
      "leido_por_destinatario": true,
      "leido_at": "2026-03-30T12:05:00Z",
      "editado": false,
      "editado_at": null,
      "created_at": "2026-03-30T12:00:00Z"
    }
  ]
}
```

---

### 4. Enviar Mensaje

```http
POST /conversaciones/{conversacion_id}/mensajes/
Authorization: Bearer {token}
Content-Type: application/json

{
  "contenido": "Hola, revisa [PRY-001] por favor",
  "responde_a_id": "uuid"  // opcional
}
```

**Response 201:**
```json
{
  "id": "uuid-nuevo",
  "conversacion_id": "uuid",
  "remitente": {...},
  "contenido": "Hola, revisa [PRY-001] por favor",
  "contenido_html": "Hola, revisa <a href=\"/proyectos/uuid\">PRY-001</a> por favor",
  "imagen_url": null,
  "responde_a": {
    "id": "uuid",
    "contenido": "Mensaje original",
    "remitente_nombre": "María García"
  },
  "leido_por_destinatario": false,
  "created_at": "2026-03-30T12:10:00Z"
}
```

**Response 400:**
```json
{
  "error": "El contenido no puede estar vacío"
}
```

**Response 404:**
```json
{
  "error": "El mensaje al que intentas responder no existe"
}
```

---

### 5. Marcar Mensaje como Leído

```http
POST /mensajes/{mensaje_id}/marcar-leido/
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "id": "uuid",
  "leido_por_destinatario": true,
  "leido_at": "2026-03-30T12:15:00Z"
}
```

**Response 403:**
```json
{
  "error": "No tienes permiso para marcar este mensaje como leído"
}
```

---

### 6. Editar Mensaje

```http
PATCH /mensajes/{mensaje_id}/editar/
Authorization: Bearer {token}
Content-Type: application/json

{
  "contenido": "Hola, revisa [PRY-001] URGENTE por favor"
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "contenido": "Hola, revisa [PRY-001] URGENTE por favor",
  "contenido_html": "Hola, revisa <a href=\"/proyectos/uuid\">PRY-001</a> URGENTE por favor",
  "editado": true,
  "editado_at": "2026-03-30T12:20:00Z"
}
```

**Response 403:**
```json
{
  "error": "Solo puedes editar tus propios mensajes dentro de 15 minutos"
}
```

---

### 7. Upload Archivo

```http
POST /upload-archivo/
Authorization: Bearer {token}
Content-Type: multipart/form-data

archivo: [File]
```

**Validaciones:**
- Tamaño máximo: 10 MB
- Formatos permitidos: PDF, DOCX, XLSX

**Response 200:**
```json
{
  "archivo_url": "https://r2.cloudflarestorage.com/.../files/documento.pdf",
  "archivo_nombre": "documento.pdf",
  "archivo_tamanio": 2457600
}
```

**Response 400:**
```json
{
  "error": "El archivo debe ser PDF, DOCX o XLSX"
}
```

**Response 413:**
```json
{
  "error": "El archivo excede el tamaño máximo de 10 MB"
}
```

---

### 8. Upload Imagen

```http
POST /upload-imagen/
Authorization: Bearer {token}
Content-Type: multipart/form-data

imagen: [File]
```

**Validaciones:**
- Tamaño máximo: 5 MB
- Formatos permitidos: JPG, PNG, WEBP

**Response 200:**
```json
{
  "imagen_url": "https://r2.../images/original/abc123.jpg",
  "thumbnail_url": "https://r2.../images/thumbnails/abc123.webp",
  "width": 1920,
  "height": 1080
}
```

**Proceso backend:**
1. Recibe imagen
2. Genera thumbnail 320x320 con Pillow (mantiene aspect ratio)
3. Convierte thumbnail a WEBP
4. Upload paralelo a R2: original + thumbnail
5. Retorna ambas URLs

---

### 9. Autocomplete Entidades

```http
GET /autocomplete/entidades/?query=PRY&tipo=proyecto
Authorization: Bearer {token}
```

**Query Parameters:**
- `query` (string, requerido): Texto a buscar (min 2 caracteres)
- `tipo` (string, requerido): `proyecto` | `tarea` | `fase`

**Response 200:**
```json
{
  "resultados": [
    {
      "id": "uuid",
      "codigo": "PRY-001",
      "nombre": "Proyecto Alpha",
      "tipo": "proyecto"
    },
    {
      "id": "uuid",
      "codigo": "PRY-002",
      "nombre": "Proyecto Beta",
      "tipo": "proyecto"
    }
  ]
}
```

**Filtrado:**
- Solo entidades del mismo tenant
- Solo entidades donde usuario tiene permiso de lectura
- Ordenado por relevancia (nombre ILIKE)

---

### 10. Autocomplete Usuarios

```http
GET /autocomplete/usuarios/?query=Juan
Authorization: Bearer {token}
```

**Query Parameters:**
- `query` (string, requerido): Texto a buscar (min 2 caracteres)

**Response 200:**
```json
{
  "resultados": [
    {
      "id": "uuid",
      "nombre": "Juan Pérez",
      "email": "juan@example.com"
    },
    {
      "id": "uuid",
      "nombre": "Juana García",
      "email": "juana@example.com"
    }
  ]
}
```

**Filtrado:**
- Solo usuarios del mismo tenant
- Búsqueda en nombre y email (ILIKE)
- Excluye al usuario actual
- Max 10 resultados

---

### 11. Búsqueda en Conversación

```http
GET /conversaciones/{conversacion_id}/buscar/?q=proyecto
Authorization: Bearer {token}
```

**Query Parameters:**
- `q` (string, requerido): Texto a buscar (min 3 caracteres)

**Response 200:**
```json
{
  "resultados": [
    {
      "id": "uuid",
      "contenido": "Hola, revisa el proyecto PRY-001 por favor",
      "contenido_highlight": "Hola, revisa el <mark>proyecto</mark> PRY-001 por favor",
      "remitente": {...},
      "created_at": "2026-03-30T12:00:00Z"
    }
  ],
  "total": 3
}
```

**Búsqueda:**
- Full-text search en `contenido` (case-insensitive)
- Highlight del texto encontrado con `<mark>` tags
- Ordenado por relevancia (más recientes primero)

---

### 12. Presencia Usuarios

```http
GET /presencia/
Authorization: Bearer {token}
```

**Query Parameters:**
- `user_ids` (string, opcional): Lista de UUIDs separados por coma

**Response 200:**
```json
{
  "presencias": {
    "uuid-1": {
      "status": "online",
      "last_seen": null
    },
    "uuid-2": {
      "status": "offline",
      "last_seen": "2026-03-30T11:50:00Z"
    },
    "uuid-3": {
      "status": "away",
      "last_seen": "2026-03-30T12:15:00Z"
    }
  }
}
```

**Estados:**
- `online`: Heartbeat recibido en últimos 35s
- `offline`: Sin heartbeat, desconectado
- `away`: Heartbeat expiró, inactivo

---

## 🔌 WebSocket Events

### Conexión

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/?token=JWT_TOKEN');

ws.onopen = () => {
  console.log('WebSocket conectado');
  // Backend automáticamente:
  // 1. Valida JWT
  // 2. Join a grupos de conversaciones del usuario
  // 3. Set user status = online
};

ws.onclose = () => {
  console.log('WebSocket desconectado');
  // Backend automáticamente:
  // 1. Set user status = offline
  // 2. Leave grupos de conversaciones
};
```

---

### Eventos Cliente → Servidor

#### 1. Enviar Mensaje

```javascript
ws.send(JSON.stringify({
  type: 'chat.send_message',
  conversacion_id: 'uuid',
  contenido: 'Hola, ¿cómo estás?',
  responde_a_id: 'uuid'  // opcional
}));
```

**Respuesta backend:**
1. Guarda mensaje en PostgreSQL
2. Procesa enlaces `[PRY-001]` y menciones `@usuario`
3. Broadcast a ambos participantes vía `chat.new_message`
4. Genera notificación si hay mención

---

#### 2. Typing Indicator

```javascript
ws.send(JSON.stringify({
  type: 'chat.typing',
  conversacion_id: 'uuid',
  is_typing: true
}));
```

**Comportamiento:**
- Broadcast a otro participante
- TTL 5 segundos en Redis
- Si no se envía mensaje en 5s, desaparece automáticamente

---

#### 3. Marcar Mensaje Leído

```javascript
ws.send(JSON.stringify({
  type: 'chat.mark_read',
  mensaje_id: 'uuid'
}));
```

**Respuesta backend:**
1. Update mensaje: `leido_por_destinatario=true`
2. Broadcast a remitente vía `chat.message_read`

---

#### 4. Heartbeat

```javascript
// Cada 25 segundos
setInterval(() => {
  ws.send(JSON.stringify({
    type: 'chat.heartbeat'
  }));
}, 25000);
```

**Comportamiento:**
- Refresh TTL Redis (35s)
- Mantiene status = `online`
- Si no se envía en 35s → status = `away`

---

### Eventos Servidor → Cliente

#### 1. Mensaje Nuevo

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'chat.new_message') {
    console.log('Nuevo mensaje:', data.mensaje);
    // {
    //   id: 'uuid',
    //   conversacion_id: 'uuid',
    //   remitente: {...},
    //   contenido: 'Hola',
    //   contenido_html: 'Hola',
    //   created_at: '2026-03-30T12:00:00Z',
    //   leido_por_destinatario: false
    // }
  }
};
```

---

#### 2. Mensaje Leído

```javascript
if (data.type === 'chat.message_read') {
  console.log('Mensaje leído:', data);
  // {
  //   type: 'chat.message_read',
  //   mensaje_id: 'uuid',
  //   leido_at: '2026-03-30T12:05:00Z'
  // }
}
```

---

#### 3. Mensaje Editado

```javascript
if (data.type === 'chat.message_edited') {
  console.log('Mensaje editado:', data);
  // {
  //   type: 'chat.message_edited',
  //   mensaje_id: 'uuid',
  //   contenido: 'nuevo texto',
  //   contenido_html: 'nuevo HTML',
  //   editado_at: '2026-03-30T12:10:00Z'
  // }
}
```

---

#### 4. Typing Indicator

```javascript
if (data.type === 'chat.typing') {
  console.log('Usuario escribiendo:', data);
  // {
  //   type: 'chat.typing',
  //   conversacion_id: 'uuid',
  //   user_id: 'uuid',
  //   is_typing: true
  // }
}
```

---

#### 5. Presencia Cambiada

```javascript
if (data.type === 'chat.presence_changed') {
  console.log('Presencia actualizada:', data);
  // {
  //   type: 'chat.presence_changed',
  //   user_id: 'uuid',
  //   status: 'online'  // online | offline | away
  // }
}
```

---

## 📦 Modelos de Datos

### Conversacion

```typescript
interface Conversacion {
  id: string;  // UUID
  participante_1: Usuario;
  participante_2: Usuario;
  ultimo_mensaje: Mensaje | null;
  ultimo_mensaje_at: string | null;  // ISO 8601
  unread_count: number;  // Calculado
}
```

### Mensaje

```typescript
interface Mensaje {
  id: string;  // UUID
  conversacion_id: string;
  remitente: Usuario;
  contenido: string;  // Texto original
  contenido_html: string;  // HTML procesado con links
  imagen_url: string | null;
  thumbnail_url: string | null;
  archivo_url: string | null;
  archivo_nombre: string | null;
  archivo_tamanio: number | null;  // Bytes
  responde_a: MensajePreview | null;
  leido_por_destinatario: boolean;
  leido_at: string | null;  // ISO 8601
  editado: boolean;
  editado_at: string | null;  // ISO 8601
  created_at: string;  // ISO 8601
}
```

### MensajePreview

```typescript
interface MensajePreview {
  id: string;
  contenido: string;  // Max 50 caracteres
  remitente_nombre: string;
}
```

### Usuario

```typescript
interface Usuario {
  id: string;  // UUID
  nombre: string;
  email: string;
  avatar_url: string | null;
}
```

---

## ⚠️ Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Bad Request — Datos inválidos |
| 401 | Unauthorized — JWT inválido o expirado |
| 403 | Forbidden — Sin permisos para esta acción |
| 404 | Not Found — Recurso no existe |
| 413 | Payload Too Large — Archivo demasiado grande |
| 429 | Too Many Requests — Rate limit excedido |
| 500 | Internal Server Error — Error del servidor |
| 503 | Service Unavailable — Servicio temporalmente no disponible |

### Ejemplos de Errores

**401 Unauthorized:**
```json
{
  "detail": "Token inválido o expirado"
}
```

**403 Forbidden:**
```json
{
  "error": "Solo puedes editar tus propios mensajes dentro de 15 minutos"
}
```

**413 Payload Too Large:**
```json
{
  "error": "El archivo excede el tamaño máximo de 10 MB"
}
```

**429 Too Many Requests:**
```json
{
  "error": "Has excedido el límite de solicitudes. Intenta nuevamente en 60 segundos."
}
```

---

## 🚦 Rate Limits

### Endpoints REST

| Endpoint | Límite | Ventana |
|----------|--------|---------|
| POST /conversaciones/ | 20 req | 1 min |
| POST /mensajes/ | 100 req | 1 min |
| POST /upload-archivo/ | 10 req | 1 min |
| POST /upload-imagen/ | 10 req | 1 min |
| GET * | 1000 req | 1 min |

### WebSocket

| Evento | Límite | Ventana |
|--------|--------|---------|
| chat.send_message | 60 msg | 1 min |
| chat.typing | 30 events | 1 min |
| chat.mark_read | Sin límite | - |
| chat.heartbeat | 3 events | 1 min |

**Headers de Rate Limit:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1711801200
```

---

## 📚 Referencias

- **Arquitectura:** Ver `ARQUITECTURA_CHAT.md`
- **Deployment:** Ver `DEPLOYMENT_CHAT.md`
- **Decisiones:** Ver `DECISIONS.md`
- **Notion:** https://www.notion.so/333ee9c3690a8122873cd2a03c123812
