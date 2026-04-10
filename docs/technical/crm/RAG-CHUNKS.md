# RAG-CHUNKS — Módulo CRM SaiSuite
# Generado: 2026-04-10 | Versión: 1.1 (v2 Sprint UX/Features)

---

## CHUNK-CRM-001: Visión general del módulo CRM

El módulo CRM de SaiSuite gestiona el ciclo de ventas completo: desde la captación de leads hasta el cierre de oportunidades y emisión de cotizaciones. Se integra con Saiopen (ERP Windows/Firebird) vía SQS para sincronización de productos, impuestos y cotizaciones aceptadas.

**Tecnologías:** Django 5 (backend) + Angular 18 (frontend) + PostgreSQL 16
**URL base:** `/api/v1/crm/`
**Guard de acceso:** `moduleAccessGuard` con `data: { requiredModule: 'crm' }`
**Clave de módulo en licencia:** `crm`

---

## CHUNK-CRM-002: Modelos de datos — Pipeline y Etapas

**CrmPipeline:** Pipeline de ventas. Campo `es_default` indica el que carga por defecto en el Kanban. Una empresa puede tener múltiples pipelines.

**CrmEtapa:** Etapa dentro de un pipeline. Campos clave:
- `orden` (int): posición en el pipeline
- `probabilidad` (Decimal): porcentaje de cierre estimado
- `es_ganado` (bool): si es True, mover aquí cierra la oportunidad como ganada
- `es_perdido` (bool): si es True, mover aquí marca la oportunidad como perdida
- `color` (str): color hexadecimal para el Kanban

**Regla de negocio:** Cada pipeline debe tener exactamente una etapa con `es_ganado=True` y una con `es_perdido=True` para que `ganar()` y `perder()` funcionen.

---

## CHUNK-CRM-003: Modelos de datos — Lead

**CrmLead:** Prospecto en etapa pre-oportunidad.

Campos clave:
- `fuente` (FuenteLead): manual | webhook | csv | referido | otro
- `score` (int): puntaje calculado por `LeadScoringService`
- `convertido` (bool): True cuando el lead se convierte en oportunidad
- `pipeline` (FK opcional): pipeline objetivo al convertir
- `asignado_a` (FK User, nullable): vendedor responsable del lead
- `sai_key` (str): clave de integración con Saiopen (si aplica)

**Serializer `asignado_a_nombre`:** Tanto `CrmLeadListSerializer` como `CrmLeadDetailSerializer` exponen `asignado_a_nombre: str | null` (campo calculado `get_asignado_a_nombre`). Devuelve `full_name` o `email` del vendedor asignado.

**CrmLeadScoringRule:** Regla de scoring. Evalúa un campo del lead con un operador (eq, neq, contains, not_empty, gt, lt) y suma `puntos` al score si se cumple. Las reglas se evalúan en `LeadScoringService.calcular_score()`.

**Conversión a oportunidad:** `LeadService.convertir()` crea un `CrmOportunidad` en la etapa indicada, marca `lead.convertido=True` y registra evento `LEAD_CONVERTIDO` en el timeline.

---

## CHUNK-CRM-004: Modelos de datos — Oportunidad

**CrmOportunidad:** Núcleo del CRM. Representa una negociación activa.

Campos clave:
- `titulo` (str): nombre de la oportunidad
- `contacto` (FK Tercero): cliente asociado (reutiliza módulo Terceros)
- `pipeline` / `etapa` (FK): ubicación en el pipeline
- `valor_esperado` (Decimal): valor estimado del negocio
- `probabilidad` (Decimal): heredado de la etapa, ajustable manualmente
- `valor_ponderado` (property): valor_esperado × (probabilidad / 100)
- `ganada_en` / `perdida_en` (datetime): timestamps de cierre
- `motivo_perdida` (str): razón de pérdida (requerido al perder)
- `proxima_actividad_fecha` / `proxima_actividad_tipo`: denormalizados para performance en Kanban

**Propiedades computadas:** `esta_ganada` (bool), `esta_perdida` (bool), `valor_ponderado` (Decimal)

---

## CHUNK-CRM-005: Flujo de oportunidad — estados

```
ABIERTA → [mover_etapa()] → ABIERTA (etapa diferente)
ABIERTA → [ganar()]       → GANADA  (etapa es_ganado=True, ganada_en=now)
ABIERTA → [perder()]      → PERDIDA (etapa es_perdido=True, perdida_en=now, motivo_perdida requerido)
GANADA  → [perder()]      → PERDIDA (permite reabrir como perdida)
```

Cada transición genera automáticamente un evento `CAMBIO_ETAPA` en el timeline vía `TimelineService.registrar()`.

---

## CHUNK-CRM-006: Modelos de datos — Actividad

**CrmActividad:** Tarea programada sobre una oportunidad **o sobre un lead**.

Tipos (TipoActividad): llamada | reunion | email | tarea | whatsapp | otro

Campos clave:
- `oportunidad` (FK nullable): oportunidad asociada (exclusivo con `lead`)
- `lead` (FK nullable): lead asociado (exclusivo con `oportunidad`)
- `fecha_programada` (datetime): cuándo se debe realizar
- `completada` (bool): se marca True al completar
- `completada_en` (datetime): timestamp de completado
- `resultado` (str): descripción del resultado (registrado al completar)
- `proxima_actividad_fecha` / `tipo` en CrmOportunidad: se actualizan automáticamente vía `ActividadService._actualizar_proxima_actividad()` al crear/completar/eliminar actividades de oportunidad

**Actividades en Lead (v2):**
- `ActividadService.create_for_lead(lead, data)` — crea actividad asociada al lead (oportunidad=None)
- `ActividadService.list_for_lead(lead, solo_pendientes=False)` — filtra actividades del lead; con `solo_pendientes=True` excluye `completada=True`
- Solo las actividades de oportunidad tienen entrada en timeline; las de lead no (guard en signal)

**Signal `actividad_creada_timeline`:** Solo se dispara si `instance.oportunidad_id is not None`. Las actividades de lead no generan evento de timeline (ya que `CrmTimelineEvent.oportunidad` es NOT NULL).

---

## CHUNK-CRM-007: Modelos de datos — Timeline

**CrmTimelineEvent:** Registro inmutable de eventos en la oportunidad. No se elimina.

Tipos (TipoTimelineEvent):
- `nota`: nota manual del vendedor
- `cambio_etapa`: cambio de etapa (incluye ganar/perder)
- `actividad_completada`: actividad marcada como completada
- `email_enviado`: email enviado al contacto
- `cotizacion_creada`: cotización creada en la oportunidad
- `cotizacion_aceptada`: cotización aceptada por el cliente
- `lead_convertido`: lead convertido a oportunidad
- `sistema`: evento automático del sistema (creación, actividad programada)

**`metadata` (JSONField):** datos adicionales del evento (etapa anterior/nueva, ID de actividad, etc.)

---

## CHUNK-CRM-008: Modelos de datos — Cotización

**CrmCotizacion:** Propuesta comercial formal ligada a una oportunidad.

Estados (EstadoCotizacion): borrador → enviada → aceptada | rechazada | vencida | anulada

Campos financieros:
- `subtotal` = suma de (cantidad × vlr_unitario × (1 - descuento_p/100)) por línea
- `descuento_adicional_p` / `descuento_adicional_val`: descuento global sobre subtotal
- `total_iva`: suma de IVA de todas las líneas
- `total` = subtotal - descuento_adicional_val + total_iva
- `validez_dias`: días de vigencia (default: 30)
- `sai_key` / `saiopen_synced`: para integración con Saiopen al aceptar

**CrmLineaCotizacion:** Línea de detalle de la cotización.
- `vlr_unitario` (Decimal): precio unitario
- `descuento_p` (Decimal): descuento por línea en porcentaje
- `impuesto` (FK CrmImpuesto): IVA u otro impuesto aplicable
- `iva_valor` (Decimal): valor calculado del impuesto
- `total_parcial` = (cantidad × vlr_unitario × (1-desc_p/100)) + iva_valor

**IMPORTANTE:** Toda la aritmética usa `Decimal`, nunca `float`. División por 100 siempre como `Decimal('100')`.

---

## CHUNK-CRM-009: Integración Saiopen — Productos e Impuestos

**ImpuestoSyncService:** Sincroniza TAXAUTH de Saiopen → CrmImpuesto.
- Endpoint: `POST /api/v1/crm/sync/impuestos/` (solo superadmin)
- Actualiza o crea por `sai_key` (código fiscal de Saiopen)

**ProductoSyncService:** Sincroniza ITEM de Saiopen → CrmProducto.
- Endpoint: `POST /api/v1/crm/sync/productos/` (solo superadmin)
- Unidireccional: solo lectura en CRM, no escribe de vuelta a Saiopen

**SyncCotizacionService:** Envía cotización aceptada a Saiopen vía SQS.
- Se dispara automáticamente al `aceptar()` una cotización
- `sai_key` en cotización = `"{numero}_{tipo}_{empresa}_{sucursal}"`
- Solo si la empresa tiene `saiopen_enabled=True`

---

## CHUNK-CRM-010: API REST — Endpoints principales

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/v1/crm/pipelines/` | Lista pipelines de la empresa |
| GET | `/api/v1/crm/pipelines/{id}/kanban/` | Vista Kanban del pipeline |
| POST | `/api/v1/crm/pipelines/{id}/etapas/reordenar/` | Reordena etapas |
| GET/POST | `/api/v1/crm/leads/` | Lista y crea leads |
| POST | `/api/v1/crm/leads/{id}/convertir/` | Convierte lead a oportunidad |
| POST | `/api/v1/crm/leads/importar/` | Importación masiva CSV |
| GET/POST | `/api/v1/crm/oportunidades/` | Lista y crea oportunidades |
| POST | `/api/v1/crm/oportunidades/{id}/mover-etapa/` | Drag&Drop Kanban |
| POST | `/api/v1/crm/oportunidades/{id}/ganar/` | Cierra como ganada |
| POST | `/api/v1/crm/oportunidades/{id}/perder/` | Cierra como perdida (requiere motivo) |
| GET | `/api/v1/crm/oportunidades/{id}/timeline/` | Timeline de eventos |
| POST | `/api/v1/crm/oportunidades/{id}/notas/` | Agrega nota al timeline |
| GET/POST | `/api/v1/crm/oportunidades/{id}/actividades/` | Actividades de la oportunidad |
| POST | `/api/v1/crm/actividades/{id}/completar/` | Marca actividad como completada |
| POST | `/api/v1/crm/oportunidades/{id}/cotizaciones/crear/` | Crea cotización |
| POST | `/api/v1/crm/cotizaciones/{id}/enviar/` | Envía cotización por email |
| POST | `/api/v1/crm/cotizaciones/{id}/aceptar/` | Acepta y sincroniza a Saiopen |
| GET | `/api/v1/crm/cotizaciones/{id}/pdf/` | Genera PDF WeasyPrint |
| GET | `/api/v1/crm/dashboard/` | KPIs del pipeline |
| GET | `/api/v1/crm/dashboard/forecast/` | Forecast ponderado |
| GET/POST | `/api/v1/crm/leads/{id}/actividades/` | Lista/crea actividades del lead |
| GET | `/api/v1/crm/leads/{id}/actividades/?solo_pendientes=true` | Solo actividades pendientes del lead |
| POST | `/api/v1/crm/leads/{id}/round-robin/` | Asigna lead a vendedor (round-robin) |
| POST | `/api/v1/crm/leads/asignar-masivo/` | Asigna todos los leads sin asignar (round-robin) |
| GET | `/api/v1/crm/agenda/` | Agenda unificada: actividades de leads y oportunidades |
| GET | `/api/v1/crm/agenda/?fecha_desde=X&fecha_hasta=Y&solo_pendientes=true` | Agenda filtrada |

**Autenticación:** JWT Bearer. Multi-tenant: company_id filtrado automáticamente.
**Permisos:** `IsAuthenticated` base. Endpoints de sync requieren `IsSuperAdmin`.

---

## CHUNK-CRM-011: Dashboard y Métricas

**CrmDashboard** (endpoint `/dashboard/`):
- `total_leads`: total de leads de la empresa
- `leads_nuevos_mes`: leads creados en el mes actual
- `oportunidades_activas`: oportunidades abiertas (no ganadas ni perdidas)
- `valor_total_activo`: suma de valor_esperado de oportunidades activas
- `tasa_conversion`: % leads convertidos a oportunidad
- `forecast`: suma del valor_ponderado de oportunidades activas
- `funnel`: lista de etapas con count y valor total
- `rendimiento_vendedores`: por usuario: oportunidades activas, ganadas/perdidas del mes, valor ganado

**CrmForecast** (endpoint `/dashboard/forecast/`):
- `total_forecast`: suma valor_ponderado (valor × probabilidad)
- `total_valor_esperado`: suma valor_esperado sin ponderar
- `detalle`: desglose por etapa

---

## CHUNK-CRM-012: Frontend Angular — Estructura

**Ruta base:** `/crm` (lazy-loaded, protegida por `moduleAccessGuard`)

| Ruta | Componente | Descripción |
|------|-----------|-------------|
| `/crm` | KanbanPageComponent | Pipeline visual CDK DragDrop |
| `/crm/leads` | LeadsPageComponent | Tabla paginada con filtros |
| `/crm/leads/nuevo` | LeadFormPageComponent | Crear lead |
| `/crm/leads/:id/editar` | LeadFormPageComponent | Editar lead |
| `/crm/oportunidades/nueva` | OportunidadFormPageComponent | Crear oportunidad |
| `/crm/oportunidades/:id/editar` | OportunidadFormPageComponent | Editar oportunidad |
| `/crm/oportunidades/:id` | OportunidadDetailPageComponent | Detalle con Timeline/Actividades/Cotizaciones |
| `/crm/cotizaciones/:id` | CotizacionPageComponent | Editor de cotización |
| `/crm/dashboard` | CrmDashboardPageComponent | KPIs y forecast |

**Servicio principal:** `CrmService` (`providedIn: 'root'`) — 46 métodos HTTP.
**Patrón de estado:** Signals (`signal()`, `computed()`) + `takeUntil(destroy$)`.
**Dialogs:** `ActividadDialogComponent`, `PerderDialogComponent`, `CompletarActividadDialogComponent`, `LeadImportDialogComponent`, `LeadConvertirDialogComponent`.
**Round-robin en UI:** `LeadsPageComponent` tiene botón "Auto-asignar" para asignación masiva y botón `person_add` por lead (visible solo si sin asignar) para asignación individual.

---

## CHUNK-CRM-013: Reglas de negocio críticas

1. **Multi-tenancy:** Toda consulta filtra por `company_id`. Nunca exponer datos entre empresas.
2. **Decimal aritmético:** Nunca usar `float` para dinero. Siempre `Decimal` y dividir por `Decimal('100')`.
3. **Timeline inmutable:** `CrmTimelineEvent` no se elimina. Solo se crea.
4. **Actividad → pipeline de próxima actividad:** Al crear/completar/eliminar actividades, `_actualizar_proxima_actividad()` actualiza `proxima_actividad_fecha` y `proxima_actividad_tipo` en la oportunidad (denormalizado para Kanban).
5. **Cotización: solo push al aceptar.** `SyncCotizacionService.push_to_saiopen()` se llama únicamente en `aceptar()`, no en `enviar()`.
6. **Perder requiere motivo:** `OportunidadService.perder()` lanza `ValueError` si `motivo` está vacío.
7. **Pipeline con etapas ganado/perdido:** `ganar()` y `perder()` buscan etapa con `es_ganado=True`/`es_perdido=True`. Si no existe, lanzan `ValueError`.
8. **Signal actividad con lead:** El signal `actividad_creada_timeline` DEBE verificar `instance.oportunidad_id` antes de crear `CrmTimelineEvent`. `CrmTimelineEvent.oportunidad` es NOT NULL — pasar `None` genera `IntegrityError` que envenena la sesión PostgreSQL y causa `TransactionManagementError` en toda la transacción. Guard obligatorio: `if not instance.oportunidad_id: return`.
9. **Round-robin:** `LeadService.asignar_round_robin(lead)` asigna al vendedor (`role='seller'`) con menor cantidad de leads activos (`annotate(leads_count=Count('crm_leads')).order_by('leads_count')`). Si no hay vendedores, el lead queda sin asignar (no es error). `asignar_masivo_round_robin(company)` procesa todos los leads sin asignar y devuelve el conteo.

---

## CHUNK-CRM-014: Tests

**Backend (pytest):**
- Ubicación: `backend/apps/crm/tests/`
- Archivos v1: `test_pipeline_services.py`, `test_lead_services.py`, `test_oportunidad_services.py`, `test_cotizacion_services.py`, `test_crm_views.py` (47 tests)
- Archivos v2: `test_v2_services.py` (10 tests: actividades en lead, round-robin), `test_v2_views.py` (15 tests: endpoints agenda, actividades lead, round-robin, asignar-masivo)
- Resultado: **72/72 passing** | Cobertura `apps.crm`: **74.22%**
- Configuración especial `testing.py`: excluye `apps.ai`, `apps.dashboard`, `django.contrib.postgres` (incompatibles con SQLite)
- Comando: `pytest apps/crm/tests/ -v --no-cov`

**Frontend (Karma/Jasmine):**
- `crm.service.spec.ts`: 58 tests, 100% cobertura del servicio
- `kanban-page.component.spec.ts`: ≥70% cobertura
- `leads-page.component.spec.ts`: ≥70% cobertura
- `oportunidad-detail-page.component.spec.ts`: ≥70% cobertura

---

## CHUNK-CRM-015: Decisiones técnicas (DECs)

- **DEC-057:** CRM usa módulo `Tercero` existente para contactos (no duplicar modelo Cliente)
- **DEC-058:** Cotización solo se sincroniza a Saiopen al aceptar (no al enviar) para evitar borradores en el ERP
- **DEC-059:** `sai_key` de cotización = `"{numero}_{tipo}_{empresa}_{sucursal}"` para unicidad en Saiopen
- **DEC-060:** Valor ponderado = valor_esperado × (probabilidad_etapa / 100) — calculado en frontend y backend por separado para performance
- **DEC-061:** Timeline inmutable (no DELETE) — trazabilidad completa de la oportunidad
- **DEC-062:** `proxima_actividad_fecha` y `proxima_actividad_tipo` denormalizados en `CrmOportunidad` para evitar JOIN en cada card del Kanban
- **DEC-063:** Actividades pueden pertenecer a `oportunidad` OR a `lead` (ambas FKs nullable). Signal de timeline sólo aplica para actividades de oportunidad.
- **DEC-064:** Round-robin basado en mínimo de leads activos asignados por vendedor (`annotate` + `order_by`). Sin vendedores → lead sin asignar (no es error, 200 OK).
- **DEC-065:** `CrmActividadAgendaSerializer` extiende `CrmActividadSerializer` con `contexto_tipo` ('lead' | 'oportunidad') y `contexto_nombre`. El endpoint `/agenda/` devuelve actividades de ambos tipos en rango de fechas.

---

## CHUNK-CRM-016: Agenda — endpoint unificado

**Endpoint:** `GET /api/v1/crm/agenda/`

Devuelve actividades de la empresa (leads + oportunidades) en un rango de fechas. Sin fecha → devuelve todo.

**Query params:**
- `fecha_desde` (date ISO): inicio del rango (inclusive)
- `fecha_hasta` (date ISO): fin del rango (inclusive)
- `solo_pendientes` (bool): si `true`, excluye actividades `completada=True`

**Response:** Lista de `CrmActividadAgendaSerializer`:
```json
[
  {
    "id": "uuid",
    "tipo": "llamada",
    "tipo_display": "Llamada",
    "titulo": "Seguimiento inicial",
    "fecha_programada": "2026-04-12T10:00:00Z",
    "completada": false,
    "lead": "uuid | null",
    "oportunidad": "uuid | null",
    "contexto_tipo": "lead | oportunidad",
    "contexto_nombre": "nombre del lead u oportunidad"
  }
]
```

**Aislamiento:** Filtra por `company` del usuario autenticado. Nunca muestra actividades de otras empresas.

---

## CHUNK-CRM-017: Actividades en Lead

**Endpoints:**
- `GET /api/v1/crm/leads/{id}/actividades/` — lista actividades del lead
- `GET /api/v1/crm/leads/{id}/actividades/?solo_pendientes=true` — solo pendientes
- `POST /api/v1/crm/leads/{id}/actividades/` — crea actividad para el lead

**Service:** `ActividadService`
```python
# Crear actividad para lead
ActividadService.create_for_lead(lead, data)
# data: {tipo, titulo, fecha_programada, [asignado_a_id], [descripcion]}

# Listar actividades del lead
ActividadService.list_for_lead(lead, solo_pendientes=False)
# Retorna QuerySet filtrado por lead__id, excluye oportunidad__isnull=False
```

**Regla:** Las actividades de lead NO generan evento de timeline (`CrmTimelineEvent`). El signal verifica `instance.oportunidad_id` antes de intentar crear el evento.

---

## CHUNK-CRM-018: Round-Robin — Asignación de Leads

**Algoritmo:** Asigna el lead al vendedor activo (`role='seller'`, `is_active=True`) con menor número de leads asignados.

**Service:** `LeadService`
```python
# Asignar un lead
LeadService.asignar_round_robin(lead: CrmLead) -> CrmLead
# Sin vendedores → devuelve lead sin modificar (asignado_a=None)

# Asignar todos los leads sin asignar de la empresa
LeadService.asignar_masivo_round_robin(company) -> int
# Retorna cantidad de leads efectivamente asignados
```

**Endpoints:**
- `POST /api/v1/crm/leads/{id}/round-robin/` → `{id, nombre, asignado_a, asignado_a_nombre, ...}`
- `POST /api/v1/crm/leads/asignar-masivo/` → `{"asignados": N}`

**Nota:** La ruta `asignar-masivo/` debe declararse ANTES de `<uuid:pk>/` en `urls.py` para evitar conflicto de resolución.
