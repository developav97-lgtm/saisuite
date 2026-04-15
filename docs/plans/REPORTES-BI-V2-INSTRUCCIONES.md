# REPORTES BI v2 — Instrucciones para Planificación y Diseño

**Tipo:** IMPROVEMENT (mejoras mayores + features nuevas)
**Módulo:** Dashboard / Reportes BI
**Fecha:** 12 Abril 2026
**Prioridad:** Alta — Estas mejoras transforman el builder de reportes en una herramienta BI real

---

## Contexto Actual

El módulo de Reportes BI tiene:
- Modelo `ReportBI` con `fuentes` (JSON list), `campos_config`, `filtros`, `tipo_visualizacion`
- Modelo `ReportBIShare` para compartir reportes (ya existe en models.py)
- `BIQueryEngine` en `bi_engine.py` con `SOURCE_MODEL_MAP` (gl, facturacion, facturacion_detalle, cartera, inventario, terceros)
- `SOURCE_FIELDS` con campos por fuente organizados por categoría
- 12 templates predefinidos en `bi_templates.py`
- Frontend: `report-builder`, `report-viewer`, `report-list`, `field-panel`
- Dashboard con tarjetas (`DashboardCard`) alimentadas por `ReportEngine` (report_engine.py) con 30+ tipos hardcodeados
- CFO Virtual con endpoint `suggest-report`
- El usuario puede seleccionar múltiples fuentes de datos y campos, pero **NO se ejecutan JOINs entre tablas**

### Estado de modelos sincronizados desde Saiopen (Firebird)

| App | Modelo | Tabla Firebird | Sync |
|---|---|---|---|
| contabilidad | `MovimientoContable` | GL | ✅ Activo |
| contabilidad | `FacturaEncabezado` | OE | ✅ Activo |
| contabilidad | `FacturaDetalle` | OEDET | ✅ Activo |
| contabilidad | `MovimientoCartera` | CARPRO | ✅ Activo |
| contabilidad | `MovimientoInventario` | ITEMACT | ✅ Activo |
| contabilidad | `TerceroSaiopen` | CUST | ✅ Activo |
| contabilidad | `ShipToSaiopen` | SHIPTO | ✅ Activo |
| contabilidad | `CuentaContable` | ACCT | ✅ Activo |
| contabilidad | `ListaSaiopen` | LISTA (DP/CC) | ✅ Activo |
| contabilidad | `ProyectoSaiopen` | PROYECTOS | ✅ Activo |
| contabilidad | `ActividadSaiopen` | ACTIVIDADES | ✅ Activo |
| contabilidad | `TipdocSaiopen` | TIPDOC | ✅ Activo |
| crm | `CrmProducto` | ITEM | ✅ Activo (vía ProductoSyncService) |
| crm | `CrmImpuesto` | TAXAUTH | ✅ Activo |

---

## BLOQUE 1: JOINS AUTOMÁTICOS ENTRE FUENTES (BUG CRÍTICO / FEATURE)

### Problema
El usuario selecciona múltiples fuentes (ej: `facturacion_detalle` + `inventario`), elige campos de ambas, pero el sistema no relaciona las tablas. Los datos no se cruzan ni aparecen en la tabla resultante.

### Solución Requerida

**1.1 — Definir mapa de relaciones entre fuentes (backend)**

Crear un `SOURCE_JOINS_MAP` en `bi_engine.py` que defina las relaciones automáticas entre tablas SAI. Las relaciones conocidas son:

| Fuente A | Fuente B | Campos de unión (A → B) |
|---|---|---|
| `facturacion` | `facturacion_detalle` | `FacturaEncabezado.pk` = `FacturaDetalle.factura_id` (FK directa) |
| `facturacion_detalle` | `inventario` | `item_codigo` + `tipo` + `batch` ↔ `item_codigo` + `tipo` + `batch` |
| `facturacion` | `terceros_saiopen` | `tercero_id` ↔ `id_n` |
| `facturacion` | `cartera` | `tercero_id` + `tipo` + `batch` ↔ `tercero_id` + `tipo` + `batch` |
| `gl` | `terceros_saiopen` | `tercero_id` ↔ `id_n` |
| `gl` | `cartera` | `tercero_id` + `tipo` + `batch` ↔ `tercero_id` + `tipo` + `batch` |
| `cartera` | `terceros_saiopen` | `tercero_id` ↔ `id_n` |
| `inventario` | `terceros_saiopen` | `tercero_id` ↔ `id_n` |
| `inventario` | `productos` | `item_codigo` ↔ `codigo` (CrmProducto.codigo) |
| `facturacion_detalle` | `productos` | `item_codigo` ↔ `codigo` (CrmProducto.codigo) |
| `gl` | `cuentas_contables` | `auxiliar` ↔ `codigo` |
| `gl` | `proyectos_saiopen` | `proyecto_codigo` ↔ `codigo` |
| `gl` | `actividades_saiopen` | `actividad_codigo` ↔ `codigo` |
| `gl` | `departamentos` | `departamento_codigo` ↔ `codigo` (ListaSaiopen tipo=DP) |
| `gl` | `centros_costo` | `centro_costo_codigo` ↔ `codigo` (ListaSaiopen tipo=CC) |
| `terceros_saiopen` | `direcciones_envio` | `id_n` ↔ `id_n` (ShipToSaiopen) |
| `productos` | `impuestos` | `CrmProducto.impuesto_id` ↔ `CrmImpuesto.id` (FK) |

**1.2 — Implementar JOINs en BIQueryEngine**

Cuando el usuario selecciona campos de múltiples fuentes, el engine debe:
1. Identificar una fuente principal (la primera seleccionada o la que tiene más campos)
2. Buscar en `SOURCE_JOINS_MAP` la ruta de unión entre fuentes
3. Aplicar los JOINs vía Django ORM (`select_related`, `Subquery`, o `annotations` según el caso)
4. Si no existe relación directa entre dos fuentes → error informativo al usuario

**1.3 — Endpoint de relaciones (metadata)**

`GET /api/v1/dashboard/reportes/meta/joins/` — Retorna las relaciones disponibles entre fuentes para que el frontend pueda mostrar cómo se conectan las tablas.

---

## BLOQUE 2: NUEVAS FUENTES DE DATOS

### 2.1 — Agregar Productos como fuente

**IMPORTANTE — Decisión arquitectónica requerida:**

Actualmente los productos sincronizados desde Saiopen (tabla ITEM de Firebird) viven en `crm.CrmProducto`. Este modelo YA tiene campos de sync (`sai_key`, `saiopen_synced`, `ultima_sync`) y se sincroniza vía `ProductoSyncService` en `crm/producto_services.py`. Funciona de forma similar a como `TerceroSaiopen` en contabilidad maneja los terceros.

Sin embargo, a diferencia de terceros donde existe `contabilidad.TerceroSaiopen` (espejo de CUST) Y `terceros.Tercero` (modelo operativo SaiSuite), para productos solo existe `CrmProducto` que cumple ambos roles (espejo de ITEM + modelo operativo CRM).

**Opción A (recomendada — menor riesgo):** Usar `crm.CrmProducto` directamente como fuente en el BI engine. Ya tiene los datos de ITEM sincronizados. Es la ruta más rápida.

```python
'productos': 'crm.CrmProducto',
```

**Opción B (consistencia arquitectónica — mayor esfuerzo):** Crear un `ItemSaiopen` en contabilidad (como `TerceroSaiopen`) que sea el espejo puro de ITEM, y que `CrmProducto` se alimente de este. Esto es más consistente con el patrón de terceros pero implica migración, nuevo modelo, nuevo sync.

**El equipo debe decidir esto en fase de planificación y registrar en DECISIONS.md.**

Campos disponibles para BI: `codigo`, `nombre`, `descripcion`, `precio_base`, `unidad_venta`, `clase`, `grupo`, `is_active`

### 2.2 — Agregar Terceros Saiopen con Direcciones de Envío

Los terceros para BI deben venir de `contabilidad.TerceroSaiopen` (espejo de CUST), NO de `terceros.Tercero` (modelo operativo). Esto porque `TerceroSaiopen` tiene los datos crudos de Saiopen que coinciden con las llaves de facturación, GL, cartera e inventario.

```python
'terceros_saiopen': 'contabilidad.TerceroSaiopen',
'direcciones_envio': 'contabilidad.ShipToSaiopen',
```

Campos TerceroSaiopen: `id_n`, `nit`, `nombre`, `direccion`, `ciudad`, `departamento`, `telefono`, `email`, `es_cliente`, `es_proveedor`, `es_empleado`, `creditlmt`, `regimen`

Campos ShipToSaiopen: `succliente`, `descripcion`, `nombre`, `addr1`, `addr2`, `ciudad`, `departamento`, `cod_dpto`, `cod_municipio`, `telefono`, `email`, `zona`

Relación: `ShipToSaiopen.id_n` = `TerceroSaiopen.id_n`

### 2.3 — Agregar fuentes dimensionales ya sincronizadas

```python
'cuentas_contables': 'contabilidad.CuentaContable',
'proyectos_saiopen': 'contabilidad.ProyectoSaiopen',
'actividades_saiopen': 'contabilidad.ActividadSaiopen',
'departamentos_cc': 'contabilidad.ListaSaiopen',  # tipo=DP o CC
'tipos_documento': 'contabilidad.TipdocSaiopen',
```

Estas fuentes se usan principalmente para enriquecer reportes vía JOINs (traer descripciones, datos adicionales de dimensiones).

---

## BLOQUE 3: REDISEÑO UX — PANEL DE CAMPOS

### Problema Actual
Los campos se muestran en acordeones por fuente. Con múltiples fuentes y JOINs es confuso e inmanejable.

### Solución Requerida

**3.1 — Listado scrolleable unificado**

Reemplazar los acordeones por un listado vertical scrolleable donde cada campo muestre:
- Nombre del campo
- Badge/chip indicando la tabla de origen (ej: `GL`, `Facturación`, `Inventario`, `Producto`)
- Ícono de tipo (texto, número, fecha, booleano)
- Indicador si es dimensión o métrica

**3.2 — Buscador de campos**

Input de búsqueda en la parte superior del panel que filtre campos en tiempo real por nombre o tabla de origen.

**3.3 — Campos calculados/personalizados**

- Botón "Crear campo calculado" que abre un modal
- En el modal: nombre del campo, fórmula (con selector de campos disponibles)
- Las fórmulas pueden operar entre campos de diferentes tablas (ej: `facturacion_detalle.precio_unitario - inventario.costo_peps`)
- Los campos calculados aparecen en el listado con un badge/chip especial que diga "Calculado" y un ícono diferenciador
- Se persisten en `campos_config` del `ReportBI` con `type: 'calculated'`
- CRUD completo de campos calculados dentro del builder

**3.4 — Indicador visual de relaciones**

Cuando se seleccionan campos de múltiples fuentes, mostrar un indicador visual de cómo están conectadas las tablas (mini diagrama o texto: "Facturación Detalle → conectada con Inventario vía item_codigo").

---

## BLOQUE 4: FILTROS FLEXIBLES (REDISEÑO)

### Problema Actual
Los filtros son limitados y predefinidos. El usuario no puede filtrar por cualquier campo ni elegir el tipo de filtro.

### Solución Requerida

**4.1 — Cualquier campo puede ser filtro**

Todos los campos disponibles (de cualquier fuente seleccionada) deben poder usarse como filtro.

**4.2 — Tipos de filtro configurables por el usuario**

Al agregar un filtro, el usuario selecciona:

| Tipo de campo | Operadores disponibles |
|---|---|
| **Texto** | `igual a`, `contiene`, `empieza con`, `termina con`, `en lista` (selección múltiple), `diferente de` |
| **Numérico** | `igual a`, `mayor que`, `menor que`, `mayor o igual`, `menor o igual`, `entre` (desde/hasta), `en lista` |
| **Fecha** | `igual a`, `entre` (desde/hasta), `mayor que`, `menor que`, `en período` (seleccionar período contable) |
| **Booleano** | `es verdadero`, `es falso` |

**4.3 — UX del builder de filtros**

- El usuario hace clic en "Agregar filtro"
- Selecciona el campo (con buscador, mostrando la fuente/tabla de origen)
- Selecciona el operador (según tipo de campo)
- Ingresa el/los valores
- Cada filtro agregado se muestra como chip removible con resumen (ej: "Tercero ID ∈ [1001, 1002]")
- Soporte para múltiples filtros combinados con AND (y en futuro OR)

**4.4 — Persistencia**

Los filtros se guardan en el campo `filtros` (JSON) del `ReportBI` con estructura:
```json
[
  {
    "source": "facturacion",
    "field": "tercero_id",
    "operator": "in",
    "value": ["1001", "1002"]
  },
  {
    "source": "inventario",
    "field": "fecha",
    "operator": "between",
    "value": ["2026-01-01", "2026-03-31"]
  }
]
```

**4.5 — Backend: traducción de filtros a ORM**

En `BIQueryEngine`, implementar un `FilterTranslator` que convierta cada operador a su equivalente Django:
- `igual a` → `field=value`
- `contiene` → `field__icontains=value`
- `mayor que` → `field__gt=value`
- `entre` → `field__gte=value[0], field__lte=value[1]`
- `en lista` → `field__in=value`
- etc.

---

## BLOQUE 5: LÍMITE DE REGISTROS

### Problema
El sistema no permite definir un límite de registros. Esto impide crear reportes tipo "Top N" (ej: Top 20 productos más vendidos).

### Solución Requerida

**5.1 — Campo en UI**

Agregar en el builder de reportes un input numérico opcional: "Límite de registros" con placeholder "Sin límite".

**5.2 — Backend**

El modelo `ReportBI` ya tiene `limite_registros` (IntegerField nullable). Asegurar que `BIQueryEngine.execute()` aplique `[:limite]` al queryset final DESPUÉS de ordenar.

**5.3 — Ordenamiento obligatorio con límite**

Si el usuario define un límite, debe obligatoriamente definir al menos un campo de ordenamiento. Validar esto en frontend y backend. Mostrar advertencia: "Para usar límite de registros debes definir al menos un ordenamiento".

---

## BLOQUE 6: GALERÍA DE REPORTES PÚBLICOS

### 6.1 — Modelo/Concepto

Los reportes de galería son `ReportBI` con `es_template=True` y un nuevo campo `categoria_galeria` (choice field):

```python
CATEGORIAS_GALERIA = [
    ('contabilidad', 'Contabilidad'),
    ('cuentas_pagar', 'Cuentas por Pagar'),
    ('cuentas_cobrar', 'Cuentas por Cobrar'),
    ('ventas', 'Ventas'),
    ('inventario', 'Inventario'),
    ('costos', 'Costos y Gastos'),
    ('proyectos', 'Proyectos'),
    ('tributario', 'Tributario'),
    ('gerencial', 'Gerencial / KPIs'),
]
```

### 6.2 — Galería pública (todos los usuarios)

- Nueva vista/página: "Galería de Reportes"
- Muestra los reportes agrupados por categoría en formato de cards/grid
- Cada card muestra: título, descripción breve, tipo de visualización (ícono), categoría, fuentes que usa
- El usuario puede filtrar por categoría y buscar por nombre
- Al hacer clic en un reporte de galería → se abre en **modo solo lectura** (report-viewer sin edición)

### 6.3 — Gestión de galería (solo `valmen_admin`)

- El rol `valmen_admin` corresponde a `is_staff=True` en el sistema (ver `.claude/rules/general/architecture.md`)
- Solo este rol puede:
  - Crear reportes de galería
  - Editar reportes de galería existentes
  - Eliminar reportes de galería
- En el menú/sidebar del admin, agregar opción: "Gestionar Galería" o similar
- La vista de gestión usa el mismo report-builder pero con el campo `es_template=True` y `categoria_galeria` visible

### 6.4 — Reportes predefinidos a crear

Crear templates reales (con `campos_config`, `filtros`, `orden_config` funcionales) para al menos:

**Contabilidad:**
- Balance de comprobación
- Libro mayor por cuenta
- Movimientos por período

**Cuentas por Pagar:**
- CXP por proveedor
- Aging de CXP (vencimiento)
- CXP por período

**Cuentas por Cobrar:**
- CXC por cliente
- Aging de CXC
- CXC por vendedor

**Ventas:**
- Ventas por vendedor
- Ventas por producto (Top 20)
- Ventas por período
- Detalle de facturación con costo e inventario (multi-tabla)
- Margen bruto por producto

**Inventario:**
- Movimientos de inventario por producto
- Inventario por lote/serie
- Kardex por producto (movimientos + saldo)

**Costos:**
- Costos por proyecto
- Costos por centro de costo
- Costos por actividad

**Proyectos:**
- Ejecución presupuestal por proyecto
- Costos vs. presupuesto

**Gerencial:**
- P&G resumido
- Top 10 clientes por facturación
- Top 10 proveedores por CXP

---

## BLOQUE 7: DUPLICAR REPORTES

### 7.1 — Funcionalidad

Aplica para TODOS los reportes (galería y propios):
- Botón "Duplicar" visible en el listado de reportes y en el viewer
- Al hacer clic → modal con input "Nombre del reporte" (prellenado con el nombre original + " (copia)")
- El nombre debe ser editable
- Al confirmar: se crea un nuevo `ReportBI` con todos los campos copiados EXCEPTO:
  - `id` → nuevo UUID
  - `user` → usuario actual
  - `titulo` → nombre ingresado
  - `es_template` → `False` (siempre queda como reporte propio)
  - `template_origen` → referencia al reporte original
  - `es_privado` → `True` por defecto
  - `es_favorito` → `False`
- El reporte duplicado queda en "Mis Reportes" del usuario

### 7.2 — Endpoint

`POST /api/v1/dashboard/reportes/{id}/duplicate/`
Body: `{ "titulo": "Mi reporte personalizado" }`

---

## BLOQUE 8: ACTUALIZAR IA (CFO Virtual / Sugerencias)

### 8.1 — El endpoint `suggest-report` debe conocer las nuevas capacidades

Actualizar el prompt/contexto del `CfoVirtualService.suggest_report()` para incluir:
- Las nuevas fuentes disponibles (productos, terceros con direcciones, cuentas contables, etc.)
- La capacidad de hacer JOINs entre tablas
- Los campos calculados
- Los filtros avanzados (todos los operadores)
- El límite de registros (para sugerir Top N)
- Los reportes de la galería como referencia
- La posibilidad de incorporar reportes BI como tarjetas de dashboard

### 8.2 — Sugerencias más inteligentes

Cuando el usuario pregunte algo como "quiero ver los productos más vendidos con su costo", la IA debe sugerir un reporte que:
- Use `facturacion_detalle` + `inventario` + `productos` (con JOINs)
- Incluya campo calculado de margen
- Tenga filtro de período
- Use límite de registros (Top 20)
- Ordene por cantidad descendente

---

## BLOQUE 9: COMPARTIR REPORTES BI

### Problema
El modelo `ReportBIShare` ya existe pero la funcionalidad debe estar completa y al nivel del dashboard sharing.

### 9.1 — Funcionalidad completa de compartir

- Botón "Compartir" en el listado de reportes y en el viewer/builder
- Modal de compartir: buscar usuario por nombre/email (dentro de la misma empresa)
- Permisos: `puede_editar` (true/false) — si no puede editar solo ve en modo lectura
- El usuario que recibe el reporte lo ve en su lista de "Compartidos conmigo"
- El dueño puede revocar el acceso en cualquier momento

### 9.2 — Endpoints

Ya deberían existir basados en el modelo, verificar que estén completos:
- `POST /api/v1/dashboard/reportes/{id}/share/` — compartir
- `DELETE /api/v1/dashboard/reportes/{id}/share/{user_id}/` — revocar
- Incluir en `GET /api/v1/dashboard/reportes/` los reportes compartidos conmigo

---

## BLOQUE 10: INTEGRAR REPORTES BI EN DASHBOARD (FEATURE NUEVA MAYOR)

### Concepto

Permitir que un reporte BI guardado (tipo gráfico: bar, line, pie, area, waterfall, gauge, KPI) pueda incorporarse como tarjeta en un dashboard. **Las tablas y pivots NO se pueden incorporar al dashboard** — solo visualizaciones gráficas.

### 10.1 — Nuevo tipo de tarjeta: `bi_report`

Agregar al catálogo de tarjetas un tipo especial:

```python
# En card_catalog.py o en DashboardCard model
card_type_code = 'bi_report'
# referencia al ReportBI
bi_report_id = UUID  # nuevo campo en DashboardCard
```

Agregar campo en `DashboardCard`:
```python
bi_report = models.ForeignKey('ReportBI', null=True, blank=True, on_delete=models.SET_NULL)
```

### 10.2 — Flujo en el Dashboard Builder

1. Al agregar tarjeta al dashboard, entre las opciones del catálogo aparece: "Reporte personalizado BI"
2. Se abre un selector que muestra "Mis Reportes" + "Compartidos conmigo" (solo los de tipo gráfico, excluyendo table y pivot)
3. Al seleccionar un reporte → se agrega como tarjeta al dashboard
4. La tarjeta renderiza el gráfico del reporte BI usando los mismos componentes de chart-renderer

### 10.3 — Ejecución

Cuando el dashboard se carga, para cada tarjeta tipo `bi_report`:
1. Leer la configuración del `ReportBI` referenciado
2. Ejecutar vía `BIQueryEngine` con los filtros del reporte
3. Renderizar el gráfico en la tarjeta
4. **Override de filtros del dashboard** (ver Bloque 12)

### 10.4 — Restricciones

- Solo se pueden incorporar reportes con `tipo_visualizacion` en: `bar`, `line`, `pie`, `area`, `waterfall`, `gauge`, `kpi`
- NO se pueden incorporar: `table`, `pivot` (demasiado grandes/complejas para una tarjeta)
- Si el reporte BI original se elimina → la tarjeta muestra "Reporte no disponible" con opción de eliminar la tarjeta
- Si el reporte BI se modifica → la tarjeta refleja los cambios automáticamente (siempre ejecuta la última versión)

---

## BLOQUE 11: MIGRAR TARJETAS DE DASHBOARD AL MOTOR BI (TRAZABILIDAD DE DATOS)

### Problema

Las tarjetas actuales del dashboard usan `ReportEngine` (report_engine.py) con 30+ métodos hardcodeados. El usuario no tiene forma de verificar qué datos se están mostrando, de qué tablas vienen, ni aplicar filtros granulares. Los reportes BI resuelven esto porque muestran las fuentes, campos y filtros de forma transparente.

### 11.1 — Estrategia de migración (gradual, no destructiva)

**IMPORTANTE:** Esta es una migración de largo plazo. No eliminar `ReportEngine` de inmediato.

**Fase A — Coexistencia:**
- Las tarjetas existentes (`card_type_code` del catálogo) siguen funcionando con `ReportEngine`
- Las nuevas tarjetas tipo `bi_report` usan `BIQueryEngine`
- Ambos motores coexisten

**Fase B — Migración progresiva (posterior a este sprint):**
- Para cada tipo de tarjeta hardcodeada, crear un equivalente como `ReportBI` template
- Marcar las tarjetas migradas como "obsoletas" en el catálogo
- Eventualmente deprecar `ReportEngine` cuando todas las tarjetas tengan equivalente BI

### 11.2 — Beneficios para el usuario

- Transparencia: el usuario puede ver exactamente qué fuentes y campos alimentan la tarjeta
- Filtros granulares: puede aplicar filtros por campo a cada tarjeta individual
- Consistencia: un solo motor de datos para todo (BIQueryEngine)
- Confianza: puede "abrir" la tarjeta como reporte completo para validar los datos

### 11.3 — "Ver como reporte"

Para tarjetas tipo `bi_report` en el dashboard, agregar opción en el menú contextual: **"Ver como reporte completo"** → abre el reporte BI original en el report-viewer donde el usuario puede ver la tabla completa, todos los filtros, y validar los datos.

---

## BLOQUE 12: FILTROS DE DASHBOARD OVERRIDE SOBRE FILTROS BI (FEATURE CRÍTICA)

### Problema

El dashboard tiene filtros generales (período, tercero, proyecto, etc.). Si las tarjetas ahora vienen de reportes BI que tienen sus propios filtros, debe haber un mecanismo para que los filtros del dashboard modifiquen los valores de los filtros del reporte BI **solo para esa vista de dashboard**, sin alterar el reporte BI original.

### 12.1 — Concepto: Filtros en 3 capas

```
Capa 1: Filtros del ReportBI original (guardados en ReportBI.filtros)
   ↓ se copian como base
Capa 2: Filtros override por tarjeta en dashboard (guardados en DashboardCard.filtros_config)
   ↓ el usuario puede cambiar VALORES, no estructura
Capa 3: Filtros globales del dashboard (guardados en Dashboard.filtros_default)
   ↓ aplican a TODAS las tarjetas que tengan filtros compatibles
```

### 12.2 — Cómo funciona

**Al agregar un reporte BI al dashboard:**
- Se copian los filtros del reporte BI a `DashboardCard.filtros_config` como estado inicial
- Estos son los filtros "de la tarjeta"

**Al cambiar filtros globales del dashboard:**
- El sistema busca en cada tarjeta BI si tiene un filtro del mismo tipo (misma fuente + mismo campo)
- Si lo encuentra → **reemplaza SOLO el valor** del filtro en la tarjeta, no el operador ni la estructura
- Ejemplo: Dashboard cambia "fecha entre [2026-01-01, 2026-03-31]" → todas las tarjetas BI que tengan un filtro de fecha se actualizan con ese rango
- Si la tarjeta no tiene ese campo como filtro → no se afecta

**El reporte BI original NO se modifica:**
- Los cambios de filtro en el dashboard son transitorios, solo para esa sesión de visualización
- Si se guardan los filtros del dashboard (`Dashboard.filtros_default`) → los override se persisten en `DashboardCard.filtros_config`
- El `ReportBI.filtros` original siempre permanece intacto

### 12.3 — UX en el dashboard

- Al hacer clic en una tarjeta BI → opción "Ajustar filtros" que muestra los filtros de esa tarjeta (heredados del reporte BI) y permite cambiar los valores
- Los filtros globales del dashboard muestran un indicador si están afectando tarjetas BI
- Tooltip en tarjeta BI: "Filtros modificados respecto al reporte original" cuando hay override activo

### 12.4 — Backend: ejecución con override

```python
def execute_card_bi_report(card: DashboardCard, dashboard_filters: dict):
    report = card.bi_report
    # 1. Tomar filtros base del reporte
    base_filters = copy.deepcopy(report.filtros)
    # 2. Aplicar override de la tarjeta
    card_overrides = card.filtros_config or {}
    merged = merge_filters(base_filters, card_overrides)
    # 3. Aplicar filtros globales del dashboard
    final = apply_dashboard_global_filters(merged, dashboard_filters)
    # 4. Ejecutar
    return BIQueryEngine(report, filters_override=final).execute()
```

---

## BLOQUE 13: MEJORAS ADICIONALES

### 13.1 — Previsualización en vivo

Al construir el reporte en el builder, un botón "Previsualizar" que ejecute el query con `LIMIT 50` y muestre los resultados parciales en tiempo real. Permite validar JOINs y filtros antes de guardar.

### 13.2 — Indicador de rendimiento

Si el reporte involucra muchas tablas o no tiene filtros restrictivos, mostrar advertencia: "Este reporte puede tardar. Considera agregar filtros de fecha o período."

### 13.3 — Exportación (solo Excel y CSV)

**IMPORTANTE: NO implementar exportación a PDF para reportes BI.** Las tablas pueden ser muy largas o anchas y no caben bien en PDF. Solo soportar:
- **Excel (.xlsx)** — exportación completa con formato, encabezados de columna, y nombre del reporte
- **CSV** — exportación plana para importar en otras herramientas

Verificar que la exportación funcione correctamente con reportes multi-tabla y campos calculados.

### 13.4 — Ordenamiento multi-campo

Asegurar que el usuario pueda definir múltiples campos de ordenamiento con dirección (ASC/DESC) y prioridad. UI: lista sorteable de campos de orden.

### 13.5 — Validación de integridad

Al guardar un reporte:
- Validar que todas las fuentes seleccionadas tienen relación entre sí (o advertir)
- Validar que los campos calculados referencian campos que existen en las fuentes seleccionadas
- Validar que los filtros referencian campos válidos

---

## Archivos Clave a Modificar

### Backend
- `backend/apps/dashboard/bi_engine.py` — JOINs, nuevas fuentes, FilterTranslator, SOURCE_JOINS_MAP, execute con override
- `backend/apps/dashboard/services.py` — ReportBIService (duplicate, galería, share, metadata joins), CardService (bi_report type)
- `backend/apps/dashboard/models.py` — `categoria_galeria` en ReportBI, `bi_report` FK en DashboardCard
- `backend/apps/dashboard/serializers.py` — nuevos serializers para duplicate, galería, filtros avanzados, card bi_report
- `backend/apps/dashboard/views.py` — nuevos endpoints (duplicate, galería admin, meta/joins, card bi execution)
- `backend/apps/dashboard/urls.py` — nuevas rutas
- `backend/apps/dashboard/bi_templates.py` — templates reales multi-tabla para galería
- `backend/apps/dashboard/card_catalog.py` — nuevo tipo `bi_report`
- `backend/apps/dashboard/report_engine.py` — sin cambios inmediatos, coexiste con BIQueryEngine

### Frontend
- `components/field-panel/` — rediseño completo (listado, buscador, calculados)
- `components/filter-builder/` — rediseño completo (filtros flexibles, operadores por tipo)
- `components/report-builder/` — límite registros, preview, validaciones, share
- `components/report-viewer/` — modo solo lectura para galería, botón duplicar
- `components/dashboard-builder/` — selector de reporte BI como tarjeta
- `components/dashboard-viewer/` — ejecución de tarjetas BI, filtros override
- `components/card-selector/` — agregar opción "Reporte personalizado BI"
- `components/chart-card/` — renderizar tarjetas tipo `bi_report`
- Nuevo: `components/report-gallery/` — galería pública de reportes
- Nuevo: `components/gallery-admin/` — gestión de galería (valmen_admin)
- Nuevo: `components/duplicate-dialog/` — modal de duplicación
- Nuevo: `components/calculated-field-dialog/` — modal de campo calculado
- Nuevo: `components/share-report-dialog/` — modal de compartir reporte
- Nuevo: `components/card-filter-override/` — ajustar filtros de tarjeta BI en dashboard
- `services/report-bi.service.ts` — nuevos endpoints (duplicate, share, galería, meta/joins)
- `services/dashboard.service.ts` — ejecución de tarjetas BI
- `models/report-bi.model.ts` — interfaces actualizadas
- `models/dashboard.model.ts` — bi_report en DashboardCard

---

## Metodología de Ejecución

### Fases (ejecutar una por una, documentar cada una)

Seguir la metodología de 10 fases del proyecto. Cada fase se documenta en `PROGRESS-DASHBOARD.md` con tickets individuales.

```
FASE 0: Planificación (Opus) — PRD + PLAN con esta instrucción como entrada
FASE 1: Diseño técnico — Modelo de datos, diagramas de flujo, contratos API
FASE 4: Implementación Backend — Multi-agente (Sonnet ejecuta, Opus revisa)
FASE 5: Implementación Frontend — Multi-agente
FASE 6: Protección de ventana — /compact entre fases, PROGRESS actualizado
FASE 7: Revisión final — skill saicloud-revision-final
FASE 9: Validación UI/UX — skill saicloud-validacion-ui
```

### Uso de Agentes y Subagentes

```
Agente Principal (Opus) — Planificación, revisión, decisiones arquitectónicas
├── Subagente Backend (Sonnet) — models, services, views, serializers, tests
├── Subagente Frontend (Sonnet) — components, services, models TS, templates
├── Subagente QA (Sonnet) — tests unitarios, integration tests
└── Subagente Docs (Sonnet) — documentación técnica, RAG chunks
```

**Usar `context: fork` para investigación** que no contamine el contexto principal.
**Ejecutar `/compact` al completar cada fase** con foco en la fase actual.

### Skills a usar por fase

| Fase | Skills |
|---|---|
| 0 - Planificación | `saicloud-planificacion` |
| 1 - Diseño | `saicloud-backend-django`, `saicloud-frontend-angular` |
| 4 - Backend | `saicloud-backend-django`, `saicloud-pruebas-unitarias` |
| 5 - Frontend | `saicloud-frontend-angular`, `saicloud-pruebas-unitarias` |
| 6 - Protección | `saicloud-proteccion-ventana` |
| 7 - Revisión | `saicloud-revision-final` |
| 9 - UI/UX | `saicloud-validacion-ui` |

### Documentación (actualizar al finalizar)

Al completar TODAS las fases:

1. **Documentación técnica:** Actualizar `docs/technical/dashboard/` con:
   - Nuevos endpoints documentados
   - Diagrama de flujo de JOINs
   - Arquitectura del sistema de filtros
   - Modelo de datos actualizado

2. **Documentación de usuario:** Actualizar `docs/manuales/` con:
   - Manual del builder de reportes BI (actualizado)
   - Guía de la galería de reportes
   - Cómo incorporar reportes BI en dashboards
   - Cómo usar filtros avanzados

3. **RAG Chunks:** Actualizar/crear `docs/technical/dashboard/RAG-CHUNKS.md` con chunks para el chat IA que cubran:
   - Qué fuentes de datos están disponibles y cómo se relacionan
   - Cómo crear reportes con múltiples tablas
   - Cómo usar campos calculados
   - Cómo usar filtros avanzados
   - Cómo incorporar reportes en dashboards
   - Cómo duplicar y compartir reportes
   - Catálogo de reportes de galería disponibles
   - Tipos de exportación disponibles (Excel, CSV)

4. **DECISIONS.md:** Registrar:
   - Decisión sobre productos (CrmProducto vs ItemSaiopen)
   - Decisión sobre migración de ReportEngine → BIQueryEngine
   - Decisión sobre filtros en 3 capas (BI → tarjeta → dashboard)

5. **PROGRESS-DASHBOARD.md:** Actualizar con tickets de cada bloque y su estado

---

## Orden de Implementación por Fases

### Sprint 1 — Cimientos (Bloques 1, 2, 4, 5)
1. Backend: SOURCE_JOINS_MAP + JOINs en BIQueryEngine
2. Backend: Nuevas fuentes (productos, terceros_saiopen, dimensionales)
3. Backend: FilterTranslator (filtros avanzados)
4. Backend: Límite de registros funcional
5. Tests backend de todo lo anterior

### Sprint 2 — UX del Builder (Bloques 3, 7, 9)
6. Frontend: Rediseño panel de campos (listado, buscador)
7. Frontend: Campos calculados (modal + persistencia)
8. Frontend: Filtros flexibles (nuevo filter-builder)
9. Frontend: Límite registros + ordenamiento multi-campo
10. Frontend: Duplicar reportes (dialog + endpoint)
11. Frontend: Compartir reportes (dialog + endpoints)
12. Tests frontend

### Sprint 3 — Galería (Bloque 6)
13. Backend: modelo categoria_galeria + endpoints admin
14. Frontend: Galería pública (vista cards)
15. Frontend: Gestión galería (valmen_admin)
16. Backend: Templates reales multi-tabla para galería
17. Tests

### Sprint 4 — Integración Dashboard ↔ BI (Bloques 10, 11, 12)
18. Backend: DashboardCard.bi_report FK + ejecución
19. Backend: Filtros override (3 capas)
20. Frontend: Selector de reporte BI en dashboard builder
21. Frontend: Renderizado de tarjetas BI en dashboard
22. Frontend: Filtros override en dashboard viewer
23. Frontend: "Ver como reporte completo" desde tarjeta
24. Tests integración

### Sprint 5 — IA + Docs (Bloque 8 + documentación)
25. Backend: Actualizar CFO Virtual con nuevas capacidades
26. Documentación técnica actualizada
27. Manual de usuario actualizado
28. RAG chunks para chat IA
29. Validación UI/UX completa (skill saicloud-validacion-ui)
30. Revisión final (skill saicloud-revision-final)

---

## Notas Técnicas

- **Multi-tenant**: TODOS los queries deben mantener `company_id` como filtro obligatorio
- **Django ORM only**: No SQL crudo. Los JOINs se hacen vía `Subquery`, `annotations`, o modelos proxy
- **Rendimiento**: Los JOINs multi-tabla pueden ser costosos. Considerar `select_related`/`prefetch_related` donde aplique, y siempre filtrar por `company_id` + al menos `periodo` o `fecha`
- **Angular**: Componentes standalone, OnPush, Angular Material (NO PrimeNG), signals, `@if`/`@for`
- **Tests**: Backend services ≥80%, frontend services 100%, components ≥70%
- **Exportación**: Solo Excel (.xlsx) y CSV — NO PDF para reportes BI
- **Lógica en services.py**: Nunca en views ni modelos (regla del proyecto)

---

*Documento preparado para planificación con Opus — 12 Abril 2026*
*Proyecto: SaiSuite — ValMen Tech*
