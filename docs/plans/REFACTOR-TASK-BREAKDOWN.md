# Refactor Task Breakdown: Español → English + New Navigation
# SaiCloud — Senior PM FASE 0
# Generated: 2026-03-26 | 27 tareas ejecutables

---

## Resumen de hallazgos (código real)

- `models.py` — 14 clases, ~120 campos en español
- `serializers.py` — 20+ serializer classes con nombres en español
- `views.py` — `TareaViewSet`, `ProyectoViewSet`, etc. **URL hardcodeada en línea ~589**
- `tarea_services.py` — `TareaService`, `DependenciaService`
- Frontend — 24 componentes, 6 modelos/servicios, 1 routes file
- `timesheet.service.ts` tiene `tareaBase = '/api/v1/proyectos/tareas'` hardcodeada

### Riesgo oculto confirmado
`views.py` línea ~589 tiene `url_accion=f'/proyectos/tareas/{instance.id}'` en la notificación de asignación.
Esta URL hardcodeada NO cambiará automáticamente con el rename — debe corregirse explícitamente en REFT-08.

---

## Decisiones requeridas ANTES de iniciar

| Decisión | Recomendación | Impacto si se difiere |
|---|---|---|
| D1. ¿Renombrar campos en BD (`nombre`, `descripcion`, etc.)? | **NO** — diferir a segundo ciclo | Riesgo alto, beneficio bajo ahora |
| D2. ¿Renombrar URLs de API a `/api/v1/projects/`? | **SÍ** — con coexistencia temporal de `/proyectos/` | Sin coexistencia → frontend rompe en deploy |
| D3. ¿Renombrar interfaces Angular `ProyectoList` → `ProjectList`? | **Diferir** — actualizar tipos internos solo | Reduce scope 30% |
| D4. ¿Valores TextChoices en BD cambian? | **NO** — solo clases Python | Cambiarlo requiere data migration + ventana de mantenimiento |

---

## Las 27 Tareas (REFT-01 a REFT-27)

---

### Bloque 0 — Preparación (prerequisito de todo)

**REFT-01** — Crear rama git y verificar baseline
- Estimación: 0.5h
- Dependencias: ninguna
- Archivos: ninguno (solo git)
- Acciones:
  ```bash
  git add backend/apps/proyectos/migrations/0012_timesheetentry.py
  git commit -m "chore(proyectos): add untracked 0012 migration"
  git checkout -b refactor/english-rename
  python manage.py test apps.proyectos --verbosity=2 > test_baseline.txt
  ```
- Criterio: Tests en verde, branch creada, 0012 commiteada

**REFT-02** — Backup BD + documentar baseline de tests
- Estimación: 0.5h
- Dependencias: REFT-01
- Acciones:
  ```bash
  pg_dump -U saisuite_user -d saisuite_dev -F c -f backup_pre_refactor_$(date +%Y%m%d).dump
  # Verificar restore a DB temporal
  ```
- Criterio: Backup restaurable verificado, output de tests guardado

---

### Bloque 1 — Migración BD (CRÍTICO — ejecutar primero)

**REFT-03** — Crear migración `0013_rename_models_to_english.py`
- Estimación: 1.5h
- Dependencias: REFT-02
- Archivos: `backend/apps/proyectos/migrations/0013_rename_models_to_english.py`
- Nota crítica: `SesionTrabajo` tiene `db_table = 'sesiones_trabajo'` — NO necesita `RenameModel`. `TimesheetEntry` tiene `db_table = 'timesheet_entries'` — NO necesita `RenameModel`. Los otros 12 modelos SÍ.
- Acciones:
  1. Renombrar clases en `models.py` (solo los nombres de clase, sin campos)
  2. `python manage.py makemigrations proyectos --name="rename_models_to_english"`
  3. Verificar que la migración generada usa `migrations.RenameModel` exclusivamente
  4. `python manage.py migrate proyectos`
  5. Verificar en psql que las tablas existen con los nuevos nombres
- Criterio: `python manage.py showmigrations proyectos` muestra 0013 aplicada, sin errores

---

### Bloque 2 — Backend Python (REFT-04 a REFT-11)

**REFT-04** — Renombrar clases en `models.py` + aliases temporales
- Estimación: 2h
- Dependencias: REFT-03
- Archivos: `backend/apps/proyectos/models.py`
- Nota: Agregar al final del archivo aliases `Proyecto = Project`, `Tarea = Task`, etc. para que el resto del codebase no rompa mientras se actualiza. Estos aliases se eliminan en REFT-10.
- Criterio: `from apps.proyectos.models import Proyecto` sigue funcionando gracias al alias

**REFT-05** — Actualizar `serializers.py` (20+ clases)
- Estimación: 1.5h
- Dependencias: REFT-04
- Archivos: `backend/apps/proyectos/serializers.py`
- Criterio: `python manage.py check` sin errores

**REFT-06** — Actualizar `tarea_services.py`
- Estimación: 1.5h
- Dependencias: REFT-04
- Archivos: `backend/apps/proyectos/tarea_services.py`
- Criterio: Tests de services pasan

> **REFT-05, REFT-06, REFT-07 pueden ejecutarse en paralelo**

**REFT-07** — Actualizar `services.py`, `filters.py`, `permissions.py`, `signals.py`
- Estimación: 1.5h
- Dependencias: REFT-04
- Archivos: los 4 archivos mencionados + `admin.py`
- Criterio: `python manage.py check` sin errores

**REFT-08** — Actualizar `views.py` + URL hardcodeada
- Estimación: 2h
- Dependencias: REFT-05 + REFT-06 + REFT-07
- Archivos: `backend/apps/proyectos/views.py`
- ⚠️ CRÍTICO: Línea ~589 tiene `url_accion=f'/proyectos/tareas/{instance.id}'` — actualizar a `/projects/tasks/{instance.id}` en este paso
- Criterio: Tests de views pasan, URL de notificación corregida

**REFT-09** — Actualizar `urls.py` + `config/urls.py` — coexistencia temporal
- Estimación: 1h
- Dependencias: REFT-08
- Archivos: `backend/apps/proyectos/urls.py`, `backend/config/urls.py`
- Estrategia:
  ```python
  # config/urls.py — mantener AMBAS durante transición
  path('api/v1/projects/', include('apps.proyectos.urls')),  # NUEVO
  path('api/v1/proyectos/', include('apps.proyectos.urls')),  # DEPRECADO — eliminar en REFT-21
  ```
- Criterio: `GET /api/v1/projects/tareas/` y `GET /api/v1/proyectos/tareas/` ambos responden 200

**REFT-10** — Limpiar aliases temporales del backend
- Estimación: 1h
- Dependencias: REFT-08 + REFT-09
- Archivos: `backend/apps/proyectos/models.py`
- Criterio: Todos los imports usan nombres en inglés, aliases eliminados, tests pasan

**REFT-11** — Corregir tests del backend (26 archivos)
- Estimación: 1.5h
- Dependencias: REFT-10
- Archivos: todos en `backend/apps/proyectos/tests/`
- Criterio: `python manage.py test apps.proyectos` — 100% verde

---

### Bloque 3 — Frontend Modelos y Servicios (REFT-12 a REFT-15)

**REFT-12** — Actualizar `tarea.model.ts` (11 interfaces/tipos)
- Estimación: 1h
- Dependencias: REFT-09 (API respondiendo en inglés)
- Archivos: `frontend/src/app/features/proyectos/models/tarea.model.ts`
- Criterio: Sin errores TypeScript strict

**REFT-13** — Actualizar `timesheet.model.ts` (`SesionTrabajo → WorkSession`)
- Estimación: 0.5h
- Dependencias: REFT-12
- Archivos: `frontend/src/app/features/proyectos/models/timesheet.model.ts`
- Criterio: Sin errores TypeScript strict

**REFT-14** — Actualizar modelos de proyecto en Angular
- Estimación: 0.5h
- Dependencias: REFT-12
- Archivos: `frontend/src/app/features/proyectos/models/proyecto.model.ts` (si existe)
- Nota: Solo actualizar campos de interfaces TS que deben coincidir con serializers Django actualizados

**REFT-15** — Actualizar URLs en servicios Angular (13 servicios)
- Estimación: 1h
- Dependencias: REFT-09 + REFT-13
- Archivos: `proyecto.service.ts`, `timesheet.service.ts` y todos los servicios que usan `/api/v1/proyectos/`
- Criterio: Todos los servicios apuntan a `/api/v1/projects/`

---

### Bloque 4 — Frontend Componentes (REFT-16 a REFT-21)

**REFT-16** — Actualizar `tarea-list`, `tarea-kanban`, `tarea-card`
- Estimación: 2h
- Dependencias: REFT-12 + REFT-15
- Archivos: los 3 componentes + sus tests si existen

**REFT-17** — Actualizar `tarea-detail`, `tarea-form`, `tarea-dialog`
- Estimación: 2h
- Dependencias: REFT-16

**REFT-18** — Actualizar `selector-dependencias`, `timer`, `timesheet-semanal`, `gantt-view`
- Estimación: 1.5h
- Dependencias: REFT-17

**REFT-19** — Actualizar `proyecto-detail`, `proyecto-list`
- Estimación: 1.5h
- Dependencias: REFT-17 + REFT-15

**REFT-20** — Actualizar rutas en `proyectos.routes.ts` y `app.routes.ts`
- Estimación: 1h
- Dependencias: REFT-19
- Acción extra: `grep -r "router.navigate" frontend/src/app/features/proyectos` para encontrar navegaciones hardcodeadas
- Criterio: Sin referencias a rutas `/proyectos` en código Angular

**REFT-21** — Limpieza final: eliminar URL `/proyectos/` del backend + `ng build` sin errores
- Estimación: 0.5h
- Dependencias: REFT-16 + REFT-17 + REFT-18 + REFT-19 + REFT-20
- Acciones:
  - Eliminar el alias deprecated en `config/urls.py`
  - `cd frontend && ng build --configuration=production` — debe compilar sin errores
- Criterio: 0 errores TypeScript strict, build exitoso

---

### Bloque 5 — Nuevas Funcionalidades (REFT-22 a REFT-25)

**REFT-22** — Landing Page de Módulos (`ModuleLauncherComponent`)
- Estimación: 2.5h
- Dependencias: REFT-20
- Stack: `mat-card` por módulo, Angular Material únicamente
- Archivos nuevos:
  - `frontend/src/app/features/home/components/module-launcher/`
  - `frontend/src/app/features/home/module-card/`
- Criterio: Post-login redirige a `/home`, módulos muestran cards con Angular Material, CRM/Soporte/Finanzas como "coming soon"

**REFT-23** — Sidebar contextual por módulo
- Estimación: 3h
- Dependencias: REFT-22
- Stack: `mat-sidenav`, detectar módulo activo desde URL, `@switch` en template
- Archivos: Modificar `shell.component` o `layout.component`, crear `proyectos-sidebar.component`
- Criterio: Al entrar a `/projects`, sidebar muestra solo items de Proyectos. Botón "← Módulos" visible.

> **REFT-24 y REFT-25 pueden ejecutarse en paralelo con REFT-23**

**REFT-24** — Toggle Kanban/Lista para Tasks (`mat-button-toggle-group`)
- Estimación: 2h
- Dependencias: REFT-20
- Archivos: `task-view.component.ts/html` (nuevo) o modificar componente existente
- Criterio: `mat-button-toggle-group` persiste en localStorage, una sola entrada "Tasks" en sidebar

**REFT-25** — Vista Cards de Proyectos (`mat-card` + `mat-progress-bar`)
- Estimación: 3h
- Dependencias: REFT-22
- Archivos: nuevo `proyecto-card.component`, nuevo `proyectos-card-list.component`
- Criterio: Cards muestran progreso, tareas completadas/total, horas registradas/estimadas

---

### Bloque 6 — Verificación y Cierre

**REFT-26** — Test de integración end-to-end (checklist 20 items)
- Estimación: 2h
- Dependencias: REFT-25 (todos los componentes completos)
- Flujos a verificar: Login → Landing módulos → Proyectos lista/cards → Tarea detail → Kanban → Timesheet semanal → Timer → Logout

**REFT-27** — Actualizar `CONTEXT.md` y `DECISIONS.md`
- Estimación: 0.5h
- Dependencias: REFT-26
- Nuevas decisiones a documentar: DEC-023 (rename español→inglés), DEC-024 (landing módulos), DEC-025 (toggle Kanban/Lista)

---

## Estimación total

| Categoría | Horas |
|---|---|
| Bloque 0 — Preparación | 1h |
| Bloque 1 — Migración BD | 1.5h |
| Bloque 2 — Backend Python | 11h |
| Bloque 3 — Frontend modelos/servicios | 3h |
| Bloque 4 — Frontend componentes | 8.5h |
| Bloque 5 — Nuevas funcionalidades | 10.5h |
| Bloque 6 — Verificación y cierre | 2.5h |
| **Subtotal** | **38h** |
| Buffer imprevistos 20% | 8h |
| **TOTAL** | **46h** |

| Escenario | Días |
|---|---|
| Optimista (senior sin interrupciones) | 5-6 días |
| Realista (context switching normal) | **7-8 días** |
| Conservador (bugs no anticipados) | 10-12 días |

---

## Ruta crítica

```
REFT-01 → REFT-02 → REFT-03 → REFT-04
                               ↓
                    REFT-05/06/07 (paralelo)
                               ↓
                    REFT-08 → REFT-09 → REFT-10 → REFT-11
                                                    ↓
                                         REFT-12/13/14 → REFT-15
                                                          ↓
                                              REFT-16 → 17 → 18/19/20 → REFT-21
                                                                          ↓
                                                    REFT-22 → REFT-23/24/25
                                                                    ↓
                                                         REFT-26 → REFT-27
```

**El bloqueante más largo:** REFT-11 (tests del backend) debe estar en verde antes de tocar cualquier archivo frontend.

---

*Plan generado por Senior PM — FASE 0*
*Requiere aprobación de las 4 decisiones D1-D4 antes de ejecutar REFT-01*
