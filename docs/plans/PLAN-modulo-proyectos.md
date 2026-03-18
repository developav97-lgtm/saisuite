# 📋 Plan de Desarrollo — Módulo de Proyectos

> **Fecha:** 17 Marzo 2026  
> **Estado:** ✅ Planificación Completada — Pendiente Aprobación  
> **Complejidad:** L (Large) — 3-4 semanas  

---

## 📌 Resumen Ejecutivo

**Problema que resuelve:**  
Saiopen solo permite asignar proyectos/actividades a documentos contables para clasificación (imputación), pero **NO tiene gestión de ejecución**: sin fases, cronogramas, presupuestos detallados por etapa, terceros vinculados con roles, ni análisis de rentabilidad.

**Solución:**  
Módulo de Proyectos en Saicloud que complementa Saiopen con:
- ✅ Gestión de fases con presupuestos detallados (mano de obra, materiales, subcontratos, equipos)
- ✅ Cronogramas y seguimiento de avance físico/financiero
- ✅ Terceros vinculados al proyecto (cliente, subcontratistas, proveedores, consultores, interventores)
- ✅ Consumo automático de documentos contables generados en Saiopen
- ✅ Facturación por avance/hitos
- ✅ Cálculo de AIU (Administración, Imprevistos, Utilidad)
- ✅ Reportes de rentabilidad por proyecto y fase

**Usuarios objetivo:**
- Gerente de Proyectos (crea, define fases, asigna presupuestos, seguimiento)
- Director Financiero (rentabilidad, aprobaciones, desviaciones)
- Coordinador de Obra/Consultoría (actualiza avances, reporta costos)
- Contador (consulta docs contables, imputación)

---

## 🏗️ Arquitectura Decidida

### Híbrido: Django (core) + Go microservice (agente Saiopen)

**Django (Backend Principal)**
- App: `backend/apps/proyectos/`
- CRUD completo de proyectos, fases, terceros, presupuestos
- 27 endpoints REST para Angular
- Consumo de docs contables sincronizados desde Saiopen
- Reportes y dashboards financieros
- Gestión de usuarios y permisos
- Admin panel

**Go Microservice: "saiopen-agent"**
- Ubicación: `backend/microservices/saiopen-agent/`
- **Justificación:** Criterio 3 cumplido (Ejecutable standalone) + Criterio 2 parcial (procesamiento batch)
  - ✅ Agente instalado en PC Windows del cliente (binario .exe ~10-15MB)
  - ✅ Sin dependencias Python (distribución simple)
  - ✅ Actualizaciones: reemplazar .exe vs gestionar pip/venv
  - ✅ Instalación como servicio Windows
  - ✅ Auto-actualización consultando `/api/v1/sync/version/`
- **Responsabilidades:**
  1. Sincronizar proyectos creados en Saicloud → tabla de proyectos/actividades en Firebird
  2. Polling de documentos contables en Saiopen con código de proyecto
  3. Enviar batch de docs a Django vía POST `/api/v1/sync/documentos/`
  4. Recibir solicitudes de facturación y crearlas en Saiopen
  5. Reportar status/health a Django

**Comunicación:**
- Django → Go: REST (Django expone `/api/v1/sync/status/` para heartbeat)
- Go → Django: REST (Go POST batch a `/api/v1/sync/proyectos/`, `/api/v1/sync/documentos/`)
- Go → Firebird: Conexión directa (go-firebirdsql)
- Autenticación: JWT generado por Django para el agente

---

## 🔌 Contrato API — 27 Endpoints

### Proyectos (7 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| GET | `/api/v1/proyectos/` | Listar proyectos (paginado, filtros) | JWT |
| POST | `/api/v1/proyectos/` | Crear proyecto | JWT |
| GET | `/api/v1/proyectos/{id}/` | Detalle proyecto | JWT |
| PATCH | `/api/v1/proyectos/{id}/` | Actualizar proyecto | JWT |
| DELETE | `/api/v1/proyectos/{id}/` | Eliminar proyecto (soft delete) | JWT |
| POST | `/api/v1/proyectos/{id}/cambiar-estado/` | Cambiar estado del proyecto | JWT |
| GET | `/api/v1/proyectos/{id}/estado-financiero/` | Reporte financiero del proyecto | JWT |

### Fases (4 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| GET | `/api/v1/proyectos/{id}/fases/` | Listar fases del proyecto | JWT |
| POST | `/api/v1/proyectos/{id}/fases/` | Crear fase | JWT |
| PATCH | `/api/v1/fases/{id}/` | Actualizar fase | JWT |
| DELETE | `/api/v1/fases/{id}/` | Eliminar fase | JWT |

### Terceros Vinculados (3 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| GET | `/api/v1/proyectos/{id}/terceros/` | Listar terceros del proyecto | JWT |
| POST | `/api/v1/proyectos/{id}/terceros/` | Vincular tercero | JWT |
| DELETE | `/api/v1/proyectos/{id}/terceros/{tercero_id}/` | Desvincular tercero | JWT |

### Documentos Contables (2 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| GET | `/api/v1/proyectos/{id}/documentos/` | Docs contables del proyecto | JWT |
| GET | `/api/v1/documentos/{id}/` | Detalle documento | JWT |

### Hitos y Facturación (3 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| GET | `/api/v1/proyectos/{id}/hitos/` | Hitos facturables | JWT |
| POST | `/api/v1/proyectos/{id}/hitos/` | Crear hito | JWT |
| POST | `/api/v1/hitos/{id}/generar-factura/` | Solicitar factura en Saiopen | JWT |

### Reportes (2 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| GET | `/api/v1/reportes/proyectos/` | Dashboard general de proyectos | JWT |
| GET | `/api/v1/reportes/rentabilidad/` | Top proyectos rentables | JWT |

### Sync (para agente Go) (3 endpoints)
| Método | URL | Descripción | Auth |
|--------|-----|----------------|------|
| POST | `/api/v1/sync/proyectos/` | Batch de proyectos desde Saiopen | JWT |
| POST | `/api/v1/sync/documentos/` | Batch de docs desde Saiopen | JWT |
| GET | `/api/v1/sync/status/` | Status del agente | JWT |

**Autenticación:** JWT obligatorio en todos los endpoints

**Paginación:** PageNumberPagination, page_size=20

**Filtros (proyectos):** estado, tipo, cliente, rango de fechas, responsable

**Búsqueda:** código, nombre, cliente

---

## 🗃️ Modelos de Datos (PostgreSQL)

### 1. Proyecto
```python
class Proyecto(BaseModel):  # UUID PK, created_at, updated_at
    tenant = ForeignKey(Tenant)
    codigo = CharField(max_length=50, unique=True)  # Sync con Saiopen
    nombre = CharField(max_length=255)
    tipo = CharField(choices=TipoProyecto)  # obra_civil, consultoria, manufactura, servicios, licitacion_publica, otro
    estado = CharField(choices=EstadoProyecto, default='borrador')  # borrador, planificado, en_ejecucion, suspendido, cerrado, cancelado
    
    # Cliente principal
    cliente_id = CharField(max_length=50)  # NIT/ID en Saiopen
    cliente_nombre = CharField(max_length=255)
    
    # Responsables
    gerente = ForeignKey(User, related_name='proyectos_gerente')
    coordinador = ForeignKey(User, null=True, related_name='proyectos_coordinador')
    
    # Fechas
    fecha_inicio_planificada = DateField()
    fecha_fin_planificada = DateField()
    fecha_inicio_real = DateField(null=True)
    fecha_fin_real = DateField(null=True)
    
    # Presupuesto
    presupuesto_total = DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # AIU
    porcentaje_administracion = DecimalField(max_digits=5, decimal_places=2, default=10.00)
    porcentaje_imprevistos = DecimalField(max_digits=5, decimal_places=2, default=5.00)
    porcentaje_utilidad = DecimalField(max_digits=5, decimal_places=2, default=10.00)
    
    # Sincronización con Saiopen
    saiopen_proyecto_id = CharField(max_length=50, null=True)
    sincronizado_con_saiopen = BooleanField(default=False)
    ultima_sincronizacion = DateTimeField(null=True)
    
    activo = BooleanField(default=True)
```

### 2. Fase
```python
class Fase(BaseModel):
    proyecto = ForeignKey(Proyecto, related_name='fases')
    nombre = CharField(max_length=255)
    descripcion = TextField(blank=True)
    orden = PositiveIntegerField(default=0)
    
    # Fechas
    fecha_inicio_planificada = DateField()
    fecha_fin_planificada = DateField()
    fecha_inicio_real = DateField(null=True)
    fecha_fin_real = DateField(null=True)
    
    # Presupuesto por categoría
    presupuesto_mano_obra = DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_materiales = DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_subcontratos = DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_equipos = DecimalField(max_digits=15, decimal_places=2, default=0)
    presupuesto_otros = DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Avance
    porcentaje_avance = DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    
    activo = BooleanField(default=True)
```

### 3. TerceroProyecto
```python
class TerceroProyecto(BaseModel):
    proyecto = ForeignKey(Proyecto, related_name='terceros')
    tercero_id = CharField(max_length=50)  # NIT/ID en Saiopen
    tercero_nombre = CharField(max_length=255)
    rol = CharField(choices=RolTercero)  # cliente, subcontratista, proveedor, consultor, interventor, supervisor
    fase = ForeignKey(Fase, null=True, related_name='terceros')
    
    activo = BooleanField(default=True)
    
    class Meta:
        unique_together = ['proyecto', 'tercero_id', 'rol', 'fase']
```

### 4. DocumentoContable
```python
class DocumentoContable(BaseModel):
    tenant = ForeignKey(Tenant)
    proyecto = ForeignKey(Proyecto, related_name='documentos')
    fase = ForeignKey(Fase, null=True, related_name='documentos')
    
    # Datos del documento en Saiopen
    saiopen_doc_id = CharField(max_length=100, unique=True)
    tipo_documento = CharField(choices=TipoDocumento)  # factura_venta, factura_compra, orden_compra, recibo_caja, comprobante_egreso, nomina, anticipo, acta_obra
    numero_documento = CharField(max_length=100)
    fecha_documento = DateField()
    
    # Tercero
    tercero_id = CharField(max_length=50)
    tercero_nombre = CharField(max_length=255)
    
    # Montos
    valor_bruto = DecimalField(max_digits=15, decimal_places=2)
    valor_descuento = DecimalField(max_digits=15, decimal_places=2, default=0)
    valor_neto = DecimalField(max_digits=15, decimal_places=2)
    
    observaciones = TextField(blank=True)
    sincronizado_desde_saiopen = DateTimeField(auto_now_add=True)
```

### 5. Hito
```python
class Hito(BaseModel):
    proyecto = ForeignKey(Proyecto, related_name='hitos')
    fase = ForeignKey(Fase, null=True)
    
    nombre = CharField(max_length=255)
    descripcion = TextField(blank=True)
    porcentaje_proyecto = DecimalField(max_digits=5, decimal_places=2)  # % del proyecto total
    valor_facturar = DecimalField(max_digits=15, decimal_places=2)
    
    # Facturación
    facturable = BooleanField(default=True)
    facturado = BooleanField(default=False)
    documento_factura = ForeignKey(DocumentoContable, null=True)
    fecha_facturacion = DateField(null=True)
```

---

## ⚖️ Reglas de Negocio

1. **Código de proyecto único:** Al crear proyecto en Saicloud, generar código único que se sincroniza a Saiopen
2. **Presupuesto de fases ≤ presupuesto total:** Validar que suma de presupuestos de fases no exceda presupuesto total
3. **AIU:** Precio de venta = Costos directos × (1 + %admin + %imprevistos + %utilidad)
4. **Cambio de estado con validaciones:**
   - Borrador → Planificado: Debe tener ≥1 fase y presupuesto definido
   - Planificado → En Ejecución: Debe estar sincronizado con Saiopen
   - En Ejecución → Cerrado: Todas las fases completadas (100% avance) o justificadas
5. **Soft delete:** Proyectos eliminados marcan `activo=False`
6. **Docs contables solo se asocian a proyectos sincronizados**
7. **Facturación por hitos:** Al marcar hito "facturado", generar solicitud al agente Go para que Saiopen cree factura
8. **Terceros vinculados:** Un tercero puede tener múltiples roles en el mismo proyecto

---

## 🔄 Integración con Saiopen (vía Agente Go)

### Flujo de Sincronización

**1. Proyecto creado en Saicloud →**
- Agente detecta nuevo proyecto (polling cada 5 min)
- Crea registro en tabla de proyectos/actividades de Firebird
- Actualiza `saiopen_proyecto_id` en Saicloud

**2. Documento generado en Saiopen →**
- Agente detecta docs con código de proyecto asignado
- Extrae datos: tipo, número, fecha, tercero, montos
- Envía batch a `/api/v1/sync/documentos/`
- Django crea `DocumentoContable` asociado al proyecto

**3. Solicitud de factura desde Saicloud →**
- Usuario marca hito como "facturado"
- Django envía request a agente Go
- Agente crea factura en Saiopen
- Saiopen genera factura → agente la detecta → sincroniza a Saicloud

### Instalación del Agente

- Binario Windows .exe (~10-15MB)
- Instalador NSIS con configuración inicial:
  - URL de Saicloud API
  - Credenciales de sync (JWT)
  - Ruta de base de datos Firebird local
- Se registra como servicio Windows
- Auto-actualización: consulta `/api/v1/sync/version/` y descarga nuevo .exe si aplica

---

## 🔧 Integraciones n8n

### Workflow 1: Alerta de Sobrecosto
- **Trigger:** Webhook desde Django cuando `costo_real > presupuesto × 1.1`
- **Acción:** Email al gerente + notificación Slack

### Workflow 2: Proyectos Próximos a Vencer
- **Trigger:** Scheduled (diario 8am)
- **Acción:** Query `/api/v1/proyectos/?estado=en_ejecucion&dias_para_vencer_lte=7`
- **Output:** Resumen por email

### Workflow 3: Sync Stats a Notion
- **Trigger:** Scheduled (semanal, domingos)
- **Acción:** GET `/api/v1/reportes/proyectos/`, crear página en Notion con stats

---

## 📁 Estructura de Archivos a Crear

### Backend Django (15 archivos)
```
backend/apps/proyectos/
├── models.py                    # 5 modelos (Proyecto, Fase, TerceroProyecto, DocumentoContable, Hito)
├── serializers.py               # 5 serializers
├── views.py                     # 5 ViewSets
├── services.py                  # Lógica de negocio (validaciones, cálculos AIU, cambios de estado)
├── urls.py                      # Router DRF
├── permissions.py               # Permisos custom por rol
├── filters.py                   # django-filter (estado, tipo, cliente, fechas)
├── admin.py                     # Registro de 5 modelos en Django Admin
├── apps.py                      # AppConfig
└── tests/
    ├── test_models.py           # Tests de validaciones de modelos
    ├── test_serializers.py      # Tests de serializers
    ├── test_services.py         # Tests de lógica de negocio
    ├── test_views.py            # Tests de endpoints
    └── test_sync.py             # Tests de sincronización con Saiopen
```

### Backend Go (12 archivos)
```
backend/microservices/saiopen-agent/
├── main.go                      # Entry point, HTTP server
├── config/
│   └── config.go                # Configuración (URLs, credenciales, polling interval)
├── handlers/
│   ├── sync.go                  # Handlers HTTP para comunicación con Django
│   └── firebird.go              # Handlers para queries Firebird
├── models/
│   ├── proyecto.go              # Struct Proyecto
│   └── documento.go             # Struct DocumentoContable
├── services/
│   ├── sync_service.go          # Lógica de sincronización bidireccional
│   └── firebird_service.go      # Conexión y queries a Firebird
├── Dockerfile                   # Build optimizado multi-stage
├── go.mod                       # Dependencies
├── go.sum
├── README.md                    # Justificación técnica, instalación, configuración
└── install/
    └── setup.nsi                # Instalador NSIS para Windows
```

### Frontend Angular (25 archivos)
```
frontend/src/app/features/proyectos/
├── proyectos.routes.ts          # Standalone routes
├── components/
│   ├── proyecto-list/
│   │   ├── proyecto-list.component.ts
│   │   ├── proyecto-list.component.html
│   │   ├── proyecto-list.component.scss
│   │   └── proyecto-list.component.spec.ts
│   ├── proyecto-detail/
│   │   ├── proyecto-detail.component.ts
│   │   ├── proyecto-detail.component.html
│   │   ├── proyecto-detail.component.scss
│   │   └── proyecto-detail.component.spec.ts
│   ├── proyecto-form/
│   │   ├── proyecto-form.component.ts
│   │   ├── proyecto-form.component.html
│   │   ├── proyecto-form.component.scss
│   │   └── proyecto-form.component.spec.ts
│   ├── fase-list/
│   ├── tercero-list/
│   └── dashboard-financiero/
├── services/
│   ├── proyecto.service.ts
│   ├── proyecto.service.spec.ts
│   ├── fase.service.ts
│   └── fase.service.spec.ts
├── models/
│   ├── proyecto.model.ts
│   ├── fase.model.ts
│   ├── tercero-proyecto.model.ts
│   └── documento-contable.model.ts
└── guards/
    └── proyecto-access.guard.ts
```

**Total:** 52 archivos

---

## 📊 Estimación Detallada

**Complejidad:** L (Large)

### Desglose por Componente

**Backend Django (1 semana):**
- Modelos + migraciones: 1 día
- Serializers + services: 2 días
- Views + URLs + permisos + filtros: 2 días
- Tests: 2 días

**Backend Go (1 semana):**
- Setup proyecto + config: 0.5 días
- Conexión Firebird + queries: 1 día
- Lógica de sync bidireccional: 2 días
- Handlers HTTP + comunicación Django: 1 día
- Instalador NSIS: 1 día
- Tests: 1.5 días

**Frontend Angular (1.5 semanas):**
- Módulo + routing + servicios: 1 día
- Componentes lista/detalle/form (3 × 6 componentes): 4 días
- Dashboard financiero: 2 días
- Tests: 1.5 días

**n8n Workflows (0.5 días):**
- 3 workflows: 0.5 días

**Total:** 3-4 semanas (1 desarrollador full-time)

### Riesgos
- Complejidad de sincronización bidireccional con Firebird
- Instalador Windows puede requerir pruebas en múltiples versiones de Windows
- Validaciones de presupuesto pueden generar edge cases

---

## ✅ Checklist de Aprobación

**Antes de continuar a Fase 2:**
- [x] Requerimientos funcionales documentados
- [x] Contrato API definido (27 endpoints)
- [x] Modelos de datos diseñados (5 modelos)
- [x] Reglas de negocio identificadas (8 reglas)
- [x] Permisos y roles definidos
- [x] Integraciones n8n identificadas (3 workflows)
- [x] Estimación de complejidad (L — 3-4 semanas)
- [x] Lista de archivos a crear (52 archivos)
- [x] Evaluación Django vs Go completada
- [x] Justificación Go documentada (Criterio 3 cumplido)
- [x] Contrato de comunicación Django ↔ Go definido
- [x] **Archivo PLAN.md generado en `docs/plans/`**
- [ ] **README.md del agente Go con justificación técnica**
- [ ] **Aprobación final del usuario para continuar a Fase 2**

---

## 🔗 Referencias

- Decisiones Arquitectónicas: `DECISIONS.md` (DEC-001 a DEC-009)
- DEC-009: Arquitectura Híbrida Django + Go
- Metodología: 10 fases documentadas en Notion
- Notion Page: [Módulo de Proyectos](https://www.notion.so/327ee9c3690a81f296a2ec384b557049)

---

*Documento generado: 17 Marzo 2026*  
*Próxima fase: Gestión de Contexto*
