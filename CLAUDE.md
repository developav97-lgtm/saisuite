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

#### UI Framework: PrimeNG (DEC-007)
- Framework de componentes: **PrimeNG** con preset `Aura` customizado — `npm install primeng @primeuix/themes primeicons` ← ya instalado
- **NUNCA** usar Angular Material, Bootstrap ni Tailwind
- Importar módulos PrimeNG solo en el feature module (no AppModule)
- Notificaciones: `MessageService` + `p-toast` — nunca `alert()`
- Confirmaciones: `ConfirmationService` + `p-confirmdialog` — nunca `confirm()`
- Tablas: `p-table` con paginación server-side
- Dark mode: clase `.app-dark` en `<html>`, gestionada por `ThemeService`
- Tema: azules corporativos ValMen Tech — ⚠️ HEX pendientes de recibir

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
## Sección a agregar: Arquitectura Híbrida Django + Go

### Principio general
El proyecto Saicloud usa **Django como núcleo principal** y **Go para microservicios estratégicos**. 

**Regla de oro:** Django por defecto, Go solo cuando esté justificado por métricas o requisitos específicos.

### Cuándo recomendar Django (80% de los casos)

✅ Usa Django para:
- CRUD de entidades (clientes, productos, pedidos, inventario, etc.)
- APIs REST estándar
- Autenticación y permisos (JWT, roles, multi-tenancy)
- Lógica de negocio que cambia frecuentemente
- Integraciones con n8n vía webhooks
- Panel de administración
- Reportes y exports (CSV, PDF)
- Procesos que pueden ser async con Celery o Django Q

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
- "Por aprender Go" (este es un proyecto productivo)
- CRUDs simples o APIs REST estándar
- Lógica que cambia frecuentemente
- Casos sin métricas que justifiquen la complejidad

### Proceso de recomendación

Cuando en fase de **Planificación** identifiques un proceso que PODRÍA beneficiarse de Go:

1. **Documenta los criterios que cumple:**
   ```
   Proceso: [nombre]
   Criterios cumplidos:
   - [ ] Alta concurrencia (estimado: X req/s)
   - [ ] Procesamiento intensivo (volumen: X registros)
   - [ ] Ejecutable standalone (contexto: X)
   - [ ] Optimización de costos (ahorro proyectado: $X/mes)
   
   Justificación: [explicación con métricas estimadas o reales]
   ```

2. **Compara con alternativa Django:**
   ```
   Alternativa Django + Celery:
   - Ventajas: [lista]
   - Desventajas: [lista]
   
   Alternativa Go microservice:
   - Ventajas: [lista]
   - Desventajas: [lista]
   
   Recomendación: [Django/Go] porque [razones]
   ```

3. **Si recomiendas Go, define el contrato:**
   ```
   API del microservicio:
   - Endpoint: POST /api/v1/[recurso]
   - Auth: JWT validado
   - Input: [schema]
   - Output: [schema]
   - Comunicación con Django: [REST/SQS/gRPC]
   ```

### Estructura de microservicios Go

```
backend/
├── config/                    # Django principal
├── apps/                      # Apps Django
└── microservices/             # Microservicios Go
    ├── saiopen-agent/         # Agente local Saiopen
    │   ├── main.go
    │   ├── go.mod
    │   ├── Dockerfile
    │   └── README.md          # Justificación y documentación
    └── [nombre-servicio]/
        ├── main.go
        ├── handlers/
        ├── models/
        ├── go.mod
        ├── Dockerfile
        └── README.md          # REQUERIDO: justificación técnica
```

### Stack Go aprobado

**Framework web:** Gin o Echo (similar a Django REST)
**ORM (si necesario):** GORM
**Base de datos:** PostgreSQL (compartida con Django)
**Auth:** JWT validation (compatible con djangorestframework-simplejwt)
**Logging:** Structured JSON a stdout → CloudWatch
**Config:** Variables de entorno (misma filosofía que django-environ)

### Comunicación entre servicios

#### Opción 1: REST (síncrono, <100ms latencia)
```
Django → HTTP → Go Microservice
Auth: Bearer JWT (mismo que Django)
```

#### Opción 2: SQS (asíncrono, procesos batch)
```
Django → SQS Queue → Go Worker
Auth: IAM roles (AWS)
```

#### Opción 3: gRPC (alto rendimiento, baja latencia)
```
Django → gRPC → Go Service
Auth: Metadata con JWT
```

**Regla:** Prefiere REST para simplicidad, SQS para desacoplamiento, gRPC solo si latencia <10ms es crítica.

### Deployment

- Cada microservicio Go en su propio contenedor Docker
- Mismo ECS cluster que Django
- Variables de entorno compartidas donde aplique
- Logs centralizados en CloudWatch
- Métricas en CloudWatch Metrics

**docker-compose.yml incluye todos los servicios:**
```yaml
services:
  django:
    # ... config Django
  
  go-service-name:
    build: ./backend/microservices/service-name
    environment:
      DATABASE_URL: ${DATABASE_URL}
      JWT_SECRET: ${JWT_SECRET}
    ports:
      - "8001:8001"
```

### Testing de integración

Cuando haya microservicios Go:

1. **Unit tests Go:** `go test ./...`
2. **Integration tests:** Django test que llama al microservicio
3. **Contract tests:** Validar que el contrato API se cumple
4. **E2E tests:** Flujo completo desde frontend

### Skill aplicable

Cuando se decida usar Go, usar skill:
- `saicloud-planificacion` → evalúa y documenta decisión
- `saicloud-infraestructura-aws` → actualizado para soportar Go
- (Futuro) `saicloud-microservicio-go` → generación de código Go

### Ejemplo: Agente Saiopen (caso validado)

✅ **Justificación:**
- Criterio 3: Ejecutable standalone que corre en PC del cliente
- Requiere bajo consumo de recursos (PCs antiguos)
- Binario sin dependencias externas
- No cambia frecuentemente

**Implementación:**
```
backend/microservices/saiopen-agent/
├── main.go                 # CLI entrypoint
├── sync/
│   ├── firebird.go        # Conexión a Firebird
│   ├── api.go             # Llamadas a Django
│   └── sqs.go             # Comunicación SQS
├── config/
│   └── config.go          # Variables de entorno
├── go.mod
├── Dockerfile             # Build multi-stage
└── README.md              # Documentación de instalación
```

**Comunicación:**
1. Agente lee Firebird local
2. Envía a SQS mensaje cifrado
3. Django worker procesa mensaje
4. Respuesta vía SQS o polling API

### Reglas de código para Go

Cuando generes código Go:

1. **Estructura de handlers similar a Django views:**
   ```go
   // Similar a Django view function
   func CreateOrder(c *gin.Context) {
       // Validación (como Django serializer)
       // Lógica (como Django service)
       // Response (como DRF Response)
   }
   ```

2. **Logging estructurado:**
   ```go
   log.WithFields(log.Fields{
       "user_id": userID,
       "action": "create_order",
   }).Info("Order created successfully")
   ```

3. **Error handling explícito:**
   ```go
   if err != nil {
       log.WithError(err).Error("Failed to create order")
       c.JSON(500, gin.H{"error": "Internal server error"})
       return
   }
   ```

4. **Config desde env (como Django):**
   ```go
   type Config struct {
       DatabaseURL string `env:"DATABASE_URL,required"`
       JWTSecret   string `env:"JWT_SECRET,required"`
   }
   ```

### Documentación requerida

Cada microservicio Go DEBE tener `README.md` con:

```markdown
# [Nombre del Microservicio]

## Justificación técnica
[Por qué este servicio está en Go y no en Django]

## Criterios cumplidos
- [ ] Alta concurrencia: [detalles]
- [ ] Procesamiento intensivo: [detalles]
- [ ] Ejecutable standalone: [detalles]
- [ ] Optimización de costos: [ahorro proyectado]

## Contrato API
[Endpoints, inputs, outputs]

## Comunicación con Django
[REST/SQS/gRPC + auth]

## Deploy
[Instrucciones específicas]

## Métricas
[Cómo medir éxito]
```

### Checklist antes de aprobar Go

Antes de generar código Go para un microservicio:

- [ ] ¿Cumple al menos 1 criterio de los 4?
- [ ] ¿La alternativa Django+Celery fue considerada?
- [ ] ¿La justificación está documentada?
- [ ] ¿El contrato API está definido?
- [ ] ¿El usuario aprobó la complejidad adicional?
- [ ] ¿Hay plan de métricas para validar el beneficio?

**Si alguna respuesta es NO → Recomienda Django.**

## Documentación Base del Proyecto

Hay 5 documentos Word en `docs/base-reference/` con información técnica general:

1. **AWS_Setup_SaiSuite_v1.docx** → Infraestructura AWS
2. **Esquema_BD_SaiSuite_v1.docx** → Diseño de base de datos
3. **Estandares_Codigo_SaiSuite_v1.docx** → Convenciones de código
4. **Flujo_Feature_SaiSuite_v1.docx** → Metodología de desarrollo
5. **Infraestructura_SaiSuite_v2.docx** → Arquitectura del sistema

**Cuándo consultarlos:**
- Al configurar nuevos servicios AWS → AWS_Setup
- Al diseñar modelos de BD → Esquema_BD
- Al escribir código → Estandares_Codigo
- Al seguir metodología → Flujo_Feature
- Al entender arquitectura → Infraestructura

Estos NO reemplazan la documentación por feature.
Cada feature genera su propia documentación en `docs/plans/`, `docs/technical/`, etc.

## Documentación Base
Ver docs/base-reference/ para docs técnicos generales del proyecto.
