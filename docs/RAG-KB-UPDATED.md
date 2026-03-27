# RAG KNOWLEDGE BASE — SaiSuite v2.0
**ValMen Tech | Saicloud**
**Versión:** 2.0.0
**Fecha:** 27 Marzo 2026
**Uso:** Contexto de referencia para generación de código asistida por IA

---

## 1. MODELOS DJANGO — NOMBRES ACTUALES

### App: `apps.proyectos`

| Clase Python | Tabla PostgreSQL | Import |
|---|---|---|
| `Project` | `proyectos_project` | `from apps.proyectos.models import Project` |
| `Phase` | `proyectos_phase` | `from apps.proyectos.models import Phase` |
| `Task` | `proyectos_task` | `from apps.proyectos.models import Task` |
| `WorkSession` | `proyectos_worksession` | `from apps.proyectos.models import WorkSession` |
| `TaskDependency` | `proyectos_taskdependency` | `from apps.proyectos.models import TaskDependency` |
| `ProjectStakeholder` | `proyectos_projectstakeholder` | `from apps.proyectos.models import ProjectStakeholder` |
| `AccountingDocument` | `proyectos_accountingdocument` | `from apps.proyectos.models import AccountingDocument` |
| `Milestone` | `proyectos_milestone` | `from apps.proyectos.models import Milestone` |
| `Activity` | `proyectos_activity` | `from apps.proyectos.models import Activity` |
| `ProjectActivity` | `proyectos_projectactivity` | `from apps.proyectos.models import ProjectActivity` |
| `SaiopenActivity` | `proyectos_saiopenactivity` | `from apps.proyectos.models import SaiopenActivity` |
| `TaskTag` | `proyectos_tasktag` | `from apps.proyectos.models import TaskTag` |
| `ModuleSettings` | `proyectos_modulesettings` | `from apps.proyectos.models import ModuleSettings` |

### Related names actuales

```python
# Phase → Project
project.phases.all()           # antes: project.fases.all()

# Task → Phase
phase.tasks.all()              # antes: phase.tareas.all()

# Task → Task (subtareas)
task.subtasks.all()            # antes: task.subtareas.all()

# WorkSession → Task
task.work_sessions.all()       # antes: task.sesiones.all()

# Milestone → Project
project.milestones.all()       # antes: project.hitos.all()
```

---

## 2. CHOICES / STATUS VALUES

### EstadoProyecto (Project.estado)

```python
class EstadoProyecto(models.TextChoices):
    DRAFT      = 'draft',      'Borrador'
    PLANNED    = 'planned',    'Planificado'
    IN_PROGRESS = 'in_progress', 'En ejecución'
    SUSPENDED  = 'suspended',  'Suspendido'
    CLOSED     = 'closed',     'Cerrado'
    CANCELLED  = 'cancelled',  'Cancelado'
```

**Flujo de estados:**
```
draft → planned → in_progress → suspended → closed
                              → cancelled
```

### TareaEstado (Task.estado)

```python
class TareaEstado(models.TextChoices):
    TODO       = 'todo',       'Por Hacer'
    IN_PROGRESS = 'in_progress', 'En Progreso'
    IN_REVIEW  = 'in_review',  'En Revisión'
    BLOCKED    = 'blocked',    'Bloqueada'
    COMPLETED  = 'completed',  'Completada'
    CANCELLED  = 'cancelled',  'Cancelada'
```

### SesionTrabajoEstado (WorkSession.estado)

```python
class SesionTrabajoEstado(models.TextChoices):
    ACTIVE   = 'active',   'Activa'
    PAUSED   = 'paused',   'Pausada'
    FINISHED = 'finished', 'Finalizada'
```

### EstadoFase (Phase.estado)

```python
class EstadoFase(models.TextChoices):
    PLANNED   = 'planned',   'Planificada'
    ACTIVE    = 'active',    'Activa'
    COMPLETED = 'completed', 'Completada'
    CANCELLED = 'cancelled', 'Cancelada'
```

---

## 3. API ENDPOINTS

**Base URL local:** `http://localhost:8000/api/v1/`
**Base URL producción:** `https://api.saisuite.com/api/v1/`
**Auth:** `Authorization: Bearer <jwt_access_token>`

### Proyectos

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/projects/` | Lista paginada |
| POST | `/projects/` | Crear proyecto |
| GET | `/projects/{id}/` | Detalle completo |
| PATCH | `/projects/{id}/` | Actualizar parcial |
| PATCH | `/projects/{id}/cambiar-estado/` | Cambiar estado |
| GET | `/projects/{id}/gantt-data/` | Datos Gantt |
| GET | `/projects/{id}/estado-financiero/` | Estado financiero |

### Tareas

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/projects/tasks/` | Lista paginada |
| POST | `/projects/tasks/` | Crear tarea |
| GET | `/projects/tasks/{id}/` | Detalle |
| PATCH | `/projects/tasks/{id}/` | Actualizar parcial |
| PATCH | `/projects/tasks/{id}/cambiar-estado/` | Cambiar estado |
| POST | `/projects/tasks/{id}/agregar-horas/` | Agregar horas manualmente |

### Fases (anidadas bajo proyecto)

| Método | Endpoint |
|---|---|
| GET | `/projects/{proyecto_id}/phases/` |
| POST | `/projects/{proyecto_id}/phases/` |
| GET | `/projects/{proyecto_id}/phases/{id}/` |
| PATCH | `/projects/{proyecto_id}/phases/{id}/` |

### Hitos (anidados bajo proyecto)

| Método | Endpoint |
|---|---|
| GET | `/projects/{proyecto_id}/milestones/` |
| POST | `/projects/{proyecto_id}/milestones/` |

### Work Sessions (timesheets)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/projects/tasks/{id}/work-sessions/iniciar/` | Iniciar cronómetro |
| POST | `/projects/tasks/{id}/work-sessions/{session_id}/pausar/` | Pausar |
| POST | `/projects/tasks/{id}/work-sessions/{session_id}/finalizar/` | Finalizar |

### Otros

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/projects/activities-saiopen/` | Catálogo Saiopen |
| GET | `/projects/activities/` | Actividades internas |
| GET | `/terceros/` | Lista terceros |

> **NOTA CRÍTICA:** El alias `/api/v1/proyectos/` fue eliminado en REFT-21. Usar siempre `/api/v1/projects/`.

---

## 4. PATRONES DE CÓDIGO BACKEND

### Service pattern (toda lógica de negocio aquí)

```python
# apps/proyectos/services.py
import logging
from apps.proyectos.models import Project

logger = logging.getLogger(__name__)

def cambiar_estado_proyecto(project_id: str, nuevo_estado: str, user) -> Project:
    project = Project.objects.get(id=project_id, company=user.company)
    # validaciones...
    project.estado = nuevo_estado
    project.save()
    logger.info("proyecto_estado_cambiado", extra={
        "proyecto_id": str(project_id),
        "nuevo_estado": nuevo_estado,
        "user_id": str(user.id),
    })
    return project
```

### View pattern (solo orquesta)

```python
# apps/proyectos/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.proyectos import services

class ProjectViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['patch'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        project = services.cambiar_estado_proyecto(pk, request.data['estado'], request.user)
        return Response(ProjectSerializer(project).data)
```

### Query con filtro multi-tenant

```python
# SIEMPRE filtrar por company
qs = Project.objects.filter(company=request.user.company)

# Con related
qs = Task.objects.select_related('phase', 'phase__project', 'responsable') \
                 .filter(phase__project__company=request.user.company)
```

---

## 5. ARQUITECTURA FRONTEND ANGULAR

### Estructura de rutas

```
/dashboard                    → ModuleSelectorComponent (landing post-login)
/proyectos                    → ProyectoListComponent
/proyectos/cards              → ProyectoCardsComponent  ← NUEVO
/proyectos/:id                → ProyectoDetailComponent
/proyectos/tareas             → TareaListComponent
/proyectos/tareas/kanban      → TareaKanbanComponent
/proyectos/actividades        → ActividadListComponent
/proyectos/configuracion      → ProyectosConfigComponent
/terceros                     → TerceroListComponent
/admin/usuarios               → UsuariosComponent
/admin/empresa                → EmpresaComponent
```

> **IMPORTANTE:** La ruta `/proyectos/cards` debe declararse ANTES de `/proyectos/:id` en el array de rutas para evitar que el router capture `"cards"` como un UUID.

### Sidebar contextual

El sidebar muestra navegación distinta según el módulo activo:

```typescript
// core/components/sidebar/sidebar.component.ts
private detectModule(url: string): string {
  if (url.startsWith('/proyectos')) return 'proyectos';
  if (url.startsWith('/admin'))     return 'admin';
  if (url.startsWith('/terceros'))  return 'terceros';
  return 'home';
}
```

Los items de navegación se actualizan en cada evento `NavigationEnd`.

### localStorage — Vista de Tareas

```typescript
const TAREAS_VIEW_KEY = 'saisuite.tareasView';  // valores: 'list' | 'kanban'

// Escribir al entrar a cada vista:
// En TareaListComponent.ngOnInit():
localStorage.setItem(TAREAS_VIEW_KEY, 'list');

// En TareaKanbanComponent.ngOnInit():
localStorage.setItem(TAREAS_VIEW_KEY, 'kanban');

// Leer al navegar desde el sidebar:
const view = localStorage.getItem(TAREAS_VIEW_KEY) ?? 'list';
this.router.navigate([view === 'kanban' ? '/proyectos/tareas/kanban' : '/proyectos/tareas']);
```

### Patrón de componente con signals

```typescript
@Component({
  selector: 'app-proyecto-cards',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  // ...
})
export class ProyectoCardsComponent {
  private readonly proyectoService = inject(ProyectoService);
  private readonly router = inject(Router);

  readonly proyectos = signal<Proyecto[]>([]);
  readonly loading = signal(false);
  readonly searchText = signal('');
  readonly estadoFilter = signal('');

  constructor() {
    this.cargarProyectos();
  }

  private cargarProyectos(): void {
    this.loading.set(true);
    this.proyectoService.getProyectos({ page_size: 100 }).subscribe({
      next: (res) => { this.proyectos.set(res.results); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }
}
```

---

## 6. MODELOS TYPESCRIPT

### Proyecto

```typescript
export type EstadoProyecto = 'draft' | 'planned' | 'in_progress' | 'suspended' | 'closed' | 'cancelled';
export type TipoProyecto = 'civil_works' | 'consulting' | 'manufacturing' | 'services' | 'public_tender' | 'other';

export interface Proyecto {
  id: string;
  codigo: string;
  nombre: string;
  tipo: TipoProyecto;
  estado: EstadoProyecto;
  cliente_nombre: string;
  gerente: { id: string; full_name: string; email: string };
  fecha_inicio_planificada: string | null;
  fecha_fin_planificada: string | null;
  presupuesto_total: string;
  porcentaje_avance: string;
  activo: boolean;
  created_at: string;
}
```

### Tarea

```typescript
export type TareaEstado = 'todo' | 'in_progress' | 'in_review' | 'blocked' | 'completed' | 'cancelled';
export type TareaPrioridad = 1 | 2 | 3 | 4;

export interface Tarea {
  id: string;
  codigo: string;
  nombre: string;
  estado: TareaEstado;
  prioridad: TareaPrioridad;
  porcentaje_completado: number;
  horas_estimadas: number;
  horas_registradas: number;
  fase: string;
  fase_nombre: string;
  proyecto: string;
  proyecto_nombre: string;
  responsable: { id: string; full_name: string } | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  fecha_limite: string | null;
}
```

---

## 7. LABELS DE UI (español para mostrar al usuario)

### EstadoProyecto → Label

```typescript
export const ESTADO_PROYECTO_LABELS: Record<EstadoProyecto, string> = {
  draft:       'Borrador',
  planned:     'Planificado',
  in_progress: 'En ejecución',
  suspended:   'Suspendido',
  closed:      'Cerrado',
  cancelled:   'Cancelado',
};
```

### TipoProyecto → Label

```typescript
export const TIPO_LABELS: Record<TipoProyecto, string> = {
  civil_works:    'Obra Civil',
  consulting:     'Consultoría',
  manufacturing:  'Fabricación',
  services:       'Servicios',
  public_tender:  'Licitación Pública',
  other:          'Otro',
};
```

### TareaEstado → Label

```typescript
export const TAREA_ESTADO_LABELS: Record<TareaEstado, string> = {
  todo:        'Por Hacer',
  in_progress: 'En Progreso',
  in_review:   'En Revisión',
  blocked:     'Bloqueada',
  completed:   'Completada',
  cancelled:   'Cancelada',
};
```

---

## 8. REGLAS UI/UX — RESUMEN PARA GENERACIÓN

### Obligatorio en TODOS los componentes Angular

| Regla | Implementación |
|---|---|
| Framework | Angular Material — NUNCA PrimeNG/Bootstrap/Tailwind |
| Iconos | `mat-icon` con Material Icons |
| Notificaciones | `MatSnackBar` con `panelClass: ['snack-success'\|'snack-error'\|'snack-warning']` |
| Confirmaciones de eliminación | `MatDialog` con `ConfirmDialogComponent` — NUNCA `confirm()` |
| Tablas vacías | `sc-empty-state` fuera de `mat-table` |
| Estado de carga en listados | `mat-progress-bar` encima de tabla (NUNCA spinner centrado) |
| Sintaxis Angular 18 | `@if` / `@for` / `@switch` — NUNCA `*ngIf` / `*ngFor` |
| Colores CSS | `var(--sc-*)` siempre, sin hardcodear colores |
| Change detection | `ChangeDetectionStrategy.OnPush` |
| Suscripciones | `async pipe` en template — nunca `subscribe()` sin `unsubscribe` |
| TypeScript | `strict: true` — nunca `any`, usar `unknown` con narrowing |

### Filtros en vistas de listado (patrón canónico)

```html
<!-- Siempre en una sola línea, mismos 3 campos en lista y cards -->
<mat-card class="pl-filters-card">
  <div class="pl-filters-row">
    <mat-form-field class="pl-search" appearance="outline">
      <mat-label>Buscar</mat-label>
      <input matInput [value]="searchText()" (input)="onSearch($event)" placeholder="Código, nombre..." />
      <mat-icon matSuffix>search</mat-icon>
    </mat-form-field>

    <mat-form-field class="pl-filter" appearance="outline">
      <mat-label>Estado</mat-label>
      <mat-select [value]="estadoFilter()" (selectionChange)="onEstadoChange($event.value)">
        <mat-option value="">Todos</mat-option>
        @for (opt of estadoOptions; track opt.value) {
          <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
        }
      </mat-select>
    </mat-form-field>

    <mat-form-field class="pl-filter" appearance="outline">
      <mat-label>Tipo</mat-label>
      <mat-select [value]="tipoFilter()" (selectionChange)="onTipoChange($event.value)">
        <mat-option value="">Todos</mat-option>
        @for (opt of tipoOptions; track opt.value) {
          <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
        }
      </mat-select>
    </mat-form-field>
  </div>
</mat-card>
```

---

## 9. CONVENCIONES DE CÓDIGO

### Commits

```
feat(proyectos): add gantt view component
fix(tasks): correct estado filter in kanban
refactor(sidebar): make navigation contextual per module
test(projects): add service unit tests
docs(api): update endpoint reference
```

### Archivos Angular por feature

```
features/proyectos/
├── components/
│   ├── proyecto-list/          # Listado tabla
│   ├── proyecto-cards/         # Vista tarjetas
│   ├── proyecto-detail/        # Detalle con tabs
│   ├── proyecto-form/          # Formulario crear/editar
│   ├── tarea-list/             # Listado tareas
│   └── tarea-kanban/           # Kanban
├── models/
│   ├── proyecto.model.ts       # Interfaces TS
│   └── tarea.model.ts
├── services/
│   └── proyecto.service.ts     # HTTP calls
└── proyectos.routes.ts
```

### Archivos Django por app

```
apps/proyectos/
├── models.py         # Modelos — clases en inglés, campos en español
├── serializers.py    # Lista (mínimo) + Detalle (todos)
├── services.py       # TODA la lógica de negocio
├── views.py          # Solo orquesta → service → response
├── urls.py           # Router DRF
├── tests/
│   ├── test_services.py   # 80% cobertura mínima
│   └── test_views.py
└── migrations/
```

---

## 10. MULTI-TENANT — PATRÓN OBLIGATORIO

```python
# Todo queryset DEBE filtrar por company
Project.objects.filter(company=request.user.company)
Task.objects.filter(phase__project__company=request.user.company)

# BaseModel provee: id (UUID), company (FK), created_at, updated_at
class Project(BaseModel):
    nombre = models.CharField(max_length=200)
    # company ya está en BaseModel
```

```typescript
// Angular — el interceptor añade JWT automáticamente
// NUNCA añadir headers manualmente
this.http.get<ApiResponse<Proyecto[]>>('/api/v1/projects/')  // ✅
this.http.get('/api/v1/projects/', { headers: { Authorization: '...' } })  // ❌
```

---

## 11. PRÓXIMOS PASOS — FEATURES PENDIENTES (REFT-22+)

Según el estado del proyecto al 27 Marzo 2026:

1. **Tabs de Fases en Detalle Proyecto** — implementar gestión de fases con activar/desactivar
2. **Endpoint comparación Saiopen** — comparar actividades locales vs catálogo Saiopen
3. **Sincronización de Actividades desde Saiopen** — agente + SQS + worker Django
4. **Notificaciones en tiempo real** — WebSocket o polling para updates de tareas

---

*Base de conocimiento actualizada: 27 Marzo 2026 — SaiSuite v2.0.0*
