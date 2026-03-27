# CONTEXT.md - Estado del Proyecto Saicloud

**Última actualización:** 27 Marzo 2026
**Sesión:** Feature #5 — Reporting & Analytics (Completa)

---

## 📊 ESTADO ACTUAL

### Proyecto
- **Nombre:** Saicloud (SaiSuite)
- **Stack:** Django 5 + Angular 18 + PostgreSQL 16 + n8n + AWS
- **Fase:** Desarrollo activo
- **Último milestone:** Feature #5 — Reporting & Analytics completa (9 endpoints, 4 gráficos Chart.js, exportación Excel)

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #5: Reporting & Analytics

### Backend completado
- ✅ **analytics_services.py**: 8 funciones — `get_project_kpis`, `get_task_distribution`, `get_velocity_data`, `get_burn_rate_data`, `get_burn_down_data`, `get_resource_utilization`, `compare_projects`, `get_project_timeline`
- ✅ **analytics_views.py**: 9 APIViews — `ProjectKPIsView`, `ProjectTaskDistributionView`, `ProjectVelocityView`, `ProjectBurnRateView`, `ProjectBurnDownView`, `ProjectResourceUtilizationView`, `ProjectTimelineView`, `CompareProjectsView`, `ExportExcelView`
- ✅ **analytics_serializers.py**: 13 serializers read-only + 2 request serializers (`CompareProjectsRequestSerializer`, `ExportExcelRequestSerializer`)
- ✅ **urls.py**: 9 nuevas rutas bajo `# Analytics — Feature #5`
- ✅ Zero nuevos modelos — todo calculado desde datos existentes
- ✅ Exportación Excel con openpyxl (3 hojas: Summary, KPIs, Task Distribution)

### Endpoints disponibles — Feature #5
- `GET  /api/v1/projects/{id}/analytics/kpis/`
- `GET  /api/v1/projects/{id}/analytics/task-distribution/`
- `GET  /api/v1/projects/{id}/analytics/velocity/?periods=8`
- `GET  /api/v1/projects/{id}/analytics/burn-rate/?periods=8`
- `GET  /api/v1/projects/{id}/analytics/burn-down/?granularity=week`
- `GET  /api/v1/projects/{id}/analytics/resource-utilization/`
- `GET  /api/v1/projects/{id}/analytics/timeline/`
- `POST /api/v1/projects/analytics/compare/`
- `POST /api/v1/projects/analytics/export-excel/`

### Frontend completado
- ✅ **analytics.model.ts**: 13 interfaces TypeScript + 2 request interfaces
- ✅ **analytics.service.ts**: 9 métodos (`getKPIs`, `getTaskDistribution`, `getVelocity`, `getBurnRate`, `getBurnDown`, `getResourceUtilization`, `getTimeline`, `compareProjects`, `exportExcel`)
- ✅ **project-analytics-dashboard**: Componente OnPush con forkJoin paralelo + 4 gráficos Chart.js (burn down, velocity, task distribution doughnut, resource utilization horizontal bar)

### Documentación generada — Feature #5
- ✅ `docs/FEATURE-5-API-DOCS.md` — 9 endpoints documentados con ejemplos JSON
- ✅ `docs/FEATURE-5-USER-GUIDE.md` — Guía para gerentes y coordinadores (español)
- ✅ `docs/FEATURE-5-ARCHITECTURE.md` — Decisiones de diseño y cálculo de métricas

### Decisiones de diseño — Feature #5
- Sin nuevos modelos de BD — métricas calculadas on-the-fly desde `Task`, `TimesheetEntry`, `ResourceAssignment`, `ResourceCapacity`
- Caché: Django file-based cuando sea necesario (Redis no requerido en MVP)
- PDF: jsPDF en frontend (evita dependencias del servidor)
- Excel: openpyxl en backend (streaming como Blob)
- On-Time Rate usa `updated_at` como proxy de `fecha_completion` (limitación conocida MVP)
- Burn Down usa `itertools.accumulate` en Python (evita window functions SQL no portables)

---

## ✅ COMPLETADO (27 Marzo 2026) — Feature #4: Resource Management

### Backend completado
- ✅ **Modelos** (migration 0015): `ResourceAssignment`, `ResourceCapacity`, `ResourceAvailability`, `AvailabilityType`
- ✅ **Seed**: 3 registros `ResourceCapacity` (40h/semana) para usuarios existentes
- ✅ **Django Admin**: 3 admin classes con fieldsets
- ✅ **Serializers** (9 clases): List/Detail/Create para assignments; Capacity; Availability + Create; WorkloadSummary; TeamAvailability
- ✅ **Services** (`resource_services.py`): BK-11 a BK-18 — assign, remove, overallocation, workload, team timeline, capacity, availability, approve
- ✅ **Views** (6 clases): `ResourceAssignmentViewSet`, `ResourceCapacityViewSet`, `ResourceAvailabilityViewSet`, `WorkloadView`, `TeamAvailabilityView`, `UserCalendarView`
- ✅ **URLs** (BK-25): 11 nuevas rutas bajo `/api/v1/projects/`
- ✅ `python manage.py check` — 0 issues

### Endpoints disponibles — Feature #4
- `GET/POST   /api/v1/projects/tasks/{task_pk}/assignments/`
- `GET/DEL    /api/v1/projects/tasks/{task_pk}/assignments/{pk}/`
- `GET        /api/v1/projects/tasks/{task_pk}/assignments/check-overallocation/`
- `GET/POST   /api/v1/projects/resources/capacity/`
- `GET/PATCH/DEL /api/v1/projects/resources/capacity/{pk}/`
- `GET/POST   /api/v1/projects/resources/availability/`
- `GET/DEL    /api/v1/projects/resources/availability/{pk}/`
- `POST       /api/v1/projects/resources/availability/{pk}/approve/`
- `GET        /api/v1/projects/resources/workload/`
- `GET        /api/v1/projects/resources/calendar/`
- `GET        /api/v1/projects/{proyecto_pk}/team-availability/`

### Pendiente — Feature #4 (deuda técnica)
- [ ] Tests: BK-26 test_resource_models, BK-27 test_resource_services (85% min), BK-28 test_resource_views
- [ ] Angular FE-1–FE-10: 8 componentes (ResourceAssignmentCard, ResourceCalendar, WorkloadChart, TeamTimeline, ResourcePanel, AvailabilityForm, CapacityForm, OverallocationBadge)
- [ ] Integración: Tab "Recursos" en TareaDetail (IT-1), avatares en Gantt (IT-2), Tab "Equipo" en ProyectoDetail (IT-3)

---

## ✅ COMPLETADO RECIENTEMENTE (26 Marzo 2026)

### Rename Completo Español → Inglés (REFT-01–REFT-21)
**Tiempo:** ~3 sesiones
**Complejidad:** XL

**Cambios principales:**
- ✅ Migration 0013: 13 `RenameModel` + 11 `AlterField` + 11 `RunSQL` data migrations
- ✅ Todos los modelos renombrados: `Proyecto→Project`, `Fase→Phase`, `Tarea→Task`, `SesionTrabajo→WorkSession`, `TareaDependencia→TaskDependency`, `TerceroProyecto→ProjectStakeholder`, `DocumentoContable→AccountingDocument`, `Hito→Milestone`, `Actividad→Activity`, `ActividadProyecto→ProjectActivity`, `ActividadSaiopen→SaiopenActivity`, `EtiquetaTarea→TaskTag`, `ConfiguracionModulo→ModuleSettings`
- ✅ TextChoices en inglés: `por_hacer→todo`, `en_progreso→in_progress`, `completada→completed`, etc.
- ✅ Related names en inglés: `fases→phases`, `tareas→tasks`, `subtareas→subtasks`, etc.
- ✅ URLs: `/api/v1/proyectos/` → `/api/v1/projects/`, path segments en inglés
- ✅ Todos los aliases de compatibilidad eliminados (REFT-10)
- ✅ 365 tests backend pasando (REFT-11)
- ✅ Angular: status values, URLs y modelos actualizados (REFT-12–16)
- ✅ Management command `migrar_actividades_a_tareas` actualizado
- ✅ URL deprecated `/api/v1/proyectos/` eliminada (REFT-21)

**Decisiones:** DEC-010 (snake_case API), DEC-011 (Angular Material), y decisions de rename en DECISIONS.md

---

## ✅ COMPLETADO (24 Marzo 2026)

### Refactor Arquitectura Proyectos
**Tiempo:** 2 días (23-24 Marzo)  
**Complejidad:** XL  

**Backend Django:**
- ✅ Modelo `ActividadSaiopen` (catálogo maestro reutilizable)
- ✅ Modelo `Fase` actualizado (estado, orden, solo 1 activa)
- ✅ Modelo `Tarea` refactorizado (sin FK proyecto, con FK actividad_saiopen)
- ✅ Campos `cantidad_registrada`, `cantidad_objetivo`
- ✅ Signals progreso automático (Tarea → Fase → Proyecto)
- ✅ `FaseService.activar_fase()`
- ✅ 4 migraciones ejecutadas
- ✅ 19 tests corregidos (services, signals, views)

**Frontend Angular:**
- ✅ Service `ActividadSaiopenService`
- ✅ Autocomplete actividades en formulario
- ✅ **Detalle Tarea con UI Adaptativa** (3 modos):
  - `solo_estados`: Solo selector estado (sin actividad)
  - `timesheet`: Cronómetro + horas (actividad en horas)
  - `cantidad`: Campo clickeable + edición inline (actividad en días/m³/ton)
- ✅ **Kanban con Filtro de Fase**
- ✅ **Activar Fase en FaseList** (columna estado + botón)

**Métricas:**
- Archivos modificados: ~35
- Líneas de código: ~6,500
- Tests corregidos: 19
- Decisiones arquitectónicas: 3 (DEC-020, DEC-021, DEC-022)

---

## 🗂️ ESTRUCTURA ACTUAL

### Backend (Django)
```
apps/proyectos/
├── models/
│   ├── proyecto.py
│   ├── fase.py (estado, orden)
│   ├── tarea.py (sin FK proyecto, con actividad_saiopen)
│   └── actividad_saiopen.py (NUEVO - catálogo compartido)
├── services/
│   ├── proyecto_service.py
│   ├── fase_service.py (activar_fase)
│   └── tarea_service.py
├── serializers/
│   ├── actividad_saiopen_serializer.py (NUEVO)
│   └── tarea_serializer.py (actualizado)
├── views/
│   ├── fase_viewset.py (endpoint activar)
│   └── tarea_viewset.py (endpoint actualizar-cantidad)
└── signals.py (progreso automático)
```

### Frontend (Angular)
```
frontend/src/app/proyectos/
├── models/
│   ├── actividad-saiopen.model.ts (NUEVO)
│   └── tarea.model.ts (actualizado)
├── services/
│   ├── actividad-saiopen.service.ts (NUEVO)
│   ├── fase.service.ts (obtenerFaseActiva, activar)
│   └── tarea.service.ts (actualizarCantidad)
├── components/
│   ├── tarea-form/ (autocomplete actividad)
│   ├── tarea-detail/ (UI adaptativa 3 modos)
│   ├── tarea-kanban/ (filtro fase)
│   └── fase-list/ (columna estado + activar)
```

---

## 📋 DECISIONES ARQUITECTÓNICAS

### DEC-020: Jerarquía Estricta Proyecto → Fases → Tareas
- **Estado:** ✅ Activa
- **Fecha:** 24 Marzo 2026
- **Cambio principal:** Eliminado FK `tarea.proyecto` (redundante)
- **Razón:** Modelo más limpio, progreso automático predecible
- **Consecuencia:** Todas las tareas DEBEN tener fase

### DEC-021: ActividadSaiopen como Catálogo Compartido
- **Estado:** ✅ Activa
- **Fecha:** 24 Marzo 2026
- **Cambio principal:** Actividades reutilizables entre proyectos
- **Razón:** Compatibilidad con Saiopen (ERP local)
- **Consecuencia:** Sincronización vía SQS desde Saiopen

### DEC-022: Medición de Progreso según Unidad de Actividad
- **Estado:** ✅ Activa
- **Fecha:** 24 Marzo 2026
- **Cambio principal:** UI adaptativa según `unidad_medida`
- **Razón:** Cada actividad se mide naturalmente (horas/días/m³)
- **Consecuencia:** 3 modos de UI en detalle de tarea

**Decisiones previas activas:** DEC-001 a DEC-019 (ver DECISIONS.md)

---

## 🚧 PENDIENTES

### Prioridad Alta
- [ ] REFT-22–REFT-27: Angular features pendientes (ModuleLauncher, sidebar contextual, Kanban/Lista toggle, Project cards view, E2E verify)
- [ ] Tabs de Fases en Detalle Proyecto

### Prioridad Media
- [ ] Endpoint Comparación Saiopen (`GET /api/v1/projects/{id}/comparacion-saiopen/`)
- [ ] Sincronización Actividades desde Saiopen (agente + SQS)

### Prioridad Baja
- [ ] Documentación técnica actualizada
- [ ] Panel Admin para SaiopenActivity

---

## 🧪 PRUEBAS PENDIENTES

**Guía completa:** https://www.notion.so/32dee9c3690a810187f7fe510faee8aa

### Casos de Prueba
1. **Detalle Tarea UI Adaptativa:**
   - Caso 1: Tarea sin actividad (solo estados)
   - Caso 2: Tarea con actividad en horas (timesheet)
   - Caso 3: Tarea con actividad en m³ (edición inline)

2. **Kanban con Filtro de Fase:**
   - Dropdown aparece al seleccionar proyecto
   - Filtrado funciona correctamente
   - Limpiar filtros resetea todo

3. **Activar Fase:**
   - Columna estado visible
   - Botón activar solo en planificadas
   - Confirmación + recarga

---

## 📚 DOCUMENTACIÓN

### Notion
- **Metodología:** https://www.notion.so/31dee9c3690a81668fc3cd5080240bb7
- **Decisiones:** https://www.notion.so/323ee9c3690a817e9919cf7f810289fe
- **Refactor Completado:** https://www.notion.so/32dee9c3690a813a8b9fcd45b0f05c60
- **Guía de Pruebas:** https://www.notion.so/32dee9c3690a810187f7fe510faee8aa

### Archivos Locales
- `CLAUDE.md` — Reglas permanentes del proyecto
- `DECISIONS.md` — Decisiones arquitectónicas (DEC-XXX)
- `ERRORS.md` — Registro de errores resueltos
- `CONTEXT.md` — Este archivo (estado sesión a sesión)

### Documentos Base
- `docs/base-reference/Infraestructura_SaiSuite_v2.docx`
- `docs/base-reference/Flujo_Feature_SaiSuite_v1.docx`
- `docs/base-reference/Estandares_Codigo_SaiSuite_v1.docx`
- `docs/base-reference/Esquema_BD_SaiSuite_v1.docx`
- `docs/base-reference/AWS_Setup_SaiSuite_v1.docx`

---

## 🎯 PRÓXIMA SESIÓN — Feature #6 sugerida

### Opción A: Completar deuda técnica Feature #4
Prioridad alta si el cliente va a usar el módulo de recursos pronto.

1. Tests backend Feature #4: `test_resource_models`, `test_resource_services` (cobertura 85% mínimo), `test_resource_views`
2. Componentes Angular Feature #4: `ResourceAssignmentCard`, `ResourceCalendar`, `WorkloadChart`, `TeamTimeline`
3. Integración: Tab "Recursos" en TareaDetail, Tab "Equipo" en ProyectoDetail

**Prerequisitos:**
- `python manage.py migrate` (ya ejecutado, solo verificar)
- `ng serve`

### Opción B: Feature #6 — Notificaciones y Alertas
Notificaciones en tiempo real cuando: tarea vence, presupuesto supera umbral, recurso sobreasignado.

**Stack sugerido:** Django Channels + WebSocket o polling periódico (más simple).
**Decisión pendiente:** Redis para WebSockets vs. polling cada 60s (sin infraestructura adicional).

### Opción C: Feature #6 — Portal de cliente / Stakeholders
Vista de solo lectura para stakeholders externos: progreso del proyecto, hitos, documentos.
Sin autenticación JWT propia — token de acceso público por proyecto.

### Opción D: Completar Analytics — Mejoras MVP
1. Agregar campo `Task.fecha_completion` (migration + signal) para On-Time Rate preciso
2. Implementar granularidad `month` en burn-down
3. Conectar parámetros `metrics` y `date_range` en export-excel

**Recomendación:** Opción A primero (deuda técnica Feature #4), luego Feature #6 Notificaciones.

---

## 📞 CONTACTO & RECURSOS

- **Desarrollador:** Juan David (Fundador, CEO, CTO)
- **Empresa:** ValMen Tech
- **Email:** juan@valmentech.com
- **Repositorio:** (Git local, sin remote por ahora)

---

*Última sesión: 27 Marzo 2026*
*Estado: Feature #5 Analytics completa — 9 endpoints, 4 gráficos Chart.js, exportación Excel, documentación FASE 4 generada*
*Listo para: Feature #4 deuda técnica (tests + Angular FE) o Feature #6 nueva*