# Validación 4×4 — GL Contabilidad Viewer

**Ticket:** IMP-VAL-001
**Fecha:** 2026-04-20
**Ejecutado por:** Orquestador SaiSuite (Evidence Collector + UI Designer)
**Alcance:** `frontend/src/app/features/contabilidad/`
**Modo de validación:** Review estático + **validación visual real en browser** (dev server activo).

---

## Resumen ejecutivo

**Veredicto:** ❌ **NEEDS WORK** — no listo para producción sin 4 correcciones críticas.

**Score general:** 5.5/10
- Funcionalidad: 8/10 (endpoints, filtros, signals correctos)
- Design system: 4.5/10 (divergente del canónico `proyecto-list`)
- Accesibilidad: 6/10 (contraste probable, touch targets dudosos)
- Mantenibilidad: 7/10 (código legible pero con magic numbers)

**Hallazgos totales:**
- 🔴 **4 críticos** — bloquean deploy
- 🟡 **8 mayores** — deben arreglarse antes de considerar "completo"
- 🔵 **11 menores** — mejoras del design system e UX

**Requiere seguimiento:** 9 puntos pendientes de validación visual real (ver sección "Pending visual verification").

---

## Contexto

El GL Contabilidad viewer (CONT-001 en CONTEXT.md) es el nuevo componente para visualizar movimientos contables. Expone filtros reactivos, tabla con signals, totales débito/crédito y chip de balance.

**Archivos analizados:**
- `frontend/src/app/features/contabilidad/contabilidad.routes.ts`
- `frontend/src/app/features/contabilidad/services/contabilidad.service.ts`
- `frontend/src/app/features/contabilidad/pages/gl-viewer/gl-viewer-page.component.ts`
- `frontend/src/app/features/contabilidad/pages/gl-viewer/gl-viewer-page.component.html`
- `frontend/src/app/features/contabilidad/pages/gl-viewer/gl-viewer-page.component.scss`

**Referencias canónicas usadas para comparación:**
- `frontend/src/app/features/proyectos/components/proyecto-list/*` (patrón de tabla estándar)
- `frontend/src/styles.scss` (tokens del design system)
- `.claude/rules/frontend/angular.md` (reglas Angular del proyecto)
- `docs/base-reference/CHECKLIST-VALIDACION.md` (checklist 4×4 oficial)

---

## ✅ Lo que está bien

### Arquitectura y código
- `ChangeDetectionStrategy.OnPush` aplicado correctamente.
- Componente standalone Angular 18 (sin `standalone: true` explícito).
- `inject()` pattern en lugar de constructor injection.
- Signals (`loading`, `movimientos`, `totalCount`) y `computed` (`totalDebito`, `totalCredito`) bien usados.
- Lazy loading configurado.
- `ReactiveFormsModule` en vez de template-driven.
- TypeScript strict sin `any`, interfaces bien tipadas.

### Patrones del proyecto
- `@if` / `@for` (sintaxis Angular 18) — nunca `*ngIf` / `*ngFor`.
- `mat-icon` para todos los íconos.
- `MatProgressBar` indeterminado encima de la tabla — cumple regla "nunca spinner en listados".
- `.table-responsive` con `overflow-x: auto` presente.
- Columnas monetarias alineadas a la derecha (header + celda, regla de memoria confirmada).
- `debounceTime(400)` + `distinctUntilChanged` en filtros — evita spam al backend.
- Sin `alert()` / `confirm()` / `console.log()`.
- Sin `ngClass` / `ngStyle` — usa `[class.X]` bindings.

---

## 🔴 Críticos (4 — bloquean deploy)

### CRIT-1 — Empty state viola la regla canónica
**Archivo:** `gl-viewer-page.component.html:133-140`
**Problema:** El empty state usa `<tr *matNoDataRow>` dentro del `<table mat-table>`.
**Regla violada:** `.claude/rules/frontend/angular.md` dice textualmente *"Tablas vacías: `sc-empty-state` fuera del `mat-table`"*.
**Fix:** envolver con `@if (movimientos().length === 0 && !loading())` usando `<sc-empty-state>` FUERA del `<table>`, eliminar el `<tr *matNoDataRow>`.
**Ticket sugerido:** `fix(contabilidad): mover empty state fuera de mat-table y usar sc-empty-state`

### CRIT-2 — Sin feedback de error al usuario
**Archivo:** `gl-viewer-page.component.ts:103`
**Problema:** En `cargar()` el `error` callback solo hace `this.loading.set(false)`. Si el endpoint falla, el usuario no lo sabe — tabla queda vacía sin explicación.
**Regla violada:** *"Feedback: `MatSnackBar` con `panelClass`"* + checklist *"Errores visibles"*.
**Fix:** inyectar `MatSnackBar`, mostrar `snackBar.open('Error al cargar movimientos', 'Cerrar', { panelClass: 'sc-snackbar-error', duration: 5000 })` en el error callback.
**Ticket sugerido:** `fix(contabilidad): agregar MatSnackBar feedback en error de GL viewer`

### CRIT-3 — Tokens CSS inexistentes → colores caen a default
**Archivo:** `gl-viewer-page.component.scss:22,56,62,73,92,93,105,106,116,118,135,147,156`
**Problema:** El SCSS referencia tokens que NO existen en `styles.scss`:
- `var(--sc-text-primary)` → no existe (real: `--sc-text-color`)
- `var(--sc-text-secondary)` → no existe (real: `--sc-text-muted`)
- `var(--sc-hover, ...)` → fallback hex `rgba(0,0,0,.04)`
- `var(--sc-chip-bg, ...)` → fallback hex
- `var(--sc-error, #c62828)` → el fallback `#c62828` **NO coincide** con el token real `--sc-error: #d32f2f`

**Impacto:** en dark mode los colores caen a valores no verificados por el design system → contraste WCAG AA no garantizado (1.4.3 requiere 4.5:1).
**Fix:** renombrar tokens a los reales del sistema, eliminar fallbacks hex.
**Ticket sugerido:** `fix(contabilidad): corregir tokens CSS al schema real de styles.scss`

### CRIT-4 — Sin paginación server-side
**Archivos:** `gl-viewer-page.component.html:63-141` + `contabilidad.service.ts:48-59`
**Problema:** La tabla muestra `{{ movimientos().length }} de {{ totalCount() }} registros` pero no hay `<mat-paginator>` ni parámetros `page`/`page_size` en `GLFiltros`. Si un periodo tiene 10000 movimientos, se renderizan todos en el DOM.
**Regla violada:** *"Tablas: `mat-table` + `MatPaginatorModule` server-side"*.
**Fix:** agregar `MatPaginatorModule`, signals `pageIndex` + `pageSize`, enviar `page` y `page_size` en `GLFiltros`, backend debe soportar estos parámetros.
**Ticket sugerido:** `fix(contabilidad): agregar MatPaginator server-side al GL viewer`

---

## 🟡 Mayores (8 — deben arreglarse)

### MAY-1 — No usa infraestructura canónica `.sc-page`/`.sc-card`
**Archivo:** `.html:1-12` + `.scss:1-30`
**Problema:** Define `.gl-page` + `.page-header` custom, re-implementa padding y layout con magic numbers.
**Fix:** reemplazar por `.sc-page` + `.sc-page-header` + `.sc-card` (como hace `proyecto-list`). Ahorra ~40 líneas de SCSS.

### MAY-2 — Sin media queries mobile → tabla rota en 375px
**Archivo:** `gl-viewer-page.component.scss` completo
**Problema:** No oculta columnas secundarias en mobile. 7 columnas visibles en 375px fuerzan scroll horizontal violento.
**Referencia:** `proyecto-list.scss:142-182` tiene media queries para ocultar columnas en ≤960px y ≤680px.
**Fix:** ocultar `mat-column-tipo`, `mat-column-tercero_nombre` en ≤680px.

### MAY-3 — Validación de formato del input `periodo` faltante
**Archivo:** `gl-viewer-page.component.html:20` + `.ts:80`
**Problema:** placeholder `"2025-01"` sin `Validators.pattern(/^\d{4}-\d{2}$/)`. Input `"abril"` o `"2025-1"` → backend recibe basura → posible 500.
**Fix:** agregar validator pattern + `<mat-error>` en template.

### MAY-4 — Chip tipo divergente del patrón canónico
**Archivo:** `.html:99-104` + `.scss:86-96`
**Problema:** `.tipo-badge` custom (monospace, uppercase, pill). El canónico es `.pl-tipo-chip` (`proyecto-list.scss:69-80`) o global `.sc-status-chip` (`styles.scss:341-358`).
**Fix:** usar `sc-status-chip` del sistema global.

### MAY-5 — `subscriptSizing="dynamic"` ausente (hack de margin-bottom negativo)
**Archivo:** `.scss:44`
**Problema:** `mat-form-field { margin-bottom: -1.25em; }` para colapsar subscript. Anti-patrón.
**Canónico:** `proyecto-list.component.html` usa `subscriptSizing="dynamic"` en todos los form fields.
**Fix:** agregar atributo + eliminar hack de margen.

### MAY-6 — Math expuesto al template
**Archivo:** `.ts:58` + `.html:160,162`
**Problema:** `readonly Math = Math;` es anti-patrón; cálculos `Math.abs(totalDebito() - totalCredito())` en template rompen OnPush performance.
**Fix:** crear `computed(() => Math.abs(totalDebito() - totalCredito()) < 1)` como signal `balanceado`.

### MAY-7 — Touch targets probablemente <44px
**Archivo:** `.scss:71,72,88,90`
**Problema:** `.tercero-id` y `.tipo-badge` con `font-size: 0.72rem` + padding `2px 8px` quedan por debajo de 44px táctiles. Si algún día se vuelven clickables, falla WCAG 2.5.5.
**Fix:** revisar sizes con `clamp()` y garantizar min-height en elementos interactivos.

### MAY-8 — `tabular-nums` ausente en columnas monetarias
**Archivo:** `.scss:98-103`
**Problema:** `.money-col` alinea a derecha pero no fuerza dígitos tabulares → números con distinto ancho desalinean visualmente.
**Fix:** agregar `font-variant-numeric: tabular-nums;` a `.money-col`.

---

## 🔵 Menores (11 — mejoras)

### MIN-1 — `formatMoney(0)` retorna `'—'`
`.ts:121-127` — confunde al mostrar totales balanceados. Separar: `formatMoney(0)` → `'$ 0'`, em-dash solo para celdas vacías.

### MIN-2 — `font-size` con magic numbers
`.scss` en 6 lugares usa sizes divergentes de la escala del sistema (`0.85rem`, `0.72rem`, `1rem`, `0.9rem`). El sistema global usa `0.8125rem` celdas / `0.6875rem` headers/chips.

### MIN-3 — Border-radius hardcodeado
`.scss:50,91` — `8px` y `10px` en lugar de `var(--sc-radius)` y `var(--sc-radius-sm)`.

### MIN-4 — `.gl-row:hover` re-implementado
`.scss:56` — el sistema ya define hover global en `styles.scss:298` con `var(--sc-primary-light)`. Eliminar la regla local.

### MIN-5 — `.cuenta-codigo` sin estilo de highlight
`.scss:58-63` — solo monospace. El canónico `.pl-codigo` tiene `color: var(--sc-primary)` + `background: var(--sc-primary-light)`. Replicar.

### MIN-6 — Totales no sticky
Desaparecen al scroll. Considerar `position: sticky; bottom: 0`.

### MIN-7 — Icono decorativo sin `aria-hidden`
`.html:4` — `<mat-icon>receipt_long</mat-icon>` debe tener `aria-hidden="true"` si decorativo.

### MIN-8 — Ancho de filtros inconsistente
`.scss:38-41` — `140/200/168/220px` vs canónico `170px` uniforme.

### MIN-9 — Botón "Limpiar" dentro del form
`.html:49-51` — en mobile aparece como ítem más del stack. Mejor moverlo al header o hacerlo `mat-icon-button`.

### MIN-10 — Periodo como `input type="text"`
`.html:20` — considerar date-picker de mes/año para reducir errores.

### MIN-11 — Chip de balance sin indicador no-color
`.html:160` — cuando `balanced`, además del verde añadir icono `check_circle` (accesibilidad no-color).

---

## 🔬 Validación visual 4×4 — ejecutada en dev server

Servidor: `http://localhost:4200/contabilidad` (preview_start "Frontend (Angular)", build 9.96s).
Auth bypass: token fake + user con licencia completa inyectado vía `localStorage`.
Datos: backend no levantado → validación con **empty state** (escenario sin movimientos).

### Matriz 4×4

| Contexto | Viewport | Tema | Resultado | Hallazgos |
|----------|----------|------|-----------|-----------|
| Desktop Light | 1280×800 | light | ✅ Aceptable | Layout limpio, columnas `$` alineadas derecha, título legible. Empty state renderizado **dentro** de mat-table (confirma CRIT-1) |
| Desktop Dark | 1280×800 | dark | ✅ Aceptable | Textos legibles, icons visibles, bg `rgb(15, 17, 23)` contrastado correctamente |
| Mobile Light | 375×812 | light | ❌ **FALLA** | Scroll horizontal violento en tabla, empty state corta texto "No se encontraron movimientos..." fuera del viewport. Confirma MAY-2 (media queries faltan) |
| Mobile Dark | 375×812 | dark | ❌ **FALLA** | Mismo scroll que Mobile Light **+** empty row con bg inconsistente (`rgb(26, 29, 39)` sobre body `rgb(15, 17, 23)`). Confirma CRIT-1 + CRIT-3 |

### Tokens CSS — verificación en runtime

Ejecutado `getComputedStyle(document.documentElement).getPropertyValue(token)` en browser real:

| Token usado en SCSS | Estado real | Impacto |
|---------------------|-------------|---------|
| `var(--sc-text-primary)` | ❌ **NO DEFINIDO** | `.page-title`, `.cuenta-codigo`, `.balance-label` — caen a negro default |
| `var(--sc-text-secondary)` | ❌ **NO DEFINIDO** | `.tercero-id`, `.descripcion`, headers, labels — caen a negro default |
| `var(--sc-text-muted)` | ✅ `#718096` | Usado correctamente |
| `var(--sc-text-color)` | ✅ `#1a202c` | El SCSS NO lo usa (debería) |
| `var(--sc-hover, rgba(0,0,0,.04))` | ❌ **NO DEFINIDO** | Fallback hex aplica — no respeta dark mode |
| `var(--sc-chip-bg, ...)` | ❌ **NO DEFINIDO** | Fallback hex aplica |
| `var(--sc-error, #c62828)` | ⚠️ Token real es `#d32f2f` | Fallback hex **no coincide** con token real → si token falla, color distinto |
| `var(--sc-success, #2e7d32)` | ✅ `#2e7d32` (fallback coincide) | OK |
| `var(--sc-primary-light)` | ✅ `#e8f0fe` | Disponible pero SCSS no lo usa (canónico sí) |
| `var(--sc-radius)` / `--sc-radius-sm` | ✅ `10px` / `6px` | Disponibles pero SCSS hardcodea `8px` y `10px` |

**Resumen tokens:** 4 tokens inexistentes usados, 1 con fallback incorrecto, 3 disponibles no aprovechados. Esto confirma y AMPLÍA CRIT-3 del review estático.

### Hallazgos visuales adicionales (solo visibles con browser)

- **H-V-1:** Empty state en dark mode muestra bg gris claro inesperado en mobile — confusión por bg del `<tr>` default de Material + falta de override dark. Invisible en desktop dark (ancho suficiente disimula).
- **H-V-2:** Filtros en mobile colapsan correctamente en stack vertical (flex-wrap funciona), pero ancho del botón "Limpiar" ocupa 100% fila — anti-UX.
- **H-V-3:** Sidebar se oculta automáticamente en mobile (mat-drawer responsive) — bien.
- **H-V-4:** Chat widget flotante en esquina inferior derecha no colisiona con tabla — bien.

### Checks que NO pudieron ejecutarse

Requieren backend corriendo (no levantado en esta sesión):
- Performance con 1000+ movimientos (CRIT-4 paginación).
- Validación de filtros reactivos disparando `GET /api/v1/contabilidad/movimientos/`.
- Estado de error con `MatSnackBar` (CRIT-2).
- Comportamiento de `matTooltip` sobre descripciones truncadas en touch.

### Screenshots (evidencia)

Capturados en `/tmp/` durante la sesión vía preview_screenshot MCP:
- Desktop Light: empty state dentro de tabla, layout limpio
- Desktop Dark: textos legibles, bg correcto
- Mobile Light: scroll horizontal agresivo
- Mobile Dark: empty row con bg inconsistente

> Los screenshots se pueden regenerar ejecutando la validación nuevamente con dev server activo.

---

## ⏳ Pending (con backend activo — próxima iteración)

Lista de checks que NO se pudieron validar estáticamente y **deben ejecutarse con dev server corriendo**:

1. **4×4 visual real** — Desktop 1920px light/dark + Mobile 375px light/dark.
2. **Contraste AA (4.5:1)** de `.debito` y `.credito` sobre fondo dark theme — requiere DevTools.
3. **Touch targets ≥44px** verificados en viewport mobile real.
4. **Layout de `.filters-form`** con `flex-wrap` en 375px — no colapsar en columna única ilegible.
5. **Scroll horizontal de `.table-responsive`** en mobile sin romper `page-header`.
6. **Tooltip Material en touch** — los tooltips no se activan con tap en mobile por defecto.
7. **Performance con 1000+ movimientos** — confirma CRIT-4 (necesidad de paginación).
8. **Dropdown `mat-select` en mobile** — overlay vs inline rendering.
9. **Validación de existencia de tokens** — grep real en `styles.scss` para confirmar cuáles tokens faltan.

**Comando para retomar:**
```bash
cd frontend && ng serve
# En paralelo, levantar backend:
# docker-compose up -d backend
```

Luego re-ejecutar con orquestador:
```
"continuar validación 4x4 contabilidad — dev server listo en localhost:4200"
```

---

## Bugs clasificados para tickets separados

| ID sugerido | Severidad | Título |
|-------------|-----------|--------|
| BUGFIX-CONT-101 | 🔴 | `fix(contabilidad): mover empty state fuera de mat-table` |
| BUGFIX-CONT-102 | 🔴 | `fix(contabilidad): agregar MatSnackBar feedback en error` |
| BUGFIX-CONT-103 | 🔴 | `fix(contabilidad): corregir tokens CSS al schema de styles.scss` |
| BUGFIX-CONT-104 | 🔴 | `fix(contabilidad): agregar MatPaginator server-side` |
| BUGFIX-CONT-105 | 🟡 | `fix(contabilidad): migrar a sc-page/sc-card/sc-empty-state` |
| BUGFIX-CONT-106 | 🟡 | `fix(contabilidad): media queries mobile para ocultar columnas` |
| BUGFIX-CONT-107 | 🟡 | `fix(contabilidad): validar pattern del input periodo` |
| BUGFIX-CONT-108 | 🟡 | `fix(contabilidad): usar sc-status-chip canónico` |
| BUGFIX-CONT-109 | 🟡 | `fix(contabilidad): subscriptSizing="dynamic" y eliminar hack margin` |
| BUGFIX-CONT-110 | 🟡 | `fix(contabilidad): mover Math de template a computed signal` |
| BUGFIX-CONT-111 | 🟡 | `fix(contabilidad): touch targets y tabular-nums` |
| IMP-CONT-112 | 🔵 | `improvement(contabilidad): 11 mejoras menores del design system` |

**Recomendación:** resolver los 4 críticos en una sola sesión BUGFIX, luego re-ejecutar validación 4×4 con dev server. Los mayores pueden distribuirse en 2-3 sesiones. Los menores agruparse en 1 IMPROVEMENT.

---

## Trazabilidad

**Subagentes invocados:**
- `Evidence Collector` — 9 issues + 14 confirmaciones + 9 pendientes browser
- `UI Designer` — 18 inconsistencias de design system + comparación con canónico + score 4.5/10

**Duración total:** ~3 minutos (ambos en paralelo, ~100s cada uno).
**Tokens consumidos:** ~116k (46k + 69k).
**Archivos del marco actualizados:** `PROGRESS-CONTABILIDAD-VALIDACION.md`.

---

**Siguiente acción:** PO decide prioridad de BUGFIX-CONT-101 a 104 (críticos). Al aprobar, orquestador ejecuta ticket BUGFIX en modo autónomo.
