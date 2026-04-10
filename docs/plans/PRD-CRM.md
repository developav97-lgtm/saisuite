# PRD — Módulo CRM SaiSuite
**Versión:** 1.0  
**Fecha:** 10 Abril 2026  
**Estado:** PENDIENTE APROBACIÓN PO  
**Módulo:** `crm`  
**Ticket:** CRM-001 (MODULE)

---

## 1. Contexto y Restricciones Saicloud

### Restricciones técnicas que aplican:
- **Multi-tenancy:** `company_id` en todos los modelos sin excepción
- **BaseModel:** UUID pk, company FK, `created_at`, `updated_at`, `is_active`
- **Frontend:** Angular 18, Material Design, `OnPush`, variables `var(--sc-*)`, NUNCA PrimeNG/Bootstrap/Tailwind
- **Backend:** Lógica en `services.py` exclusivamente
- **Sync:** Via `sync_agent` existente (mismo patrón que `terceros`)
- **Licencias:** Registrar en `CompanyModule.Module` al deploy

### Integración crítica con módulos existentes:
- **`terceros`**: El CRM **reutiliza** `Tercero` como base de contactos y cuentas. NO se duplica el modelo. Un lead calificado se convierte en `Tercero`.
- **`sync_agent`**: La sincronización con Saiopen usa el agente Windows ya implementado. El CRM extiende el `SYNC_GRAPH` existente.
- **`proyectos`**: Las oportunidades ganadas podrán generar un proyecto (integración futura, no MVP).
- **`chat`**: El Copiloto de Ventas IA usará la infraestructura de `chat` con contexto `'crm'`.

### Tablas Saiopen mapeadas:
| Tabla Saiopen | Modelo CRM | Estado |
|---|---|---|
| `CUST` | `Tercero` (existente en `terceros`) | ✅ Ya implementada |
| `ACTIVIDADES` | Referencia para tipos de actividad | ✅ Schema disponible |
| `COTIZACIONES` | `CrmCotizacion` | ⚠️ **Pendiente**: Juan David debe subir schema a `docs/saiopen/` |
| `LISTA` (precios) | `CrmProducto` / `LineaCotizacion` | ✅ Schema disponible |

---

## 2. Requerimientos Funcionales

### MVP (Módulo entregable v1.0)

#### RF-P: Pipeline de Ventas
- **RF-P.1** Vista Kanban con columnas por etapa: `Nuevo → Calificado → Propuesta Enviada → Negociación → Ganado → Perdido`
- **RF-P.2** Drag & Drop entre etapas (CDK DragDrop de Angular Material)
- **RF-P.3** Cada columna muestra suma dinámica de ingresos esperados de sus oportunidades
- **RF-P.4** Múltiples pipelines por empresa (pipeline principal + por línea de negocio)
- **RF-P.5** Probabilidad configurable por etapa (afecta forecast)
- **RF-P.6** Virtual scroll en columnas con > 50 tarjetas (RNF-2)

#### RF-L: Leads
- **RF-L.1** Creación manual de lead (formulario simple: nombre/empresa/email/teléfono/fuente)
- **RF-L.2** Importación masiva CSV/Excel (mapeo de columnas, validación, preview)
- **RF-L.3** Captura automática vía webhook público (`POST /api/crm/leads/webhook/`) — para formularios web
- **RF-L.4** Lead Scoring automático: puntuación 1-100 basada en reglas configurables (tamaño empresa, sector, fuente, interacciones). Reglas gestionadas por admin.
- **RF-L.5** Conversión Lead → Oportunidad: crea `CrmOportunidad` + opcionalmente crea/vincula `Tercero` existente
- **RF-L.6** Asignación automática: Round-Robin entre vendedores activos del mismo pipeline

#### RF-O: Oportunidades
- **RF-O.1** Modelo central: vinculada a un `Tercero` (cliente), pipeline, etapa, valor esperado, probabilidad, fecha cierre estimada, vendedor asignado
- **RF-O.2** Vista de detalle con tabs: Información general | Timeline | Actividades | Cotizaciones | IA
- **RF-O.3** Marcar como `Ganada` (trigger: notificación, posibilidad de crear proyecto) o `Perdida` (requiere motivo)
- **RF-O.4** Historial de cambios de etapa con fecha y usuario

#### RF-A: Actividades y Timeline
- **RF-A.1** Timeline (muro) por oportunidad: registra notas, cambios de estado, emails, llamadas, reuniones cronológicamente
- **RF-A.2** Programar actividades: Llamada | Reunión | Email | Tarea — con fecha, hora, responsable
- **RF-A.3** "Próxima acción" destacada en la tarjeta Kanban (ícono + días restantes)
- **RF-A.4** Envío de email desde oportunidad (SMTP configurado en sistema, log en timeline)
- **RF-A.5** Notificaciones in-app cuando vence una actividad (usa `notifications` existente)

#### RF-C: Cotizaciones
- **RF-C.1** Crear cotización desde oportunidad, seleccionando productos del catálogo (sincronizado desde Saiopen `LISTA`)
- **RF-C.2** Cálculo automático: subtotal, descuento (%), impuestos (configurable por empresa), total
- **RF-C.3** Exportar cotización a PDF (template Django/WeasyPrint con logo empresa)
- **RF-C.4** Enviar cotización por email directamente desde CRM (log en timeline)
- **RF-C.5** Sincronización bidireccional con tabla `COTIZACIONES` de Saiopen (pendiente schema)
- **RF-C.6** Estados de cotización: Borrador | Enviada | Aceptada | Rechazada | Vencida

#### RF-D: Dashboard y Analytics
- **RF-D.1** Widgets principales: Oportunidades por etapa (funnel), Ingresos este mes vs meta, Actividades vencidas, Tasa de conversión Lead→Oportunidad→Ganado
- **RF-D.2** Tabla de rendimiento por vendedor (oportunidades, valor, conversión)
- **RF-D.3** Forecast del período: suma `valor_esperado × probabilidad_etapa` de oportunidades activas
- **RF-D.4** Filtros: período, vendedor, pipeline, fuente del lead

### Mejoras (v1.1 — post-MVP)

#### MJ-1: Copiloto de Ventas IA (Prioridad Alta)
- Redacción de borradores de email personalizados basados en contexto de la oportunidad + notas previas (usa infraestructura `chat` con `bot_context='crm'`)
- Resumen automático de timeline de una oportunidad ("¿qué pasó con este cliente en los últimos 30 días?")
- Sugerencia de siguiente acción basada en historial y etapa

#### MJ-2: Document Tracking (Prioridad Media)
- Al enviar cotización, generar link seguro único (token UUID) en lugar de solo PDF
- Página web de vista de cotización (Angular, pública)
- Registrar en timeline: `"Cliente abrió cotización el DD/MM/YYYY a las HH:MM"` (webhook de apertura)
- Tiempo de lectura por sección (futuro)

#### MJ-3: Cadencias de Ventas (Prioridad Media)
- Crear secuencias automatizadas: `Día 1: Email → Día 3: si no abrió → Llamada → Día 5: SMS`
- Motor de cadencias basado en n8n workflows (ya instalado en stack)
- Asignar cadencia a lead o segmento de leads

#### MJ-4: Gamificación (Prioridad Baja)
- Leaderboard semanal de vendedores (oportunidades ganadas, valor, actividades completadas)
- Logros: "Cerrador de la semana", "Racha 5 días seguimiento" — badges en perfil de usuario
- Visible en dashboard CRM

#### MJ-5: Sincronización Email IMAP (Prioridad Baja)
- Configurar cuenta IMAP por usuario para recibir emails en timeline de oportunidades
- Matching automático por email del contacto

---

## 3. Requerimientos No Funcionales

| ID | Tipo | Descripción | Métrica |
|---|---|---|---|
| RNF-1 | Usabilidad | Responsive Mobile-first | Funcional en viewport 375px |
| RNF-2 | Rendimiento | Kanban con 1,000+ tarjetas | < 2s render (virtual scroll CDK) |
| RNF-3 | Seguridad | company_id en todo, permisos por rol | 100% cubierto en tests |
| RNF-4 | Multi-tenancy | Datos completamente aislados por empresa | Validado en todos los endpoints |
| RNF-5 | Sync | Cotizaciones sincronizadas con Saiopen | Bidireccional, misma arquitectura que terceros |

---

## 4. Clasificación MVP vs Mejoras

```
MVP v1.0 (este módulo):
✅ Pipeline Kanban + D&D
✅ Leads: manual + CSV + webhook
✅ Lead Scoring por reglas
✅ Round-Robin asignación
✅ Oportunidades (modelo completo)
✅ Timeline / Muro de actividades
✅ Actividades programadas + notificaciones
✅ Email desde oportunidad
✅ Cotizaciones (depende schema Saiopen)
✅ PDF + envío email cotización
✅ Sincronización Saiopen (CUST ya existe, COTIZACIONES pendiente)
✅ Dashboard con forecast básico
✅ Licencia + guard + menú

MEJORAS v1.1 (tickets futuros):
⏳ MJ-1: Copiloto IA
⏳ MJ-2: Document Tracking
⏳ MJ-3: Cadencias n8n
⏳ MJ-4: Gamificación
⏳ MJ-5: Email IMAP
```

---

## 5. Modelos de Datos (Preliminar — detalle en PLAN)

| Modelo | Propósito | Sync Saiopen |
|---|---|---|
| `CrmPipeline` | Pipeline de ventas (multi por empresa) | No |
| `CrmEtapa` | Etapas de un pipeline + probabilidad | No |
| `CrmLead` | Lead antes de calificar | No |
| `CrmLeadScoringRule` | Reglas de puntuación configurables | No |
| `CrmOportunidad` | Oportunidad (FK: Tercero, Etapa, Pipeline) | No |
| `CrmActividad` | Actividad programada (call, meet, email, task) | No |
| `CrmTimelineEvent` | Evento en muro (audit trail inmutable) | No |
| `CrmProducto` | Catálogo de productos/servicios | Sí — LISTA |
| `CrmCotizacion` | Cotización vinculada a oportunidad | Sí — COTIZACIONES ⚠️ |
| `CrmLineaCotizacion` | Línea de producto en cotización | Sí — COTIZACIONES detalle |
| `CrmCadencia` | Definición de cadencia de ventas (v1.1) | No |

---

## 6. Dependencias e Integraciones

### Bloqueantes para implementación:
1. **Schema COTIZACIONES de Saiopen** — Juan David debe subir a `docs/saiopen/cotizaciones.txt`
   - Necesario para: RF-C.5, CrmCotizacion, sync bidireccional
   - Workaround MVP: implementar cotizaciones sin sync, activar sync cuando llegue schema

### Dependencias de módulos existentes:
- `terceros.Tercero` — FK de `CrmOportunidad.contacto`
- `companies.Company` — FK en todos los modelos
- `users.User` — FK en vendedor asignado, actividades
- `notifications` — Alertas de actividades vencidas
- `chat` / `ai` — Copiloto IA (v1.1)
- `sync_agent` — Extensión para CUST → Lead/Oportunidad y COTIZACIONES
- n8n — Cadencias (v1.1)

### Impacto en módulos existentes:
- `terceros`: Agregar campo `crm_lead_origen` para trazabilidad (opcional)
- `sync_agent`: Extender `SYNC_GRAPH` con entidades CRM
- `DECISIONS.md`: Registrar decisión sobre reutilización de `Tercero`

---

## 7. Casos de Uso Principales (User Stories)

| ID | Como... | Quiero... | Para... |
|---|---|---|---|
| US-01 | Vendedor | ver mis oportunidades en tablero Kanban | saber en qué etapa está cada negocio |
| US-02 | Vendedor | arrastrar tarjetas entre etapas | actualizar el pipeline sin formularios |
| US-03 | Gerente | ver el forecast del mes | proyectar ingresos con el equipo |
| US-04 | Vendedor | crear un lead desde el formulario web | capturar prospectos automáticamente |
| US-05 | Vendedor | programar una llamada de seguimiento | no perder oportunidades por falta de contacto |
| US-06 | Vendedor | generar una cotización en PDF | enviarla al cliente desde el CRM |
| US-07 | Gerente | ver rendimiento de vendedores | evaluar al equipo comercial |
| US-08 | Admin | importar leads masivamente desde Excel | cargar base de datos histórica |
| US-09 | Vendedor | ver toda la historia de un cliente | retomar conversaciones con contexto |
| US-10 | Sistema | sincronizar cotizaciones con Saiopen | mantener datos financieros consistentes |

---

## 8. Pendientes que requieren acción del PO

| # | Acción requerida | Urgencia |
|---|---|---|
| 1 | Subir schema `COTIZACIONES` de Saiopen a `docs/saiopen/cotizaciones.txt` | Alta — bloquea RF-C.5 |
| 2 | ¿Se sincroniza también la tabla de PRODUCTOS/LISTA de Saiopen con el catálogo CRM? | Alta |
| 3 | ¿Qué roles de usuario aplican? (ej: `crm_admin`, `crm_vendedor`, `crm_readonly`) | Media |
| 4 | ¿El módulo CRM es independiente de `terceros` en el menú o integrado? | Media |
| 5 | ¿La cotización CRM reemplaza el proceso en Saiopen o coexiste? | Alta |

---

*PRD generado por Orquestador Saicloud — Fase 0 — 10 Abril 2026*
