## DEC-023: Refactoring Completo — Renombrado Español → Inglés
**Fecha:** 2026-03-26
**Estado:** 🔄 En ejecución — rama `refactor/english-rename`
**Contexto:** El codebase de `apps/proyectos` usaba nombres en español para modelos, campos, enums y URLs. Decisión tomada por Juan David para estandarizar a inglés antes de escalar el equipo.

**Alcance aprobado:**
- D1 ✅ Campos en BD cambian (vía RenameField migrations)
- D2 ✅ URLs cambian `/proyectos/` → `/projects/` (con alias temporal por 1 release)
- D3 ✅ Valores de TextChoices en BD cambian (vía RunSQL data migrations)
- D4 ✅ `'proyectos'` en `companies_companymodule` cambia a `'projects'`

**Mapeo de clases:**
- Proyecto → Project, Tarea → Task, Fase → Phase, TareaDependencia → TaskDependency
- SesionTrabajo → WorkSession (db_table='sesiones_trabajo' se preserva)
- TimesheetEntry → sin cambio (ya en inglés)

**Decisiones de naming específicas:**
- `interventor` (RolTercero) → `inspector` (evita colisión con `supervisor`)
- Tarea.estado: `por_hacer`→`todo`, `en_progreso`→`in_progress`, `en_revision`→`in_review`
- WorkSession estados: `activa`→`active`, `pausada`→`paused`, `finalizada`→`finished`

**Consecuencia:** 27 tareas (REFT-01 a REFT-27), estimación 7-8 días. Ver `docs/plans/REFACTOR-TASK-BREAKDOWN.md`.

---

## DEC-024: Nueva Arquitectura de Navegación — Landing de Módulos
**Fecha:** 2026-03-26
**Estado:** 🔄 Pendiente implementación (REFT-22 a REFT-25)
**Contexto:** Sidebar global con todos los módulos no escala al crecer la plataforma.

**Decisión:** Post-login muestra landing de módulos (`/modulos`). Cada módulo tiene su propio sidebar contextual. Toggle Kanban/Lista con localStorage. Vista Cards de Proyectos con `mat-card`.

**Stack:** Angular Material únicamente — NUNCA PrimeNG.

---

## DEC-012: Terceros y Consecutivos como Módulos Transversales

**Fecha:** 19 Marzo 2026
**Estado:** ✅ Aprobada e implementada (Terceros) / ⏳ Pendiente (Consecutivos)
**Contexto:** Módulo de Proyectos

### Problema
Durante la implementación del Grupo 3 (Terceros), se detectó que el diseño inicial ubicaba Terceros dentro de la app `proyectos`, lo que implicaba:
- Terceros exclusivos de Proyectos
- No reutilizables en otros módulos (SaiReviews, SaiCash, SaiRoute, etc.)
- Duplicación de datos si otros módulos necesitaban terceros
- API fragmentada

El mismo problema aplica para Consecutivos.

### Opciones Evaluadas

**Opción A: Mantener en app específica (proyectos)**
- ❌ No reutilizable
- ❌ Duplicación de código/datos
- ❌ Inconsistencia entre módulos
- ✅ Más simple inicialmente

**Opción B: Módulos transversales en app `core`** ⭐ SELECCIONADA
- ✅ Reutilizable en todos los módulos
- ✅ Un solo registro de tercero compartido
- ✅ API centralizada `/api/v1/terceros/`
- ✅ Relaciones específicas por módulo
- ❌ Requiere refactorización

### Decisión

**Terceros y Consecutivos se implementan como módulos TRANSVERSALES en app `core`.**

**Arquitectura:**
```
apps/core/  (TRANSVERSAL)
├── models.py
│   ├── Tercero              ← Encabezado
│   ├── TerceroDireccion     ← Líneas (direcciones)
│   └── ConfiguracionConsecutivo  ← Pendiente implementar
├── serializers.py
├── views.py
└── urls.py  → /api/v1/terceros/, /api/v1/consecutivos/

apps/proyectos/  (ESPECÍFICO)
├── models.py
│   └── TerceroProyecto      ← Relación Tercero + Proyecto
└── ...

apps/reviews/  (FUTURO)
└── models.py
    └── TerceroReview        ← Relación Tercero + Review

apps/cash/  (FUTURO)
└── models.py
    └── TerceroCash          ← Relación Tercero + CxC/CxP
```

### Implementación

**Terceros:**
- ✅ Modelo `Tercero` en `apps/core/models.py`
- ✅ Modelo `TerceroDireccion` en `apps/core/models.py`
- ✅ Serializers, Views, URLs en app `core`
- ✅ Service transversal `TerceroService` en frontend
- ✅ Componente reutilizable `tercero-selector` (autocomplete)
- ✅ `TerceroProyecto` en app `proyectos` con FK a `core.Tercero`

**Consecutivos:**
- ⏳ Pendiente implementar como transversal
- ⏳ Modelo `ConfiguracionConsecutivo` en app `core`
- ⏳ Service `generar_consecutivo()` centralizado

### Consecuencias

**Positivas:**
- ✅ Un tercero puede usarse en Proyectos, SaiReviews, SaiCash simultáneamente
- ✅ Consistencia de datos (un cliente es el mismo en todos los módulos)
- ✅ API única `/api/v1/terceros/` para todos
- ✅ Componentes frontend reutilizables
- ✅ Sincronización Saiopen centralizada

**Negativas:**
- ⚠️ Requirió refactorización de código ya generado
- ⚠️ Mayor complejidad inicial

### Criterios de Revisión
- ✅ Terceros funciona en Proyectos
- ⏳ Terceros funciona en al menos un segundo módulo (SaiReviews)
- ⏳ Consecutivos implementado como transversal

### Referencias
- Grupo 3: https://www.notion.so/329ee9c3690a811eab5ecd3fd8105c22
- Cierre Sesión: https://www.notion.so/329ee9c3690a814398b3de9a87fcf5db
