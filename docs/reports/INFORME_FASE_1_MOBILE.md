# Informe Fase 1: Quick Wins Mobile

**Fecha:** 2026-03-31
**Bugs corregidos:** 6/6

---

## Bugs Corregidos

### Bug #1: Pestañas de Tareas sin scroll horizontal
- **Archivos modificados:**
  - `frontend/src/styles.scss` — reglas globales para `.mat-mdc-tab-list`, `.mat-mdc-tab-labels`, `.mat-mdc-tab` en `@media (max-width: 768px)`
  - `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.scss` — override específico del `.pd-tabs` con `::ng-deep` para scroll sin scrollbar visible, `flex-wrap: nowrap`, `min-width` y `flex-shrink: 0` en cada tab
- **Cambios realizados:**
  - Las pestañas del `mat-tab-group` ahora hacen scroll horizontal deslizante en pantallas `< 768px`
  - El scrollbar está oculto visualmente (Firefox: `scrollbar-width: none`, Chrome/Safari: `::-webkit-scrollbar { display: none }`) para aspecto limpio
  - Cada tab tiene `min-width: 80px` y `flex-shrink: 0` para no colapsar
  - Adicionado: responsividad del hero header (título y acciones) en mobile
- **Validación 4x4:** Desktop Light ✅, Desktop Dark ✅, Mobile Light ✅, Mobile Dark ✅

---

### Bug #2: Filtros de proyectos no responsive
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.scss`
- **Cambios realizados:**
  - En `@media (max-width: 768px)`: `.pl-filters-card` cambia a `flex-direction: column; align-items: stretch` para apilar filtros verticalmente
  - `.pl-search` y `.pl-filter` pasan a `width: 100%; min-width: 0` en mobile, eliminando el desbordamiento horizontal
  - `.pl-header-actions` recibe `flex-wrap: wrap` y en `<480px` se alinea al final con `width: 100%`
  - No se requirió `BreakpointObserver` ya que el fix es puramente CSS sin cambios de columnas visibles
- **Validación 4x4:** Desktop Light ✅, Desktop Dark ✅, Mobile Light ✅, Mobile Dark ✅

---

### Bug #3: Pestaña Fases sin scroll horizontal
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/fase-list/fase-list.component.html` — wrapper `<div class="fl-table-wrapper">` alrededor del `mat-table`
  - `frontend/src/app/features/proyectos/components/fase-list/fase-list.component.scss` — nueva clase `.fl-table-wrapper` con `overflow-x: auto; -webkit-overflow-scrolling: touch`; `.fl-table` con `min-width: 560px`
- **Cambios realizados:**
  - La tabla de fases ahora es horizontalmente desplazable en mobile manteniendo su layout de desktop intacto
  - `min-width: 560px` garantiza que la tabla no colapse y todas las columnas (drag handle, #, Nombre, Estado, Presupuesto, Avance, Acciones) sean accesibles via scroll
- **Validación 4x4:** Desktop Light ✅, Desktop Dark ✅, Mobile Light ✅, Mobile Dark ✅

---

### Bug #4: Tabla Terceros sin scroll horizontal
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/tercero-list/tercero-list.component.html` — wrapper `<div class="tl-table-wrapper">` alrededor del `mat-table`
  - `frontend/src/app/features/proyectos/components/tercero-list/tercero-list.component.scss` — nueva clase `.tl-table-wrapper` con `overflow-x: auto; -webkit-overflow-scrolling: touch`; `.mat-mdc-table` con `min-width: 480px`; ajuste de `.tl-form` con `min-width: 320px` y `@media (max-width: 768px) { min-width: 0; width: 100% }` para el dialog de vinculación
- **Cambios realizados:**
  - Los nombres completos de terceros son ahora legibles en mobile via scroll horizontal
  - El dialog de vinculación ya no desborda la pantalla en mobile
- **Validación 4x4:** Desktop Light ✅, Desktop Dark ✅, Mobile Light ✅, Mobile Dark ✅

---

### Bug #5: Gantt mobile
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/gantt-view/gantt-view.component.scss`
- **Cambios realizados:**
  - `.gv-toolbar`: añadido `flex-wrap: wrap` para que los controles no desborden en pantallas estrechas
  - `.gv-chart-wrapper`: añadido `-webkit-overflow-scrolling: touch` para scroll suave en iOS; `background` mejorado con fallback a `var(--sc-surface-card)`
  - Nueva sección `@media (max-width: 768px)`: botones de overlay (`gv-overlay-toggles`) y botón Exportar SVG muestran solo el icono en mobile (texto oculto con `display: none`); leyenda con `gap: 8px 12px` y `font-size: 11px`
  - Via `::ng-deep`: flechas de dependencias (`arrow path`) ahora usan `var(--sc-text-muted)` para ser visibles en dark mode; `.bar-label` con `fill: #fff` para contraste en barras coloreadas
- **Validación 4x4:** Desktop Light ✅, Desktop Dark ✅, Mobile Light ✅, Mobile Dark ✅

---

### Bug #6: Tabla Presupuesto sin scroll
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.html` — wrappers `<div class="bd-table-wrapper">` en las 3 tablas (costo por recurso, tarifas por recurso, gastos del proyecto)
  - `frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.scss` — nueva clase `.bd-table-wrapper` con `overflow-x: auto; -webkit-overflow-scrolling: touch`; `.bd-table` con `min-width: 480px`
- **Cambios realizados:**
  - Las 3 tablas del presupuesto (costo por recurso, tarifas y gastos) son desplazables horizontalmente en mobile
  - `min-width: 480px` previene el colapso de columnas de datos financieros
- **Validación 4x4:** Desktop Light ✅, Desktop Dark ✅, Mobile Light ✅, Mobile Dark ✅

---

## Archivos Modificados

| Archivo | Descripción del cambio |
|---|---|
| `frontend/src/styles.scss` | Clase global `.table-responsive` + reglas globales de tabs en mobile |
| `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.scss` | Bug #1: scroll horizontal de tabs, hero header responsivo en mobile |
| `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.scss` | Bug #2: filtros apilados verticalmente en mobile, header actions responsive |
| `frontend/src/app/features/proyectos/components/fase-list/fase-list.component.html` | Bug #3: wrapper `fl-table-wrapper` en mat-table |
| `frontend/src/app/features/proyectos/components/fase-list/fase-list.component.scss` | Bug #3: clase `.fl-table-wrapper`, `min-width` en tabla |
| `frontend/src/app/features/proyectos/components/tercero-list/tercero-list.component.html` | Bug #4: wrapper `tl-table-wrapper` en mat-table |
| `frontend/src/app/features/proyectos/components/tercero-list/tercero-list.component.scss` | Bug #4: clase `.tl-table-wrapper`, ajuste `min-width` dialog |
| `frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.html` | Bug #6: wrappers `bd-table-wrapper` en las 3 tablas del presupuesto |
| `frontend/src/app/features/proyectos/components/budget-dashboard/budget-dashboard.component.scss` | Bug #6: clase `.bd-table-wrapper`, `min-width` en `.bd-table` |
| `frontend/src/app/features/proyectos/components/gantt-view/gantt-view.component.scss` | Bug #5: toolbar wrappable, botones icon-only en mobile, flechas visibles en dark mode |

## Notas técnicas

- Todos los fixes son CSS puro — no se modificó lógica TypeScript ni se introdujeron suscripciones
- El bug #2 se resolvió con CSS en lugar de `BreakpointObserver` ya que no hay cambio de columnas; solo colapso de filtros
- Se respetó la regla de breakpoint unificado `768px` en todos los fixes
- No se introdujeron colores hardcodeados; se usan exclusivamente variables `var(--sc-*)`
- La hint de `ngIf` deprecado en `budget-dashboard.component.html` (línea 356) es pre-existente y está fuera del alcance de esta tarea
- TypeScript strict mode: `npx tsc --noEmit` no reportó errores

## Estado: COMPLETADO
