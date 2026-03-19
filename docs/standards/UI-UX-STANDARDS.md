# UI/UX Standards — SaiSuite Frontend
# Angular Material · ValMen Tech
# Leer COMPLETO antes de generar cualquier componente Angular.

---

## REGLA GENERAL: Referencia canónica

**El componente `proyecto-list` es la referencia canónica de estilo para todos los listados.**
Antes de crear cualquier componente de tipo lista, leer:
`frontend/src/app/features/proyectos/components/proyecto-list/`

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

## 8. Checklist antes de entregar un componente

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
