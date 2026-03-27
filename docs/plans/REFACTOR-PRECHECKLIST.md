# Refactor Pre-Checklist: Español → English + Angular Navigation
# SaiCloud — Reality Check FASE 0
# Generated: 2026-03-26 | Reality Checker

---

## VEREDICTO: PROCEDER CON PRECAUCIÓN

El refactor es viable, pero **4 bloqueantes deben resolverse antes de escribir una sola línea de código**.
El riesgo principal: `0012_timesheetentry.py` no está commiteada + sin decisión documentada sobre si los valores de `TextChoices` cambian. Esa sola decisión determina si esto es un rename de código (bajo riesgo, 2-3 días) o una migración de datos en vivo (alto riesgo, requiere ventana de mantenimiento).

---

## 1. Inventario exacto del impacto

### 1.1 Modelos Django (14 clases — models.py 934 líneas)

| Modelo actual (ES) | Propuesto (EN) | Criticidad |
|---|---|---|
| `Proyecto` | `Project` | CRÍTICO — entidad central, FK en todos los demás |
| `Tarea` | `Task` | CRÍTICO — FK en 6+ modelos, M2M x2 |
| `Fase` | `Phase` | CRÍTICO — FK en 8+ modelos |
| `TareaDependencia` | `TaskDependency` | ALTO |
| `SesionTrabajo` | `WorkSession` | ALTO — tiene `db_table` explícito |
| `TareaTag` | `TaskTag` | ALTO |
| `Actividad` | `Activity` | ALTO |
| `ActividadProyecto` | `ProjectActivity` | ALTO |
| `TerceroProyecto` | `ProjectStakeholder` | MEDIO |
| `DocumentoContable` | `AccountingDocument` | MEDIO |
| `Hito` | `Milestone` | MEDIO |
| `ActividadSaiopen` | `SaiopenActivity` | MEDIO |
| `ConfiguracionModulo` | `ModuleConfig` | MEDIO |
| `TimesheetEntry` | `TimesheetEntry` | — ya en inglés, sin cambio |

**13 modelos a renombrar. 12 con tabla PostgreSQL que cambia de nombre.**

### 1.2 Enums TextChoices (7 clases)

Los **nombres de clase** son solo código. Los **valores** (`'en_ejecucion'`, `'obra_civil'`, `'por_hacer'`) están almacenados en columnas PostgreSQL.
Si los valores cambian → every existing row becomes invalid → data migration obligatoria.

### 1.3 Campos con nombres en español (estimado)

| Modelo | Campos en español |
|---|---|
| `Tarea` | ~25 |
| `Proyecto` | ~21 |
| `Fase` | ~16 |
| 10 modelos restantes | ~58 |
| **Total estimado** | **~120 campos** |

### 1.4 Archivos backend afectados

| Archivo | Líneas | Referencias ES |
|---|---|---|
| `models.py` | 934 | ~120 campos + 14 clases + 7 enums |
| `serializers.py` | 930 | ~80+ |
| `views.py` | 1,098 | ~60+ |
| `tarea_services.py` | 1,024 | ~40+ |
| `signals.py` | ~60 | 8+ referencias |
| `urls.py` | 146 | 12 patterns + imports |
| `filters.py`, `permissions.py`, `admin.py` | no contados | ~35 estimado |

### 1.5 Archivos de tests (26 archivos — todos rompen el día 1)

Cada uno de los 26 archivos de test importa clases por nombre en español. Ejemplos confirmados:
- `conftest.py`: `from apps.proyectos.models import Proyecto, Fase, Tarea`
- `test_tarea_services.py`: `from apps.proyectos.models import Tarea`
- `test_dependencias.py`: `from apps.proyectos.models import TareaDependencia`
- `test_signals.py`: `from apps.proyectos.models import Actividad, ActividadProyecto`

**~60-80 líneas de import a actualizar en 26 archivos.**

### 1.6 Frontend afectado

- **13 servicios Angular** con URLs `/api/v1/proyectos/` hardcodeadas
- **13+ interfaces TypeScript** con campos en español
- **~40 archivos Angular** en total (services, models, components, routes, guards)

---

## 2. Riesgos críticos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| RISK-01 | 12 tablas PostgreSQL cambian de nombre sin `RenameModel` migration | CIERTA si se olvida | CATASTRÓFICO | Verificar cada migration antes de aplicar |
| RISK-02 | Valores de TextChoices en DB se invalidan si se cambian | ALTA | CATASTRÓFICO | **Decisión D1 obligatoria antes de empezar** |
| RISK-03 | Los 26 archivos de test rompen el día 1 | CIERTA | ALTO | Actualizar tests en el mismo commit que el modelo |
| RISK-04 | Frontend-backend contract breaks | CIERTA | ALTO | Mantener alias de URLs por 1 release |
| RISK-05 | `0012_timesheetentry.py` no commiteada | CONFIRMADO | CRÍTICO | **Commitear ANTES de nueva migración** |
| RISK-06 | `related_name` en español usados en queries | ALTA | ALTO | Grep exhaustivo antes de renombrar |
| RISK-07 | `'proyectos'` en `companies_companymodule` es string en DB | ALTA | ALTO | Data migration + decisión D4 |
| RISK-08 | n8n workflows y agente Windows usan URLs `/proyectos/` | MEDIA | ALTO | Mantener alias, avisar a los equipos |

---

## 3. Checklist pre-refactor

### BLOQUE A: Estado del repositorio (BLOQUEANTES)

- [ ] **A1. CRÍTICO: Commitear `0012_timesheetentry.py`** — está untracked. Sin esto, las nuevas migraciones crean una cadena ambigua.
  ```bash
  git add backend/apps/proyectos/migrations/0012_timesheetentry.py
  git commit -m "chore(proyectos): add 0012_timesheetentry migration"
  ```
- [ ] **A2. Evaluar todos los archivos untracked** — `test_gantt.py`, `test_timesheets.py`, `gantt-view/`, `timer/`, `timesheet-semanal/`, `timesheet.model.ts`, `timesheet.service.ts`, `agency-agents/` — decidir si entran o no en el scope del refactor.
- [ ] **A3. Crear rama de trabajo**
  ```bash
  git checkout -b refactor/models-to-english
  ```
- [ ] **A4. Verificar que main esté limpio** antes de branching.

### BLOQUE B: Backups (BLOQUEANTES)

- [ ] **B1. Backup de base de datos de desarrollo**
  ```bash
  pg_dump -U saisuite_user -d saisuite_dev -F c -f ~/backups/saisuite_pre_refactor_$(date +%Y%m%d_%H%M%S).dump
  ```
- [ ] **B2. Verificar que el backup sea restaurable** — probar restore a una DB temporal
- [ ] **B3. AWS RDS snapshot** si hay staging/producción activa

### BLOQUE C: Baseline de tests (BLOQUEANTES)

- [ ] **C1. Ejecutar suite completa y verificar verde**
  ```bash
  cd backend && python manage.py test apps.proyectos --verbosity=2
  ```
- [ ] **C2. Guardar output** como baseline antes de cualquier cambio
- [ ] **C3. Verificar que Angular compila limpio**
  ```bash
  cd frontend && ng build --configuration development 2>&1 | tail -20
  ```

### BLOQUE D: Decisiones de diseño (deben tomarse ANTES de codificar)

- [ ] **D1. DECISIÓN CRÍTICA: ¿Cambian los valores de TextChoices en DB?**
  - **Opción A (segura)**: Solo renombrar clases Python (`EstadoProyecto` → `ProjectStatus`), los valores en BD quedan igual (`'en_ejecucion'` sigue siendo `'en_ejecucion'`). Sin data migration.
  - **Opción B (completa, alto riesgo)**: Renombrar también los valores de BD. Requiere UPDATE migrations en todas las tablas afectadas.
  - **Recomendación: Opción A para este ciclo.**

- [ ] **D2. DECISIÓN: ¿Cambian las URLs de la API?**
  - `/api/v1/proyectos/` → `/api/v1/projects/` duplica el scope del frontend y rompe n8n + agente Windows
  - Si sí: mantener alias `/proyectos/` por 1 release

- [ ] **D3. DECISIÓN: ¿Cambian las rutas Angular?**
  - `/proyectos` → `/projects` es visible para usuarios finales (rompe bookmarks)

- [ ] **D4. DECISIÓN: ¿Qué pasa con `'proyectos'` en `companies_companymodule`?**
  - Este string en BD controla el acceso al módulo. Un rename sin data migration bloquea a todas las empresas del módulo.

- [ ] **D5. Crear `REFACTOR-SCOPE.md`** — documento explícito de qué se renombra y qué NO. Sin esto, el scope creep está garantizado.

### BLOQUE E: Preparación técnica

- [ ] **E1. Grep de imports cross-módulo**
  ```bash
  grep -rn "from apps.proyectos" backend/apps/ --include="*.py" | grep -v "apps/proyectos/"
  ```
- [ ] **E2. Grep de related_names en español** que se usen en queries/serializers
- [ ] **E3. Buscar `/proyectos/` en workflows n8n** (`n8n/workflows/`)
- [ ] **E4. Buscar `/proyectos/` en el directorio `agent/`**
- [ ] **E5. Leer `services.py`, `filters.py`, `permissions.py`, `admin.py`** — no incluidos en la evaluación

---

## 4. Señales de alarma — condiciones para NO proceder

- **ALARM-01 (BLOQUEANTE):** Tests no están en verde antes de empezar.
- **ALARM-02 (BLOQUEANTE):** `0012_timesheetentry.py` no commiteada.
- **ALARM-03 (BLOQUEANTE):** Sin backup verificado de la BD.
- **ALARM-04 (BLOQUEANTE):** Scope no documentado en `REFACTOR-SCOPE.md`.
- **ALARM-05 (RIESGO ALTO):** Cambios pendientes mezclados en la rama de trabajo.
- **ALARM-06 (RIESGO ALTO):** Refactor en un solo commit masivo — imposible debuggear.

---

## 5. Orden de ejecución recomendado

```
1.  Commitear migración 0012 y evaluar untracked files
2.  Crear rama refactor/models-to-english
3.  Backup BD y verificar restore
4.  Documentar scope en REFACTOR-SCOPE.md
5.  Agregar db_table explícito a los 12 modelos que no lo tienen (paso protector)
6.  Renombrar clases en models.py + generar RenameModel migrations
7.  Aplicar migración a dev DB y verificar que las tablas existen
8.  Actualizar serializers.py
9.  Actualizar services.py y tarea_services.py
10. Actualizar views.py y urls.py
11. Actualizar signals.py, filters.py, permissions.py, admin.py
12. Actualizar los 26 archivos de tests
13. Ejecutar suite completa — debe estar 100% verde
14. Actualizar interfaces TypeScript
15. Actualizar servicios Angular (URLs y tipos)
16. Actualizar componentes Angular
17. Actualizar routing, sidebar, guards
18. Compilar Angular — 0 errores con strict: true
19. Test de integración manual end-to-end
20. PR con descripción completa del scope
```

**Estimación realista: 3-5 días de desarrollo** para un refactor de este tamaño hecho correctamente con tests en verde en cada paso.

---

## 6. Nota sobre la calidad del código actual

Antes de iniciar, es importante notar que el codebase actual es arquitectónicamente sólido:
- Separación correcta services.py / views
- 26 archivos de tests con cobertura real
- Modelos bien tipados con documentación
- Cadena de 12 migraciones en estado válido
- Angular con TypeScript strict y servicios bien organizados

Este refactor es una mejora de legibilidad para el equipo, **no un fix de bug funcional**. El sistema funciona correctamente con nombres en español. No hay urgencia técnica.

---

*Evaluación: Reality Checker — FASE 0*
*Re-evaluación requerida: después de resolver los 4 bloqueantes del Bloque A-C-D*
