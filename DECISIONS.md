## DEC-029: Automatización de Snapshots — Management Command vs Celery
**Fecha:** 2026-03-28
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #7 (BG-47) requería ejecutar snapshots semanales de presupuesto automáticamente. El plan original contemplaba una Celery task (`@shared_task`).

**Opciones consideradas:**
1. **Celery task** — requiere broker Redis/RabbitMQ + worker process, nada de esto existe en el stack
2. **Django management command** — invocable desde cron, AWS EventBridge, n8n o curl; cero dependencias nuevas

**Decisión:** Django management command `budget_weekly_snapshot`.

**Razón:** El stack actual no tiene broker (Redis no está en `docker-compose.yml` ni en settings). Agregar Celery solo para este proceso sería sobreingeniería. Un management command es suficiente para frecuencia semanal y puede dispararse síncronamente desde EventBridge o n8n.

**Consecuencia:** Si en el futuro se agrega Celery, el command se envuelve trivialmente: `call_command('budget_weekly_snapshot')` dentro de `@shared_task`. La migración no requiere cambiar la lógica del command.

**Scheduling recomendado:**
- AWS EventBridge: `cron(0 6 ? * MON *)`
- n8n: workflow cron → HTTP POST al endpoint de gestión interno
- Sistema: `0 6 * * 1 /app/manage.py budget_weekly_snapshot`

---

## DEC-028: EVM — Fórmula Simplificada vs Earned Value Completo
**Fecha:** 2026-03-28
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #7 (BG-29) requería métricas EVM (CPI, SPI, EAC, etc.). La fórmula estándar de EVM requiere un baseline detallado de planificación por período (baseline distribution), que no existe en el modelo de datos actual.

**Opciones consideradas:**
1. **EVM completo** — requiere `BaselinePeriod` con distribución de PV por semana/mes; modelo no existe
2. **EVM simplificado** — PV estimado linealmente, EV basado en porcentaje de avance de tareas

**Decisión:** EVM simplificado con estas fórmulas:
- `PV = BAC × (elapsed_days / total_days)` — valor planificado lineal
- `EV = BAC × avg(task.porcentaje_completado / 100)` — valor ganado real
- `AC` = costo real de timesheets + gastos
- Resto de métricas (CPI, SPI, EAC, ETC, TCPI, VAC) se calculan con las fórmulas estándar PMI

**Razón:** El modelo no tiene distribución de costos planificada por período. La aproximación lineal es suficiente para alertas tempranas y tendencias. Implementar la distribución completa es una feature independiente (Feature #8+).

**Consecuencia:** Los valores de PV son aproximados. Para proyectos con esfuerzo muy no-lineal, los índices SPI pueden ser engañosos. Se documenta esta limitación en la guía de usuario. Cuando se implemente `BaselinePeriod`, `EVMService.get_evm_metrics()` se actualiza sin cambiar la API.

---

## DEC-027: Gantt Overlay — Re-render completo vs patch DOM
**Fecha:** 2026-03-27
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #6 (SK-41) requería añadir overlays visuales sobre el Gantt (ruta crítica, holgura, baseline) sin reescribir Frappe Gantt.

**Opciones consideradas:**
- Opción A: Parchear el DOM del SVG de Frappe Gantt post-render para cambiar estilos/labels
- Opción B: Re-render completo de Frappe Gantt con `renderTasks` enriquecidos (`custom_class`, `name` con sufijos)

**Decisión:** Opción B — re-render completo vía `rerenderGantt()`.

**Razón:** Frappe Gantt no expone API de actualización granular por tarea. El parche DOM sería frágil ante actualizaciones de la librería y difícil de revertir. El re-render es más costoso (~50ms) pero simple, correcto y mantenible. Con debounce de 400ms en drag, no hay conflicto.

**Consecuencia:** `initGantt()` ahora delega a `rerenderGantt()`. El array `this.tasks` permanece como la fuente de verdad sin mutaciones; `renderTasks` es el array derivado temporal para cada render.

---

## DEC-026: DisableMigrations en testing.py — Fix SQLite FK enforcement
**Fecha:** 2026-03-27
**Estado:** ✅ Decidido e implementado

**Contexto:** Feature #6 Chunk 5 — Los tests de scheduling fallaban con `OperationalError: no such table: main.proyectos_tarea` porque la migración 0013 (`RenameModel Tarea→Task`) no actualiza FK constraints en SQLite. Django reconstruye el schema copiando tablas, pero deja referencias rotas en SQLite.

**Decisión:** Agregar `DisableMigrations` class en `backend/config/settings/testing.py` para que Django use `CREATE TABLE` directo desde el estado actual de los modelos, sin reproducir el historial de migraciones.

**Razón:** La alternativa (regenerar todas las migraciones) rompería el historial de producción. `DisableMigrations` es el patrón estándar de Django para entornos de test con SQLite que no soportan todas las operaciones de migración.

**Consecuencia:** Los tests no validan que las migraciones sean correctas. Los tests de integración en CI/CD contra PostgreSQL (producción) siguen corriendo con migraciones reales — eso es la validación real.

---

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

## DEC-025: Definición de Sobreasignación de Recursos — Feature #4
**Fecha:** 2026-03-26
**Estado:** ✅ Decidido

**Contexto:** Feature #4 (Resource Management) requiere detectar cuándo un usuario tiene >100% de su capacidad asignada. Se evaluaron dos definiciones posibles.

**Opciones consideradas:**
- Opción A (Diaria): sobreasignado si la suma de `porcentaje_asignacion` en **cualquier día** del período supera 100%
- Opción B (Semanal): sobreasignado si el promedio semanal supera 100%

**Decisión:** Opción A — detección **diaria**.

**Razón:**
1. Dominio físico: en construcción, un recurso no puede estar en dos obras el mismo día. La sobreasignación diaria es un problema operativo real.
2. El algoritmo aprobado (`detect_overallocation_conflicts`) ya trabaja por día — es la implementación natural sin lógica adicional.
3. Conservador es mejor para MVP: mejor reportar conflictos de más (ignorables por el usuario) que ocultar conflictos reales.

**Consecuencia:** La función `detect_overallocation_conflicts(user_id, company_id, start_date, end_date, threshold=100.00)` reporta cada día donde `SUM(porcentaje_asignacion) > threshold`. El parámetro `threshold` es configurable para permitir flexibilización futura por empresa (ej: 110% para permitir horas extra). Los tests de `BK-27` deben cubrir: solapamiento parcial de días, fin de semana (sin asignación), threshold exactamente en 100%, y múltiples proyectos simultáneos.

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
