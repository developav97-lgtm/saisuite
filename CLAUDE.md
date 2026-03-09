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

### Base de datos
- Multi-tenant: company_id en TODAS las tablas de negocio.
- PKs: UUID v4 en todos los modelos expuestos por API.
- Llaves Firebird → campo `sai_key` (llaves compuestas) o `sai_id` (simples).
- `unique_together: (company, sai_key)` en todos los modelos espejo de Firebird.
- Dinero: siempre `NUMERIC(15,2)`. Nunca `float`.
- Fechas con hora: `TIMESTAMPTZ` en UTC. Solo fecha: `DATE`.

### General
- Commits: `<tipo>(<scope>): <descripción en imperativo>` — ej: `feat(invoices): add list endpoint`
- Nunca commitear `.env` ni archivos con credenciales.
- Tests antes de hacer PR. Cobertura mínima en services.py: 80%.

---

## 4. Estructura del proyecto

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
├── CLAUDE.md            # Este archivo
├── ERRORS.md            # Registro de errores resueltos
├── DECISIONS.md         # Decisiones de arquitectura
├── CONTEXT.md           # Estado actual del proyecto
└── docker-compose.yml
```

---

## 5. Orden de generación de archivos en una feature nueva

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
```

---

## 6. Errores frecuentes — revisar ERRORS.md para lista completa

Los más comunes históricamente en este proyecto:

- Lógica de negocio en views → moverla siempre a services.py
- Olvidar `select_related('client')` en queries de facturas → N+1 query
- `sai_key` sin `unique_together(company, sai_key)` → duplicados en sync
- `any` en TypeScript → rompe strict mode
- Suscripción manual sin unsubscribe en Angular → memory leak

---

## 7. Roles de usuario — siempre validar permisos

| Role | Acceso |
|---|---|
| `company_admin` | Todo dentro de su empresa |
| `seller` | SaiVentas — clientes, productos, pedidos |
| `collector` | SaiCobros — cartera, gestiones, pagos |
| `viewer` | Solo lectura — dashboards y reportes |
| `valmen_admin` | Plataforma completa (is_staff=True) |
| `valmen_support` | Solo lectura de datos de cliente |

---

## 8. Bucle de mejora automática — instrucciones para esta sesión

Al terminar cada sesión o al resolver un problema significativo:

1. Si resolviste un error → agregar entrada en `ERRORS.md`
2. Si tomaste una decisión de diseño no cubierta en los docs → agregar en `DECISIONS.md`
3. Al final de la sesión → actualizar `CONTEXT.md` con el estado actual

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
## [FECHA] DECISIÓN: [descripción corta]
**Contexto:** por qué se necesitaba tomar esta decisión
**Opciones consideradas:** qué alternativas había
**Decisión:** qué se eligió
**Razón:** por qué
**Consecuencia:** qué implica esta decisión hacia adelante
```
