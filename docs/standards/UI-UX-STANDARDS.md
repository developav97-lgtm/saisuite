# UI/UX Standards — SaiSuite Frontend
# Angular Material · ValMen Tech
# Leer COMPLETO antes de generar cualquier componente Angular.

---

## REGLA GENERAL: Referencias canónicas

| Patrón | Referencia canónica |
|---|---|
| Listado con tabla | `proyecto-list` |
| Vista tarjetas | `proyecto-cards` |
| Toggle Lista/Cards | `actividad-list` (in-page) ó `proyecto-list` + `proyecto-cards` (rutas) |
| Quick Access modal | `sidebar.component` + `QuickAccessDialogComponent` |

Antes de crear cualquier componente, leer el componente canónico correspondiente.

---

## 1. Estructura de una página de listado (ESTÁNDAR OBLIGATORIO)

Todo componente que sea una página completa (cargado por router) sigue esta estructura:

```html
<div class="sc-page">

  <!-- 1. Header con título y botón de acción principal -->
  <div class="sc-page-header">
    <h1 class="sc-page-header__title">Título</h1>
    <button mat-raised-button color="primary" (click)="nuevo()">
      <mat-icon>add</mat-icon> Nueva entidad
    </button>
  </div>

  <!-- 2. Filtros en sc-card -->
  <div class="xx-filters-card sc-card">
    <mat-form-field appearance="outline" subscriptSizing="dynamic" class="xx-search">
      <mat-label>Buscar…</mat-label>
      <input matInput [ngModel]="searchText()" (ngModelChange)="searchText.set($event)" (keyup.enter)="onSearch()" />
      <button mat-icon-button matSuffix (click)="onSearch()"><mat-icon>search</mat-icon></button>
    </mat-form-field>
    <!-- Filtros adicionales con mat-select -->
  </div>

  <!-- 3. Progress bar de carga — NUNCA spinner centrado en listados de página -->
  @if (loading()) {
    <mat-progress-bar mode="indeterminate" class="xx-progress" />
  }

  <!-- 4. Tabla con mat-table (NO table mat-table) -->
  <mat-table [dataSource]="items()" class="xx-table">
    <!-- columnas con mat-header-cell / mat-cell -->
    <mat-header-row *matHeaderRowDef="displayedColumns" />
    <mat-row *matRowDef="let row; columns: displayedColumns;" />
  </mat-table>

  <!-- 5. Empty state — FUERA del mat-table, con sc-empty-state -->
  @if (!loading() && items().length === 0) {
    <div class="sc-empty-state xx-empty">
      <mat-icon>inbox</mat-icon>
      <p>No hay [entidad] registradas.</p>
      <button mat-raised-button color="primary" (click)="nuevo()">
        <mat-icon>add</mat-icon> Nueva entidad
      </button>
    </div>
  }

  <!-- 6. Paginador -->
  <mat-paginator
    [length]="totalCount()"
    [pageSize]="pageSize"
    [pageSizeOptions]="[25, 50, 100]"
    (page)="onPage($event)"
    showFirstLastButtons
  />

</div>
```

### Reglas críticas de estructura
- Usar `mat-table` (no `table mat-table`) y `mat-header-cell`/`mat-cell` (no `th`/`td`).
- `mat-header-row` y `mat-row` con auto-close `/>` (no `></mat-row>`).
- **NUNCA** `mat-progress-spinner` centrado en un listado de página completa. Usar `mat-progress-bar` delgado arriba de la tabla.
- El empty state va FUERA del `mat-table`, al mismo nivel en el DOM.
- El empty state usa la clase global `sc-empty-state` + clase local `xx-empty` para el borde inferior.
- `*ngIf` está deprecado — usar siempre `@if` / `@for` / `@switch`.

---

## 2. SCSS de un listado — Variables CSS obligatorias

**NUNCA hardcodear colores. Siempre usar las variables del design system:**

```scss
// ── Filtros ────────────────────────────────────
.xx-filters-card {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: center;
  padding: 0.875rem 1rem;
  margin-bottom: 1rem;
}
.xx-search { flex: 1; min-width: 200px; }
.xx-filter { width: 170px; flex-shrink: 0; }

// ── Progress bar ────────────────────────────────
.xx-progress {
  margin-bottom: -4px;
  border-radius: var(--sc-radius) var(--sc-radius) 0 0;
}

// ── Tabla ───────────────────────────────────────
.xx-table { width: 100%; border-radius: var(--sc-radius); }

// ── Código monoespaciado (PKs, IDs) ─────────────
.xx-codigo {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--sc-primary);
  background: var(--sc-primary-light);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

// ── Chip de tipo/categoría ───────────────────────
.xx-tipo-chip {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--sc-text-muted);
  background: var(--sc-surface-ground);
  border: 1px solid var(--sc-surface-border);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

// ── Columnas ────────────────────────────────────
.xx-col-right    { text-align: right !important; justify-content: flex-end !important; }
.xx-col-acciones { width: 96px; justify-content: flex-end !important; }

// ── Empty state ─────────────────────────────────
.xx-empty {
  border: 1px solid var(--sc-surface-border);
  border-top: none;
  border-radius: 0 0 var(--sc-radius) var(--sc-radius);
}
```

### Variables CSS disponibles
| Variable | Uso |
|---|---|
| `var(--sc-primary)` | Color primario (azul ValMen) |
| `var(--sc-primary-light)` | Fondo tenue del primario |
| `var(--sc-surface-ground)` | Fondo de superficie |
| `var(--sc-surface-border)` | Borde de separación |
| `var(--sc-text-muted)` | Texto secundario / apagado |
| `var(--sc-radius)` | Border-radius estándar |

---

## 3. Componentes dentro de tabs (sub-listas)

Para componentes que viven dentro de un tab (ej: `fase-list`, `actividad-proyecto-list`), NO usar `sc-page`. Estructura simplificada:

```html
<!-- Header con contador y botón -->
<div class="xx-header">
  <span>{{ items().length }} elementos</span>
  <button mat-raised-button color="primary" (click)="nuevo()">
    <mat-icon>add</mat-icon> Agregar
  </button>
</div>

<!-- Progress bar -->
@if (loading()) { <mat-progress-bar mode="indeterminate" /> }

<!-- Tabla -->
<mat-table [dataSource]="items()" class="xx-table">
  ...
  <mat-header-row *matHeaderRowDef="cols" />
  <mat-row *matRowDef="let r; columns: cols;" />
</mat-table>

<!-- Empty state -->
@if (!loading() && items().length === 0) {
  <div class="sc-empty-state">
    <mat-icon>inbox</mat-icon>
    <p>No hay registros.</p>
  </div>
}
```

---

## 4. Formularios

```html
<form [formGroup]="form" (ngSubmit)="onSubmit()">
  <mat-form-field appearance="outline">
    <mat-label>Nombre del campo</mat-label>
    <input matInput formControlName="campo" />
    @if (form.get('campo')?.hasError('required')) {
      <mat-error>Este campo es obligatorio</mat-error>
    }
  </mat-form-field>

  <div class="form-actions">
    <button mat-stroked-button type="button" (click)="onCancel()">Cancelar</button>
    <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid || loading">
      @if (loading) {
        <mat-progress-spinner diameter="18" mode="indeterminate"></mat-progress-spinner>
      }
      Guardar
    </button>
  </div>
</form>
```

### Reglas
- `appearance="outline"` en todos los `mat-form-field`.
- Errores con `@if` dentro del `mat-form-field`, **nunca** `*ngIf`.
- Botón **Cancelar**: `mat-stroked-button`, tipo `button`.
- Botón **Guardar**: `mat-raised-button color="primary"`, tipo `submit`.
- Spinner de 18px dentro del botón mientras guarda, no reemplaza el texto.

```scss
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
```

---

## 5. Acciones en Tablas

| Tipo | Componente | Cuándo |
|---|---|---|
| Acción principal | `mat-raised-button color="primary"` | Crear / Agregar |
| Ver detalle | `mat-icon-button` con `chevron_right` | Navegar al detalle |
| Editar inline | `mat-icon-button` con `edit` | Abrir dialog de edición |
| Eliminar | `mat-icon-button color="warn"` con `delete_outline` | Eliminar (con confirmación) |

**SIEMPRE** abrir `MatDialog` con `ConfirmDialogComponent` antes de eliminar. Nunca `confirm()` del browser.

---

## 6. Estados de Carga

| Contexto | Componente | Posición |
|---|---|---|
| Listado de página completa | `mat-progress-bar` | Encima de la tabla, `margin-bottom: -4px` |
| Subcomponente en tab | `mat-progress-bar` | Encima de la tabla |
| Botón guardando | `mat-progress-spinner diameter="18"` | Dentro del botón |

**NUNCA** `mat-progress-spinner` centrado en una página de listado.

---

## 7. Mensajes de Feedback (MatSnackBar)

```typescript
// Éxito — 3 segundos
this.snackBar.open('Entidad creada correctamente.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });

// Error — 5 segundos
this.snackBar.open('Error al guardar.', 'Cerrar', { duration: 5000, panelClass: ['snack-error'] });

// Advertencia — 4 segundos
this.snackBar.open('Advertencia.', 'Cerrar', { duration: 4000, panelClass: ['snack-warning'] });
```

```scss
// En styles.scss (global)
.snack-success .mdc-snackbar__surface { background-color: #2e7d32 !important; }
.snack-error   .mdc-snackbar__surface { background-color: #c62828 !important; }
.snack-warning .mdc-snackbar__surface { background-color: #f57f17 !important; color: #000 !important; }
```

---

---

## 8. Patrón: Toggle Lista / Cards (ESTÁNDAR OBLIGATORIO)

Cualquier listado que soporte dos modos de visualización (tabla y tarjetas) sigue este patrón:

### Visual
- **Un solo botón stroked** que muestra el nombre de la vista alternativa.
- En vista lista → botón `Cards` con ícono `grid_view`.
- En vista tarjetas → botón `Lista` con ícono `view_list`.
- **NUNCA** un `mat-button-toggle-group` de dos opciones simultáneas.

### Implementación: mismo componente (in-page toggle)

Usar cuando el volumen de datos es el mismo y no hay razón de URL separada (ej: `actividad-list`).

**TS:**
```typescript
readonly viewMode = signal<'list' | 'cards'>(
  (localStorage.getItem('saisuite.[feature]View') as 'list' | 'cards') ?? 'list',
);

setViewMode(mode: 'list' | 'cards'): void {
  this.viewMode.set(mode);
  localStorage.setItem('saisuite.[feature]View', mode);
}
```

**HTML — header:**
```html
<div class="xx-header-actions">
  @if (viewMode() === 'list') {
    <button mat-stroked-button matTooltip="Ver como tarjetas" (click)="setViewMode('cards')">
      <mat-icon>grid_view</mat-icon>
      Cards
    </button>
  } @else {
    <button mat-stroked-button matTooltip="Ver como tabla" (click)="setViewMode('list')">
      <mat-icon>view_list</mat-icon>
      Lista
    </button>
  }
  <button mat-raised-button color="primary" (click)="nuevo()">
    <mat-icon>add</mat-icon> Nueva entidad
  </button>
</div>
```

**HTML — contenido:**
```html
@if (viewMode() === 'list') {
  <!-- mat-table + empty state + mat-paginator -->
} @else {
  <!-- grid de cards + empty state + mat-paginator -->
}
```

**SCSS:**
```scss
.xx-header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
```

### Implementación: rutas separadas

Usar cuando cada vista justifica su propia URL (ej: `proyecto-list` en `/proyectos` y `proyecto-cards` en `/proyectos/cards`).

- En el componente de lista: `<button mat-stroked-button (click)="irACards()"><mat-icon>grid_view</mat-icon> Cards</button>`
- En el componente de cards: `<button mat-stroked-button (click)="irALista()"><mat-icon>view_list</mat-icon> Lista</button>`
- La preferencia se guarda con `localStorage.getItem('saisuite.[feature]View')` y se respeta en el guard/resolver de la ruta.

### Cards grid — estructura HTML canónica

```html
<div class="xx-cards-grid">
  @for (row of items(); track row.id) {
    <div class="xx-card sc-card">
      <div class="xx-card-header">
        <span class="xx-codigo">{{ row.codigo }}</span>
        <span class="xx-tipo-chip">{{ tipoLabel(row.tipo) }}</span>
      </div>
      <p class="xx-card-nombre">{{ row.nombre }}</p>
      <div class="xx-card-meta">
        <!-- métricas secundarias -->
      </div>
      <div class="xx-card-actions">
        <button mat-icon-button matTooltip="Editar" (click)="editar(row)"><mat-icon>edit</mat-icon></button>
        <button mat-icon-button matTooltip="Eliminar" color="warn" (click)="eliminar(row)"><mat-icon>delete_outline</mat-icon></button>
      </div>
    </div>
  }
</div>
```

**SCSS canónico de cards:**
```scss
.xx-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.xx-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  cursor: pointer;
  transition: box-shadow 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
  border: 1px solid var(--sc-surface-border) !important;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    border-color: var(--sc-primary) !important;
    transform: translateY(-1px);
  }
}

.xx-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.xx-card-nombre {
  font-weight: 500;
  font-size: 0.9375rem;
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-clamp: 2;
}

.xx-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.25rem;
  border-top: 1px solid var(--sc-surface-border);
  padding-top: 0.5rem;
  margin-top: 0.25rem;
}
```

### Persistencia de preferencia
- **Clave localStorage:** `saisuite.[feature]View` (ej: `saisuite.actividadesView`, `saisuite.proyectosView`)
- **Valores válidos:** `'list'` | `'cards'`
- **Default cuando no existe:** `'list'`
- La preferencia es por feature, no global.

---

## 9. Patrón: Quick Access Modal (componentes de administración)

Para abrir vistas completas de administración (formularios de Terceros, Usuarios, etc.) dentro de un `MatDialog` sin salir de la pantalla actual, se usa el patrón **Quick Access**.

### Cuándo usarlo
- El usuario necesita crear/editar una entidad de catálogo desde un contexto diferente (ej: vincular un tercero a un proyecto → crear el tercero sin abandonar el proyecto).
- El componente ya existe como página de ruta — se reutiliza dentro del dialog.

### Arquitectura

```
sidebar.component → QuickAccessNavigatorService
                  → QuickAccessDialogComponent
                       └─ NgComponentOutlet (carga el componente destino)
                       └─ quickAccessGuard (controla navegación interna)
```

**Archivos clave:**
- `frontend/src/app/shared/components/quick-access-dialog/quick-access-dialog.component.ts`
- `frontend/src/app/core/services/quick-access-navigator.service.ts`
- `frontend/src/app/core/guards/quick-access.guard.ts`

### Cómo agregar un nuevo acceso rápido al sidebar

En `sidebar.component.ts`, en el array `PROYECTOS_NAV` (o el nav correspondiente), agregar:

```typescript
{
  label: 'Nombre de la sección',
  icon: 'icon_name',
  action: () => this.openQuickAccess(
    'Título del dialog',
    () => import('path/al/componente').then(m => m.MiComponenteComponent),
    [
      {
        path: '/ruta/nueva',
        loadComponent: () => import('path/al/form').then(m => m.MiFormComponent),
      },
      {
        path: '/ruta/:id/editar',
        loadComponent: () => import('path/al/form').then(m => m.MiFormComponent),
      },
    ],
  ),
},
```

### Reglas
- El componente que se carga en el dialog debe ser **standalone**.
- Las rutas internas (`QuickAccessRoute[]`) manejan navegación dentro del dialog (ej: lista → form nuevo → form edición).
- El dialog siempre tiene `width: '92vw', maxWidth: '92vw', height: '88vh'`.
- **NUNCA** abrir un `MatDialog` genérico con un componente arbitrario para esto — siempre pasar por `QuickAccessDialogComponent`.

---

## 10. Checklist antes de entregar un componente

- [ ] Página completa: usa `sc-page`, `sc-page-header`, filtros en `sc-card`
- [ ] Tabla usa `mat-table` (no `table mat-table`) y `mat-header-cell`/`mat-cell`
- [ ] Loading usa `mat-progress-bar` (no spinner) en listados
- [ ] Empty state con `sc-empty-state` FUERA del `mat-table`
- [ ] SCSS usa variables CSS (`var(--sc-primary)`, etc.), sin colores hardcodeados
- [ ] No hay `*ngIf` / `*ngFor` — todo con `@if` / `@for`
- [ ] No hay `any` en TypeScript
- [ ] `ChangeDetectionStrategy.OnPush` en todos los componentes
- [ ] Eliminaciones con `MatDialog` de confirmación, nunca `confirm()`
- [ ] Feedback con `MatSnackBar` con panelClass correcto, nunca `alert()`
- [ ] No hay suscripciones manuales sin `async pipe` o `takeUntilDestroyed`
- [ ] Toggle Lista/Cards: un solo `mat-stroked-button` con el nombre de la vista alternativa (sección 8)
- [ ] Toggle guarda preferencia en `localStorage` con clave `saisuite.[feature]View` (sección 8)
- [ ] Quick Access modal: usa `QuickAccessDialogComponent`, no `MatDialog` genérico (sección 9)
