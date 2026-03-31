# CLAUDE.md — SaiSuite
# ValMen Tech × Saiopen | Django + Angular + PostgreSQL + n8n + AWS
# Lee este archivo COMPLETO antes de tocar cualquier archivo del proyecto.

---

## 1. Qué es este proyecto

SaiSuite es una plataforma SaaS multi-tenant construida para el ecosistema Saiopen
(ERP Windows/Firebird de Grupo SAI S.A.S). Permite a las empresas cliente acceder
a sus datos de Saiopen desde la nube, con módulos de ventas, cobros y dashboards.

**Desarrollado por:** ValMen Tech  
**Stack:** Django 5 + DRF + PostgreSQL 16 + Angular 18 + n8n + AWS (ECS Fargate)  
**Integración clave:** Agente Python Windows ↔ Firebird ↔ AWS SQS ↔ Django

---

## 2. Documentación de referencia obligatoria

Antes de generar código, leer el documento relevante según la tarea:

| Tarea | Documento (en docs/) |
|---|---|
| Crear o modificar cualquier modelo | Esquema_BD_SaiSuite_v1.docx |
| Crear cualquier archivo de código | Estandares_Codigo_SaiSuite_v1.docx |
| **Crear cualquier componente Angular** | **docs/standards/UI-UX-STANDARDS.md** |
| **Validar cualquier funcionalidad** | **docs/base-reference/CHECKLIST-VALIDACION.md** ⚡ NUEVO |
| Construir una feature nueva de cero | Flujo_Feature_SaiSuite_v1.docx |
| Configurar o modificar AWS | AWS_Setup_SaiSuite_v1.docx |
| Diseñar infraestructura | Infraestructura_SaiSuite_v2.docx |

**Siempre leer también:**
- `ERRORS.md` — errores ya resueltos, no repetirlos
- `DECISIONS.md` — decisiones de arquitectura tomadas, respetarlas
- `CONTEXT.md` — estado actual del proyecto y sesión anterior

---

## 3. Reglas absolutas — nunca violarlas

### Backend Django
- TODA la lógica de negocio va en `services.py`. Nunca en views, nunca en modelos.
- Las views solo orquestan: reciben request → llaman service → retornan response.
- Los serializers solo transforman datos. No calculan, no llaman APIs, no tienen efectos secundarios.
- Todo modelo de negocio hereda de `BaseModel` (UUID pk, company FK, timestamps).
- Migraciones: solo con `python manage.py makemigrations`. Nunca SQL manual.
- Logging: siempre `logger.info("evento", extra={"key": "value"})`. Nunca `print()`.
- Nunca hardcodear secrets. Todos vienen de variables de entorno o AWS Secrets Manager.

### Frontend Angular
- `strict: true` en TypeScript. Si no compila con strict, el código está mal.
- Componentes presentacionales: siempre `ChangeDetectionStrategy.OnPush`.
- Nunca suscripción manual sin `unsubscribe`. Usar `async pipe` en el template.
- Nunca `any`. Si no se conoce el tipo exacto, usar `unknown` con narrowing.
- Servicios globales en `core/`. Servicios de feature en `features/[x]/services/`.
- JWT se añade automáticamente via interceptor. Nunca añadir headers manualmente.

#### UI Framework: Angular Material (DEC-011)
- Framework de componentes: **Angular Material** — `npm install @angular/material @angular/cdk`
- **NUNCA** usar PrimeNG, Bootstrap ni Tailwind
- Iconos: Material Icons (Google Font) — `mat-icon` en templates
- Notificaciones: `MatSnackBar` — nunca `alert()`
- Confirmaciones: `MatDialog` con `ConfirmDialogComponent` — nunca `confirm()`
- Tablas: `mat-table` con `MatPaginatorModule` server-side
- Dark mode: clase `.dark-theme` en `<body>`, gestionada por `ThemeService`
- Tema: M3 con paleta azul corporativo ValMen Tech

### Base de datos
- Multi-tenant: company_id en TODAS las tablas de negocio.
- PKs: UUID v4 en todos los modelos expuestos por API.
- Llaves Firebird → campo `sai_key` (llaves compuestas) o `sai_id` (simples).
- `unique_together: (company, sai_key)` en todos los modelos espejo de Firebird.
- Dinero: siempre `NUMERIC(15,2)`. Nunca `float`.
- Fechas con hora: `TIMESTAMPTZ` en UTC. Solo fecha: `DATE`.
- `DEFAULT_AUTO_FIELD = BigAutoField` en settings es inerte — todos los modelos
  heredan UUID de `BaseModel`. No eliminar, es el default seguro de Django.

### General
- Commits: `<tipo>(<scope>): <descripción en imperativo>` — ej: `feat(invoices): add list endpoint`
- Nunca commitear `.env` ni archivos con credenciales.
- Tests antes de hacer PR. Cobertura mínima en services.py: 80%.

---

## 4. ⚡ NUEVO: Validación Multi-Plataforma Obligatoria

**REGLA CRÍTICA:** Toda funcionalidad (nueva o modificada) DEBE validarse en:

✅ **Desktop** (1920x1080)  
✅ **Mobile** (375px - 768px)  
✅ **Tema Claro** (light mode)  
✅ **Tema Oscuro** (dark mode)

**Validación 4x4 obligatoria:**
1. Desktop + Light
2. Desktop + Dark
3. Mobile + Light
4. Mobile + Dark

**Documento:** `docs/base-reference/CHECKLIST-VALIDACION.md`

### Criterios de Rechazo Automático

Una funcionalidad NO está completa si:

❌ **No funciona en mobile** (responsive roto, scroll bloqueado, elementos cortados)  
❌ **No funciona en algún tema** (contraste ilegible, colores incorrectos)  
❌ **Touch targets < 44x44px** en mobile  
❌ **Tablas sin scroll horizontal** en mobile (sin vista alternativa)  
❌ **Texto ilegible** por falta de contraste  
❌ **Elementos superpuestos** en cualquier viewport

### Fixes Comunes Mobile

```scss
// Tablas responsive
.table-responsive {
  display: block;
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  
  @media (max-width: 768px) {
    max-width: 100vw;
  }
}

// Touch targets mínimos
@media (max-width: 768px) {
  button, .icon-button {
    min-width: 44px;
    min-height: 44px;
    padding: 8px;
  }
}

// Tabs con scroll
.mat-tab-labels {
  @media (max-width: 768px) {
    overflow-x: auto !important;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
}
```

**Breakpoints estándar:**
- Mobile: `< 768px`
- Tablet: `768px - 1024px`
- Desktop: `> 1024px`

---

## 5. Estructura del proyecto

```
saisuite/
├── backend/
│   ├── config/          # settings (base, development, production), urls, wsgi
│   ├── apps/
│   │   ├── core/        # BaseModel, managers, middleware, excepciones base
│   │   ├── companies/   # Company, CompanyModule
│   │   ├── users/       # User, ActiveSession, roles
│   │   ├── sync_agent/  # Modelos espejo Firebird (SaiClient, SaiInvoice, etc.)
│   │   └── integrations/# Webhooks n8n, clientes API externos
│   └── manage.py
├── frontend/
│   └── src/app/
│       ├── core/        # auth, interceptors, guards — singletons
│       ├── shared/      # componentes reutilizables sin estado de negocio
│       └── features/    # un módulo lazy por feature de producto
├── agent/               # Agente Python Windows ↔ Firebird ↔ SQS
├── n8n/workflows/       # Workflows .json versionados
├── docs/                # Documentos técnicos de referencia
│   ├── base-reference/  # Docs generales del proyecto
│   │   └── CHECKLIST-VALIDACION.md  ⚡ NUEVO
│   ├── standards/       # Estándares de código y UI/UX
│   ├── plans/           # Planes de features
│   ├── technical/       # Documentación técnica por módulo
│   └── manuales/        # Manuales de usuario
├── CLAUDE.md            # Este archivo
├── ERRORS.md            # Registro de errores resueltos
├── DECISIONS.md         # Decisiones de arquitectura
├── CONTEXT.md           # Estado actual del proyecto
└── docker-compose.yml
```

---

## 6. Orden de generación de archivos en una feature nueva

Seguir SIEMPRE este orden. No saltarse pasos ni invertirlos:

```
1. Modelo (models.py)          → verificar primero en Esquema_BD
2. Migración                   → python manage.py makemigrations
3. Serializers (serializers.py)→ lista (campos mínimos) + detalle (todos)
4. Service (services.py)       → toda la lógica aquí
5. View + URL                  → solo orquesta, llama al service
6. Tests                       → services primero, luego views
7. Angular model (interfaz TS) → espeja exactamente el serializer
8. Angular service             → tipado con la interfaz
9. Angular component           → presentacional, OnPush
10. Angular container          → inteligente, async pipe
11. Angular module + routing   → lazy loading
12. ⚡ VALIDACIÓN 4x4          → Desktop/Mobile × Light/Dark ⚡ NUEVO
```

---

## 7. Errores frecuentes — revisar ERRORS.md para lista completa

Los más comunes históricamente en este proyecto:

- Lógica de negocio en views → moverla siempre a services.py
- Olvidar `select_related('client')` en queries de facturas → N+1 query
- `sai_key` sin `unique_together(company, sai_key)` → duplicados en sync
- `any` en TypeScript → rompe strict mode
- Suscripción manual sin unsubscribe en Angular → memory leak
- ⚡ **NUEVO:** No validar responsive mobile → bugs en producción
- ⚡ **NUEVO:** Hardcodear colores → temas rotos

---

## 8. Roles de usuario — siempre validar permisos

| Role | Acceso |
|---|---|
| `company_admin` | Todo dentro de su empresa |
| `seller` | SaiVentas — clientes, productos, pedidos |
| `collector` | SaiCobros — cartera, gestiones, pagos |
| `viewer` | Solo lectura — dashboards y reportes |
| `valmen_admin` | Plataforma completa (is_staff=True) |
| `valmen_support` | Solo lectura de datos de cliente |

---

## 9. Bucle de mejora automática — instrucciones para esta sesión

Al terminar cada sesión o al resolver un problema significativo:

1. Si resolviste un error → agregar entrada en `ERRORS.md`
2. Si tomaste una decisión de diseño no cubierta en los docs → agregar en `DECISIONS.md`
3. ⚡ **NUEVO:** Si encontraste bug responsive → agregar a backlog Notion
4. Al final de la sesión → actualizar `CONTEXT.md` con el estado actual

**Formato de entrada en ERRORS.md:**
```
## [FECHA] ERROR: [descripción corta]
**Síntoma:** qué pasaba
**Causa:** por qué pasaba
**Fix:** cómo se resolvió
**Prevención:** qué hacer para que no vuelva a pasar
```

**Formato de entrada en DECISIONS.md:**
```
## DEC-XXX: [Título corto]
**Fecha:** YYYY-MM-DD
**Contexto:** Por qué se necesitaba tomar esta decisión
**Opciones consideradas:** Qué alternativas había
**Decisión:** Qué se eligió
**Razón:** Por qué se eligió esta opción
**Consecuencias:** Qué implica esta decisión hacia adelante
**Criterios de revisión:** Cuándo/cómo revisar esta decisión
```

---

## 10. Arquitectura Híbrida Django + Go

### Principio general
El proyecto Saicloud usa **Django como núcleo principal** y **Go para microservicios estratégicos**. 

**Regla de oro:** Django por defecto (80% casos), Go solo cuando esté justificado por métricas.

### Cuándo usar Django (80% de los casos)

✅ Usa Django para:
- CRUD de entidades (clientes, productos, pedidos, inventario, etc.)
- APIs REST estándar
- Autenticación y permisos (JWT, roles, multi-tenancy)
- Lógica de negocio que cambia frecuentemente
- Integraciones con n8n vía webhooks
- Panel de administración
- Reportes y exports (CSV, PDF)
- Procesos async con Celery o Django Q

### Cuándo considerar Go (20% de los casos)

⚙️ Solo recomienda Go cuando se cumpla AL MENOS UNO de estos criterios:

#### Criterio 1: Alta concurrencia sostenida
- >1000 req/s simultáneas
- WebSockets persistentes con miles de conexiones
- Streaming de datos en tiempo real

#### Criterio 2: Procesamiento intensivo
- Workers de procesamiento batch pesado
- Transformación de grandes volúmenes (50k+ registros)
- Cálculos matemáticos o estadísticos complejos

#### Criterio 3: Ejecutables standalone
- Agentes que corren en PC del cliente
- CLI tools sin dependencias pesadas
- Servicios que deben ser binarios compilados

#### Criterio 4: Optimización de costos demostrada
- El proceso corre 24/7 y consume >$300/mes
- Métricas reales muestran que Go reduce costos >50%
- ROI del desarrollo se recupera en <6 meses

### ❌ NO uses Go para:
- "Porque Go es más rápido" (sin métricas)
- CRUDs simples
- Prototipado rápido
- Features que cambian frecuentemente
- "Queremos aprender Go"

---

## 11. Backlog de Funcionalidades — Notion

**Base de datos:** https://www.notion.so/0f5116945f4346ffa18fee534371923c

Al encontrar bugs o funcionalidades faltantes:
1. Crear tarea en backlog Notion
2. Clasificar: Funcionalidad / Bug Mobile / Mejora
3. Priorizar: Alta / Media / Baja
4. Estimar: 1-2h / 2-4h / 4-8h / 8+h
5. Documentar: Ubicación UI + Descripción + Notas técnicas

**Módulos con backlog activo:**
- Proyectos: https://www.notion.so/327ee9c3690a81f296a2ec384b557049

---

## 12. Estándares UI/UX — Angular

**CRÍTICO:** Antes de generar CUALQUIER componente Angular, leer:
- `docs/standards/UI-UX-STANDARDS.md`

Estos estándares se aplican a TODOS los componentes sin excepción:
- Tablas vacías: `sc-empty-state` con icono + mensaje + botón, FUERA del `mat-table`
- Formularios: `appearance="outline"`, errores con `@if` dentro del `mat-form-field`
- Estados de carga: `mat-progress-bar` encima de la tabla (NUNCA spinner centrado en listados)
- Feedback: `MatSnackBar` con `panelClass: ['snack-success'|'snack-error'|'snack-warning']`
- Confirmaciones de eliminación: `MatDialog` con `ConfirmDialogComponent` (NUNCA `confirm()`)
- Acciones en tablas: `mat-icon-button` con tooltip, orden: Ver | Editar | Eliminar
- Sintaxis Angular 18: `@if` / `@for` / `@switch` — NUNCA `*ngIf` / `*ngFor`
- SCSS: variables `var(--sc-*)` siempre, sin colores hardcodeados
- ⚡ **NUEVO:** Responsive mobile: class `table-responsive` en TODAS las tablas
- ⚡ **NUEVO:** Dark mode: usar variables CSS del tema, nunca hardcodear colores
- Referencia canónica de listados: `proyecto-list` component

---

## 13. Lecciones Aprendidas — Sistema de Chat

**Del desarrollo del Sistema de Comunicaciones (Fases 1-9):**

### Multi-Agent Parallel Execution
✅ **Usar 3 agentes en paralelo** para features complejas:
- Backend Agent: modelos + serializers + services + tests
- Frontend Agent: componentes + servicios + templates
- Integration Agent: tests E2E + validación

**Beneficio:** ~10x más rápido que secuencial

### Testing Browser Manual es Esencial
✅ **E2E browser testing encuentra bugs reales** que unit/integration tests NO detectan

**Bugs encontrados en Fase 8 del Chat:**
1. Mensajes en tiempo real no actualizaban → signals refactored
2. Menciones @usuario no funcionaban → NotificacionService integration fixed
3. Enlaces [PRY-001] no navegaban → bleach whitelist updated
4. Imágenes no se visualizaban → lazy loading directive applied

**Aprendizaje:** SIEMPRE validar en navegador real antes de dar por terminado.

### Claude Opus vs Sonnet
✅ **Opus para arquitectura compleja**, **Sonnet para features incrementales**

- Opus: Fases 1-4 del Chat (infraestructura + decisiones arquitectónicas)
- Sonnet: Fases 5-9 (features + validación) — ~10x más rápido

### Docker Compose `down -v`
✅ **Siempre hacer `docker-compose down -v`** cuando:
- Cambias dependencias npm/pip
- Angular no compila por paquetes cached
- Volúmenes anónimos persisten datos stale

**Síntoma:** `node_modules` desactualizados aunque rebuilds contenedor

### Upstash Redis + Cloudflare R2
✅ **Proveedores serverless** ahorraron 82-93% vs AWS nativo

**DEC-033:** Upstash Redis ($1.70/mes vs $9.79 ElastiCache)  
**DEC-034:** Cloudflare R2 ($0.68/mes vs $9.91 S3, egress gratis)

---

## 14. Documentación Base del Proyecto

Hay 5 documentos Word en `docs/base-reference/` con información técnica general:

1. **AWS_Setup_SaiSuite_v1.docx** → Infraestructura AWS
2. **Esquema_BD_SaiSuite_v1.docx** → Diseño de base de datos
3. **Estandares_Codigo_SaiSuite_v1.docx** → Convenciones de código
4. **Flujo_Feature_SaiSuite_v1.docx** → Metodología de desarrollo
5. **Infraestructura_SaiSuite_v2.docx** → Arquitectura del sistema
6. ⚡ **CHECKLIST-VALIDACION.md** → Validación multi-plataforma ⚡ NUEVO

**Cuándo consultarlos:**
- Al configurar nuevos servicios AWS → AWS_Setup
- Al diseñar modelos de BD → Esquema_BD
- Al escribir código → Estandares_Codigo
- Al seguir metodología → Flujo_Feature
- Al entender arquitectura → Infraestructura
- ⚡ **Al validar cualquier feature** → CHECKLIST-VALIDACION ⚡ NUEVO

Estos NO reemplazan la documentación por feature.
Cada feature genera su propia documentación en `docs/plans/`, `docs/technical/`, etc.

---

## 15. Metodología de 10 Fases

**Cada módulo sigue este flujo:**

1. **Planificación** — skill: saicloud-planificacion
2. **Gestión de Contexto** — skill: saicloud-contexto
3. **Skills/MCP/APIs** — preparar herramientas
4. **Agente Único** — setup inicial con Claude Code CLI
5. **Iteración** — ciclos de desarrollo + validación
6. **Protección de Ventana** — skill: saicloud-proteccion-ventana
7. **Revisión Final** — skill: saicloud-revision-final
8. **Panel Admin** — skill: saicloud-panel-admin
9. **Validación UI/UX** — skill: saicloud-validacion-ui + ⚡ **CHECKLIST-VALIDACION.md**
10. **Despliegue** — skill: saicloud-despliegue

**NUNCA saltarse fases.**

---

## 16. ⚡ NUEVO: Prioridades Actuales

**Módulo de Proyectos — Backlog Activo:**

### Fase 1: Quick Wins Mobile (10-16h) — EN CURSO
6 bugs de Alta Prioridad responsive mobile

### Fase 2: Funcionalidades Alta Prioridad (12-16h)
1. Notificaciones automáticas de tareas (4-8h)
2. Nivelación de recursos (8+h)

### Fase 3: Mobile Media/Baja (8-12h)
7 bugs responsive prioridad media/baja

### Fase 4: Funcionalidades Media/Baja (16-24h)
3 funcionalidades restantes

**Estado:** Manual de usuario actualizado (v1.1), auditoría completa, backlog planificado.

---

**Última actualización:** 31 de Marzo de 2026  
**Mantenido por:** Equipo Saicloud — ValMen Tech