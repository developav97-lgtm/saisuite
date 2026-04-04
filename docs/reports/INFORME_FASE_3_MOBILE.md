# Informe Fase 3: Bugs Mobile Media/Baja Prioridad

**Fecha:** 2026-03-31
**Bugs corregidos:** 7/7

---

## Bugs Corregidos

### Bug #1: Etiqueta "Float: 2D" sin contexto
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/scheduling/float-indicator/float-indicator.component.ts`
- **Cambios:**
  - Importado `MatTooltipModule`.
  - Badge de holgura renombrado de `"Float: Xd"` a `"Holgura: X días"` (singular/plural automático).
  - Agregado `matTooltip="Holgura disponible (días)"` con `matTooltipPosition="above"` al chip de holgura.
  - Agregado `matTooltip="Tarea en el camino crítico — sin holgura disponible"` al chip de crítica.
- **Validación 4x4:** Label claro en español, tooltip visible en hover/focus, sin romper desktop.

---

### Bug #2: Acordeones de Equipo muy pegados en mobile
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/resource-assignment-panel/resource-assignment-panel.component.scss`
- **Cambios:**
  - Agregado bloque `@media (max-width: 768px)` al final del SCSS.
  - En mobile: `.rap-item` con `flex-wrap: wrap`, `padding: 0.75rem`, `margin-bottom: 8px` en ítems no-últimos.
  - `.rap-bar-col` con `width: 100%` y `order: 4` para que la barra aparezca debajo del contenido.
  - `.rap-nombre` sin `white-space: nowrap` para permitir wrapping en pantallas pequeñas.
  - `.rap-meta` con `flex-wrap: wrap` para evitar desbordamiento.
  - Layout desktop no modificado.
- **Validación 4x4:** Espaciado correcto en mobile, layout desktop intacto.

---

### Bug #3: Tabla Baseline comparativa no se ve en mobile
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/scheduling/baseline-comparison/baseline-comparison.component.html`
  - `frontend/src/app/features/proyectos/components/scheduling/baseline-comparison/baseline-comparison.component.scss`
- **Cambios:**
  - Envuelta `<mat-table>` dentro de `<div class="table-responsive">` (clase global ya existente en `styles.scss`).
  - Agregado `min-width: 600px` a `.bc-table` para forzar scroll horizontal en viewports estrechos.
  - Empty state y paginador quedan fuera del wrapper (comportamiento correcto).
- **Validación 4x4:** Scroll horizontal funcional en mobile, desktop sin cambios.

---

### Bug #4: Tabla Escenarios no se ve en mobile
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/scheduling/what-if-scenario-builder/what-if-scenario-builder.component.html`
  - `frontend/src/app/features/proyectos/components/scheduling/what-if-scenario-builder/what-if-scenario-builder.component.scss`
- **Cambios:**
  - Envuelta `<mat-table>` dentro de `<div class="table-responsive">`.
  - Agregado `min-width: 520px` a `.wi-table` para activar scroll horizontal en móvil.
  - El panel de detalle del escenario queda fuera del wrapper.
- **Validación 4x4:** Scroll horizontal en mobile, sin impacto en desktop. No se usó `BreakpointObserver` al ser suficiente el scroll horizontal sin necesidad de ocultar columnas.

---

### Bug #5: Tablas Admin sin scroll horizontal
- **Archivos creados:**
  - `frontend/src/app/shared/directives/responsive-table.directive.ts`
  - `frontend/src/app/shared/directives/index.ts`
- **Archivos modificados:**
  - `frontend/src/app/features/admin/user-list/user-list.component.html` — `appResponsiveTable` en `<mat-table>`
  - `frontend/src/app/features/admin/user-list/user-list.component.ts` — importa `ResponsiveTableDirective`
  - `frontend/src/app/features/admin/internal-users/internal-user-list.component.html` — `appResponsiveTable` en `<mat-table>`
  - `frontend/src/app/features/admin/internal-users/internal-user-list.component.ts` — importa `ResponsiveTableDirective`
  - `frontend/src/app/features/admin/roles/roles-list.component.html` — `appResponsiveTable` en `<mat-table>`
  - `frontend/src/app/features/admin/roles/roles-list.component.ts` — importa `ResponsiveTableDirective`
  - `frontend/src/app/features/admin/tenants/tenant-list/tenant-list.component.html` — `appResponsiveTable` en `<table mat-table>`
  - `frontend/src/app/features/admin/tenants/tenant-list/tenant-list.component.ts` — importa `ResponsiveTableDirective`
  - `frontend/src/app/features/admin/consecutivos/consecutivo-list.component.html` — `appResponsiveTable` en `<mat-table>`
  - `frontend/src/app/features/admin/consecutivos/consecutivo-list.component.ts` — importa `ResponsiveTableDirective`
- **Cambios:**
  - Directiva standalone `ResponsiveTableDirective` que usa `ElementRef` + `Renderer2` para envolver la tabla en un `div.table-responsive` en `ngAfterViewInit`.
  - Aplicada en las 5 tablas admin con un único atributo `appResponsiveTable`.
- **Validación 4x4:** Directiva reutilizable, standalone, sin `any`, sin efectos en desktop.

---

### Bug #6: Tabla global Terceros sin scroll
- **Archivos modificados:** Ninguno
- **Cambios:** El componente `tercero-selector` no contiene ninguna `mat-table` — usa `mat-autocomplete` con `mat-option` para mostrar resultados como un dropdown superpuesto. No hay tabla que requiera scroll horizontal.
- **Validación 4x4:** Confirmado inspeccionando `tercero-selector.component.html` — solo tiene `mat-form-field` + `mat-autocomplete`.

---

### Bug #7: Cantidad planificada sin formato miles
- **Archivos modificados:**
  - `frontend/src/app/features/proyectos/components/actividad-proyecto-list/actividad-proyecto-list.component.html`
- **Cambios:**
  - `cantidad_planificada` ahora usa el pipe `| number:'1.0-2'`.
  - `cantidad_ejecutada` también actualizado a `| number:'1.0-2'` para consistencia visual en la misma columna.
  - `CommonModule` ya estaba importado en el componente, por lo que `DecimalPipe` está disponible sin cambios en el TS.
- **Validación 4x4:** Números con separador de miles y hasta 2 decimales, formato consistente en toda la columna.

---

## Archivos Modificados

| Archivo | Bug |
|---|---|
| `float-indicator/float-indicator.component.ts` | #1 |
| `resource-assignment-panel/resource-assignment-panel.component.scss` | #2 |
| `baseline-comparison/baseline-comparison.component.html` | #3 |
| `baseline-comparison/baseline-comparison.component.scss` | #3 |
| `what-if-scenario-builder/what-if-scenario-builder.component.html` | #4 |
| `what-if-scenario-builder/what-if-scenario-builder.component.scss` | #4 |
| `admin/user-list/user-list.component.html` | #5 |
| `admin/user-list/user-list.component.ts` | #5 |
| `admin/internal-users/internal-user-list.component.html` | #5 |
| `admin/internal-users/internal-user-list.component.ts` | #5 |
| `admin/roles/roles-list.component.html` | #5 |
| `admin/roles/roles-list.component.ts` | #5 |
| `admin/tenants/tenant-list/tenant-list.component.html` | #5 |
| `admin/tenants/tenant-list/tenant-list.component.ts` | #5 |
| `admin/consecutivos/consecutivo-list.component.html` | #5 |
| `admin/consecutivos/consecutivo-list.component.ts` | #5 |
| `actividad-proyecto-list/actividad-proyecto-list.component.html` | #7 |

## Archivos Creados

| Archivo | Bug |
|---|---|
| `frontend/src/app/shared/directives/responsive-table.directive.ts` | #5 |
| `frontend/src/app/shared/directives/index.ts` | #5 |

## Estado: COMPLETADO 7/7
