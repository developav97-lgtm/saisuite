## DEC-067: Exportación BI = Excel + CSV únicamente (sin PDF)
**Fecha:** 2026-04-12
**Estado:** Decidido — Pendiente migrar frontend

**Contexto:** El módulo de Reportes BI V2 necesita exportación. La exportación PDF fue implementada en V1.

**Decisión:** Eliminar `export_pdf` del servicio BI para reportes BI. Solo Excel (.xlsx vía openpyxl) y CSV.

**Razón:** Las tablas BI pueden tener cientos de columnas y miles de filas. PDF no es formato adecuado. El export-menu del frontend ya soporta Excel/CSV.

**Consecuencia:** El endpoint `/export-pdf/` se mantiene en el router V1 hasta que se migre el frontend (2026-04-13: `report-bi.service.ts:73` aún llama al endpoint). Cuando se elimine del frontend, quitar de `urls.py` y `views.py`.

---

## DEC-066: Coexistencia ReportEngine + BIQueryEngine (migración gradual)
**Fecha:** 2026-04-12
**Estado:** Decidido

**Contexto:** Las 31 tarjetas existentes usan `ReportEngine`. BIQueryEngine V2 agrega capacidades multi-fuente.

**Decisión:** Las tarjetas legacy siguen usando `ReportEngine`. Solo el nuevo tipo `bi_report` usa `BIQueryEngine`. No se elimina ReportEngine.

**Razón:** Migración no-destructiva. Las tarjetas legacy están probadas y funcionan. Migrar 30+ métodos hardcodeados es un proyecto separado.

**Consecuencia:** Dos motores coexisten. `BIQueryEngine` es el motor futuro.

---

## DEC-065: Filtros en 3 capas para integración Dashboard ↔ BI
**Fecha:** 2026-04-12
**Estado:** Decidido

**Contexto:** Sprint 4 necesita que tarjetas BI en dashboard hereden pero puedan sobrescribir filtros.

**Decisión:** Capa 1 (ReportBI.filtros) → Capa 2 (DashboardCard.filtros_config override) → Capa 3 (Dashboard.filtros_default global). Nivel más externo gana para el mismo campo.

**Razón:** Permite filtros independientes por tarjeta más filtros globales del dashboard de forma transparente.

**Consecuencia:** El ReportBI original nunca se modifica. Los overrides son por tarjeta. Implementar en Sprint 4.

---

## DEC-064: JOINs multi-tabla vía Subquery + OuterRef (sin SQL crudo)
**Fecha:** 2026-04-12
**Estado:** Decidido

**Contexto:** Los modelos espejo de contabilidad no tienen FK entre sí. El motor BI necesita unir datos de múltiples fuentes.

**Decisión:** Los JOINs entre tablas sin FK Django se implementan con `Subquery(Model.objects.filter(company_id=OuterRef('company_id'), campo_join=OuterRef('campo_local')).values('campo')[:1])`.

**Razón:** La regla del proyecto prohíbe SQL crudo. `Subquery` es la única alternativa en Django ORM puro.

**Consecuencia:** Performance aceptable con índices existentes. Limitación: campos de fuente secundaria usados como dimensión (GROUP BY) requieren post-procesamiento en Python.

---

## DEC-063: Productos en BI = CrmProducto directamente
**Fecha:** 2026-04-12
**Estado:** Decidido

**Contexto:** El BI engine necesita una fuente de productos. `CrmProducto` ya existe con sync desde ITEM de Saiopen.

**Decisión:** Usar `crm.CrmProducto` como fuente en el BI engine sin crear modelo espejo `ItemSaiopen`.

**Razón:** Ya tiene sync desde ITEM, company FK, campos necesarios (codigo, nombre, precio_base, clase, grupo). Crear un espejo duplicaría datos sin beneficio.

**Consecuencia:** Import cross-app (`crm.CrmProducto`) desde `dashboard.bi_engine`. Aceptable porque es solo lectura.

---

## DEC-062: sai_key cotizacion CRM = "{numero}_{tipo}_{empresa}_{sucursal}"
**Fecha:** 2026-04-10
**Estado:** Decidido

**Contexto:** La PK de COTIZACI en Saiopen es compuesta por 4 campos (NUMERO + TIPO + ID_EMPRESA + ID_SUCURSAL). El campo `sai_key` de BaseModel es un CharField simple. Se necesita una representación única y legible.

**Decisión:** `sai_key = f"{sai_numero}_{sai_tipo}_{sai_empresa}_{sai_sucursal}"`. Unique_together con `company`.

**Consecuencias:** Trazabilidad directa. El agente retorna los 4 campos y Django construye el sai_key al confirmar sync.

---

## DEC-061: Permisos CRM sobre roles existentes — sin roles nuevos
**Fecha:** 2026-04-10
**Estado:** Decidido

**Contexto:** CRM necesita control de acceso. Opciones: (a) roles CRM específicos, (b) permisos Django sobre roles existentes.

**Decisión:** Opción (b). Se agregan permisos estándar Django (`view_*`, `add_*`, `change_*`, `delete_*`) + custom (`import_leads`, `sync_productos`, `export_pdf_cotizacion`) sobre los roles existentes: `company_admin` full, `seller` CRUD propio, `viewer` lectura.

**Consecuencias:** Empresas pueden crear sus propios roles en admin y asignar permisos CRM granularmente. Consistente con el resto de la plataforma.

---

## DEC-060: Cotización CRM → Saiopen solo al aceptar (AUTORIZADO='S')
**Fecha:** 2026-04-10
**Estado:** Decidido

**Contexto:** Saiopen no tiene estados de borrador en COTIZACI. CRM necesita ciclo de vida completo (Borrador → Enviada → Aceptada/Rechazada). Sincronizar borradores contaminaría Saiopen con cotizaciones incompletas.

**Decisión:** CRM gestiona ciclo completo internamente. Solo al cambiar a `aceptada` se hace push a Saiopen como COTIZACI con `AUTORIZADO='S'`. Si Saiopen anula (ANULAR cambia), el agente actualiza CRM a `anulada`.

**Consecuencias:** Saiopen solo recibe cotizaciones confirmadas. Hay un gap temporal entre aprobación en CRM y creación en Saiopen (tiempo de procesamiento SQS < 30s).

---

## DEC-059: Catálogo CRM = ITEM de Saiopen (unidireccional Saiopen→CRM)
**Fecha:** 2026-04-10
**Estado:** Decidido

**Contexto:** Los productos son gestionados en Saiopen. CRM necesita un catálogo para cotizaciones. "Bidireccional" confirmado por PO = cambios en ITEM llegan al CRM automáticamente.

**Decisión:** `CrmProducto` se sincroniza desde `ITEM` vía agente (con watermark). Desde CRM no se crean/modifican productos. `CrmImpuesto` se sincroniza desde `TAXAUTH`. ITEM.IMPOVENTA → lookup en TAXAUTH → FK a CrmImpuesto.

**Consecuencias:** El catálogo CRM siempre refleja Saiopen. Si un producto se desactiva en Saiopen (`ESTADO='False'`), se desactiva en CRM (`is_active=False`) y deja de aparecer en buscador de cotizaciones.

---

## DEC-058: CRM reutiliza `terceros.Tercero` — sin duplicar modelo de cliente
**Fecha:** 2026-04-10
**Estado:** Decidido

**Contexto:** `terceros.Tercero` ya sincroniza clientes con CUST de Saiopen. CRM necesita vincular oportunidades a clientes.

**Decisión:** `CrmOportunidad.contacto` es FK a `terceros.Tercero`. Al convertir un lead, se busca Tercero por email/NIT existente o se crea uno nuevo. El CRM no tiene su propio modelo de "contacto".

**Consecuencias:** Oportunidades siempre ligadas a un tercero real en Saiopen. Al crear cotización, `ID_CLIENTE` en COTIZACI viene del `Tercero.saiopen_id`. Sin duplicación de datos de clientes.

---

## DEC-057: Módulo CRM en Django — no Go
**Fecha:** 2026-04-10
**Estado:** Decidido

**Contexto:** Evaluación rutinaria Django vs Go para nuevo módulo.

**Decisión:** Django. CRM es CRUD + lógica comercial sin >1000 req/s, sin batch masivo, sin standalone. Los 4 criterios de Go no se cumplen.

**Consecuencias:** Consistente con resto de backend. Menor overhead de mantenimiento.

---

## DEC-056: CUST sync atómico — SHIPTO y TRIBUTARIA viajan en el mismo mensaje SQS
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** Al sincronizar un tercero modificado en CUST, Django necesita tanto los datos de contacto (CUST) como las direcciones (SHIPTO) y los datos tributarios (TRIBUTARIA) para poder construir correctamente el modelo `Tercero`. Enviarlos en mensajes separados generaría ventanas de inconsistencia.

**Decisión:** El mensaje SQS `cust_batch` incluye tres arrays: `records` (CUST), `shipto` (solo IDs afectados), `tributaria` (solo IDs afectados). Django procesa los tres en un único `transaction.atomic()`.

**Consecuencias:** Mensajes más grandes → chunking a 150 registros CUST por mensaje para mantenerse bajo 256KB. Sin inconsistencias parciales.

---

## DEC-055: CUST incremental por campo "Version" (no CONTEO)
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** CUST en Firebird 2.5 tiene tanto `CONTEO` como `"Version"` (generado por trigger). GL usa CONTEO como watermark. Para CUST se eligió `Version` porque es el campo que se actualiza en INSERT y UPDATE de terceros.

**Decisión:** Watermark `LastVersionCust` en `SyncConfig`. Query: `WHERE "Version" > lastVersion`. CUST corre en el ticker de GL (cada 5 min), no en el de referencias (24h).

**IMPORTANTE:** `Version` es palabra reservada en Firebird SQL — siempre usar comillas dobles en el SQL: `"Version"`. Sin comillas el driver retorna `Column unknown VERSION` sin lanzar error Go visible, causando hang silencioso.

**Consecuencias:** Terceros nuevos/modificados llegan a Django en máximo 5 minutos.

---

## DEC-054: KB Admin UI solo para company_admin y valmen_admin
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** La pantalla de gestión de la knowledge base (listar/eliminar fuentes, subir archivos) debía ser accesible pero no expuesta a usuarios finales.

**Decisión:** La ruta `/admin/knowledge-base` está disponible para ambos roles: `valmen_admin` (ve además el botón "Re-indexar todo") y `company_admin` (solo upload + delete). Sin guard adicional porque toda la sección `/admin` ya está protegida por el rol correspondiente.

**Consecuencias:** Un `company_admin` puede subir sus propios documentos (normas internas, manuales) y el bot de su empresa los usará inmediatamente.

---

## DEC-053: Redis cache con invalidación por versión para búsquedas RAG
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** Las búsquedas RAG (embedding + pgvector) son costosas (~200ms + tokens OpenAI). Muchas preguntas frecuentes repiten la misma consulta.

**Opciones consideradas:**
1. Cache simple key→value con TTL (sin invalidación explícita)
2. Cache con invalidación por patrón (`delete_pattern`) → requiere `django-redis`, no funciona con built-in backend
3. Cache con versión lógica por (company, module) — incrementar versión = invalidar todos los resultados

**Decisión:** Opción 3. Clave = `rag:{company_id}:{module}:{version}:{query_hash}`. Al ingestar conocimiento nuevo, se incrementa la versión → claves antiguas inaccesibles, expiran por TTL (2h).

**Razón:** No requiere dependencia adicional (Django 4+ tiene backend Redis built-in), es testeable, y el overhead de leer la versión es O(1).

**Consecuencias:** Conocimiento nuevo es buscable inmediatamente tras invalidación. Máximo 2h de datos stale si la invalidación falla.

---

## DEC-052: LearningService — feedback +1 genera FAQ chunk automáticamente
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** El sistema acumula feedback positivo sobre respuestas del bot pero no lo aprovechaba para mejorar el RAG.

**Decisión:** Cuando `AIFeedback.rating = 1`, `LearningService.process_positive_feedback()` crea un `KnowledgeChunk(source_type=FAQ_APRENDIDA)` con el par P&A embebido. Deduplicación via MD5 del contenido. Mínimo 50 tokens para filtrar respuestas triviales.

**Consecuencias:** La knowledge base crece orgánicamente con preguntas reales. Preguntas frecuentes serán respondidas con contexto propio del historial validado por usuarios.

---

## DEC-051: Token optimization dinámico en AIOrchestrator
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** `max_tokens=1024` fijo desperdicia tokens en preguntas cortas (¿Cuál es mi saldo? → respuesta de 80 tokens).

**Decisión:** `completion_tokens` dinámico según longitud de pregunta: ≤50 tok → 512, ≤150 → 768, >150 → 1024.

**Consecuencias:** Reducción estimada del 30-40% en costo por completion para preguntas simples.

---

## DEC-050: AIOrchestrator reemplaza CfoVirtualService+n8n para el bot de chat
**Fecha:** 2026-04-07
**Estado:** Decidido

**Contexto:** `BotResponseService` llamaba a `CfoVirtualService` que a su vez llamaba a n8n (workflow externo). Esto añadía latencia (~800ms extra), un punto de fallo adicional y limites de contexto del workflow.

**Opciones consideradas:**
1. Mantener n8n como orquestador (bajo acoplamiento)
2. `AIOrchestrator` directo en Django (RAG nativo + DataCollectors + OpenAI SDK)

**Decisión:** Opción 2. `AIOrchestrator` en `apps/ai/services.py` reemplaza el workflow n8n para el bot de chat. n8n se mantiene solo para el endpoint legacy `/api/v1/dashboard/cfo-virtual/`.

**Razón:** Latencia -800ms, RAG nativo con pgvector, DataCollectors multi-módulo (5 collectors), historial multi-turno (6 turnos), control total de tokens.

**Consecuencias:** n8n workflow `cfo-virtual.json` queda deprecated para nuevas interacciones. El endpoint HTTP `/dashboard/cfo-virtual/` sigue funcionando para compatibilidad.

---

## DEC-049: Asistente IA como bot en el sistema de chat existente
**Fecha:** 2026-04-03
**Estado:** Decidido

**Contexto:** El CFO Virtual tenia endpoint backend pero no UI accesible. Se necesitaba decidir donde ubicar la interaccion con IA.

**Opciones consideradas:**
1. Widget flotante independiente por modulo (ya existia ai-assistant component)
2. Canal especial en el chat existente (bot como participante)
3. Pagina/ruta dedicada para IA

**Decision:** Bot como participante de conversacion en el chat existente (#2).

**Razon:** Reutiliza toda la infraestructura de chat (WebSocket, UI, historial, search). Un solo lugar para comunicacion humana e IA. El campo `bot_context` permite saber desde que modulo se habla para enrutar a la logica correcta (dashboard→CfoVirtual, proyectos→futuro).

**Implementacion:**
- `User.is_bot=True` para usuario bot global
- `Conversacion.bot_context` para contexto del modulo
- `BotResponseService` enruta segun contexto
- Thread daemon en consumer para no bloquear WebSocket

**Consecuencias:** Futuras integraciones IA (asistente de proyectos, guia de manuales) solo requieren agregar un case en `BotResponseService` y un nuevo `bot_context`.

---

## DEC-048: LicensePackage como catalogo global para licencias modulares
**Fecha:** 2026-04-03
**Estado:** Decidido

**Contexto:** El sistema de licencias necesitaba ser "armable" — modulos, usuarios y tokens IA como items independientes con precios editables.

**Opciones:**
1. Campos fijos en CompanyLicense (ya existente)
2. Paquetes como entidades separadas con relacion many-to-many

**Decision:** Modelo `LicensePackage` global + `LicensePackageItem` de relacion.

**Razon:** Permite agregar/quitar paquetes sin cambiar schema. Precios editables. Cada empresa puede tener combinacion unica de paquetes.

**Tipos de paquete:** module, user_seats, ai_tokens, ai_messages
**Efecto:** Al agregar/quitar un paquete, `PackageService` actualiza automaticamente los campos de `CompanyLicense` (modules_included, max_users, ai_tokens_quota, messages_quota).

---

## DEC-047: AIUsageLog para tracking granular de consumo IA
**Fecha:** 2026-04-03
**Estado:** Decidido

**Contexto:** Se necesita registrar cada request IA para control de cuota y visibilidad de consumo por usuario.

**Decision:** Modelo `AIUsageLog` con tracking por request (prompt_tokens, completion_tokens, model, user, module_context). `AIUsageService.check_quota()` verifica antes de cada request y `record_usage()` registra despues.

**Integracion:** n8n workflow retorna `usage` de OpenAI en el response → Django lo parsea y registra.

---

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

> **Decisiones archivadas (DEC-012, DEC-023 a DEC-036):** `docs/plans/historic/DECISIONS-ARCHIVE.md`
> Incluye: Terceros transversales, refactor español→inglés, Gantt, EVM, DisableMigrations, navegación, sobreasignación, Redis Upstash, Cloudflare R2, Chat autocomplete, Chat UUID normalization.
