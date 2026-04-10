# PLAN TÉCNICO — Módulo CRM SaiSuite
**Versión:** 1.0  
**Fecha:** 10 Abril 2026  
**Estado:** PENDIENTE APROBACIÓN PO  
**Basado en:** PRD-CRM.md + schemas Saiopen confirmados  
**Decisiones:** DEC-057 a DEC-062 (registrar en DECISIONS.md)

---

## 1. Decisiones Técnicas (DECs)

### DEC-057: Backend en Django — No Go para CRM
CRM es CRUD + lógica de negocio (scoring, sync, PDF) sin carga de >1000 req/s ni batch masivo. Django cubre todos los criterios.

### DEC-058: Reutilizar `Tercero` como contacto de oportunidad
`CrmOportunidad.contacto` es FK a `terceros.Tercero`. Al convertir un lead se busca Tercero existente (por email/NIT) o se crea uno nuevo. No se duplica el modelo de cliente.

### DEC-059: Catálogo de productos = ITEM de Saiopen (solo lectura desde CRM)
`CrmProducto` se sincroniza **desde** Saiopen `ITEM` vía agente. Desde CRM no se crean/modifican productos — son gestionados en Saiopen. Sync bidireccional confirmada por PO = cambios en ITEM llegan al CRM; cambios de precio hechos en CRM se descartarán en el próximo sync.

### DEC-060: Cotización CRM → Saiopen solo cuando cliente acepta
El CRM maneja el ciclo completo de la cotización (Borrador → Enviada → Aceptada/Rechazada). Solo al cambiar a `aceptada` se empuja a Saiopen como `COTIZACI` (con `AUTORIZADO='S'`). Si Saiopen anula la cotización (`ANULAR=0`), el agente actualiza CRM a `anulada`.

### DEC-061: Permisos CRM sobre roles existentes (sin roles nuevos)
Se agregan permisos Django estándar sobre los roles existentes:
- `company_admin` / `valmen_admin` → CRUD completo
- `seller` → CRUD propio + lectura pipeline global
- `viewer` → solo lectura dashboard/pipeline
- Cada empresa configura sus propios roles custom y asigna permisos vía admin.

### DEC-062: sai_key cotizacion = `"{numero}_{tipo}_{empresa}_{sucursal}"`
La PK de COTIZACI es compuesta (NUMERO + TIPO + ID_EMPRESA + ID_SUCURSAL). Se serializa como string para el campo `sai_key` en `CrmCotizacion`, garantizando unicidad y trazabilidad.

---

## 2. Evaluación Django vs Go

| Criterio | Valor | Aplica Go? |
|---|---|---|
| >1000 req/s sostenidas | No — CRM es uso comercial puntual | No |
| Batch >50k registros | No — sync ITEM/COTIZACI en lotes de <500 | No |
| Standalone en PC cliente | No | No |
| Ahorro >50% ROI | No aplica | No |

**Resultado: 100% Django.** ✅

---

## 3. Modelos de Datos

### 3.1 Archivo: `backend/apps/crm/models.py`

```python
# CrmPipeline — Pipeline de ventas
class CrmPipeline(BaseModel):
    nombre          CharField(100)
    descripcion     CharField(255, blank=True)
    es_default      BooleanField(default=False)
    # company from BaseModel

class CrmEtapa(BaseModel):
    pipeline        FK(CrmPipeline, CASCADE)
    nombre          CharField(100)
    orden           PositiveSmallIntegerField(default=0)
    probabilidad    DecimalField(5,2, default=0)   # 0-100%
    es_ganado       BooleanField(default=False)
    es_perdido      BooleanField(default=False)
    color           CharField(7, default='#2196F3') # hex

    class Meta:
        unique_together = [('pipeline', 'orden')]
        ordering = ['orden']

class CrmLead(BaseModel):
    FUENTE = [manual, csv, webhook, email, otro]
    nombre          CharField(200)
    empresa         CharField(200, blank=True)
    email           EmailField(blank=True)
    telefono        CharField(50, blank=True)
    cargo           CharField(100, blank=True)
    fuente          CharField(20, choices=FUENTE, default='manual')
    notas           TextField(blank=True)
    score           PositiveSmallIntegerField(default=0)  # 0-100
    pipeline        FK(CrmPipeline, null=True)
    asignado_a      FK(settings.AUTH_USER_MODEL, null=True, SET_NULL)
    convertido      BooleanField(default=False)
    convertido_en   DateTimeField(null=True)
    oportunidad     OneToOneField(CrmOportunidad, null=True, SET_NULL)
    tercero         FK(Tercero, null=True, SET_NULL)       # si se vincula a existente

class CrmLeadScoringRule(BaseModel):
    OPERADORES = [eq, contains, gte, lte, exists, not_empty]
    nombre      CharField(100)
    campo       CharField(50)     # 'fuente', 'empresa', 'email', 'telefono'
    operador    CharField(20, choices=OPERADORES)
    valor       CharField(200)
    puntos      SmallIntegerField()  # positivo o negativo
    orden       PositiveSmallIntegerField(default=0)

class CrmOportunidad(BaseModel):
    titulo                  CharField(200)
    contacto                FK(Tercero, null=True, SET_NULL)  # reutiliza terceros
    pipeline                FK(CrmPipeline, PROTECT)
    etapa                   FK(CrmEtapa, PROTECT)
    valor_esperado          DecimalField(15,2, default=0)
    probabilidad            DecimalField(5,2, default=0)
    fecha_cierre_estimada   DateField(null=True)
    asignado_a              FK(settings.AUTH_USER_MODEL, null=True, SET_NULL)
    lead_origen             FK(CrmLead, null=True, SET_NULL)
    descripcion             TextField(blank=True)
    # Tracking de estados
    ganada_en               DateTimeField(null=True)
    perdida_en              DateTimeField(null=True)
    motivo_perdida          CharField(200, blank=True)
    # Próxima actividad (denormalizado para performance en kanban)
    proxima_actividad_fecha DateTimeField(null=True)
    proxima_actividad_tipo  CharField(20, blank=True)

class CrmActividad(BaseModel):
    TIPOS = [llamada, reunion, email, tarea]
    oportunidad         FK(CrmOportunidad, CASCADE)
    tipo                CharField(20, choices=TIPOS)
    titulo              CharField(200)
    descripcion         TextField(blank=True)
    fecha_programada    DateTimeField()
    completada          BooleanField(default=False)
    completada_en       DateTimeField(null=True)
    asignado_a          FK(settings.AUTH_USER_MODEL, null=True, SET_NULL)
    resultado           TextField(blank=True)

class CrmTimelineEvent(BaseModel):
    TIPOS = [nota, cambio_etapa, actividad_completada, email_enviado,
             cotizacion_creada, cotizacion_aceptada, sistema, lead_convertido]
    oportunidad     FK(CrmOportunidad, CASCADE)
    tipo            CharField(30, choices=TIPOS)
    descripcion     TextField()
    usuario         FK(settings.AUTH_USER_MODEL, null=True, SET_NULL)
    metadata        JSONField(default=dict)  # flexible: etapa_anterior, etapa_nueva, etc.
    # NOTE: timeline es inmutable — no se borra, is_active siempre True

class CrmImpuesto(BaseModel):
    nombre          CharField(50)
    porcentaje      DecimalField(6,4, default=0)   # 0.1900 = 19%
    es_default      BooleanField(default=False)
    # Sync Saiopen TAXAUTH
    sai_key         CharField(20, null=True, blank=True)  # TAXAUTH.CODIGO (smallint)
    saiopen_synced  BooleanField(default=False)

    class Meta:
        unique_together = [('company', 'sai_key')]

class CrmProducto(BaseModel):
    codigo          CharField(30)     # ITEM.ITEM
    nombre          CharField(200)    # ITEM.DESCRIPCION
    descripcion     TextField(blank=True)  # ITEM.COMMENTS
    precio_base     DecimalField(15,2, default=0)  # ITEM.PRICE
    unidad_venta    CharField(20, blank=True)       # ITEM.UOFMSALES
    impuesto        FK(CrmImpuesto, null=True, SET_NULL)  # via ITEM.IMPOVENTA → TAXAUTH
    clase           CharField(10, blank=True)  # ITEM.CLASS
    grupo           CharField(10, blank=True)  # ITEM.GRUPO
    # Sync Saiopen ITEM
    sai_key         CharField(30, null=True, blank=True)  # ITEM.ITEM
    saiopen_synced  BooleanField(default=False)
    ultima_sync     DateTimeField(null=True)

    class Meta:
        unique_together = [('company', 'sai_key')]

class CrmCotizacion(BaseModel):
    ESTADOS = [borrador, enviada, aceptada, rechazada, vencida, anulada]
    oportunidad             FK(CrmOportunidad, CASCADE)
    numero_interno          CharField(20)       # consecutivo CRM
    titulo                  CharField(200)
    contacto                FK(Tercero, null=True, SET_NULL)
    validez_dias            PositiveSmallIntegerField(default=30)
    fecha_vencimiento       DateField(null=True)
    estado                  CharField(20, choices=ESTADOS, default='borrador')
    # Totales (se recalculan al guardar líneas)
    subtotal                DecimalField(15,2, default=0)
    descuento_adicional_p   DecimalField(5,2, default=0)   # COTIZACI.DCTO_ADC_P
    descuento_adicional_val DecimalField(15,2, default=0)  # COTIZACI.DCTO_ADC_VALOR
    total_iva               DecimalField(15,2, default=0)
    total                   DecimalField(15,2, default=0)
    observaciones           TextField(blank=True)   # COTIZACI.OBSERVACIONES
    condiciones             TextField(blank=True)   # COTIZACI.COMENTARIO / validez
    # Sync Saiopen COTIZACI (solo cuando estado='aceptada')
    sai_numero              IntegerField(null=True, blank=True)
    sai_tipo                CharField(3, null=True, blank=True)
    sai_empresa             SmallIntegerField(null=True, blank=True)
    sai_sucursal            SmallIntegerField(null=True, blank=True)
    sai_key                 CharField(50, null=True, blank=True)  # "{num}_{tipo}_{emp}_{suc}"
    saiopen_synced          BooleanField(default=False)

    class Meta:
        unique_together = [('company', 'sai_key')]

class CrmLineaCotizacion(BaseModel):
    cotizacion          FK(CrmCotizacion, CASCADE)
    conteo              PositiveSmallIntegerField()      # DET_PROD.CONTEO (line order)
    producto            FK(CrmProducto, null=True, SET_NULL)
    descripcion         CharField(200)                  # DET_PROD.DESCRIPCION
    descripcion_adic    TextField(blank=True)            # DET_PROD.DESCRIPCION_ADIC
    cantidad            DecimalField(15,4, default=1)
    vlr_unitario        DecimalField(15,2, default=0)
    descuento_p         DecimalField(5,2, default=0)    # DET_PROD.DESCTOP
    impuesto            FK(CrmImpuesto, null=True, SET_NULL)
    iva_valor           DecimalField(15,2, default=0)
    total_parcial       DecimalField(15,2, default=0)   # DET_PROD.TOTAL_PARC
    # Saiopen extras (para sync fiel)
    proyecto            CharField(10, blank=True)       # DET_PROD.PROYECTO
    actividad           CharField(3, blank=True)        # DET_PROD.ACTIVIDAD

    class Meta:
        unique_together = [('cotizacion', 'conteo')]
        ordering = ['conteo']
```

---

## 4. Contrato API (Endpoints)

### Base URL: `/api/crm/`

#### Pipelines y Etapas
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `pipelines/` | Listar / crear pipelines |
| GET/PUT/PATCH/DELETE | `pipelines/{id}/` | CRUD pipeline |
| GET | `pipelines/{id}/kanban/` | Oportunidades agrupadas por etapa (virtual scroll) |
| GET/POST | `pipelines/{id}/etapas/` | Listar / crear etapas |
| POST | `etapas/{id}/reordenar/` | Cambiar orden de etapas |

#### Leads
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `leads/` | Listar / crear lead |
| GET/PUT/PATCH/DELETE | `leads/{id}/` | CRUD lead |
| POST | `leads/{id}/convertir/` | Convertir lead → oportunidad (+ opcional Tercero) |
| POST | `leads/{id}/asignar/` | Asignar a vendedor (Round-Robin o manual) |
| POST | `leads/importar/` | Import CSV/Excel (multipart) |
| POST | `leads/webhook/` | Captura externa (sin auth, HMAC-SHA256 firmado) |

#### Oportunidades
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `oportunidades/` | Listar / crear |
| GET/PUT/PATCH/DELETE | `oportunidades/{id}/` | CRUD |
| POST | `oportunidades/{id}/mover-etapa/` | D&D Kanban → `{etapa_id}` |
| POST | `oportunidades/{id}/ganar/` | Marcar ganada |
| POST | `oportunidades/{id}/perder/` | Marcar perdida (requiere motivo) |
| GET | `oportunidades/{id}/timeline/` | Timeline completo |
| POST | `oportunidades/{id}/timeline/` | Agregar nota manual |
| POST | `oportunidades/{id}/enviar-email/` | Email SMTP + log en timeline |

#### Actividades
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `oportunidades/{id}/actividades/` | Actividades de una oportunidad |
| GET/PUT/PATCH/DELETE | `actividades/{id}/` | CRUD actividad |
| POST | `actividades/{id}/completar/` | Marcar completada + resultado |

#### Cotizaciones
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `oportunidades/{id}/cotizaciones/` | Cotizaciones de una oportunidad |
| GET/PUT/PATCH/DELETE | `cotizaciones/{id}/` | CRUD cotización |
| GET/POST | `cotizaciones/{id}/lineas/` | Líneas de cotización |
| PUT/DELETE | `cotizaciones/{id}/lineas/{linea_id}/` | CRUD línea |
| POST | `cotizaciones/{id}/enviar/` | Cambiar a 'enviada' + email PDF |
| POST | `cotizaciones/{id}/aceptar/` | Cambiar a 'aceptada' + sync Saiopen |
| POST | `cotizaciones/{id}/rechazar/` | Cambiar a 'rechazada' |
| GET | `cotizaciones/{id}/pdf/` | Descargar PDF (WeasyPrint) |

#### Productos e Impuestos (catálogo)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `productos/` | Buscar productos del catálogo |
| POST | `productos/sync/` | Forzar sync manual desde Saiopen (valmen_admin) |
| GET | `impuestos/` | Listar impuestos disponibles |

#### Dashboard y Analytics
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `dashboard/` | Métricas: funnel, forecast, actividades vencidas, top vendedores |
| GET | `dashboard/forecast/` | Desglose forecast por vendedor/pipeline |

#### Configuración (Scoring Rules)
| Método | Endpoint | Descripción |
|---|---|---|
| GET/POST | `scoring-rules/` | Reglas de Lead Scoring |
| PUT/DELETE | `scoring-rules/{id}/` | Editar / eliminar regla |

---

## 5. Estructura de Archivos

### Backend: `backend/apps/crm/`
```
crm/
├── __init__.py
├── apps.py
├── models.py                    ← todos los modelos
├── admin.py
├── filters.py
├── permissions.py
├── signals.py                   ← timeline events automáticos
├── serializers.py               ← pipeline, etapas, leads, oportunidades, actividades
├── cotizacion_serializers.py    ← cotizaciones + líneas
├── services.py                  ← PipelineService, LeadService, OportunidadService, ActividadService
├── cotizacion_services.py       ← CotizacionService, PDF, email
├── producto_services.py         ← ProductoSyncService (ITEM + TAXAUTH)
├── scoring_services.py          ← LeadScoringService
├── views.py                     ← vistas principales
├── cotizacion_views.py          ← vistas cotizaciones + PDF
├── urls.py
├── migrations/
└── tests/
    ├── __init__.py
    ├── test_services.py
    ├── test_cotizacion_services.py
    ├── test_scoring_services.py
    └── test_views.py
```

### Frontend: `frontend/src/app/features/crm/`
```
crm/
├── crm.routes.ts                         ← lazy loading
├── models/
│   ├── pipeline.model.ts
│   ├── etapa.model.ts
│   ├── lead.model.ts
│   ├── oportunidad.model.ts
│   ├── actividad.model.ts
│   ├── cotizacion.model.ts
│   └── producto.model.ts
├── services/
│   ├── pipeline.service.ts
│   ├── lead.service.ts
│   ├── oportunidad.service.ts
│   ├── cotizacion.service.ts
│   └── crm-dashboard.service.ts
└── pages/
    ├── crm-shell/                         ← layout con sidebar CRM
    ├── pipeline-kanban/                   ← Kanban principal (CDK DragDrop)
    │   ├── pipeline-kanban.component.ts
    │   ├── etapa-column/
    │   └── oportunidad-card/
    ├── leads/
    │   ├── lead-list/                     ← tabla paginada
    │   └── lead-import/                   ← wizard importación CSV
    ├── oportunidad-detail/                ← vista detalle con tabs
    │   ├── timeline-tab/
    │   ├── actividades-tab/
    │   └── cotizaciones-tab/
    ├── cotizacion-detail/                 ← editor de cotización + preview PDF
    ├── crm-dashboard/                     ← métricas + forecast
    └── crm-settings/                      ← pipelines, etapas, scoring rules
```

---

## 6. Sincronización Saiopen

### 6.1 Saiopen → SaiSuite (Pull, agente Windows)

| Entidad | Tabla Saiopen | Dirección | Trigger |
|---|---|---|---|
| `CrmProducto` | `ITEM` | Saiopen → CRM | Watermark `updated_at` / `INDATE` |
| `CrmImpuesto` | `TAXAUTH` | Saiopen → CRM | Sync diaria (referencia) |
| `CrmCotizacion` (anulaciones) | `COTIZACI.ANULAR` | Saiopen → CRM | Polling cada 15min |

**Mapping ITEM → CrmProducto:**
```
ITEM.ITEM          → sai_key, codigo
ITEM.DESCRIPCION   → nombre
ITEM.PRICE         → precio_base
ITEM.UOFMSALES     → unidad_venta
ITEM.IMPOVENTA     → busca CrmImpuesto.nombre == IMPOVENTA → FK impuesto
ITEM.CLASS         → clase
ITEM.GRUPO         → grupo
ITEM.ESTADO='True' → is_active=True
```

**Mapping TAXAUTH → CrmImpuesto:**
```
TAXAUTH.CODIGO     → sai_key
TAXAUTH.AUTHORITY  → nombre
TAXAUTH.RATE       → porcentaje
```

### 6.2 SaiSuite → Saiopen (Push, solo cotizaciones aceptadas)

**Trigger:** `CotizacionService.aceptar(cotizacion)` cambia estado → POST SQS mensaje tipo `crm_cotizacion_aceptada`

**Payload SQS:**
```json
{
  "type": "crm_cotizacion_aceptada",
  "company_id": "uuid",
  "data": {
    "cotizacion_id": "uuid",
    "id_cliente": "CUST.ID_N del Tercero",
    "total": 1500000.00,
    "subtotal": ...,
    "dcto_adc_p": 0,
    "total_iva": ...,
    "observaciones": "...",
    "fecha_vencimiento": "2026-05-10",
    "lineas": [
      {
        "conteo": 1,
        "cod_desc": "ITEM.ITEM del producto",
        "descripcion": "...",
        "cantidad": 2,
        "vlr_unitario": 500000,
        "desctop": 0,
        "iva": 0.19,
        "iva_valor": ...,
        "total_parc": ...
      }
    ]
  }
}
```

**Respuesta del agente (SQS response):**
```json
{
  "sai_numero": 1042,
  "sai_tipo": "COT",
  "sai_empresa": 1,
  "sai_sucursal": 1
}
```
→ Django actualiza `CrmCotizacion.sai_key`, `sai_numero`, `saiopen_synced=True`

---

## 7. Permisos por Rol

| Rol | Pipeline | Leads | Oportunidades | Cotizaciones | Dashboard | Config |
|---|---|---|---|---|---|---|
| `valmen_admin` | CRUD | CRUD | CRUD | CRUD | ✅ | ✅ |
| `company_admin` | CRUD | CRUD | CRUD | CRUD | ✅ | ✅ |
| `seller` | Read | CRUD (propio) | CRUD (propio) | CRUD (propio) | Read | ❌ |
| `viewer` | Read | Read | Read | Read | ✅ | ❌ |
| otros | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

*"CRUD propio" = puede leer todos pero solo crear/editar/eliminar donde es `asignado_a`*

Permisos Django a registrar: `crm.view_*`, `crm.add_*`, `crm.change_*`, `crm.delete_*`  
Permisos custom: `crm.import_leads`, `crm.sync_productos`, `crm.export_pdf_cotizacion`

---

## 8. Registro en Licencias (Fase 10)

```python
# En migración de datos de licencias:
Module.objects.get_or_create(
    code='crm',
    defaults={
        'name': 'CRM',
        'description': 'Gestión de relaciones con clientes: pipeline, leads, cotizaciones',
        'icon': 'contacts',
        'route': '/crm',
    }
)
```

Guard Angular: `moduleAccessGuard` con `data: { requiredModule: 'crm' }`  
Menú: icono `contacts`, ruta `/crm`, grupo "Ventas"

---

## 9. Checklist de Implementación por Fase

### Fase 4 — Implementación (secuencia de features verticales)

**Feature 1: Pipeline + Etapas (base)**
- [ ] `models.py`: CrmPipeline, CrmEtapa
- [ ] migration
- [ ] `services.py`: PipelineService (CRUD + default pipeline por empresa)
- [ ] `serializers.py`: PipelineSerializer, EtapaSerializer
- [ ] `views.py`: PipelineViewSet, EtapaViewSet
- [ ] `urls.py`
- [ ] tests: test_pipeline_service.py
- [ ] Frontend: crm-settings/pipelines, CrmPipeline model.ts, service.ts

**Feature 2: Leads + Scoring**
- [ ] `models.py`: CrmLead, CrmLeadScoringRule
- [ ] migration
- [ ] `scoring_services.py`: LeadScoringService
- [ ] `services.py`: LeadService (CRUD, import CSV, webhook, round-robin)
- [ ] `serializers.py`: LeadSerializer
- [ ] tests
- [ ] Frontend: leads/, lead-list, lead-import wizard

**Feature 3: Oportunidades + Kanban**
- [ ] `models.py`: CrmOportunidad
- [ ] migration
- [ ] `services.py`: OportunidadService (mover etapa, ganar, perder)
- [ ] `signals.py`: auto-crear CrmTimelineEvent en cambios de etapa
- [ ] `serializers.py`: OportunidadSerializer, KanbanSerializer
- [ ] views: kanban endpoint (agrupado + virtual scroll compatible)
- [ ] tests
- [ ] Frontend: pipeline-kanban (CDK DragDrop), oportunidad-card

**Feature 4: Actividades + Timeline**
- [ ] `models.py`: CrmActividad, CrmTimelineEvent
- [ ] migration
- [ ] `services.py`: ActividadService, TimelineService
- [ ] `signals.py`: eventos auto en actividades completadas
- [ ] tests
- [ ] Frontend: timeline-tab, actividades-tab, oportunidad-detail

**Feature 5: Productos + Impuestos (sync Saiopen)**
- [ ] `models.py`: CrmImpuesto, CrmProducto
- [ ] migration
- [ ] `producto_services.py`: ProductoSyncService
- [ ] Extender `SYNC_GRAPH` en agente Python (ITEM + TAXAUTH)
- [ ] tests
- [ ] Frontend: búsqueda de productos en cotizacion-detail

**Feature 6: Cotizaciones + PDF**
- [ ] `models.py`: CrmCotizacion, CrmLineaCotizacion
- [ ] migration
- [ ] `cotizacion_services.py`: CotizacionService (CRUD + calcular totales + PDF + email)
- [ ] `cotizacion_services.py`: SyncCotizacionService (push a Saiopen al aceptar)
- [ ] Template PDF (WeasyPrint)
- [ ] tests
- [ ] Frontend: cotizacion-detail editor, preview PDF

**Feature 7: Dashboard + Forecast**
- [ ] `services.py`: DashboardService (métricas, forecast)
- [ ] tests
- [ ] Frontend: crm-dashboard con widgets MatCard + charts

---

## 10. Dependencias Externas

| Paquete | Uso | ¿Ya instalado? |
|---|---|---|
| `weasyprint` | PDF cotizaciones | Verificar |
| `openpyxl` | Import CSV/Excel leads | Verificar |
| `angular/cdk` | DragDrop Kanban | ✅ |
| `@angular/material` | Todo el UI | ✅ |

---

## 11. Preguntas resueltas del PO

| # | Pregunta | Respuesta |
|---|---|---|
| 1 | Schema COTIZACIONES | ✅ `cotizaci.txt` + `det_prod.txt` — mapeados |
| 2 | Catálogo productos | ✅ `ITEM` de Saiopen, bidireccional (ITEM→CRM en sync) |
| 3 | Cotización CRM vs Saiopen | ✅ CRM gestiona ciclo; push a Saiopen solo al aceptar |
| 4 | Roles | ✅ Permisos sobre roles existentes (company_admin, seller, viewer) |
| 5 | Schema TAXAUTH | ✅ `taxauth.txt` — mapeado a CrmImpuesto |

---

*PLAN técnico generado por Orquestador Saicloud — Fase 1 — 10 Abril 2026*
