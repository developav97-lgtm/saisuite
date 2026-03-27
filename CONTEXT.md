# CONTEXT.md - Estado del Proyecto Saicloud

**Última actualización:** 26 Marzo 2026
**Sesión:** Rename Inglés Completo — apps/proyectos (REFT-01 a REFT-21)

---

## 📊 ESTADO ACTUAL

### Proyecto
- **Nombre:** Saicloud (SaiSuite)
- **Stack:** Django 5 + Angular 18 + PostgreSQL 16 + n8n + AWS
- **Fase:** Desarrollo activo
- **Último milestone:** Refactor arquitectura Proyectos → Fases → Tareas + Actividades Saiopen

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

## 🎯 PRÓXIMA SESIÓN

**Objetivo sugerido:**
1. Ejecutar pruebas del refactor (guía en Notion)
2. Corregir bugs encontrados
3. Implementar tabs de fases en proyecto-detail
4. Documentar técnicamente el refactor

**Prerequisitos:**
- Backend: `python manage.py migrate` + datos de prueba
- Frontend: `ng serve`
- Seguir scripts de la guía de pruebas

---

## 📞 CONTACTO & RECURSOS

- **Desarrollador:** Juan David (Fundador, CEO, CTO)
- **Empresa:** ValMen Tech
- **Email:** juan@valmentech.com
- **Repositorio:** (Git local, sin remote por ahora)

---

*Última sesión: 26 Marzo 2026*
*Estado: Rename Inglés completo — 365 tests backend OK, Angular compilando sin errores TS*
*Listo para: REFT-22–27 (Angular features) o inicio de nueva feature*