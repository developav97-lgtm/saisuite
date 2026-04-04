## DEC-046: OpenAI gpt-4o-mini para CFO Virtual (en lugar de Anthropic Claude)
**Fecha:** 2026-04-03
**Estado:** ✅ Decidido

**Contexto:** El CFO Virtual del módulo SaiDashboard necesita un modelo de lenguaje para responder preguntas financieras. El plan original (PROMPT-CLAUDECODE-SAIDASHBOARD.md) asumía Claude API de Anthropic.

**Opciones consideradas:**
1. **Claude (Anthropic)** — Alta calidad, pero requiere suscripción adicional
2. **OpenAI gpt-4o-mini** — Precio muy bajo (~$0.15/M tokens input), suficiente para análisis financiero de PyMEs, API key ya disponible en el proyecto

**Decisión:** OpenAI `gpt-4o-mini` vía workflow n8n.

**Razón:** Costo 10x menor que modelos equivalentes de Anthropic para el caso de uso (respuestas de análisis financiero ~500 tokens). La empresa ya tiene API key de OpenAI activa.

**Implementación:**
- Workflow n8n: `n8n/workflows/cfo-virtual.json`
- Key en `.env` raíz (gitignored): `OPENAI_API_KEY`
- n8n la recibe como `$env.OPENAI_API_KEY`

**Consecuencias:** Si en el futuro se quiere cambiar de modelo, solo se modifica el nodo HTTP en n8n, sin tocar Django ni Angular.

**Criterios de revisión:** Si gpt-4o-mini da respuestas insuficientes para análisis complejos, evaluar gpt-4o o Claude Sonnet.

---

## DEC-042: ngx-echarts como librería de gráficos para SaiDashboard
**Fecha:** 2026-04-01
**Estado:** ✅ Decidido

**Contexto:** El módulo SaiDashboard necesita gráficos financieros avanzados (barras, líneas, torta, waterfall, gauge, área) para dashboards de BI.

**Opciones consideradas:**
1. **Chart.js** — Popular, liviano, pero limitado para waterfall y gauge
2. **ApexCharts** — Bueno, pero sin wrapper oficial para Angular 18
3. **D3.js** — Muy bajo nivel para MVP, alto esfuerzo de desarrollo
4. **ngx-echarts (Apache ECharts)** — Wrapper Angular oficial, soporte completo de series financieras

**Decisión:** ngx-echarts (Apache ECharts wrapper para Angular 18).

**Razón:** Soporte nativo para waterfall, gauge, heatmap y series financieras. Wrapper Angular mantenido. Mejor rendimiento con grandes datasets. Licencia Apache 2.0.

**Consecuencias:** Instalar `echarts` + `ngx-echarts` como dependencias npm. Todos los gráficos del módulo Dashboard usan ECharts exclusivamente.

---

## DEC-043: Estrategia de almacenamiento GL — Denormalizado en PostgreSQL
**Fecha:** 2026-04-01
**Estado:** ✅ Decidido

**Contexto:** El movimiento contable (GL) de Saiopen tiene mucha data y Firebird 2.5 se lentifica cuando hay usuarios activos. Los reportes del dashboard no deben afectar el ERP local.

**Opciones consideradas:**
1. **Consultar Firebird en tiempo real** — Afecta rendimiento del ERP, latencia alta
2. **Joins en PostgreSQL en tiempo de consulta** — Normalizado, requiere joins en cada reporte
3. **TimescaleDB** — Añade complejidad operacional sin beneficio claro para este volumen
4. **Denormalizado en PostgreSQL** — Todos los joins pre-calculados, índices compuestos

**Decisión:** Almacenar movimientos GL completamente denormalizados en PostgreSQL (modelo `MovimientoContable` con todos los joins pre-calculados del sql_gl.txt).

**Razón:** Elimina joins en tiempo de consulta de reportes. La data GL es append-only (nunca se modifica retroactivamente en contabilidad colombiana). Los índices compuestos permiten queries rápidas para los KPIs del dashboard.

**Consecuencias:** Mayor consumo de almacenamiento (~2x vs normalizado), pero consultas de reporte en <100ms para empresas PyME (~500K registros). La sincronización usa `bulk_create(update_conflicts=True)`.

---

## DEC-044: Agente Go para sync Saiopen — Criterio 3 cumplido
**Fecha:** 2026-04-01
**Estado:** ✅ Decidido

**Contexto:** Se necesita extraer datos contables de Firebird 2.5 (instalado en el PC Windows del cliente) y enviarlos a Saicloud (PostgreSQL en AWS).

**Opciones consideradas:**
1. **Django management command** — Requiere instalar Python en la PC del cliente, más pesado
2. **Agente Python standalone** — Posible con PyInstaller, pero binario de ~100MB
3. **Agente Go compilado** — Binario standalone de ~15MB, sin dependencias

**Decisión:** Agente Go compilado como ejecutable standalone para Windows.

**Razón:** Cumple Criterio 3 de CLAUDE.md sección 10: "Ejecutables standalone — agentes que corren en PC del cliente, CLI tools sin dependencias pesadas, servicios que deben ser binarios compilados." El binario Go es ~15MB, no requiere runtime ni instalación de dependencias.

**Consecuencias:** El agente se compila con `GOOS=windows GOARCH=amd64`. Soporta múltiples bases de datos Firebird en el mismo servidor. Incluye configurador web embebido (go:embed) para que el implementador configure sin editar JSON a mano.

---

## DEC-045: ModuleTrial como modelo independiente
**Fecha:** 2026-04-01
**Estado:** ✅ Decidido

**Contexto:** Las empresas pueden probar el módulo SaiDashboard por 14 días UNA sola vez antes de contratar. Se necesita un mecanismo de trial por módulo.

**Opciones consideradas:**
1. **Extender CompanyLicense con JSON de trials** — Complicaría migraciones existentes (DEC-030)
2. **Nuevo modelo ModuleTrial independiente** — Simple, aislado, unique_together(company, module_code)

**Decisión:** Modelo `ModuleTrial` independiente con `unique_together = (company, module_code)`.

**Razón:** CompanyLicense ya está estabilizado (DEC-030). Un trial usado nunca se elimina (registro permanente). El `unique_together` garantiza que cada empresa solo pueda activar UNA prueba por módulo.

**Consecuencias:** Flujo de acceso: 1) ¿'dashboard' in license.modules_included? → PERMITIR. 2) ¿Trial activo? → PERMITIR con banner. 3) ¿Trial vencido? → DENEGAR. 4) Sin trial → opción de activar.

---

## DEC-041: Estándar de Estructura de Documentación
**Fecha:** 2026-04-01
**Estado:** ✅ Aprobado

**Contexto:** La documentación del proyecto había crecido sin estructura: informes de ejecución en la raíz del proyecto, planes completados mezclados con activos, docs técnicas sin carpeta de módulo.

**Decisión:** Implementar el estándar definido en `docs/base-reference/ESTANDAR-DOCS.md`. Puntos clave:
1. Solo 5 archivos `.md` en la raíz: `CLAUDE.md`, `CONTEXT.md`, `DECISIONS.md`, `ERRORS.md`, `README.md`
2. Informes de ejecución → `docs/reports/`
3. Planes activos → `docs/plans/` | Planes completados → `docs/plans/historic/`
4. Docs técnicas por módulo → `docs/technical/[modulo]/`
5. `docs/plans/INDICE-PLANES.md` siempre actualizado

**Consecuencia:** Todo agente (Claude Code, Cowork) debe respetar esta estructura. Al generar informes, moverlos a `docs/reports/`. Al completar planes, moverlos a `docs/plans/historic/` y actualizar el índice.

**Nota para CLAUDE.md:** Se recomienda agregar una Sección 17 referenciando `docs/base-reference/ESTANDAR-DOCS.md` para que Claude Code conozca la estructura al generar archivos.

---

## DEC-030: Sistema de Licencias — Extender CompanyLicense vs nuevo modelo Licencia
**Fecha:** 2026-03-29
**Estado:** ✅ Decidido e implementado

**Contexto:** El plan de licencias requería historial, sesiones concurrentes, cuotas de mensajes/tokens IA y módulos por licencia. Existía ya `CompanyLicense` con campos básicos.

**Opciones consideradas:**
1. **Nuevo modelo `Licencia`** — reemplazar `CompanyLicense` con un modelo nuevo con `OneToMany` (historial de licencias)
2. **Extender `CompanyLicense` + nuevo `LicenseHistory`** — mantener la relación `OneToOne` empresa-licencia activa, agregar campos faltantes y crear tabla de historial separada

**Decisión:** Opción 2 — extender `CompanyLicense` con campos nuevos + crear `LicenseHistory`.

**Razón:**
1. `CompanyLicense` ya tenía migración, serializers y servicios — cambiar la FK rompería el historial de migraciones y los tests existentes.
2. El modelo de negocio es: una empresa tiene UNA licencia activa. El historial es auditoría, no estado.
3. Menor riesgo de ruptura de datos en producción.

**Consecuencia:** `CompanyLicense` ahora tiene `concurrent_users`, `modules_included` (JSON), `messages_quota/used`, `ai_tokens_quota/used`, `last_reset_date`, `created_by`. `LicenseHistory` registra cada cambio.

---

## DEC-031: Control de Sesiones — LicensePermission como DRF Permission vs Middleware WSGI
**Fecha:** 2026-03-29
**Estado:** ✅ Decidido e implementado

**Contexto:** Validar sesiones activas (session_id en JWT) y licencias en cada request autenticado.

**Opciones consideradas:**
1. **Django WSGI Middleware** — intercepta antes de que DRF procese el request
2. **DRF Permission Class (DEFAULT_PERMISSION_CLASSES)** — ya existe `LicensePermission`, extender con validación de sesión

**Decisión:** Opción 2 — extender `LicensePermission` existente para validar también `session_id`.

**Razón:** `LicensePermission` ya está en `DEFAULT_PERMISSION_CLASSES` y tiene acceso al `request.auth` (JWT payload). El middleware WSGI no tiene acceso a `request.auth` todavía (JWT se procesa después). Centraliza toda la lógica de acceso en un solo lugar.

**Consecuencia:** `LicensePermission` ahora también llama `SessionService.validate_session(session_id)` y `session.touch()` en cada request. Rutas exentas incluyen `/api/v1/admin/`.

---

## DEC-029: Automatización de Snapshots — Management Command vs Celery
**Fecha:** 2026-03-28
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #7 (BG-47) requería ejecutar snapshots semanales de presupuesto automáticamente. El plan original contemplaba una Celery task (`@shared_task`).

**Opciones consideradas:**
1. **Celery task** — requiere broker Redis/RabbitMQ + worker process, nada de esto existe en el stack
2. **Django management command** — invocable desde cron, AWS EventBridge, n8n o curl; cero dependencias nuevas

**Decisión:** Django management command `budget_weekly_snapshot`.

**Razón:** El stack actual no tiene broker (Redis no está en `docker-compose.yml` ni en settings). Agregar Celery solo para este proceso sería sobreingeniería. Un management command es suficiente para frecuencia semanal y puede dispararse síncronamente desde EventBridge o n8n.

**Consecuencia:** Si en el futuro se agrega Celery, el command se envuelve trivialmente: `call_command('budget_weekly_snapshot')` dentro de `@shared_task`. La migración no requiere cambiar la lógica del command.

**Scheduling recomendado:**
- AWS EventBridge: `cron(0 6 ? * MON *)`
- n8n: workflow cron → HTTP POST al endpoint de gestión interno
- Sistema: `0 6 * * 1 /app/manage.py budget_weekly_snapshot`

---

## DEC-028: EVM — Fórmula Simplificada vs Earned Value Completo
**Fecha:** 2026-03-28
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #7 (BG-29) requería métricas EVM (CPI, SPI, EAC, etc.). La fórmula estándar de EVM requiere un baseline detallado de planificación por período (baseline distribution), que no existe en el modelo de datos actual.

**Opciones consideradas:**
1. **EVM completo** — requiere `BaselinePeriod` con distribución de PV por semana/mes; modelo no existe
2. **EVM simplificado** — PV estimado linealmente, EV basado en porcentaje de avance de tareas

**Decisión:** EVM simplificado con estas fórmulas:
- `PV = BAC × (elapsed_days / total_days)` — valor planificado lineal
- `EV = BAC × avg(task.porcentaje_completado / 100)` — valor ganado real
- `AC` = costo real de timesheets + gastos
- Resto de métricas (CPI, SPI, EAC, ETC, TCPI, VAC) se calculan con las fórmulas estándar PMI

**Razón:** El modelo no tiene distribución de costos planificada por período. La aproximación lineal es suficiente para alertas tempranas y tendencias. Implementar la distribución completa es una feature independiente (Feature #8+).

**Consecuencia:** Los valores de PV son aproximados. Para proyectos con esfuerzo muy no-lineal, los índices SPI pueden ser engañosos. Se documenta esta limitación en la guía de usuario. Cuando se implemente `BaselinePeriod`, `EVMService.get_evm_metrics()` se actualiza sin cambiar la API.

---

## DEC-027: Gantt Overlay — Re-render completo vs patch DOM
**Fecha:** 2026-03-27
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #6 (SK-41) requería añadir overlays visuales sobre el Gantt (ruta crítica, holgura, baseline) sin reescribir Frappe Gantt.

**Opciones consideradas:**
- Opción A: Parchear el DOM del SVG de Frappe Gantt post-render para cambiar estilos/labels
- Opción B: Re-render completo de Frappe Gantt con `renderTasks` enriquecidos (`custom_class`, `name` con sufijos)

**Decisión:** Opción B — re-render completo vía `rerenderGantt()`.

**Razón:** Frappe Gantt no expone API de actualización granular por tarea. El parche DOM sería frágil ante actualizaciones de la librería y difícil de revertir. El re-render es más costoso (~50ms) pero simple, correcto y mantenible. Con debounce de 400ms en drag, no hay conflicto.

**Consecuencia:** `initGantt()` ahora delega a `rerenderGantt()`. El array `this.tasks` permanece como la fuente de verdad sin mutaciones; `renderTasks` es el array derivado temporal para cada render.

---

## DEC-026: DisableMigrations en testing.py — Fix SQLite FK enforcement
**Fecha:** 2026-03-27
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #6 Chunk 5 — Los tests de scheduling fallaban con `OperationalError: no such table: main.proyectos_tarea` porque la migración 0013 (`RenameModel Tarea→Task`) no actualiza FK constraints en SQLite. Django reconstruye el schema copiando tablas, pero deja referencias rotas en SQLite.

**Decisión:** Agregar `DisableMigrations` class en `backend/config/settings/testing.py` para que Django use `CREATE TABLE` directo desde el estado actual de los modelos, sin reproducir el historial de migraciones.

**Razón:** La alternativa (regenerar todas las migraciones) rompería el historial de producción. `DisableMigrations` es el patrón estándar de Django para entornos de test con SQLite que no soportan todas las operaciones de migración.

**Consecuencia:** Los tests no validan que las migraciones sean correctas. Los tests de integración en CI/CD contra PostgreSQL (producción) siguen corriendo con migraciones reales — eso es la validación real.

---

## DEC-023: Refactoring Completo — Renombrado Español → Inglés
**Fecha:** 2026-03-26
**Estado:** 🔄 En ejecución — rama `refactor/english-rename`
**Contexto:** El codebase de `apps/proyectos` usaba nombres en español para modelos, campos, enums y URLs. Decisión tomada por Juan David para estandarizar a inglés antes de escalar el equipo.

**Alcance aprobado:**
- D1 ✅ Campos en BD cambian (vía RenameField migrations)
- D2 ✅ URLs cambian `/proyectos/` → `/projects/` (con alias temporal por 1 release)
- D3 ✅ Valores de TextChoices en BD cambian (vía RunSQL data migrations)
- D4 ✅ `'proyectos'` en `companies_companymodule` cambia a `'projects'`

**Mapeo de clases:**
- Proyecto → Project, Tarea → Task, Fase → Phase, TareaDependencia → TaskDependency
- SesionTrabajo → WorkSession (db_table='sesiones_trabajo' se preserva)
- TimesheetEntry → sin cambio (ya en inglés)

**Decisiones de naming específicas:**
- `interventor` (RolTercero) → `inspector` (evita colisión con `supervisor`)
- Tarea.estado: `por_hacer`→`todo`, `en_progreso`→`in_progress`, `en_revision`→`in_review`
- WorkSession estados: `activa`→`active`, `pausada`→`paused`, `finalizada`→`finished`

**Consecuencia:** 27 tareas (REFT-01 a REFT-27), estimación 7-8 días. Ver `docs/plans/REFACTOR-TASK-BREAKDOWN.md`.

---

## DEC-024: Nueva Arquitectura de Navegación — Landing de Módulos
**Fecha:** 2026-03-26
**Estado:** 🔄 Pendiente implementación (REFT-22 a REFT-25)
**Contexto:** Sidebar global con todos los módulos no escala al crecer la plataforma.

**Decisión:** Post-login muestra landing de módulos (`/modulos`). Cada módulo tiene su propio sidebar contextual. Toggle Kanban/Lista con localStorage. Vista Cards de Proyectos con `mat-card`.

**Stack:** Angular Material únicamente — NUNCA PrimeNG.

---

## DEC-025: Definición de Sobreasignación de Recursos — Feature #4
**Fecha:** 2026-03-26
**Estado:** ✅ Decidido

**Contexto:** Feature #4 (Resource Management) requiere detectar cuándo un usuario tiene >100% de su capacidad asignada. Se evaluaron dos definiciones posibles.

**Opciones consideradas:**
- Opción A (Diaria): sobreasignado si la suma de `porcentaje_asignacion` en **cualquier día** del período supera 100%
- Opción B (Semanal): sobreasignado si el promedio semanal supera 100%

**Decisión:** Opción A — detección **diaria**.

**Razón:**
1. Dominio físico: en construcción, un recurso no puede estar en dos obras el mismo día. La sobreasignación diaria es un problema operativo real.
2. El algoritmo aprobado (`detect_overallocation_conflicts`) ya trabaja por día — es la implementación natural sin lógica adicional.
3. Conservador es mejor para MVP: mejor reportar conflictos de más (ignorables por el usuario) que ocultar conflictos reales.

**Consecuencia:** La función `detect_overallocation_conflicts(user_id, company_id, start_date, end_date, threshold=100.00)` reporta cada día donde `SUM(porcentaje_asignacion) > threshold`. El parámetro `threshold` es configurable para permitir flexibilización futura por empresa (ej: 110% para permitir horas extra). Los tests de `BK-27` deben cubrir: solapamiento parcial de días, fin de semana (sin asignación), threshold exactamente en 100%, y múltiples proyectos simultáneos.

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