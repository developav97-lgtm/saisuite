# DECISIONS-ARCHIVE.md — Decisiones arquitectónicas históricas

Decisiones archivadas del módulo de Proyectos y Chat (completados).
Para decisiones activas ver: DECISIONS.md en raíz del repo.

---

## DEC-012: Terceros y Consecutivos como Módulos Transversales

**Fecha:** 19 Marzo 2026
**Estado:** ✅ Aprobada e implementada (Terceros) / ⏳ Pendiente (Consecutivos)
**Contexto:** Módulo de Proyectos

### Problema
Durante la implementación del Grupo 3 (Terceros), se detectó que el diseño inicial ubicaba Terceros dentro de la app `proyectos`, lo que implicaba:
- Terceros exclusivos de Proyectos
- No reutilizables en otros módulos (SaiReviews, SaiCash, SaiRoute, etc.)
- Duplicación de datos si otros módulos necesitaban terceros
- API fragmentada

El mismo problema aplica para Consecutivos.

### Opciones Evaluadas

**Opción A: Mantener en app específica (proyectos)**
- ❌ No reutilizable
- ❌ Duplicación de código/datos
- ❌ Inconsistencia entre módulos
- ✅ Más simple inicialmente

**Opción B: Módulos transversales en app `core`** ⭐ SELECCIONADA
- ✅ Reutilizable en todos los módulos
- ✅ Un solo registro de tercero compartido
- ✅ API centralizada `/api/v1/terceros/`
- ✅ Relaciones específicas por módulo
- ❌ Requiere refactorización

### Decisión

**Terceros y Consecutivos se implementan como módulos TRANSVERSALES en app `core`.**

**Arquitectura:**
```
apps/core/  (TRANSVERSAL)
├── models.py
│   ├── Tercero              ← Encabezado
│   ├── TerceroDireccion     ← Líneas (direcciones)
│   └── ConfiguracionConsecutivo  ← Pendiente implementar
├── serializers.py
├── views.py
└── urls.py  → /api/v1/terceros/, /api/v1/consecutivos/

apps/proyectos/  (ESPECÍFICO)
├── models.py
│   └── TerceroProyecto      ← Relación Tercero + Proyecto
└── ...

apps/reviews/  (FUTURO)
└── models.py
    └── TerceroReview        ← Relación Tercero + Review

apps/cash/  (FUTURO)
└── models.py
    └── TerceroCash          ← Relación Tercero + CxC/CxP
```

### Implementación

**Terceros:**
- ✅ Modelo `Tercero` en `apps/core/models.py`
- ✅ Modelo `TerceroDireccion` en `apps/core/models.py`
- ✅ Serializers, Views, URLs en app `core`
- ✅ Service transversal `TerceroService` en frontend
- ✅ Componente reutilizable `tercero-selector` (autocomplete)
- ✅ `TerceroProyecto` en app `proyectos` con FK a `core.Tercero`

**Consecutivos:**
- ⏳ Pendiente implementar como transversal
- ⏳ Modelo `ConfiguracionConsecutivo` en app `core`
- ⏳ Service `generar_consecutivo()` centralizado

### Consecuencias

**Positivas:**
- ✅ Un tercero puede usarse en Proyectos, SaiReviews, SaiCash simultáneamente
- ✅ Consistencia de datos (un cliente es el mismo en todos los módulos)
- ✅ API única `/api/v1/terceros/` para todos
- ✅ Componentes frontend reutilizables
- ✅ Sincronización Saiopen centralizada

**Negativas:**
- ⚠️ Requirió refactorización de código ya generado
- ⚠️ Mayor complejidad inicial

### Criterios de Revisión
- ✅ Terceros funciona en Proyectos
- ⏳ Terceros funciona en al menos un segundo módulo (SaiReviews)
- ⏳ Consecutivos implementado como transversal

### Referencias
- Grupo 3: https://www.notion.so/329ee9c3690a811eab5ecd3fd8105c22
- Cierre Sesión: https://www.notion.so/329ee9c3690a814398b3de9a87fcf5db

---

## DEC-033: Redis Provider — Upstash para Sistema de Comunicaciones

**Fecha:** 2026-03-30  
**Estado:** ✅ Decidido  
**Contexto:** Sistema de notificaciones en tiempo real + chat interno requiere Redis pub/sub para Django Channels.

**Decisión:** Usar Upstash Redis (serverless) en fase MVP, con plan de migración a AWS ElastiCache si es necesario.

**Justificación:**
- **Costo:** $1.70/mes vs $9.79/mes ElastiCache (ahorro 82%)
- **Free tier:** 10,000 comandos/día (300K/mes) suficiente para 100 usuarios activos
- **Zero-ops:** Sin gestión de VPC, subnets, security groups, patching, failover
- **Setup:** 5 minutos vs 15 minutos (configuración de AWS)
- **Facturación:** Pay-as-you-go (si el módulo no se usa, costo = $0)
- **Portabilidad:** API estándar Redis, migración a ElastiCache trivial (cambio de connection string)
- **Escalabilidad:** Automática (serverless), sin necesidad de cambiar instancias

**Alternativa descartada:** AWS ElastiCache
- **Pros:** Latencia más baja (1-5ms vs 20-50ms), SLA superior (99.99% vs 99.9%), mejor para >2000 usuarios
- **Contras:** Costo 5.8x mayor en MVP, requiere gestión operacional, setup complejo (VPC, subnets)

**Trigger de revisión:**
- Volumen >5M comandos/mes (punto donde Upstash Pay-As-You-Go = ElastiCache Reserved)
- Latencia crítica (<5ms requerido para aplicación)
- Compliance estricto (datos deben permanecer dentro de VPC AWS)

**Tiempo estimado de migración:** 2-4 horas

---

## DEC-034: Storage Provider — Cloudflare R2 para Multimedia

**Fecha:** 2026-03-30  
**Estado:** ✅ Decidido  
**Contexto:** Almacenamiento de imágenes y archivos adjuntos del chat interno (imágenes, PDF, DOCX, XLSX).

**Decisión:** Usar Cloudflare R2 con API S3-compatible, con plan de migración a AWS S3 si es necesario.

**Justificación:**
- **Costo:** $0.68/mes vs $9.91/mes S3 (ahorro 93%)
- **Free tier:** 10 GB storage + 1M requests/mes (suficiente para 20,000 imágenes)
- **Egress gratis:** Chat tiene alto volumen de views (100 GB/mes = $9 en S3, $0 en R2)
- **CDN incluido:** No requiere CloudFront adicional ($5-10/mes ahorrados)
- **API S3-compatible:** boto3 funciona igual, portabilidad total
- **Latencia similar:** Edge network global de Cloudflare (10-30ms)

**Alternativa descartada:** AWS S3
- **Pros:** SLA superior (99.99% vs 99.9%), integración profunda con Lambda/EventBridge
- **Contras:** Costo 14.5x mayor, requiere CloudFront para CDN global (+$10/mes)

**Trigger de revisión:**
- SLA >99.99% requerido (crítico para negocio)
- Integración profunda con servicios AWS (Lambda, EventBridge)
- Volumen egress <50 GB/mes (donde diferencia de costo es marginal)

**Tiempo estimado de migración:** 4-6 horas

---

## DEC-035: Autocomplete de Enlaces en Chat

**Fecha:** 2026-03-30  
**Estado:** ✅ Decidido  
**Contexto:** Chat interno necesita permitir referenciar entidades del proyecto (proyectos, tareas, fases) de forma rápida e intuitiva.

**Decisión:** Implementar sistema de autocomplete con sintaxis especial que genera links HTML sanitizados.

**Sintaxis soportada:**
- `[PRY-001]` → Link a proyecto
- `[TAR-023]` → Link a tarea
- `[FAS-005]` → Link a fase
- `@Usuario` → Mención (genera notificación automática)

**Justificación:**
- **Mejora contexto:** Links directos a entidades sin salir del chat
- **UX fluida:** Autocomplete intuitivo con navegación por teclado (↑↓ Enter Esc)
- **Seguridad:** Validación de permisos antes de generar link, sanitización HTML con bleach
- **Notificaciones automáticas:** Menciones @ generan notificación push + campanita

**Alternativas descartadas:**
1. Markdown estándar `[texto](url)` — menos intuitivo para usuarios no técnicos
2. Rich text editor — peso adicional (50-100 KB), complejidad innecesaria
3. Búsqueda manual + botón "Insertar link" — UX muy inferior, baja adopción esperada

---

## DEC-036: Chat Backend — Conversación 1-to-1 con UUID Normalization

**Fecha:** 2026-03-30
**Estado:** ✅ Decidido e implementado

**Contexto:** El chat interno necesita conversaciones 1-a-1 entre usuarios del mismo tenant. El modelo `Conversacion` tiene `participante_1` y `participante_2`, pero crear A→B y B→A generaría duplicados.

**Opciones consideradas:**
1. **Constraint CHECK(participante_1 < participante_2)** — DB-level enforcement
2. **UUID normalization en service** — siempre almacenar UUID menor como participante_1
3. **Q query bidireccional** — buscar ambas combinaciones en cada query

**Decisión:** Opción 2 — UUID normalization en `ChatService.obtener_o_crear_conversacion()`.

**Razón:**
- Simple y predecible — `if str(usuario1.id) > str(usuario2.id): swap`
- `unique_together = (company, participante_1, participante_2)` previene duplicados a nivel DB
- Funciona con `get_or_create` — no necesita query bidireccional
- Evita constraints CHECK que complican migraciones

**Consecuencia:** Todo código que cree conversaciones DEBE pasar por `ChatService.obtener_o_crear_conversacion()`, nunca crear directamente via `Conversacion.objects.create()`.