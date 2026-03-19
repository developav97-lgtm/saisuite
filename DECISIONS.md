# DECISIONS.md — Registro de Decisiones Arquitectónicas
# SaiSuite | ValMen Tech

## Propósito

Este archivo documenta **decisiones arquitectónicas significativas** del proyecto.
Cada decisión tiene un ID único (DEC-XXX) para referencia cruzada en código y docs.

**Instrucciones para Claude:**
- Leer este archivo antes de tomar decisiones de diseño
- Si la decisión ya existe → respetarla
- Si tomas una decisión nueva → agregarla ANTES de continuar con código
- Usar el template al final del archivo

---

## 2026-03-18 DEC-011: Angular Material como UI Framework (Supersede DEC-007)
**Contexto:** PrimeNG 18 tiene incompatibilidades fundamentales con Angular 20 (ɵɵInputTransformsFeature eliminado, afecta 80+ componentes). PrimeNG 20 LTS muestra warning de licencia comercial.
**Opciones consideradas:** Parche postinstall (frágil en Docker CI), mantener PrimeNG, migrar a Angular Material
**Decisión:** Migrar a Angular Material 20
**Razón:** Mismo vendor que Angular (Google), garantía de compatibilidad perpetua, MIT license, sin parches ni hacks
**Consecuencia:** Reemplazar todos los componentes PrimeNG. DEC-007 queda obsoleta.

---

## Índice de Decisiones

- [DEC-001](#dec-001-estrategia-multi-tenant) - Estrategia Multi-tenant (2026-03)
- [DEC-002](#dec-002-uuids-como-primary-keys) - UUIDs como Primary Keys (2026-03)
- [DEC-003](#dec-003-mapeo-firebird-sai_key) - Mapeo Firebird → sai_key (2026-03)
- [DEC-004](#dec-004-sesiones-jwt-postgresql) - Sesiones JWT en PostgreSQL (2026-03)
- [DEC-005](#dec-005-n8n-self-hosted) - n8n Self-Hosted en ECS (2026-03)
- [DEC-006](#dec-006-deploy-manual-fase-1) - Deploy Manual en Fase 1 (2026-03)
- [DEC-007](#dec-007-primeng-ui-framework) - PrimeNG como UI Framework (2026-03-11)
- [DEC-008](#dec-008-arquitectura-hibrida-django-go) - Arquitectura Híbrida Django+Go (2026-03-12)
- [DEC-009](#dec-009-estructura-documentacion) - Estructura de Documentación (2026-03-14)
- [DEC-010](#dec-010-snake_case-en-api-y-typescript) - snake_case en API y TypeScript (2026-03-17)

---

## DEC-001: Estrategia Multi-tenant
**Fecha:** 2026-03-01  
**Estado:** Activa

### Contexto
SaiSuite sirve a múltiples empresas cliente desde una sola instancia. Necesitábamos
elegir la estrategia de aislamiento de datos entre tenants.

### Opciones Evaluadas
1. **Base de datos separada por cliente**
   - Máximo aislamiento
   - Complejidad operacional alta (backups, migraciones)
   - Costo de infraestructura escalado linealmente

2. **Schema PostgreSQL por cliente**
   - Buen aislamiento
   - Migraciones complejas (N schemas)
   - Queries cross-tenant imposibles

3. **Single database con company_id (ELEGIDA)**
   - Simple de operar
   - Escalable hasta ~500 empresas
   - Un solo punto de backup
   - Riesgo de data leak si filtro falla

### Decisión
Single database con `company_id` en todas las tablas de negocio.
El `CompanyManager` custom filtra automáticamente por empresa en cada query.

### Razón
La escala inicial (hasta 200 empresas) no justifica la complejidad de esquemas
separados. El riesgo de data leak se mitiga con:
- Manager custom que SIEMPRE filtra por company_id
- Tests de permisos obligatorios
- Auditoría de queries en logs

### Consecuencias
- ✅ **Positivas:**
  - Setup simple y rápido
  - Backups centralizados
  - Queries cross-tenant posibles (analytics agregados)
  
- ⚠️ **Negativas:**
  - Riesgo de data leak si filtro falla
  - Performance puede degradarse con >500 tenants
  
- 🔧 **Mitigaciones:**
  - TODO modelo de negocio DEBE heredar de `BaseModel`
  - NUNCA usar `.objects.all()` directo, siempre via Manager
  - Tests obligatorios de aislamiento por tenant

### Criterios de Revisión
Revisar si:
- Se alcanza >300 empresas activas
- Performance de queries degrada >200ms
- Se requiere cumplimiento regulatorio que exija aislamiento físico

---

## DEC-002: UUIDs como Primary Keys
**Fecha:** 2026-03-01  
**Estado:** Activa

### Contexto
Elegir el tipo de Primary Key para los modelos de negocio expuestos por API.

### Opciones Evaluadas
1. **Entero autoincremental**
   - Simple y eficiente en índices
   - Expone volumen del negocio (sequence gaps)
   - Colisiones al sincronizar con Saiopen

2. **UUID v4 (ELEGIDA)**
   - Sin colisiones entre sistemas
   - No expone información de negocio
   - Compatible con sync multi-fuente
   - Ligeramente más lento en índices (~10%)

### Decisión
UUID v4 en todos los modelos expuestos por API.

### Razón
Saiopen genera sus propios IDs (numéricos o compuestos). Si usáramos enteros
autoincrementales, tendríamos colisiones al sincronizar.

UUID también oculta el volumen de registros a usuarios externos (seguridad
por oscuridad).

### Consecuencias
- ✅ **Positivas:**
  - Sincronización sin colisiones
  - IDs generables offline (en agente Saiopen)
  - Ocultamiento de volumen de negocio
  
- ⚠️ **Negativas:**
  - Índices UUID ~10% más lentos que INT
  - URLs más largas
  
- 🔧 **Implementación:**
  - Todos los modelos heredan de `BaseModel`
  - `BaseModel` usa `UUIDField(primary_key=True, default=uuid4)`
  - Modelos Firebird tienen campo adicional `sai_key` con ID original

### Criterios de Revisión
No revisar — decisión permanente por compatibilidad con APIs ya publicadas.

---

## DEC-003: Mapeo Firebird → sai_key
**Fecha:** 2026-03-01  
**Estado:** Activa

### Contexto
Las facturas y pedidos en Firebird tienen llaves compuestas de 4 campos:
`(empresa, sucursal, tipo, numero)`. Django no soporta PKs compuestas.

### Opciones Evaluadas
1. **Mapear cada campo por separado (4 columnas)**
   - Queries complejas con 4 joins
   - Difícil de indexar
   
2. **Concatenar en string separado por pipe (ELEGIDA)**
   - Formato: `"1|1|FV|100245"`
   - Simple de construir y consultar
   - Indexable como VARCHAR

### Decisión
Concatenar como string en campo `sai_key` con formato: `"empresa|sucursal|tipo|numero"`.

### Razón
- Simple de construir en el agente
- Simple de consultar: `sai_key="1|1|FV|100245"`
- Indexable con `unique_together(company, sai_key)`
- El separador `|` no aparece en ningún campo de Saiopen

### Consecuencias
- ✅ **Positivas:**
  - Queries simples
  - Construcción trivial
  - Index único compound fácil
  
- 🔧 **Implementación:**
  - El agente DEBE construir `sai_key` antes de enviar a SQS
  - Django valida formato en serializer
  - Índice: `unique_together = [('company', 'sai_key')]`

### Criterios de Revisión
No revisar — formato ya en producción con agente.

---

## DEC-004: Sesiones JWT en PostgreSQL
**Fecha:** 2026-03-01  
**Estado:** Activa

### Contexto
Necesitábamos revocación activa de tokens JWT (logout inmediato).
La solución estándar usa Redis como store de sesiones.

### Opciones Evaluadas
1. **Redis (ElastiCache)**
   - Rápido (<1ms)
   - ~$15-25/mes adicionales
   - Complejidad de setup
   
2. **PostgreSQL tabla `active_sessions` (ELEGIDA)**
   - Cero costo adicional
   - Query ~5ms con índice correcto
   - Mismo backup que el resto

### Decisión
Tabla `active_sessions` en PostgreSQL con índice en `(company_id, last_seen_at)`.

### Razón
Con <80 empresas, el COUNT de sesiones activas por empresa es <5ms con el índice.
Redis se añade en Fase 2 si aparece latencia real medida.

### Consecuencias
- ✅ **Positivas:**
  - Sin costo adicional
  - Sin dependencia nueva
  - Backup incluido
  
- ⚠️ **Negativas:**
  - Latencia ~5ms vs <1ms Redis
  - No escala a >1000 empresas
  
- 🔧 **Implementación:**
  - Logout borra JTI de `active_sessions`
  - Tarea horaria limpia sesiones con `last_seen_at > 30 min`
  - Índice: `CREATE INDEX idx_sessions ON active_sessions(company_id, last_seen_at)`

### Criterios de Revisión
Migrar a Redis si:
- Latencia de login/logout >50ms (p95)
- >200 empresas activas
- >500 sesiones concurrentes

---

## DEC-005: n8n Self-Hosted en ECS
**Fecha:** 2026-03-01  
**Estado:** Activa

### Contexto
n8n tiene versión cloud ($20-50/mes) y versión self-hosted (gratis en ejecuciones).

### Opciones Evaluadas
1. **n8n Cloud**
   - Sin mantenimiento
   - Límite de ejecuciones
   - Costo mensual fijo
   
2. **n8n Self-Hosted en ECS (ELEGIDA)**
   - Ejecuciones ilimitadas
   - Control total
   - Requiere gestión

### Decisión
Self-hosted en ECS Fargate como container separado.

### Razón
Los workflows de SaiSuite se ejecutan frecuentemente (alertas de cartera,
notificaciones, sync events). El costo por ejecución en cloud escalaría rápidamente.

### Consecuencias
- ✅ **Positivas:**
  - Ejecuciones ilimitadas
  - Control total de workflows
  - Sin vendor lock-in
  
- ⚠️ **Negativas:**
  - Requiere gestión de updates
  - Sin soporte directo
  
- 🔧 **Implementación:**
  - n8n NO expuesto a internet en Fase 1 (SSH tunnel)
  - Django se comunica vía webhook interno (VPC)
  - Workflows versionados en `n8n/workflows/`

### Criterios de Revisión
Revisar si:
- Gestión de n8n toma >2 horas/semana
- Necesitamos soporte empresarial

---

## DEC-006: Deploy Manual en Fase 1
**Fecha:** 2026-03-01  
**Estado:** Activa

### Contexto
¿Automatizar el deploy desde el inicio o hacerlo manual?

### Opciones Evaluadas
1. **CI/CD desde día 1**
   - Setup toma ~3 días
   - Deploys automatizados
   
2. **Deploy manual (~8 min) en Fase 1 (ELEGIDA)**
   - Setup inmediato
   - Suficiente para <2 deploys/semana

### Decisión
Deploy manual en Fase 1. GitHub Actions + OIDC en Fase 2.

### Razón
Setup de CI/CD toma tiempo que en Fase 1 es mejor invertir en producto.
Con <2 deploys por semana, el deploy manual es manejable.

### Consecuencias
- ✅ **Positivas:**
  - Tiempo invertido en features
  - Menos complejidad inicial
  
- 🔧 **Implementación:**
  - Documentado en `docs/base-reference/AWS_Setup_SaiSuite_v1.docx`

### Criterios de Revisión
Activar CI/CD cuando:
- >2 deploys por semana
- Se incorpore un segundo desarrollador

---

## DEC-007: PrimeNG como UI Framework
**Fecha:** 2026-03-11  
**Estado:** Activa

### Contexto
El frontend Angular necesita un framework de componentes UI para construir
las pantallas del ERP (tablas, formularios, diálogos, notificaciones).

### Opciones Evaluadas
1. **Angular Material**
   - Nativo de Angular
   - Personalización de tema limitada
   - Dark mode complejo
   
2. **Bootstrap / ng-bootstrap**
   - Conocido
   - Integración menos nativa con Angular
   
3. **Tailwind CSS puro**
   - Flexible
   - Sin componentes ERP listos
   
4. **PrimeNG (ELEGIDA)**
   - Componentes ERP completos
   - Sistema de temas propio
   - Dark mode nativo

### Decisión
PrimeNG con preset `Aura` customizado (`SaicloudPreset`).
Paleta de azules corporativos ValMen Tech.
Dark mode via clase `.app-dark` en `<html>`.

### Razón
PrimeNG tiene los componentes que SaiSuite necesita listos para producción:
- `p-table` con paginación server-side
- `p-dialog`, `p-confirmdialog`
- `p-toast` para notificaciones
- Sistema de temas permite personalización profunda

### Consecuencias
- ✅ **Positivas:**
  - Componentes ERP listos
  - Dark mode incluido
  - Tema corporativo personalizable
  
- ⚠️ **Negativas:**
  - Vendor lock-in ligero
  - Menos flexible que Tailwind puro
  
- 🔧 **Implementación:**
  - NUNCA usar Angular Material, Bootstrap ni Tailwind
  - HEX corporativos ValMen Tech pendientes de recibir
  - Hasta entonces: tokens `{blue.X}` del preset base
  - Al recibir colores: actualizar `app.config.ts`

### Criterios de Revisión
No revisar — decisión permanente por código ya escrito.

---

## DEC-008: Arquitectura Híbrida Django+Go
**Fecha:** 2026-03-12  
**Estado:** Activa

### Contexto
Durante la evaluación de costos AWS, se identificó que ciertos procesos específicos
podrían beneficiarse de Go por menor consumo de recursos y mejor performance en
concurrencia. Sin embargo, reescribir todo sería contraproducente.

### Opciones Evaluadas
1. **Mantener Django puro**
   - Toda la lógica en Django + DRF
   - Skills ya desarrolladas
   - Ecosistema maduro
   
2. **Reescribir todo en Go**
   - Performance óptimo
   - Perder velocidad de desarrollo
   - Abandonar skills Django
   
3. **Arquitectura híbrida (ELEGIDA)**
   - Django como backend principal
   - Microservicios Go estratégicos
   - Mejor de ambos mundos

### Decisión
Arquitectura híbrida con Django como núcleo y microservicios Go para casos específicos.

### Django será el núcleo para:
- CRUD de entidades de negocio
- Autenticación y autorización (JWT, permisos)
- Panel de administración
- Integraciones con n8n vía webhooks
- Lógica de negocio estándar
- APIs REST principales

### Go SOLO cuando se cumpla AL MENOS UNO de estos criterios:

#### 1. Alta concurrencia sostenida
- >1000 req/s simultáneas
- WebSockets con miles de conexiones persistentes
- Streaming de datos en tiempo real

**Ejemplo válido:** Servicio de notificaciones push en tiempo real

#### 2. Procesamiento intensivo con bajo consumo de memoria
- Workers de procesamiento batch
- Transformación de grandes volúmenes de datos
- Cálculos matemáticos pesados

**Ejemplo válido:** Procesamiento de importaciones masivas (50k+ productos)

#### 3. Agentes locales o CLI tools
- Ejecutables standalone sin dependencias pesadas
- Agentes que corren en PC cliente
- Tools de migración o sincronización

**Ejemplo válido:** Agente Saiopen-Saicloud ✅ (ya identificado)

#### 4. Optimización de costos demostrada
- El proceso corre 24/7 y consume >$300/mes
- Métricas reales muestran que Go reduce costos >50%
- ROI del desarrollo se recupera en <6 meses

**Ejemplo válido:** Worker de sincronización continua con Saiopen

### ❌ NO usar Go para:
- CRUD estándar de entidades
- APIs REST simples
- Lógica de negocio que cambia frecuentemente
- Procesos que pueden ser async con Celery
- Casos donde no hay métricas que demuestren necesidad

### Razón
Django es más rápido de desarrollar (menos tiempo = menor costo).
Admin panel viene gratis. Ecosystem más maduro para APIs REST.
Go solo donde los beneficios justifican la complejidad.

### Consecuencias
- ✅ **Positivas:**
  - Flexibilidad para optimizar partes críticas sin reescribir todo
  - Mejor aprovechamiento de fortalezas de cada tecnología
  - Costos optimizados donde realmente importa
  - Mantiene velocidad de desarrollo con Django + Claude Code
  
- ⚠️ **Negativas:**
  - Mayor complejidad de infraestructura (más servicios que monitorear)
  - Requiere skills adicionales de Go
  - Comunicación entre servicios (HTTP/gRPC/SQS)
  - Más surface area para debugging
  
- 🔧 **Mitigaciones:**
  - Cada microservicio Go DEBE tener justificación documentada
  - Comunicación vía APIs REST bien definidas o SQS
  - Logging estructurado en ambos lenguajes (JSON)
  - Métricas centralizadas (CloudWatch)

### Tecnologías Go Aprobadas:
- **Framework web:** Gin o Echo
- **ORM (si aplica):** GORM
- **Base de datos:** Misma PostgreSQL del proyecto
- **Auth:** Validación de JWT (compatible con Django simplejwt)
- **Deployment:** Docker + ECS Fargate

### Integración:
```
Django Backend (Puerto 8000)
    ↓
    ├─→ PostgreSQL (compartida)
    ├─→ Redis (compartido)
    └─→ Go Microservice (Puerto 8001+)
            ↓
            ├─→ Comunicación: REST o SQS
            ├─→ Auth: JWT validado
            └─→ Logs: JSON a CloudWatch
```

### Proceso de Decisión para Nuevos Features:
1. **Planificación:** Skill `saicloud-planificacion` evalúa criterios
2. **Si aplica Go:** Se documenta justificación técnica + económica
3. **Diseño API:** Contrato claro entre Django y Go
4. **Desarrollo:** Skills Go complementan skills Django
5. **Testing:** Pruebas de integración entre servicios
6. **Deploy:** Mismo pipeline CI/CD, contenedores separados

### Versionamiento:
- Microservicios Go en `backend/microservices/[nombre-servicio]/`
- Cada uno con su Dockerfile
- docker-compose.yml incluye todos los servicios

### Criterios de Revisión
Esta decisión será exitosa si:
- Logramos optimizar costos en procesos específicos (>30% ahorro)
- NO ralentizamos el desarrollo general del producto
- La complejidad agregada se justifica con métricas reales

Revisar cada 6 meses o cuando:
- Se identifique un nuevo caso de uso para Go
- Los costos de infraestructura cambien significativamente
- Surjan nuevas tecnologías que simplifiquen la arquitectura

---

## DEC-009: Estructura de Documentación
**Fecha:** 2026-03-14  
**Estado:** Activa

### Contexto
Necesitábamos organizar documentación de manera que sirviera tanto para:
- Desarrolladores (docs técnicas)
- Usuarios finales (guías)
- Chat IA de soporte (base de conocimiento RAG)

Ya teníamos 5 documentos Word generales del proyecto.

### Opciones Evaluadas
1. **Todo en Notion**
   - Colaborativo
   - Requiere conexión
   - No versionado con código
   
2. **Todo en repo (ELEGIDA)**
   - Versionado con código
   - Offline-first
   - Sincronizable con Notion

### Decisión
Estructura dual:
- **Docs base (generales):** `docs/base-reference/` → 5 archivos Word originales
- **Docs por feature:** `docs/plans/`, `docs/technical/`, `docs/user/`, `docs/knowledge-base/`

### Razón
Los 5 .docx son referencias generales del proyecto (infraestructura, estándares, etc.).
Cada feature genera su propia documentación específica para:
- API (OpenAPI spec)
- Arquitectura (diagramas)
- Usuario (guías paso a paso)
- Chat IA (chunks para RAG)

### Consecuencias
- ✅ **Positivas:**
  - Docs base versionadas con proyecto
  - Docs por feature auto-generadas con skill
  - Base de conocimiento lista para chat IA
  - Sincronización automática con Notion vía Cowork
  
- 🔧 **Implementación:**
  - Docs base en `docs/base-reference/` (no se regeneran)
  - Skill `saicloud-documentacion` genera docs por feature
  - Script `verify-docs.sh {feature}` valida completitud
  - Cowork sincroniza con Notion automáticamente

### Criterios de Revisión
Revisar estructura si:
- Se acumulan >50 features (subdirectorios por módulo)
- Notion deja de ser la plataforma colaborativa principal

---

## DEC-010: snake_case en API y TypeScript
**Fecha:** 2026-03-17
**Estado:** Activa

### Contexto
Al diseñar el Módulo de Proyectos, se necesitaba decidir la convención de nombres para
campos de la API Django y las interfaces TypeScript del frontend Angular.

### Opciones Evaluadas
1. **camelCase en frontend, snake_case en backend**
   - Convención "correcta" por lenguaje
   - Requiere capa de transformación (interceptor HTTP) o configuración DRF
   - Complejidad adicional

2. **snake_case en todo (ELEGIDA)**
   - Consistencia total API ↔ TypeScript
   - Sin transformación necesaria
   - Menos código, menos errores

### Decisión
snake_case en todos los campos de la API DRF y en todas las interfaces TypeScript.
No hay capa de transformación camelCase↔snake_case.

### Razón
La transformación camelCase↔snake_case agrega complejidad (interceptor, mapeos) sin
beneficio real. Los campos del backend Django son snake_case por convención Python.
Mantenerlos en TypeScript simplifica el desarrollo y elimina bugs de transformación.

### Consecuencias
- ✅ **Positivas:**
  - Sin interceptor de transformación
  - Interfaces TS espejan exactamente los serializers DRF
  - Menos código, menos bugs

- ⚠️ **Negativas:**
  - snake_case en TypeScript no es la convención JS/TS estándar
  - Linters JS podrían advertir sobre nombres de campos

- 🔧 **Implementación:**
  - Interfaces TS: `fecha_inicio_planificada`, `cliente_id`, `presupuesto_total`, etc.
  - DRF serializers: sin `to_representation` ni `to_camel_case`
  - Aplicar a TODOS los módulos futuros del proyecto

### Criterios de Revisión
No revisar — decisión permanente. Cambiar requeriría actualizar todas las interfaces
y serializers del proyecto.

---

## 2026-03-19 DEC-012: Sistema de Consecutivos Configurables
**Fecha:** 2026-03-19
**Estado:** Activa

### Contexto
Proyectos y Actividades necesitaban códigos auto-generados con prefijos distintos por tipo
(PRY-0001 para proyectos tipo 'otro', OBR-0001 para 'obra_civil', MAT-0001 para materiales, etc.)
El sistema anterior usaba un simple contador secuencial con prefijo fijo ('PRY-' para todo).

### Opciones Evaluadas
1. **Prefijos hardcodeados en services.py por tipo**
   - Rápido de implementar
   - No configurable sin código
   - No extensible a otras entidades (facturas, etc.)

2. **Modelo ConfiguracionConsecutivo en apps/core (ELEGIDA)**
   - Configurable desde UI sin deployar
   - Extensible a cualquier entidad/subtipo
   - SELECT FOR UPDATE garantiza unicidad en concurrencia
   - Fallback al generador anterior si no hay config

### Decisión
Modelo `ConfiguracionConsecutivo` en `apps/core` con campos: `entidad`, `subtipo`, `prefijo`,
`ultimo_numero`, `formato` (template Python). Función `generar_consecutivo()` en `apps/core/services.py`
con `select_for_update()`. CRUD en `/api/v1/core/consecutivos/`. Panel admin en `/admin/consecutivos`.

### Razón
La configurabilidad sin deploy es clave para un SaaS multi-tenant donde cada empresa puede
necesitar formatos distintos. El `select_for_update()` es obligatorio para garantizar que
dos usuarios simultáneos no generen el mismo código.

### Consecuencias
- ✅ **Positivas:**
  - Consecutivos configurables por empresa sin deploy
  - Un solo mecanismo para todas las entidades (proyectos, actividades, facturas futuras)
  - Concurrencia segura con `select_for_update()`
  - Fallback automático si no hay configuración activa

- ⚠️ **Negativas:**
  - Una query extra por creación de proyecto/actividad
  - Requiere seed de datos por empresa nueva

- 🔧 **Implementación:**
  - `unique_together = [('company', 'entidad', 'subtipo')]`
  - `subtipo = ''` captura entidades sin subtipo específico
  - Seed: `scripts/create_consecutivos_demo.py`
  - El campo `codigo` en los formularios es **readonly** — siempre auto-generado
  - Hint muestra preview del próximo código al seleccionar tipo

### Criterios de Revisión
Revisar si se necesita reset de consecutivos por periodo (año, mes).

---

## 📝 Template para Nuevas Decisiones

```markdown
## DEC-XXX: [Título Corto]
**Fecha:** YYYY-MM-DD  
**Estado:** [Activa | Supersedida | En revisión]

### Contexto
[Por qué se necesitaba tomar esta decisión]

### Opciones Evaluadas
1. **Opción A**
   - Ventaja 1
   - Desventaja 1
   
2. **Opción B (ELEGIDA)**
   - Ventaja 1
   - Desventaja 1

### Decisión
[Qué se eligió exactamente]

### Razón
[Por qué esta opción sobre las demás]

### Consecuencias
- ✅ **Positivas:**
  - ...
  
- ⚠️ **Negativas:**
  - ...
  
- 🔧 **Mitigaciones/Implementación:**
  - ...

### Criterios de Revisión
[Cuándo revisar esta decisión]
```

---

## Historial de Cambios

- **2026-03-14:** Estandarización de formato a DEC-XXX con contexto completo
- **2026-03-12:** Agregada DEC-008 (Arquitectura Híbrida Django+Go)
- **2026-03-11:** Agregada DEC-007 (PrimeNG UI Framework)
- **2026-03-01:** Decisiones iniciales DEC-001 a DEC-006