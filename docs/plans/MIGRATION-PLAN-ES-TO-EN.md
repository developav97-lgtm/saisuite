# Migration Plan: Spanish → English Rename
# SaiCloud — apps/proyectos refactor
# Generated: 2026-03-26 | Backend Architect FASE 0

---

## 1. Current State Analysis

**Module:** `apps/proyectos`
**Migrations applied:** 0001–0012
**API mount:** `/api/v1/proyectos/` in `config/urls.py`
**Total model classes:** 14

### Key Discovery — Models with explicit `db_table`

Two models are already decoupled from their Python class name:
- `SesionTrabajo` → `db_table = 'sesiones_trabajo'` → **no ALTER TABLE needed**
- `TimesheetEntry` → `db_table = 'timesheet_entries'` → **already English, no change**

> **Rule:** `app_label` stays `proyectos` throughout. Changing it would break Django's
> `contenttypes` framework, all assigned permissions, and existing audit logs.
> Only Python class names, field names, and URLs change.

---

## 2. Options Compared

| Option | Description | Verdict |
|---|---|---|
| **A — Direct (one phase)** | Rename everything at once | ❌ Rejected — 2000+ line PR, impossible safe review |
| **B — Gradual with `db_column` anchors** | Pin column names, rename Python, then rename BD | ✅ Recommended (simplified) |
| **C — New parallel module `apps/projects/`** | Create new app, data-migrate, deprecate old | ❌ Rejected — full duplication, cross-app FK migration |

---

## 3. Recommended Strategy: Simplified Option B (4 deployable phases)

PostgreSQL implements `ALTER TABLE RENAME` and `ALTER TABLE RENAME COLUMN` as catalog-only
metadata operations — no data rewrite, no meaningful row lock. For this module's current
data volume, each rename is sub-millisecond.

### Phase 1 — RenameModel (class names)
Django generates `ALTER TABLE proyectos_proyecto RENAME TO proyectos_project`, etc.
`SesionTrabajo` and `TimesheetEntry` receive **no ALTER TABLE** due to explicit `db_table`.

### Phase 2 — RenameField (field names)
Django generates `RENAME COLUMN` for ~50 fields. Each is a metadata operation in PostgreSQL.

### Phase 3 — URL renames (no BD migrations)
Change `/api/v1/proyectos/` → `/api/v1/projects/` in `config/urls.py`.
Keep old URL as a deprecated alias during frontend transition (1 release cycle).

### Phase 4 — Python cosmetics (no BD migrations)
Rename Serializer, Service, ViewSet, Permission class names to match new model names.

**Total estimated downtime: 0 minutes** (rolling deploys with pre-applied migrations)

---

## 4. Complete Class Rename Map

| Current Python Class | New Python Class | Physical Table Change |
|---|---|---|
| `Proyecto` | `Project` | `proyectos_proyecto` → `proyectos_project` |
| `ConfiguracionModulo` | `ProjectSettings` | `proyectos_configuracionmodulo` → `proyectos_projectsettings` |
| `Fase` | `Phase` | `proyectos_fase` → `proyectos_phase` |
| `TerceroProyecto` | `ProjectStakeholder` | `proyectos_terceroproyecto` → `proyectos_projectstakeholder` |
| `DocumentoContable` | `AccountingDocument` | yes |
| `Actividad` | `Activity` | yes |
| `ActividadProyecto` | `ProjectActivity` | yes |
| `ActividadSaiopen` | `SaiopenActivity` | yes |
| `Hito` | `Milestone` | yes |
| `TareaTag` | `TaskTag` | yes |
| `Tarea` | `Task` | `proyectos_tarea` → `proyectos_task` |
| `SesionTrabajo` | `WorkSession` | **No** — `db_table='sesiones_trabajo'` preserved |
| `TimesheetEntry` | `TimesheetEntry` | Already English — no change |
| `TareaDependencia` | `TaskDependency` | yes |

### ⚠️ Out of scope: TextChoices values
Values stored in DB (`'borrador'`, `'en_ejecucion'`, `'pendiente'`, etc.) are **data, not
identifiers**. Changing them requires a separate data migration + Angular frontend coordination.
Treat as a follow-up task after the structural rename is complete.

---

## 5. Key Field Renames (Tarea / Task model — highest impact)

| Current Field | New Field | Notes |
|---|---|---|
| `nombre` | `name` | |
| `descripcion` | `description` | |
| `fecha_inicio` | `start_date` | |
| `fecha_fin` | `end_date` | |
| `fecha_inicio_real` | `actual_start_date` | |
| `fecha_fin_real` | `actual_end_date` | |
| `horas_estimadas` | `estimated_hours` | |
| `horas_registradas` | `logged_hours` | |
| `estado` | `status` | |
| `prioridad` | `priority` | |
| `empresa` | `company` | via BaseModel inheritance — verify |
| `proyecto` | `project` | FK |
| `responsable` | `assignee` | FK to User |

> Full field mapping for all 14 models to be completed in PHASE 1 implementation.

---

## 6. Step-by-Step Execution

### Pre-execution checklist (MANDATORY)
```bash
# 1. Create migration backup point
git checkout -b refactor/es-to-en-rename

# 2. Full database backup
pg_dump -U postgres -d saisuite_db > backup_pre_refactor_$(date +%Y%m%d_%H%M%S).sql

# 3. Verify all tests pass (baseline)
cd backend && python manage.py test apps.proyectos --verbosity=2

# 4. Confirm migration state is clean
python manage.py showmigrations proyectos
```

### Phase 1 — Model class renames
```python
# In models.py: rename each class
# class Proyecto → class Project
# class Tarea → class Task
# etc.

# Generate migration — Django auto-detects renames
python manage.py makemigrations proyectos --name="rename_models_to_english"

# Review generated migration: confirm only RenameModel operations
# Apply
python manage.py migrate proyectos
```

### Phase 2 — Field renames
```python
# In models.py: rename fields on each model
# After Phase 1 is committed and tested

python manage.py makemigrations proyectos --name="rename_fields_to_english"
python manage.py migrate proyectos
```

### Phase 3 — URL renames
```python
# In config/urls.py:
# Add new route FIRST, keep old as deprecated alias
path('api/v1/projects/', include('apps.proyectos.urls', namespace='projects')),
path('api/v1/proyectos/', include('apps.proyectos.urls', namespace='proyectos')),  # DEPRECATED
```

### Phase 4 — Python cosmetics
```python
# Rename: ProyectoSerializer → ProjectSerializer
# Rename: TareaService → TaskService
# Rename: ProyectoViewSet → ProjectViewSet
# No migrations needed
```

---

## 7. Rollback Plan

Every phase generates a reversible migration:

```bash
# Rollback Phase 1 (after 0013 applied):
python manage.py migrate proyectos 0012
git revert <phase-1-commit>

# Rollback Phase 2 (after 0014 applied):
python manage.py migrate proyectos 0013
git revert <phase-2-commit>

# Emergency full rollback:
python manage.py migrate proyectos 0012
psql -U postgres -d saisuite_db < backup_pre_refactor_<timestamp>.sql
git checkout main
```

Django auto-generates inverse operations for both `RenameModel` and `RenameField`.

---

## 8. Cross-cutting ForeignKey considerations

The `proyectos` module has FKs from:
- `sync_agent` app: verify no FK to `Proyecto` or `Tarea`
- `users` app: check for any FK references

**Action:** Before Phase 1, grep for `'proyectos.Proyecto'` and `'proyectos.Tarea'` string
references across ALL apps to find cross-app FKs:
```bash
grep -r "proyectos\." backend/apps/ --include="*.py" | grep -v "proyectos/migrations"
```

---

## 9. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Cross-app FK not detected | LOW | HIGH | Run grep above before Phase 1 |
| Tests breaking after field rename | HIGH | MEDIUM | Update tests in same commit as field rename |
| Frontend 404 during URL transition | MEDIUM | HIGH | Keep `/proyectos/` alias for 1 release |
| TextChoices values breaking frontend | MEDIUM | MEDIUM | Treat as separate task, not in this refactor |
| Migration auto-detect fails (asks Create/Rename?) | LOW | LOW | Answer "Rename" when Django asks |

---

*Plan generated by Backend Architect — FASE 0*
*Requires: Senior PM task breakdown + Reality Checker pre-checklist before executing*
