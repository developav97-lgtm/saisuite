# REFACTOR CHANGELOG
**Proyecto:** SaiSuite — ValMen Tech
**Versión:** 2.0.0
**Fecha:** 27 Marzo 2026
**Commits:** REFT-01 → REFT-21 + FASE 2 Frontend

---

## BREAKING CHANGES

### API Endpoints

| Antes (≤ v1.x) | Después (v2.0) | Notas |
|---|---|---|
| `GET /api/v1/proyectos/` | `GET /api/v1/projects/` | Alias eliminado en REFT-21 |
| `GET /api/v1/proyectos/{id}/` | `GET /api/v1/projects/{id}/` | |
| `POST /api/v1/proyectos/` | `POST /api/v1/projects/` | |
| `PATCH /api/v1/proyectos/{id}/cambiar-estado/` | `PATCH /api/v1/projects/{id}/cambiar-estado/` | Acción en español se mantiene |

> **⚠️ El alias `/api/v1/proyectos/` fue eliminado en REFT-21. Cualquier cliente que lo use debe actualizar.**

### Valores de status / choices

#### EstadoProyecto
| Antes | Después |
|---|---|
| `borrador` | `draft` |
| `planificado` | `planned` |
| `en_progreso` | `in_progress` |
| `suspendido` | `suspended` |
| `cerrado` | `closed` |
| `cancelado` | `cancelled` |

#### TareaEstado
| Antes | Después |
|---|---|
| `por_hacer` | `todo` |
| `en_progreso` | `in_progress` |
| `en_revision` | `in_review` |
| `bloqueada` | `blocked` |
| `completada` | `completed` |
| `cancelada` | `cancelled` |

#### SesionTrabajoEstado
| Antes | Después |
|---|---|
| `activa` | `active` |
| `pausada` | `paused` |
| `finalizada` | `finished` |

#### EstadoFase
| Antes | Después |
|---|---|
| `planificada` | `planned` |
| `activa` | `active` |
| `completada` | `completed` |
| `cancelada` | `cancelled` |

---

## MODELOS RENOMBRADOS (migration 0013)

| Modelo anterior | Modelo nuevo | Tabla BD |
|---|---|---|
| `Proyecto` | `Project` | `proyectos_project` |
| `Fase` | `Phase` | `proyectos_phase` |
| `Tarea` | `Task` | `proyectos_task` |
| `SesionTrabajo` | `WorkSession` | `proyectos_worksession` |
| `TareaDependencia` | `TaskDependency` | `proyectos_taskdependency` |
| `TerceroProyecto` | `ProjectStakeholder` | `proyectos_projectstakeholder` |
| `DocumentoContable` | `AccountingDocument` | `proyectos_accountingdocument` |
| `Hito` | `Milestone` | `proyectos_milestone` |
| `Actividad` | `Activity` | `proyectos_activity` |
| `ActividadProyecto` | `ProjectActivity` | `proyectos_projectactivity` |
| `ActividadSaiopen` | `SaiopenActivity` | `proyectos_saiopenactivity` |
| `EtiquetaTarea` | `TaskTag` | `proyectos_tasktag` |
| `ConfiguracionModulo` | `ModuleSettings` | `proyectos_modulesettings` |

> **Nota:** Las tablas de PostgreSQL NO fueron renombradas. Solo los nombres de clase Python y los `verbose_name` cambiaron. Los datos existentes no se afectaron.

---

## RELATED NAMES ACTUALIZADOS

| Modelo | Related name anterior | Related name nuevo |
|---|---|---|
| Phase.project | `fases` | `phases` |
| Task.phase | `tareas` | `tasks` |
| Task.task_padre | `subtareas` | `subtasks` |
| WorkSession.task | `sesiones` | `work_sessions` |
| Milestone.project | `hitos` | `milestones` |

---

## GUÍA DE MIGRACIÓN

### Para integraciones externas (agente, n8n, webhooks)

1. **Actualizar URLs** de `/api/v1/proyectos/` a `/api/v1/projects/`
2. **Actualizar valores de status** en todos los filtros y payloads (ver tablas arriba)
3. **Actualizar campos** en payloads JSON: los nombres de campo siguen en `snake_case` y en español donde aplica (DEC-010 se mantiene para campos individuales)

### Para código Python interno

```python
# Antes
from apps.proyectos.models import Proyecto, Tarea, Fase
proyecto = Proyecto.objects.filter(estado='borrador')

# Después
from apps.proyectos.models import Project, Task, Phase
proyecto = Project.objects.filter(estado='draft')
```

### Para código Angular interno

```typescript
// Antes
estado: 'borrador' | 'planificado' | 'en_progreso'

// Después
estado: 'draft' | 'planned' | 'in_progress'
```

---

## NUEVA ARQUITECTURA FRONTEND (FASE 2)

### Rutas nuevas
| Ruta | Componente | Descripción |
|---|---|---|
| `/dashboard` | `DashboardComponent` (reemplazado) | Module Selector — landing post-login |
| `/proyectos/cards` | `ProyectoCardsComponent` (nuevo) | Vista cards con métricas |

### Comportamiento nuevo
- **Sidebar:** Contextual por módulo. Cambia automáticamente según la URL activa.
- **Tareas:** Una sola entrada en el sidebar. Navega al último toggle usado (persistido en `localStorage['saisuite.tareasView']`).
- **Proyectos:** Toggle lista ↔ cards en el header de cada vista.

---

## DECISIONES DE DISEÑO

| ID | Decisión | Razón |
|---|---|---|
| DEC-010 | API usa `snake_case` en campos individuales | Consistencia con Django ORM y DRF |
| DEC-011 | Angular Material — nunca PrimeNG | Consistencia de tema y bundle size |
| REFT-21 | Alias `/proyectos/` eliminado | Sin double-exposure de endpoints |
