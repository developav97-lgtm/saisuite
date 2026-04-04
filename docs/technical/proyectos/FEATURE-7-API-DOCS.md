# Feature #7 — Budget & Cost Tracking: Documentación de API

**Base URL:** `/api/v1/projects/`
**Autenticación:** Todos los endpoints requieren `Authorization: Bearer <JWT>`
**Formato:** `Content-Type: application/json`

---

## Índice

1. [Presupuesto](#presupuesto)
   - [GET/POST/PATCH /budget/](#1-getpostpatch-budget)
   - [POST /budget/approve/](#2-post-budgetapprove)
   - [GET /budget/variance/](#3-get-budgetvariance)
   - [GET /budget/alerts/](#4-get-budgetalerts)
   - [GET/POST /budget/snapshots/](#5-getpost-budgetsnapshots)
2. [Costos](#costos)
   - [GET /costs/total/](#6-get-coststotal)
   - [GET /costs/by-resource/](#7-get-costsby-resource)
   - [GET /costs/by-task/](#8-get-costsBy-task)
   - [GET /costs/evm/](#9-get-costsevm)
   - [GET /invoice-data/](#10-get-invoice-data)
3. [Gastos](#gastos)
   - [GET/POST /expenses/](#11-getpost-expenses)
   - [GET/PATCH/DELETE /expenses/{pk}/](#12-getpatchdelete-expensespk)
   - [POST /expenses/{pk}/approve/](#13-post-expensespkapprove)
4. [Tarifas de Costo por Recurso](#tarifas-de-costo-por-recurso)
   - [GET/POST /resources/cost-rates/](#14-getpost-resourcescost-rates)
   - [GET/PATCH/DELETE /resources/cost-rates/{pk}/](#15-getpatchdelete-resourcescost-ratespk)
5. [Reglas de Negocio](#reglas-de-negocio)
6. [Comando de Gestión](#comando-de-gestión)

---

## Presupuesto

### 1. GET/POST/PATCH `/budget/`

**Ruta completa:** `/api/v1/projects/{project_id}/budget/`

**Descripción:** Obtiene, crea o actualiza el presupuesto de un proyecto. Cada proyecto tiene un único presupuesto (relación 1-1). Una vez aprobado, los campos `planned_labor_cost`, `planned_expense_cost`, `planned_total_budget` y `currency` son inmutables.

---

#### GET — Obtener presupuesto

**Respuesta `200 OK`:**
```json
{
  "id": "uuid",
  "project": "uuid",
  "planned_labor_cost": "500000.00",
  "planned_expense_cost": "200000.00",
  "planned_total_budget": "700000.00",
  "approved_budget": "700000.00",
  "approved_by": "uuid",
  "approved_date": "2026-03-01",
  "is_approved": true,
  "alert_threshold_percentage": "80.00",
  "currency": "COP",
  "notes": "",
  "actual_labor_cost": "320000.00",
  "actual_expense_cost": "95000.00",
  "actual_total_cost": "415000.00",
  "variance": "285000.00",
  "variance_percentage": "40.71",
  "alert": "none",
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-27T08:30:00Z"
}
```

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe o no pertenece a la empresa del usuario |

---

#### POST — Crear presupuesto

**Body:**
```json
{
  "planned_labor_cost": "500000.00",
  "planned_expense_cost": "200000.00",
  "planned_total_budget": "700000.00",
  "alert_threshold_percentage": "80.00",
  "currency": "COP",
  "notes": ""
}
```

**Respuesta `201 Created`:** Objeto `ProjectBudget` completo (ver GET).

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | Datos inválidos o presupuesto ya existe para este proyecto |
| `404` | El proyecto no existe |

---

#### PATCH — Actualizar presupuesto

**Body:** Cualquier subconjunto de los campos del POST. Los campos `planned_labor_cost`, `planned_expense_cost`, `planned_total_budget` y `currency` son de solo lectura si el presupuesto ya fue aprobado (`is_approved: true`).

**Respuesta `200 OK`:** Objeto `ProjectBudget` completo actualizado.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | Intento de modificar campo inmutable en presupuesto aprobado |
| `404` | El proyecto o presupuesto no existe |

---

### 2. POST `/budget/approve/`

**Ruta completa:** `/api/v1/projects/{project_id}/budget/approve/`

**Descripción:** Aprueba el presupuesto del proyecto. Establece `approved_by` (usuario autenticado), `approved_date` (fecha actual) e `is_approved: true`. Después de esto, los campos de planificación son inmutables.

**Body:**
```json
{
  "approved_budget": "700000.00"
}
```

**Respuesta `200 OK`:** Objeto `ProjectBudget` completo con `is_approved: true`.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | El presupuesto ya está aprobado |
| `404` | El proyecto o presupuesto no existe |

---

### 3. GET `/budget/variance/`

**Ruta completa:** `/api/v1/projects/{project_id}/budget/variance/`

**Descripción:** Retorna el análisis de variación entre presupuesto aprobado y costo real acumulado.

**Respuesta `200 OK`:**
```json
{
  "planned_budget": "700000.00",
  "actual_cost": "415000.00",
  "variance": "285000.00",
  "variance_percentage": "40.71",
  "is_over_budget": false,
  "alert_triggered": false,
  "currency": "COP"
}
```

> `variance` positivo indica que hay presupuesto disponible. Negativo indica sobrecosto.
> `alert_triggered` es `true` si `actual_cost / approved_budget >= alert_threshold_percentage / 100`.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto o presupuesto no existe |

---

### 4. GET `/budget/alerts/`

**Ruta completa:** `/api/v1/projects/{project_id}/budget/alerts/`

**Descripción:** Retorna la lista de alertas activas de presupuesto. Puede retornar lista vacía si no hay alertas.

**Posibles valores de `alert_level`:** `warning`, `critical`

**Respuesta `200 OK`:**
```json
[
  {
    "alert_level": "warning",
    "message": "El proyecto ha consumido el 85% del presupuesto aprobado.",
    "current_percentage": "85.00",
    "threshold_percentage": "80.00"
  }
]
```

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe |

---

### 5. GET/POST `/budget/snapshots/`

**Ruta completa:** `/api/v1/projects/{project_id}/budget/snapshots/`

**Descripción:** Lista los snapshots históricos de costo del proyecto, o crea uno nuevo para la fecha actual.

---

#### GET — Listar snapshots

**Respuesta `200 OK`:**
```json
[
  {
    "id": "uuid",
    "project": "uuid",
    "snapshot_date": "2026-03-25",
    "labor_cost": "300000.00",
    "expense_cost": "80000.00",
    "total_cost": "380000.00",
    "planned_budget": "700000.00",
    "variance": "320000.00",
    "completion_percentage": "54.29",
    "created_at": "2026-03-25T06:00:00Z"
  }
]
```

---

#### POST — Crear snapshot

**Body:** Ninguno requerido. El snapshot se crea para la fecha actual (UTC).

**Comportamiento idempotente:** Si ya existe un snapshot para el día actual, se actualiza en lugar de crear un duplicado.

**Respuesta `201 Created`** (nuevo) o **`200 OK`** (actualizado): Objeto `BudgetSnapshot` completo.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe |

---

## Costos

### 6. GET `/costs/total/`

**Ruta completa:** `/api/v1/projects/{project_id}/costs/total/`

**Descripción:** Retorna el resumen agregado de costos del proyecto: costo laboral (horas × tarifa), costo por gastos aprobados y total.

**Respuesta `200 OK`:**
```json
{
  "labor_cost": "320000.00",
  "expense_cost": "95000.00",
  "total_cost": "415000.00",
  "total_hours": "64.00",
  "currency": "COP",
  "entries_without_rate": 0
}
```

> `entries_without_rate`: cantidad de entradas de tiempo sin tarifa configurada. Si es mayor a 0, el costo laboral está subestimado.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe |

---

### 7. GET `/costs/by-resource/`

**Ruta completa:** `/api/v1/projects/{project_id}/costs/by-resource/`

**Descripción:** Desglose de costos agrupado por recurso (usuario) asignado al proyecto.

**Respuesta `200 OK`:**
```json
[
  {
    "user_id": "uuid",
    "user_name": "Juan Andrade",
    "total_hours": "40.00",
    "total_cost": "200000.00",
    "currency": "COP"
  }
]
```

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe |

---

### 8. GET `/costs/by-task/`

**Ruta completa:** `/api/v1/projects/{project_id}/costs/by-task/`

**Descripción:** Desglose de costos agrupado por tarea del proyecto.

**Respuesta `200 OK`:**
```json
[
  {
    "task_id": "uuid",
    "task_name": "Excavación zona norte",
    "total_hours": "16.00",
    "total_cost": "80000.00",
    "currency": "COP"
  }
]
```

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe |

---

### 9. GET `/costs/evm/`

**Ruta completa:** `/api/v1/projects/{project_id}/costs/evm/`

**Descripción:** Métricas de Earned Value Management (EVM / Gestión del Valor Ganado) para el proyecto. Permite evaluar rendimiento de costo y cronograma.

**Query params:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `as_of_date` | `YYYY-MM-DD` | No | Fecha de corte para el cálculo. Por defecto: fecha actual |

**Fórmulas aplicadas (DEC-028):**
- `PV` (Planned Value) = `BAC × (elapsed_days / total_days)`
- `EV` (Earned Value) = `BAC × promedio(tarea.porcentaje_completado / 100)`
- `CV` (Cost Variance) = `EV − AC`
- `SV` (Schedule Variance) = `EV − PV`
- `CPI` (Cost Performance Index) = `EV / AC`
- `SPI` (Schedule Performance Index) = `EV / PV`
- `EAC` (Estimate At Completion) = `BAC / CPI`

**Respuesta `200 OK`:**
```json
{
  "planned_value": "350000.00",
  "earned_value": "280000.00",
  "actual_cost": "415000.00",
  "cost_variance": "-135000.00",
  "schedule_variance": "-70000.00",
  "cost_performance_index": "0.6747",
  "schedule_performance_index": "0.8000",
  "estimate_at_completion": "1037000.00",
  "completion_percentage": "40.00",
  "as_of_date": "2026-03-27",
  "currency": "COP"
}
```

> `cost_variance` negativo = sobrecosto. `schedule_variance` negativo = retraso.
> `CPI < 1` indica ineficiencia en costos. `SPI < 1` indica retraso en cronograma.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | Formato de `as_of_date` inválido |
| `404` | El proyecto no existe |

---

### 10. GET `/invoice-data/`

**Ruta completa:** `/api/v1/projects/{project_id}/invoice-data/`

**Descripción:** Retorna los datos del proyecto estructurados como líneas de factura, listos para generar una factura a cliente. Incluye horas laborales y gastos billables aprobados.

**Respuesta `200 OK`:**
```json
{
  "project_id": "uuid",
  "project_name": "Edificio Centro Comercial Norte",
  "client_name": "Constructora XYZ",
  "currency": "COP",
  "line_items": [
    {
      "type": "labor",
      "description": "Horas - Juan Andrade",
      "quantity": "40.00",
      "unit_rate": "80000.00",
      "subtotal": "3200000.00"
    },
    {
      "type": "expense",
      "description": "Materiales - Cemento",
      "quantity": "1.00",
      "unit_rate": "500000.00",
      "subtotal": "500000.00"
    }
  ],
  "subtotal": "3700000.00",
  "total": "3700000.00"
}
```

> Solo se incluyen gastos con `billable: true` e `is_approved: true`.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | El proyecto no existe |

---

## Gastos

### 11. GET/POST `/expenses/`

**Ruta completa:** `/api/v1/projects/{project_id}/expenses/`

**Descripción:** Lista los gastos del proyecto o registra uno nuevo.

**Categorías válidas:**

| Valor | Etiqueta |
|-------|----------|
| `materials` | Materiales |
| `equipment` | Equipos |
| `subcontractor` | Subcontratista |
| `transport` | Transporte |
| `lodging` | Alojamiento |
| `food` | Alimentación |
| `other` | Otro |

---

#### GET — Listar gastos

**Respuesta `200 OK`:**
```json
[
  {
    "id": "uuid",
    "project": "uuid",
    "category": "materials",
    "category_display": "Materiales",
    "description": "Compra de cemento",
    "amount": "500000.00",
    "currency": "COP",
    "expense_date": "2026-03-15",
    "paid_by": "uuid",
    "paid_by_name": "Juan Andrade",
    "receipt_url": "",
    "billable": true,
    "notes": "",
    "approved_by": null,
    "approved_date": null,
    "is_approved": false,
    "created_at": "2026-03-15T14:00:00Z"
  }
]
```

---

#### POST — Registrar gasto

**Body:**
```json
{
  "category": "materials",
  "description": "Compra de cemento",
  "amount": "500000.00",
  "currency": "COP",
  "expense_date": "2026-03-15",
  "paid_by": "uuid",
  "receipt_url": "https://...",
  "billable": true,
  "notes": ""
}
```

**Respuesta `201 Created`:** Objeto `ProjectExpense` completo (ver GET).

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | Datos inválidos o categoría no reconocida |
| `404` | El proyecto no existe |

---

### 12. GET/PATCH/DELETE `/expenses/{pk}/`

**Ruta completa:** `/api/v1/projects/expenses/{pk}/`

**Descripción:** Obtiene, actualiza o elimina un gasto específico.

---

#### GET — Obtener gasto

**Respuesta `200 OK`:** Objeto `ProjectExpense` completo (ver sección anterior).

---

#### PATCH — Actualizar gasto

**Body:** Cualquier subconjunto de los campos del POST. No se puede modificar un gasto que ya fue aprobado.

**Respuesta `200 OK`:** Objeto `ProjectExpense` completo actualizado.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | Intento de modificar un gasto ya aprobado |
| `404` | El gasto no existe |

---

#### DELETE — Eliminar gasto

**Respuesta `204 No Content`**

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | No se puede eliminar un gasto ya aprobado |
| `404` | El gasto no existe |

---

### 13. POST `/expenses/{pk}/approve/`

**Ruta completa:** `/api/v1/projects/expenses/{pk}/approve/`

**Descripción:** Aprueba un gasto. Establece `approved_by` (usuario autenticado) y `approved_date` (fecha actual). El aprobador no puede ser el mismo usuario que `paid_by` (segregación de funciones).

**Body:** Ninguno requerido.

**Respuesta `200 OK`:** Objeto `ProjectExpense` completo con `is_approved: true`.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | El gasto ya está aprobado |
| `403` | El aprobador es el mismo usuario que registró el gasto (`paid_by`) — segregación de funciones |
| `404` | El gasto no existe |

---

## Tarifas de Costo por Recurso

### 14. GET/POST `/resources/cost-rates/`

**Ruta completa:** `/api/v1/projects/resources/cost-rates/`

**Descripción:** Lista las tarifas por hora configuradas para los recursos, o crea una nueva. Las tarifas tienen vigencia por rango de fechas. No se permiten rangos solapados para el mismo usuario.

---

#### GET — Listar tarifas

**Respuesta `200 OK`:**
```json
[
  {
    "id": "uuid",
    "user": "uuid",
    "user_name": "Juan Andrade",
    "start_date": "2026-01-01",
    "end_date": null,
    "hourly_rate": "80000.00",
    "currency": "COP",
    "notes": "",
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

> `end_date: null` indica que la tarifa está vigente indefinidamente a partir de `start_date`.

---

#### POST — Crear tarifa

**Body:**
```json
{
  "user": "uuid",
  "start_date": "2026-01-01",
  "end_date": null,
  "hourly_rate": "80000.00",
  "currency": "COP",
  "notes": ""
}
```

**Respuesta `201 Created`:** Objeto `ResourceCostRate` completo (ver GET).

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | Rango de fechas se solapa con una tarifa existente para el mismo usuario |
| `400` | `end_date` anterior a `start_date` |

---

### 15. GET/PATCH/DELETE `/resources/cost-rates/{pk}/`

**Ruta completa:** `/api/v1/projects/resources/cost-rates/{pk}/`

**Descripción:** Obtiene, actualiza o elimina una tarifa de costo específica.

---

#### GET — Obtener tarifa

**Respuesta `200 OK`:** Objeto `ResourceCostRate` completo (ver sección anterior).

---

#### PATCH — Actualizar tarifa

**Body:** Cualquier subconjunto de los campos del POST.

**Respuesta `200 OK`:** Objeto `ResourceCostRate` completo actualizado.

**Errores:**

| Código | Descripción |
|--------|-------------|
| `400` | El nuevo rango de fechas se solapa con otra tarifa existente del mismo usuario |
| `404` | La tarifa no existe |

---

#### DELETE — Eliminar tarifa

**Respuesta `204 No Content`**

**Errores:**

| Código | Descripción |
|--------|-------------|
| `404` | La tarifa no existe |

---

## Reglas de Negocio

### Bloqueo de presupuesto aprobado
Una vez que el presupuesto tiene `approved_date` establecido (`is_approved: true`), los siguientes campos son de solo lectura y cualquier intento de modificarlos retorna `400`:
- `planned_labor_cost`
- `planned_expense_cost`
- `planned_total_budget`
- `currency`

### Segregación de funciones en gastos
El usuario que aprueba un gasto (`POST /expenses/{pk}/approve/`) no puede ser el mismo que lo registró (`paid_by`). Viola esta regla retorna `403 Forbidden`.

### Idempotencia de snapshots
`POST /budget/snapshots/` es idempotente por día: si ya existe un snapshot para la fecha actual (UTC), se actualiza en lugar de crear un registro duplicado. La respuesta es `201` para creación nueva y `200` para actualización.

### Tarifas sin solapamiento
El servicio valida que los rangos `[start_date, end_date]` de las tarifas de un mismo usuario no se solapen. Intentar crear o actualizar una tarifa con rango solapado retorna `400`.

### Costo laboral y entradas sin tarifa
Si un usuario tiene entradas de tiempo registradas pero no tiene una `ResourceCostRate` vigente para ese período, sus horas no se incluyen en el costo laboral. El campo `entries_without_rate` en `/costs/total/` indica cuántas entradas quedaron sin valorizar.

### Gastos en `/invoice-data/`
Solo se incluyen en los `line_items` los gastos que cumplan simultáneamente: `billable: true` e `is_approved: true`.

---

## Comando de Gestión

### `budget_weekly_snapshot`

Genera snapshots de presupuesto para todos los proyectos activos. Diseñado para ejecutarse semanalmente via cron o tarea programada.

```bash
python manage.py budget_weekly_snapshot [opciones]
```

**Opciones:**

| Flag | Tipo | Descripción |
|------|------|-------------|
| `--dry-run` | — | Simula la ejecución sin escribir en base de datos. Imprime los proyectos que serían procesados |
| `--project-id` | `UUID` | Ejecuta el snapshot solo para el proyecto especificado |
| `--company-id` | `UUID` | Ejecuta snapshots solo para los proyectos de la empresa especificada |

**Ejemplos:**

```bash
# Snapshot para todos los proyectos activos
python manage.py budget_weekly_snapshot

# Simulación sin escritura
python manage.py budget_weekly_snapshot --dry-run

# Solo un proyecto
python manage.py budget_weekly_snapshot --project-id 550e8400-e29b-41d4-a716-446655440000

# Solo una empresa
python manage.py budget_weekly_snapshot --company-id 660e9511-f30c-52e5-b827-557766551111

# Combinado: dry-run para una empresa
python manage.py budget_weekly_snapshot --dry-run --company-id 660e9511-f30c-52e5-b827-557766551111
```

**Comportamiento:** Igual que `POST /budget/snapshots/`, el comando es idempotente: si ya existe un snapshot para la fecha del día, lo actualiza. Se puede ejecutar múltiples veces sin crear duplicados.
