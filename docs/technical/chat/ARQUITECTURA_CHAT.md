# Arquitectura Sistema de Chat — Saicloud

**Versión:** 1.0  
**Fecha:** 30 Marzo 2026  
**Módulo:** Sistema de Comunicaciones en Tiempo Real  
**Stack:** Django 5 + Angular 18 + PostgreSQL 16 + Upstash Redis + Cloudflare R2

---

## 📋 Tabla de Contenidos

1. [Stack Tecnológico](#stack-tecnológico)
2. [Decisiones Arquitectónicas](#decisiones-arquitectónicas)
3. [Modelos de Datos](#modelos-de-datos)
4. [Flujo WebSocket](#flujo-websocket)
5. [API REST](#api-rest)
6. [Seguridad](#seguridad)
7. [Performance](#performance)
8. [Costos](#costos)

---

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** Django 5.1
- **WebSocket:** Django Channels 4.1.0 + Daphne 4.1.0
- **Base de datos:** PostgreSQL 16
- **Cache/PubSub:** Upstash Redis (serverless)
- **Storage:** Cloudflare R2 (S3-compatible)
- **Sanitización HTML:** bleach 6.1.0
- **Procesamiento imágenes:** Pillow (thumbnails)

### Frontend
- **Framework:** Angular 18 (standalone components)
- **UI Library:** Angular Material
- **WebSocket Client:** Native WebSocket API
- **Notificaciones:** ngx-sonner
- **Emoji Picker:** @ctrl/ngx-emoji-mart
- **Signals:** Angular Signals (reactivity)

### Infraestructura
- **Development:** Docker Compose
- **Production (futuro):** AWS ECS + ALB + RDS
- **Redis:** Upstash (free tier: 10K comandos/día)
- **Storage:** Cloudflare R2 (free tier: 10 GB + 1M requests/mes)

---

## 🎯 Decisiones Arquitectónicas

### DEC-033: Redis Provider — Upstash

**Fecha:** 2026-03-30  
**Decisión:** Usar Upstash Redis (serverless) en fase MVP

**Justificación:**
- **Costo:** $1.70/mes vs $9.79/mes ElastiCache (ahorro 82%)
- **Free tier:** 10,000 comandos/día (300K/mes) suficiente para 100 usuarios activos
- **Zero-ops:** Sin gestión de VPC, subnets, security groups, patching, failover
- **Portabilidad:** API estándar Redis, migración a ElastiCache trivial

**Trigger de migración a ElastiCache:**
- Volumen >5M comandos/mes
- Latencia crítica (<5ms requerido)
- Compliance estricto (datos dentro de VPC AWS)

---

### DEC-034: Storage Provider — Cloudflare R2

**Fecha:** 2026-03-30  
**Decisión:** Usar Cloudflare R2 con API S3-compatible

**Justificación:**
- **Costo:** $0.68/mes vs $9.91/mes S3 (ahorro 93%)
- **Egress gratis:** Chat tiene alto volumen de views (100 GB/mes = $9 en S3, $0 en R2)
- **CDN incluido:** No requiere CloudFront adicional
- **API S3-compatible:** boto3 funciona igual, portabilidad total

**Desglose de costos (1000 usuarios, 50 imágenes/usuario/mes):**
- Storage: 25 GB × $0.015 = $0.38
- Requests: 50K uploads × $4.50/1M = $0.23
- Egress: 100 GB × $0 = $0 (gratis)
- **Total R2:** $0.68/mes vs **S3:** $9.91/mes

**Trigger de migración a S3:**
- SLA >99.99% requerido (crítico para negocio)
- Integración profunda con Lambda/EventBridge
- Compliance estricto (datos en infraestructura AWS)

---

### DEC-035: Autocomplete de Enlaces en Chat

**Fecha:** 2026-03-30  
**Decisión:** Implementar sistema de autocomplete con sintaxis especial

**Sintaxis soportada:**
- `[PRY-001]` → Link a proyecto
- `[TAR-023]` → Link a tarea
- `[FAS-005]` → Link a fase
- `@Usuario` → Mención (genera notificación automática)

**Justificación:**
- Mejora contexto: Links directos a entidades sin salir del chat
- UX fluida: Autocomplete intuitivo con navegación por teclado
- Seguridad: Validación de permisos antes de generar link
- Notificaciones automáticas: Menciones @ generan push + campanita

**Alternativas descartadas:**
1. Markdown estándar `[texto](url)` — menos intuitivo
2. Rich text editor — peso adicional (50-100 KB)
3. Búsqueda manual + botón — UX inferior

---

## 📊 Modelos de Datos

### Diagrama ERD

```
┌─────────────────────────────────────────┐
│              Conversacion               │
├─────────────────────────────────────────┤
│ id (UUID, PK)                           │
│ tenant (FK → Tenant)                    │
│ participante_1 (FK → Usuario)           │
│ participante_2 (FK → Usuario)           │
│ ultimo_mensaje (FK → Mensaje, nullable) │
│ ultimo_mensaje_at (DateTime, nullable)  │
│ created_at (DateTime)                   │
│ updated_at (DateTime)                   │
├─────────────────────────────────────────┤
│ UNIQUE: (tenant, participante_1, participante_2) │
│ INDEX: (tenant, -ultimo_mensaje_at)     │
└─────────────────────────────────────────┘
              │
              │ 1:N
              ▼
┌─────────────────────────────────────────┐
│                Mensaje                  │
├─────────────────────────────────────────┤
│ id (UUID, PK)                           │
│ conversacion (FK → Conversacion)        │
│ remitente (FK → Usuario)                │
│ contenido (TextField)                   │
│ contenido_html (TextField)              │
│ imagen_url (CharField, max 500)         │
│ thumbnail_url (CharField, max 500)      │
│ archivo_url (CharField, max 500)        │
│ archivo_nombre (CharField, max 255)     │
│ archivo_tamanio (Integer, bytes)        │
│ responde_a (FK → self, nullable)        │
│ leido_por_destinatario (Boolean)        │
│ leido_at (DateTime, nullable)           │
│ editado (Boolean)                       │
│ editado_at (DateTime, nullable)         │
│ contenido_original (TextField)          │
│ created_at (DateTime)                   │
│ updated_at (DateTime)                   │
├─────────────────────────────────────────┤
│ INDEX: (conversacion, created_at)       │
│ ORDER BY: created_at ASC                │
└─────────────────────────────────────────┘
```

### Descripción de Modelos

#### Conversacion
**Propósito:** Representa una conversación 1:1 entre dos usuarios.

**Campos clave:**
- `participante_1` y `participante_2`: Los dos usuarios de la conversación
- `ultimo_mensaje`: Referencia al último mensaje (para ordenar lista de conversaciones)
- `ultimo_mensaje_at`: Timestamp del último mensaje (para ordenar)

**Constraints:**
- `UNIQUE(tenant, participante_1, participante_2)`: Solo una conversación por par de usuarios
- Index descendente por `ultimo_mensaje_at` para listar conversaciones más recientes primero

#### Mensaje
**Propósito:** Representa un mensaje individual dentro de una conversación.

**Campos clave:**
- `contenido`: Texto original del usuario
- `contenido_html`: HTML procesado con enlaces `[PRY-001]` y menciones `@usuario`
- `imagen_url`: URL de imagen original en Cloudflare R2
- `thumbnail_url`: URL de thumbnail 320x320 (lazy loading)
- `archivo_url`: URL de archivo adjunto (PDF/DOCX/XLSX)
- `responde_a`: Mensaje al que está respondiendo (reply feature)
- `editado`: Si el mensaje fue editado (<15 min desde envío)
- `contenido_original`: Backup del contenido antes de primera edición

**Constraints:**
- Index por `(conversacion, created_at)` para listar mensajes en orden cronológico
- Orden ascendente por `created_at` (más antiguo primero)

---

## 🔌 Flujo WebSocket

### Diagrama de Secuencia

```
Usuario A              Backend (Daphne)         Redis (Upstash)         Usuario B
   │                          │                        │                    │
   │  1. Connect WS (JWT)     │                        │                    │
   ├─────────────────────────>│                        │                    │
   │                          │                        │                    │
   │  2. Validate JWT         │                        │                    │
   │     + Join grupos        │                        │                    │
   │<─────────────────────────┤                        │                    │
   │                          │                        │                    │
   │  3. Set presence online  │                        │                    │
   │                          ├───────────────────────>│                    │
   │                          │  SET user:A:status     │                    │
   │                          │  TTL 35s               │                    │
   │                          │                        │                    │
   │  4. Heartbeat (25s)      │                        │                    │
   ├─────────────────────────>│                        │                    │
   │                          ├───────────────────────>│                    │
   │                          │  REFRESH TTL           │                    │
   │                          │                        │                    │
   │  5. Send message         │                        │                    │
   ├─────────────────────────>│                        │                    │
   │                          │                        │                    │
   │  6. Save to PostgreSQL   │                        │                    │
   │                          │  INSERT mensaje        │                    │
   │                          │                        │                    │
   │  7. Publish to Redis     │                        │                    │
   │                          ├───────────────────────>│                    │
   │                          │  PUBLISH conv:UUID     │                    │
   │                          │                        │                    │
   │  8. Broadcast message    │                        │                    │
   │<─────────────────────────┤                        ├───────────────────>│
   │  {type: chat_new_message}│                        │  {type: chat_new_message}
   │                          │                        │                    │
   │  9. Disconnect           │                        │                    │
   ├─────────────────────────>│                        │                    │
   │                          │                        │                    │
   │ 10. Set presence offline │                        │                    │
   │                          ├───────────────────────>│                    │
   │                          │  DEL user:A:status     │                    │
   │                          │                        │                    │
```

### Eventos WebSocket

#### Cliente → Servidor

1. **`chat.send_message`**
   ```json
   {
     "type": "chat.send_message",
     "conversacion_id": "uuid",
     "contenido": "Texto del mensaje",
     "responde_a_id": "uuid" // opcional
   }
   ```

2. **`chat.typing`**
   ```json
   {
     "type": "chat.typing",
     "conversacion_id": "uuid",
     "is_typing": true
   }
   ```

3. **`chat.mark_read`**
   ```json
   {
     "type": "chat.mark_read",
     "mensaje_id": "uuid"
   }
   ```

4. **`chat.heartbeat`**
   ```json
   {
     "type": "chat.heartbeat"
   }
   ```

#### Servidor → Cliente

1. **`chat.new_message`**
   ```json
   {
     "type": "chat.new_message",
     "mensaje": {
       "id": "uuid",
       "conversacion_id": "uuid",
       "remitente": {...},
       "contenido": "texto",
       "contenido_html": "<a href>...</a>",
       "created_at": "2026-03-30T12:00:00Z",
       "leido_por_destinatario": false
     }
   }
   ```

2. **`chat.message_read`**
   ```json
   {
     "type": "chat.message_read",
     "mensaje_id": "uuid",
     "leido_at": "2026-03-30T12:05:00Z"
   }
   ```

3. **`chat.message_edited`**
   ```json
   {
     "type": "chat.message_edited",
     "mensaje_id": "uuid",
     "contenido": "nuevo texto",
     "contenido_html": "nuevo HTML",
     "editado_at": "2026-03-30T12:10:00Z"
   }
   ```

4. **`chat.presence_changed`**
   ```json
   {
     "type": "chat.presence_changed",
     "user_id": "uuid",
     "status": "online" // online | offline | away
   }
   ```

### Grupos Redis

Cada conversación tiene su propio grupo en Redis:
- **Grupo:** `conv_{conversacion_id}`
- **Miembros:** Ambos participantes de la conversación
- **TTL:** No tiene (permanente hasta disconnect)

### Presencia (Online/Offline)

- **Key Redis:** `user:{user_id}:status`
- **Valores:** `online` | `offline` | `away`
- **TTL:** 35 segundos
- **Heartbeat frontend:** Cada 25 segundos (antes del TTL)
- **Away detection:** Si heartbeat no llega en 35s, status → `away`

---

## 🔗 API REST

### Endpoints

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/chat/conversaciones/` | Listar conversaciones del usuario | JWT |
| POST | `/api/v1/chat/conversaciones/` | Crear/obtener conversación | JWT |
| GET | `/api/v1/chat/conversaciones/{id}/mensajes/` | Listar mensajes (paginado) | JWT |
| POST | `/api/v1/chat/conversaciones/{id}/mensajes/` | Enviar mensaje | JWT |
| POST | `/api/v1/chat/mensajes/{id}/marcar-leido/` | Marcar mensaje como leído | JWT |
| PATCH | `/api/v1/chat/mensajes/{id}/editar/` | Editar mensaje (<15 min) | JWT |
| POST | `/api/v1/chat/upload-archivo/` | Upload archivo (PDF/DOCX/XLSX) | JWT |
| POST | `/api/v1/chat/upload-imagen/` | Upload imagen + thumbnail | JWT |
| GET | `/api/v1/chat/autocomplete/entidades/` | Autocomplete proyectos/tareas/fases | JWT |
| GET | `/api/v1/chat/autocomplete/usuarios/` | Autocomplete usuarios | JWT |
| GET | `/api/v1/chat/conversaciones/{id}/buscar/` | Búsqueda full-text | JWT |
| GET | `/api/v1/chat/presencia/` | Estado presencia usuarios | JWT |

### Ejemplos de Payloads

#### POST /api/v1/chat/conversaciones/
```json
// Request
{
  "destinatario_id": "uuid-del-usuario-b"
}

// Response 200
{
  "id": "uuid",
  "participante_1": {...},
  "participante_2": {...},
  "ultimo_mensaje": null,
  "ultimo_mensaje_at": null
}
```

#### POST /api/v1/chat/conversaciones/{id}/mensajes/
```json
// Request
{
  "contenido": "Hola, revisa [PRY-001] por favor",
  "responde_a_id": "uuid" // opcional
}

// Response 201
{
  "id": "uuid",
  "conversacion_id": "uuid",
  "remitente": {...},
  "contenido": "Hola, revisa [PRY-001] por favor",
  "contenido_html": "Hola, revisa <a href=\"/proyectos/uuid\">PRY-001</a> por favor",
  "imagen_url": null,
  "responde_a": null,
  "leido_por_destinatario": false,
  "created_at": "2026-03-30T12:00:00Z"
}
```

#### POST /api/v1/chat/upload-imagen/
```json
// Request (multipart/form-data)
{
  "imagen": File (JPG/PNG, max 5 MB)
}

// Response 200
{
  "imagen_url": "https://r2.../images/original/abc123.jpg",
  "thumbnail_url": "https://r2.../images/thumbnails/abc123.webp",
  "width": 1920,
  "height": 1080
}
```

#### GET /api/v1/chat/autocomplete/entidades/?query=PRY&tipo=proyecto
```json
// Response 200
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

---

## 🔒 Seguridad

### Autenticación
- **JWT tokens** en header `Authorization: Bearer {token}`
- **WebSocket auth** vía query param `?token={jwt}` (único método soportado por WebSocket)
- **Validación** en cada request/connection

### Autorización
- **Tenant isolation:** Usuarios solo ven conversaciones de su tenant
- **Permisos:** Solo participantes de conversación pueden ver/enviar mensajes
- **Validación entidades:** Solo generar links `[PRY-001]` si usuario tiene acceso al proyecto

### XSS Prevention
- **Sanitización HTML:** bleach con whitelist de tags
  ```python
  ALLOWED_TAGS = ['a', 'span']
  ALLOWED_ATTRS = {
      'a': ['href', 'class', 'data-type', 'data-id'],
      'span': ['class', 'data-user-id']
  }
  ```
- **Validación inputs:** Rechazo de scripts, eventos HTML, etc.

### File Upload Validation
- **Archivos:**
  - Max size: 10 MB
  - Formatos: PDF, DOCX, XLSX
  - Validación MIME type + extensión
  
- **Imágenes:**
  - Max size: 5 MB
  - Formatos: JPG, PNG, WEBP
  - Compresión client-side antes de upload

### Encryption
- **WebSocket:** WSS (TLS encryption) en producción
- **Storage:** HTTPS para Cloudflare R2
- **JWT:** Firmado con SECRET_KEY de Django

---

## ⚡ Performance

### Lazy Loading Imágenes
```typescript
// Frontend: LazyImageDirective
@Directive({selector: '[lazyImage]'})
export class LazyImageDirective {
  // 1. Carga thumbnail primero (320x320 WEBP)
  // 2. IntersectionObserver detecta cuando imagen es visible
  // 3. Swap a imagen original (1920px max)
}
```

### Thumbnails
- **Tamaño:** 320x320 px
- **Formato:** WEBP (mejor compresión que JPG/PNG)
- **Generación:** Backend con Pillow (mantiene aspect ratio)
- **Carpetas R2:**
  - `/images/original/` — Imagen completa
  - `/images/thumbnails/` — Thumbnail 320x320

### Compresión Client-Side
```typescript
// utils/image-compressor.ts
async function compressImage(file: File): Promise<Blob> {
  // 1. Canvas API para resize si >1920px
  // 2. Quality 0.85
  // 3. PNG >500KB → WEBP conversion
  // Reducción promedio: 50-70%
}
```

### Scroll Infinito
- **Paginación:** 50 mensajes por página
- **Carga automática:** Al hacer scroll hacia arriba
- **Virtual scrolling:** Angular Material CDK ScrollingModule para performance

### WebSocket Connection Pooling
- **Daphne workers:** Múltiples workers para distribuir conexiones
- **Heartbeat:** Keep-alive cada 25s para mantener conexión activa
- **Reconexión:** Exponential backoff (2s, 4s, 8s, 16s, cap 30s)

### Caché Frontend
- **Signals:** Angular signals para reactividad sin re-renders innecesarios
- **OnPush:** Estrategia ChangeDetection para componentes
- **Memoization:** computed() para derivar estado sin recalcular

---

## 💰 Costos

### Fase Actual (Free Tier)
- **Upstash Redis:** $0/mes (10K comandos/día)
- **Cloudflare R2:** $0/mes (10 GB + 1M requests/mes)
- **Total:** $0/mes

**Estimación para 100 usuarios activos:**
- Redis: 300K comandos/mes (dentro del free tier)
- R2: 5 GB storage + 500K requests/mes (dentro del free tier)

### Fase MVP (0-500 usuarios)
- **Upstash Redis:** $1.70/mes
- **Cloudflare R2:** $0.68/mes
- **AWS (ECS + RDS + ALB):** $43.00/mes
- **Total:** $45.38/mes

**Comparación AWS nativo (ElastiCache + S3):**
- Redis: $9.79/mes
- S3: $9.91/mes
- AWS infra: $43.00/mes
- **Total:** $62.70/mes

**Ahorro:** $17.32/mes (38%)

### Escalabilidad
- **500-2000 usuarios:** Mantener stack actual
- **>2000 usuarios:** Evaluar migración a ElastiCache + S3
- **Trigger crítico:** Latencia >50ms o volumen >5M comandos Redis/mes

---

## 📚 Referencias

- **Decisiones:** Ver `DECISIONS.md` (DEC-033, DEC-034, DEC-035)
- **Deployment:** Ver `DEPLOYMENT_CHAT.md`
- **API Reference:** Ver `API_REFERENCE_CHAT.md`
- **Notion:** https://www.notion.so/333ee9c3690a8122873cd2a03c123812