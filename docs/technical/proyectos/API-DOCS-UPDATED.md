# API DOCUMENTATION — SaiSuite v2.0
**Base URL:** `https://api.saisuite.com/api/v1/` (producción) | `http://localhost:8000/api/v1/` (local)
**Autenticación:** JWT Bearer Token
**Fecha:** 27 Marzo 2026

---

## Autenticación

### POST `/auth/login/`
```json
// Request
{ "email": "usuario@empresa.com", "password": "contraseña" }

// Response 200
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": { "id": "uuid", "email": "...", "full_name": "...", "role": "company_admin" }
}
```

### POST `/auth/refresh/`
```json
// Request
{ "refresh": "<jwt_refresh_token>" }
// Response 200
{ "access": "<nuevo_access_token>" }
```

### GET `/auth/me/`
Retorna datos del usuario autenticado. Requiere `Authorization: Bearer <token>`.

---

## Proyectos

### GET `/projects/`
Lista paginada de proyectos de la empresa.

**Query params:**
| Param | Tipo | Descripción |
|---|---|---|
| `page` | int | Número de página (default: 1) |
| `page_size` | int | Resultados por página (default: 25, max: 100) |
| `search` | string | Busca en código, nombre y cliente |
| `estado` | string | `draft`, `planned`, `in_progress`, `suspended`, `closed`, `cancelled` |
| `tipo` | string | `civil_works`, `consulting`, `manufacturing`, `services`, `public_tender`, `other` |

**Response 200:**
```json
{
  "count": 42,
  "next": "...?page=2",
  "previous": null,
  "results": [{
    "id": "uuid",
    "codigo": "PRY-001",
    "nombre": "Construcción Edificio Comercial",
    "tipo": "civil_works",
    "estado": "in_progress",
    "cliente_nombre": "Inversiones del Valle S.A.S",
    "gerente": { "id": "uuid", "email": "...", "full_name": "Juan Pérez" },
    "fecha_inicio_planificada": "2026-04-01",
    "fecha_fin_planificada": "2027-03-31",
    "presupuesto_total": "850000000.00",
    "porcentaje_avance": "35.50",
    "activo": true,
    "created_at": "2026-03-27T..."
  }]
}
```

### POST `/projects/`
Crea un proyecto nuevo.

```json
// Request body
{
  "nombre": "Nombre del proyecto",
  "tipo": "civil_works",
  "cliente_id": "uuid-del-tercero",
  "cliente_nombre": "Nombre cliente",
  "gerente": "uuid-del-usuario",
  "fecha_inicio_planificada": "2026-04-01",
  "fecha_fin_planificada": "2027-03-31",
  "presupuesto_total": "850000000.00",
  "porcentaje_administracion": "5.00",
  "porcentaje_imprevistos": "3.00",
  "porcentaje_utilidad": "7.00"
}
```

### GET `/projects/{id}/`
Detalle completo de un proyecto. Incluye todos los campos de lista más:
`coordinador`, `fases_count`, `presupuesto_fases_total`, `saiopen_proyecto_id`, etc.

### PATCH `/projects/{id}/cambiar-estado/`
```json
// Request
{ "estado": "planned" }
// Estados válidos: draft → planned → in_progress → suspended | closed | cancelled
```

### GET `/projects/{id}/gantt-data/`
Retorna datos para renderizar el Gantt del proyecto.

### GET `/projects/{id}/estado-financiero/`
Retorna estado financiero del proyecto (presupuesto vs ejecutado).

---

## Tareas

### GET `/projects/tasks/`
Lista paginada de tareas.

**Query params:** `page`, `page_size`, `search`, `estado`, `prioridad`, `proyecto`, `fase`, `responsable`, `ordering`

**Valores de `estado`:** `todo`, `in_progress`, `in_review`, `blocked`, `completed`, `cancelled`

**Response 200:**
```json
{
  "count": 10,
  "results": [{
    "id": "uuid",
    "codigo": "TSK-001",
    "nombre": "Replanteo y localización",
    "estado": "todo",
    "prioridad": 2,
    "porcentaje_completado": 0,
    "progreso_porcentaje": 0,
    "horas_estimadas": 40,
    "horas_registradas": 0,
    "fase": "uuid",
    "fase_nombre": "Fase 1 — Preliminares",
    "proyecto": "uuid",
    "proyecto_nombre": "Construcción Edificio",
    "responsable": { "id": "uuid", "full_name": "..." },
    "fecha_inicio": "2026-04-01",
    "fecha_fin": null,
    "fecha_limite": "2026-05-31"
  }]
}
```

### PATCH `/projects/tasks/{id}/cambiar-estado/`
```json
{ "estado": "in_progress" }
```

### POST `/projects/tasks/{id}/agregar-horas/`
```json
{ "horas": 4.5, "notas": "Trabajo realizado hoy" }
```

---

## Fases

Las fases son **anidadas bajo proyecto**:

### GET `/projects/{proyecto_id}/phases/`
### POST `/projects/{proyecto_id}/phases/`
```json
{
  "nombre": "Fase 1 — Preliminares",
  "fecha_inicio_planificada": "2026-04-01",
  "fecha_fin_planificada": "2026-08-31"
}
```

---

## Hitos

### GET `/projects/{proyecto_id}/milestones/`
### POST `/projects/{proyecto_id}/milestones/`
```json
{
  "nombre": "Entrega cimentación",
  "porcentaje_proyecto": 30,
  "valor_facturar": "255000000.00",
  "facturable": true
}
```

---

## Actividades (Catálogo)

### GET `/projects/activities-saiopen/`
Catálogo de actividades Saiopen (compartido entre proyectos).

### GET `/projects/activities/`
Actividades del sistema interno.

---

## Terceros

### GET `/terceros/`
```
Query params: search, tipo_tercero (customer|supplier|partner), page, page_size
```

---

## Timesheets / Sesiones de Trabajo

### POST `/projects/tasks/{id}/work-sessions/iniciar/`
Inicia el cronómetro para la tarea.

### POST `/projects/tasks/{id}/work-sessions/{session_id}/pausar/`
Pausa la sesión activa.

### POST `/projects/tasks/{id}/work-sessions/{session_id}/finalizar/`
Finaliza la sesión y registra horas.

---

## Códigos de error comunes

| Código | Significado |
|---|---|
| 401 | Token inválido o expirado — hacer refresh |
| 403 | Sin permisos para esta acción |
| 404 | Recurso no encontrado |
| 400 | Error de validación — ver campo `detail` o errores por campo |
| 409 | Conflicto de estado (ej: tarea ya completada) |
