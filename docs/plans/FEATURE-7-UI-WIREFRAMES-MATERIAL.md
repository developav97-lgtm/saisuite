# FEATURE-7-UI-WIREFRAMES-MATERIAL.md
# Feature 7: Budget & Cost Tracking — UI Design Specification
# Angular Material · ValMen Tech · SaiSuite

---

## 0. Principios de diseño para esta feature

- Todos los componentes viven dentro del tab "Presupuesto" en `proyecto-detail`, no son páginas de ruta independiente.
- Siguen el patrón de sub-listas (sección 3 de UI-UX-STANDARDS) — sin `sc-page`, sin `sc-page-header`.
- El componente raíz `BudgetManagementComponent` es el orquestador; los demás son hijos presentacionales.
- Paleta de estado de presupuesto usa variables CSS dedicadas definidas en el componente; nunca colores hardcodeados.
- Todos los montos monetarios se formatean con `| currency:'COP':'symbol':'1.2-2'` (o la moneda del proyecto).

---

## 1. BudgetManagementComponent

### 1.1 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [mat-card — bm-summary-card]                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  RESUMEN DEL PRESUPUESTO                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │ Planificado  │  │   Ejecutado  │  │   Varianza   │            │  │
│  │  │  $120,000    │  │   $98,500    │  │  [chip OK]   │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  │  ████████████████████░░░░░░░░░  82% ejecutado                    │  │
│  │  [mat-progress-bar mode="determinate" value="82"]                │  │
│  │                                             [Aprobar presupuesto]│  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [mat-tab-group — bm-breakdown-tabs]                                    │
│  ┌─ Por Recurso ─┬─ Por Tarea ─┬─ Por Categoría ────────────────────┐  │
│  │                                                                   │  │
│  │  [mat-progress-bar si loading()]                                  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ Nombre  │ Planificado │ Ejecutado │ Varianza │ % Ejecución  │  │  │
│  │  ├─────────┼─────────────┼───────────┼──────────┼─────────────┤  │  │
│  │  │ Juan A. │  $40,000    │  $38,200  │  $1,800  │ [bar 95%]   │  │  │
│  │  │ María L.│  $30,000    │  $28,000  │  $2,000  │ [bar 93%]   │  │  │
│  │  └─────────┴─────────────┴───────────┴──────────┴─────────────┘  │  │
│  │  [sc-empty-state si no hay datos]                                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  @if (!hasBudget()) — Estado sin presupuesto definido                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [sc-empty-state bm-no-budget]                                    │  │
│  │  [mat-icon] account_balance                                       │  │
│  │  Sin presupuesto definido para este proyecto.                     │  │
│  │  [mat-raised-button primary] Definir presupuesto                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  @if (showBudgetForm()) — Formulario de definición                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [sc-card bm-form-card]                                           │  │
│  │  [mat-icon] savings   Definir presupuesto del proyecto            │  │
│  │                                                                   │  │
│  │  [mat-form-field] Monto planificado total *   [mat-form-field]   │  │
│  │  [mat-form-field] Moneda (mat-select)         Umbral de alerta % │  │
│  │  [mat-form-field] Notas (mat-textarea)                           │  │
│  │                                                                   │  │
│  │                        [Cancelar] [Guardar presupuesto]           │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Material Component Mapping

| Elemento UI | Material Component | Clase local |
|---|---|---|
| Tarjeta resumen | `mat-card` + `mat-card-content` | `bm-summary-card` |
| KPIs planificado/ejecutado | `mat-card` anidada | `bm-kpi-card` |
| Chip varianza | `mat-chip` con `[style.background]` dinámico | `bm-variance-chip` |
| Barra progreso presupuesto | `mat-progress-bar mode="determinate"` | `bm-budget-bar` |
| Botón aprobar | `mat-raised-button color="primary"` | — |
| Tabs desglose | `mat-tab-group animationDuration="200ms"` | `bm-breakdown-tabs` |
| Tabla por recurso/tarea/categoría | `mat-table` + `MatSort` | `bm-breakdown-table` |
| Mini barra % en tabla | `mat-progress-bar mode="determinate"` | `bm-row-bar` |
| Formulario presupuesto | `sc-card` + `mat-form-field appearance="outline"` | `bm-form-card` |
| Loading tab | `mat-progress-bar mode="indeterminate"` | `bm-progress` |
| Empty state sin presupuesto | `div.sc-empty-state` | `bm-no-budget` |

### 1.3 Template Snippets Clave

#### Tarjeta resumen con KPIs y barra
```html
<mat-card class="bm-summary-card">
  <mat-card-content>
    <div class="bm-kpi-row">
      <div class="bm-kpi-card sc-card">
        <span class="bm-kpi-label">
          <mat-icon>savings</mat-icon> Planificado
        </span>
        <span class="bm-kpi-value">
          {{ budget()?.monto_planificado | currency:'COP':'symbol':'1.0-0' }}
        </span>
      </div>
      <div class="bm-kpi-card sc-card">
        <span class="bm-kpi-label">
          <mat-icon>payments</mat-icon> Ejecutado
        </span>
        <span class="bm-kpi-value">
          {{ costoEjecutado() | currency:'COP':'symbol':'1.0-0' }}
        </span>
      </div>
      <div class="bm-kpi-card sc-card">
        <span class="bm-kpi-label">
          <mat-icon>trending_up</mat-icon> Varianza
        </span>
        <mat-chip
          [style.background-color]="varianzaColor() + '22'"
          [style.color]="varianzaColor()"
          class="bm-variance-chip">
          {{ varianza() | currency:'COP':'symbol':'1.0-0' }}
        </mat-chip>
      </div>
    </div>

    <div class="bm-progress-row">
      <span class="bm-progress-label">{{ porcentajeEjecutado() | number:'1.0-0' }}% ejecutado</span>
      <mat-progress-bar
        mode="determinate"
        [value]="porcentajeEjecutado()"
        [color]="progressColor()"
        class="bm-budget-bar" />
    </div>

    @if (isPM()) {
      <div class="bm-approve-row">
        <button mat-raised-button color="primary"
          [disabled]="budget()?.aprobado || saving()"
          (click)="aprobarPresupuesto()">
          <mat-icon>check_circle</mat-icon>
          @if (budget()?.aprobado) { Presupuesto aprobado } @else { Aprobar presupuesto }
        </button>
      </div>
    }
  </mat-card-content>
</mat-card>
```

#### Tabs con tabla de desglose (patrón genérico)
```html
<mat-tab-group animationDuration="200ms" class="bm-breakdown-tabs">

  <mat-tab label="Por Recurso">
    @if (loadingRecursos()) { <mat-progress-bar mode="indeterminate" /> }
    <mat-table [dataSource]="costosRecurso()" matSort class="bm-breakdown-table">

      <ng-container matColumnDef="nombre">
        <mat-header-cell *matHeaderCellDef mat-sort-header>Recurso</mat-header-cell>
        <mat-cell *matCellDef="let row">{{ row.nombre }}</mat-cell>
      </ng-container>

      <ng-container matColumnDef="planificado">
        <mat-header-cell *matHeaderCellDef mat-sort-header class="bm-col-right">
          Planificado
        </mat-header-cell>
        <mat-cell *matCellDef="let row" class="bm-col-right">
          {{ row.planificado | currency:'COP':'symbol':'1.0-0' }}
        </mat-cell>
      </ng-container>

      <ng-container matColumnDef="ejecutado">
        <mat-header-cell *matHeaderCellDef mat-sort-header class="bm-col-right">
          Ejecutado
        </mat-header-cell>
        <mat-cell *matCellDef="let row" class="bm-col-right">
          {{ row.ejecutado | currency:'COP':'symbol':'1.0-0' }}
        </mat-cell>
      </ng-container>

      <ng-container matColumnDef="varianza">
        <mat-header-cell *matHeaderCellDef class="bm-col-right">Varianza</mat-header-cell>
        <mat-cell *matCellDef="let row" class="bm-col-right"
          [style.color]="row.varianza < 0 ? 'var(--budget-danger)' : 'var(--budget-success)'">
          {{ row.varianza | currency:'COP':'symbol':'1.0-0' }}
        </mat-cell>
      </ng-container>

      <ng-container matColumnDef="porcentaje">
        <mat-header-cell *matHeaderCellDef>% Ejecución</mat-header-cell>
        <mat-cell *matCellDef="let row">
          <div class="bm-row-bar-wrap">
            <mat-progress-bar
              mode="determinate"
              [value]="row.porcentaje"
              class="bm-row-bar" />
            <span class="bm-row-bar-pct">{{ row.porcentaje | number:'1.0-0' }}%</span>
          </div>
        </mat-cell>
      </ng-container>

      <mat-header-row *matHeaderRowDef="colsRecurso" />
      <mat-row *matRowDef="let row; columns: colsRecurso;" />
    </mat-table>

    @if (!loadingRecursos() && costosRecurso().length === 0) {
      <div class="sc-empty-state bm-empty">
        <mat-icon>people_outline</mat-icon>
        <p>Sin datos de costo por recurso.</p>
      </div>
    }
  </mat-tab>

  <!-- Tabs Por Tarea y Por Categoría siguen el mismo patrón -->

</mat-tab-group>
```

#### Empty state + formulario de definición
```html
@if (!hasBudget() && !showBudgetForm()) {
  <div class="sc-empty-state bm-no-budget">
    <mat-icon>account_balance</mat-icon>
    <p class="sc-empty-state__title">Sin presupuesto definido</p>
    <p class="sc-empty-state__subtitle">
      Define el presupuesto del proyecto para habilitar el seguimiento de costos.
    </p>
    <button mat-raised-button color="primary" (click)="showBudgetForm.set(true)">
      <mat-icon>add</mat-icon> Definir presupuesto
    </button>
  </div>
}

@if (showBudgetForm()) {
  <div class="sc-card bm-form-card">
    <div class="sc-card__header">
      <mat-icon>savings</mat-icon>
      <span class="sc-card__title">Definir presupuesto del proyecto</span>
    </div>
    <div class="sc-card__body">
      <form [formGroup]="budgetForm" (ngSubmit)="guardarPresupuesto()">
        <div class="sc-form-grid">
          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Monto planificado total *</mat-label>
            <mat-icon matPrefix>attach_money</mat-icon>
            <input matInput type="number" min="0" step="0.01"
              formControlName="monto_planificado" placeholder="0.00" />
            @if (budgetForm.controls.monto_planificado.hasError('required')) {
              <mat-error>El monto planificado es obligatorio.</mat-error>
            }
            @if (budgetForm.controls.monto_planificado.hasError('min')) {
              <mat-error>El monto debe ser mayor a cero.</mat-error>
            }
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Moneda</mat-label>
            <mat-select formControlName="moneda">
              @for (m of monedaOptions; track m.value) {
                <mat-option [value]="m.value">{{ m.label }}</mat-option>
              }
            </mat-select>
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Umbral de alerta (%)</mat-label>
            <input matInput type="number" min="1" max="100" step="1"
              formControlName="umbral_alerta" placeholder="80" />
            <span matTextSuffix>%</span>
            <mat-hint>Se enviará alerta cuando el gasto supere este porcentaje.</mat-hint>
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always"
            class="sc-field--full">
            <mat-label>Notas</mat-label>
            <textarea matInput formControlName="notas" rows="3"
              placeholder="Observaciones sobre el presupuesto…"></textarea>
          </mat-form-field>
        </div>

        <div class="form-actions">
          <button mat-stroked-button type="button" (click)="showBudgetForm.set(false)">
            Cancelar
          </button>
          <button mat-raised-button color="primary" type="submit"
            [disabled]="budgetForm.invalid || saving()">
            @if (saving()) {
              <mat-progress-spinner diameter="18" mode="indeterminate" />
            }
            Guardar presupuesto
          </button>
        </div>
      </form>
    </div>
  </div>
}
```

### 1.4 SCSS Variables

```scss
// budget-management.component.scss

:host {
  --budget-success: var(--sc-success, #66bb6a);
  --budget-warning: var(--sc-warning, #ffa726);
  --budget-danger:  var(--sc-danger,  #ef5350);
  --budget-info:    var(--sc-primary, #1976d2);
}

.bm-summary-card {
  margin-bottom: 1.25rem;
  border: 1px solid var(--sc-surface-border);
}

.bm-kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.bm-kpi-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.875rem 1rem;
}

.bm-kpi-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sc-text-muted);

  mat-icon { font-size: 1rem; width: 1rem; height: 1rem; }
}

.bm-kpi-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--sc-text-primary, inherit);
  font-variant-numeric: tabular-nums;
}

.bm-progress-row {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}

.bm-progress-label {
  font-size: 0.8125rem;
  color: var(--sc-text-muted);
  text-align: right;
}

.bm-budget-bar {
  height: 10px;
  border-radius: var(--sc-radius);
}

.bm-approve-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

.bm-breakdown-tabs {
  margin-top: 0.25rem;
}

.bm-breakdown-table { width: 100%; }

.bm-col-right {
  text-align: right !important;
  justify-content: flex-end !important;
}

.bm-row-bar-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
}

.bm-row-bar { flex: 1; }

.bm-row-bar-pct {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--sc-text-muted);
  min-width: 36px;
  text-align: right;
}

.bm-empty {
  border: 1px solid var(--sc-surface-border);
  border-top: none;
  border-radius: 0 0 var(--sc-radius) var(--sc-radius);
}

.bm-no-budget {
  margin-top: 1.5rem;
  border: 1px solid var(--sc-surface-border);
  border-radius: var(--sc-radius);
}

.bm-form-card { margin-top: 1rem; }
```

### 1.5 Flujo de interacción

```
[Tab "Presupuesto" visible]
        │
        ▼
   hasBudget()?
   ┌─── NO ────────────────────────────────────────────────┐
   │  sc-empty-state + botón "Definir presupuesto"         │
   │         │                                             │
   │         ▼ click                                       │
   │  showBudgetForm.set(true)                             │
   │  [Formulario de definición aparece]                   │
   │         │ submit                                      │
   │         ▼                                             │
   │  budgetService.create(projectId, form.value)          │
   │  snackBar 'snack-success' → hasBudget.set(true)       │
   └───────────────────────────────────────────────────────┘
   ┌─── SI ─────────────────────────────────────────────────┐
   │  [Tarjeta resumen KPIs]                                │
   │  [mat-tab-group — Por Recurso | Por Tarea | Categoría] │
   │  [PM ve botón "Aprobar presupuesto"]                   │
   │         │ click aprobar                               │
   │         ▼                                             │
   │  MatDialog ConfirmDialogComponent                     │
   │  "¿Confirmar aprobación del presupuesto?"             │
   │         │ confirm                                     │
   │         ▼                                             │
   │  budgetService.approve(budget().id)                   │
   │  snackBar 'snack-success' → budget().aprobado = true  │
   └───────────────────────────────────────────────────────┘
```

---

## 2. ExpenseListComponent

### 2.1 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [div.el-header]                                                        │
│  3 gastos registrados        [Registrar gasto  mat-raised-button]       │
│                                                                         │
│  [mat-progress-bar si loading()]                                        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Fecha │ Categoría       │ Descripción │ Monto  │ Fact.│ Por │ ⋮ │   │
│  ├───────┼─────────────────┼─────────────┼────────┼──────┼─────┼───┤   │
│  │ 15/03 │ [chip]Viáticos  │ Hotel LATAM │$380,000│ [✓] │ Ana │ ✎⌫│   │
│  │ 20/03 │ [chip]Software  │ Licencia A. │$120,000│ [✗] │ Juan│ ✎⌫│   │
│  └───────┴─────────────────┴─────────────┴────────┴──────┴─────┴───┘   │
│                                                                         │
│  [sc-empty-state si no hay gastos]                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Material Component Mapping

| Elemento UI | Material Component | Clase local |
|---|---|---|
| Header con contador | `div.el-header` | Patrón sub-lista (estándar sección 3) |
| Botón registrar | `mat-raised-button color="primary"` | — |
| Loading | `mat-progress-bar mode="indeterminate"` | `el-progress` |
| Tabla | `mat-table` + `MatSort` | `el-table` |
| Chip categoría | `mat-chip` con color semántico | `el-category-chip` |
| Icono facturable | `mat-icon` `check_circle` / `cancel` | `el-billable-icon` |
| Acciones | `mat-icon-button` con `matTooltip` | — |
| Empty state | `div.sc-empty-state el-empty` | — |

### 2.3 Template Snippets Clave

#### Header y tabla
```html
<div class="el-header">
  <span class="el-count">{{ expenses().length }} gastos registrados</span>
  <button mat-raised-button color="primary" (click)="abrirFormGasto(null)">
    <mat-icon>add</mat-icon> Registrar gasto
  </button>
</div>

@if (loading()) { <mat-progress-bar mode="indeterminate" class="el-progress" /> }

<mat-table [dataSource]="expenses()" matSort class="el-table">

  <ng-container matColumnDef="fecha">
    <mat-header-cell *matHeaderCellDef mat-sort-header>Fecha</mat-header-cell>
    <mat-cell *matCellDef="let row">
      {{ row.fecha | date:'dd/MM/yyyy' }}
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="categoria">
    <mat-header-cell *matHeaderCellDef mat-sort-header>Categoría</mat-header-cell>
    <mat-cell *matCellDef="let row">
      <mat-chip class="el-category-chip"
        [style.background-color]="categoryColor(row.categoria) + '22'"
        [style.color]="categoryColor(row.categoria)">
        {{ categoryLabel(row.categoria) }}
      </mat-chip>
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="descripcion">
    <mat-header-cell *matHeaderCellDef>Descripción</mat-header-cell>
    <mat-cell *matCellDef="let row">{{ row.descripcion }}</mat-cell>
  </ng-container>

  <ng-container matColumnDef="monto">
    <mat-header-cell *matHeaderCellDef mat-sort-header class="el-col-right">
      Monto
    </mat-header-cell>
    <mat-cell *matCellDef="let row" class="el-col-right el-monto">
      {{ row.monto | currency:row.moneda:'symbol':'1.2-2' }}
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="facturable">
    <mat-header-cell *matHeaderCellDef>Fact.</mat-header-cell>
    <mat-cell *matCellDef="let row">
      @if (row.facturable) {
        <mat-icon class="el-billable-icon el-billable-icon--yes"
          matTooltip="Facturable">check_circle</mat-icon>
      } @else {
        <mat-icon class="el-billable-icon el-billable-icon--no"
          matTooltip="No facturable">cancel</mat-icon>
      }
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="pagado_por">
    <mat-header-cell *matHeaderCellDef>Pagado por</mat-header-cell>
    <mat-cell *matCellDef="let row">
      {{ row.pagado_por_detail?.nombre ?? '—' }}
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="acciones">
    <mat-header-cell *matHeaderCellDef class="el-col-acciones"></mat-header-cell>
    <mat-cell *matCellDef="let row" class="el-col-acciones">
      <button mat-icon-button matTooltip="Editar" (click)="abrirFormGasto(row)">
        <mat-icon>edit</mat-icon>
      </button>
      <button mat-icon-button color="warn" matTooltip="Eliminar"
        (click)="confirmarEliminar(row)">
        <mat-icon>delete_outline</mat-icon>
      </button>
    </mat-cell>
  </ng-container>

  <mat-header-row *matHeaderRowDef="displayedColumns" />
  <mat-row *matRowDef="let row; columns: displayedColumns;" />
</mat-table>

@if (!loading() && expenses().length === 0) {
  <div class="sc-empty-state el-empty">
    <mat-icon>receipt_long</mat-icon>
    <p class="sc-empty-state__title">Sin gastos registrados</p>
    <p class="sc-empty-state__subtitle">
      Registra los gastos del proyecto para mantener el seguimiento de costos.
    </p>
    <button mat-raised-button color="primary" (click)="abrirFormGasto(null)">
      <mat-icon>add</mat-icon> Registrar gasto
    </button>
  </div>
}
```

### 2.4 SCSS Variables

```scss
// expense-list.component.scss

.el-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.el-count {
  font-size: 0.875rem;
  color: var(--sc-text-muted);
}

.el-progress { margin-bottom: -4px; }

.el-table { width: 100%; border-radius: var(--sc-radius); }

.el-category-chip {
  font-size: 0.6875rem;
  font-weight: 600;
  min-height: 22px;
  padding: 0 0.5rem;
}

.el-monto {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  font-weight: 600;
}

.el-billable-icon {
  font-size: 1.125rem;
  width: 1.125rem;
  height: 1.125rem;

  &--yes { color: var(--sc-success, #66bb6a); }
  &--no  { color: var(--sc-text-muted); }
}

.el-col-right    { text-align: right !important; justify-content: flex-end !important; }
.el-col-acciones { width: 96px; justify-content: flex-end !important; }

.el-empty {
  border: 1px solid var(--sc-surface-border);
  border-top: none;
  border-radius: 0 0 var(--sc-radius) var(--sc-radius);
}
```

### 2.5 Flujo de interacción

```
[ExpenseListComponent carga]
        │
        ▼
  expenseService.list(projectId)
        │
   ┌─── vacío ─────────────────────────────────────┐
   │   sc-empty-state + botón "Registrar gasto"    │
   └───────────────────────────────────────────────┘
        │
        ▼ click "Registrar gasto" o click editar fila
  dialog.open(ExpenseFormDialogComponent, { data: { expense, projectId } })
        │
        ▼ dialogRef.afterClosed()
   saved? → reload expenses() → snackBar 'snack-success'
  deleted? → confirmarEliminar() → MatDialog ConfirmDialog
           → expenseService.delete(id) → reload → snackBar 'snack-success'
```

---

## 3. ExpenseFormDialogComponent

### 3.1 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  [mat-dialog-title]                                     │
│  Registrar gasto  /  Editar gasto                       │
├─────────────────────────────────────────────────────────┤
│  [mat-dialog-content]                                   │
│                                                         │
│  [mat-form-field] Categoría *  [mat-select]             │
│  [mat-form-field] Descripción *  [mat-input]            │
│                                                         │
│  [mat-form-field] Monto *       [mat-form-field] Fecha *│
│  [mat-input type=number]        [mat-datepicker]        │
│                                                         │
│  [mat-form-field] Pagado por  [mat-select usuarios]     │
│  [mat-checkbox] Facturable al cliente                   │
│                                                         │
│  [mat-form-field] URL Comprobante  [mat-input]          │
│  [mat-form-field] Notas  [mat-textarea rows=2]          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [mat-dialog-actions align="end"]                       │
│                     [Cancelar] [Guardar]                │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Material Component Mapping

| Elemento UI | Material Component |
|---|---|
| Contenedor | `MatDialogModule` — `mat-dialog-title`, `mat-dialog-content`, `mat-dialog-actions` |
| Categoría | `mat-form-field` + `mat-select` + `@for mat-option` |
| Descripción | `mat-form-field` + `input matInput` |
| Monto | `mat-form-field` + `input matInput type="number"` + `mat-icon matPrefix` |
| Fecha | `mat-form-field` + `input matInput` + `mat-datepicker` + `mat-datepicker-toggle` |
| Pagado por | `mat-form-field` + `mat-select` |
| Facturable | `mat-checkbox formControlName` |
| URL comprobante | `mat-form-field` + `input matInput` + `mat-icon matPrefix` |
| Notas | `mat-form-field` + `textarea matInput` |
| Botones | `mat-stroked-button` cancelar / `mat-raised-button color="primary"` guardar |

### 3.3 Template Snippets Clave

```html
<h2 mat-dialog-title>
  <mat-icon>{{ data.expense ? 'edit' : 'add_circle' }}</mat-icon>
  {{ data.expense ? 'Editar gasto' : 'Registrar gasto' }}
</h2>

<mat-dialog-content class="efd-content">
  <form [formGroup]="form" class="efd-form">

    <div class="sc-form-grid">

      <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
        <mat-label>Categoría *</mat-label>
        <mat-select formControlName="categoria">
          @for (cat of categoriaOptions; track cat.value) {
            <mat-option [value]="cat.value">{{ cat.label }}</mat-option>
          }
        </mat-select>
        @if (form.controls.categoria.hasError('required')) {
          <mat-error>La categoría es obligatoria.</mat-error>
        }
      </mat-form-field>

      <mat-form-field appearance="outline" subscriptSizing="dynamic"
        floatLabel="always" class="sc-field--full">
        <mat-label>Descripción *</mat-label>
        <input matInput formControlName="descripcion"
          placeholder="Describe brevemente el gasto…" />
        @if (form.controls.descripcion.hasError('required')) {
          <mat-error>La descripción es obligatoria.</mat-error>
        }
      </mat-form-field>

      <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
        <mat-label>Monto *</mat-label>
        <mat-icon matPrefix>attach_money</mat-icon>
        <input matInput type="number" min="0" step="0.01"
          formControlName="monto" placeholder="0.00" />
        @if (form.controls.monto.hasError('required')) {
          <mat-error>El monto es obligatorio.</mat-error>
        }
        @if (form.controls.monto.hasError('min')) {
          <mat-error>El monto debe ser mayor a cero.</mat-error>
        }
      </mat-form-field>

      <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
        <mat-label>Fecha *</mat-label>
        <input matInput [matDatepicker]="picker"
          formControlName="fecha" placeholder="dd/mm/aaaa" />
        <mat-datepicker-toggle matSuffix [for]="picker" />
        <mat-datepicker #picker />
        @if (form.controls.fecha.hasError('required')) {
          <mat-error>La fecha es obligatoria.</mat-error>
        }
      </mat-form-field>

      <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
        <mat-label>Pagado por</mat-label>
        <mat-select formControlName="pagado_por">
          <mat-option [value]="null">— Sin asignar —</mat-option>
          @for (u of usuarios(); track u.id) {
            <mat-option [value]="u.id">{{ u.nombre }}</mat-option>
          }
        </mat-select>
      </mat-form-field>

      <div class="efd-checkbox-row">
        <mat-checkbox formControlName="facturable">
          Facturable al cliente
        </mat-checkbox>
      </div>

      <mat-form-field appearance="outline" subscriptSizing="dynamic"
        floatLabel="always" class="sc-field--full">
        <mat-label>URL Comprobante</mat-label>
        <mat-icon matPrefix>attach_file</mat-icon>
        <input matInput formControlName="comprobante_url"
          placeholder="https://…" />
      </mat-form-field>

      <mat-form-field appearance="outline" subscriptSizing="dynamic"
        floatLabel="always" class="sc-field--full">
        <mat-label>Notas</mat-label>
        <textarea matInput formControlName="notas" rows="2"
          placeholder="Observaciones adicionales…"></textarea>
      </mat-form-field>

    </div>
  </form>
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-stroked-button type="button" mat-dialog-close>Cancelar</button>
  <button mat-raised-button color="primary"
    [disabled]="form.invalid || saving()"
    (click)="guardar()">
    @if (saving()) {
      <mat-progress-spinner diameter="18" mode="indeterminate" />
    }
    Guardar
  </button>
</mat-dialog-actions>
```

### 3.4 SCSS Variables

```scss
// expense-form-dialog.component.scss

.efd-content {
  min-width: 480px;
  max-width: 600px;
  padding-top: 0.5rem;
}

.efd-form { padding-bottom: 0.5rem; }

.efd-checkbox-row {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
}
```

---

## 4. CostRatesManagementComponent

### 4.1 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [div.cr-header]                                                        │
│  2 tarifas de costo            [Agregar tarifa  mat-raised-button]      │
│                                                                         │
│  @if (showRateForm())                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  [sc-card cr-form-card]                                           │  │
│  │  [Usuario*] [Tarifa/hora*] [Moneda] [Fecha desde*] [Fecha hasta]  │  │
│  │                                             [Cancelar] [Guardar]  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [mat-progress-bar si loading()]                                        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Usuario       │ Tarifa/h   │ Moneda │ Desde     │ Hasta    │ ⋮  │   │
│  ├───────────────┼────────────┼────────┼───────────┼──────────┼────┤   │
│  │ Juan Andrade  │ $45,000/h  │ COP    │ 01/01/2025│ Vigente  │ ✎⌫ │   │
│  │ María López   │ $38,000/h  │ COP    │ 15/02/2025│ 31/12/25 │ ✎⌫ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [sc-empty-state si no hay tarifas]                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Material Component Mapping

| Elemento UI | Material Component | Clase local |
|---|---|---|
| Header | `div.cr-header` | Patrón sub-lista |
| Botón agregar | `mat-raised-button color="primary"` | — |
| Formulario inline | `sc-card cr-form-card` + `mat-form-field` | `cr-form-card` |
| Usuario en form | `mat-form-field` + `mat-select` | — |
| Tarifa | `mat-form-field` + `input matInput type=number` | — |
| Moneda | `mat-form-field` + `mat-select` | — |
| Fechas | `mat-form-field` + `mat-datepicker` | — |
| Tabla | `mat-table` + `MatSort` | `cr-table` |
| Chip "Vigente" | `mat-chip` con color `budget-success` | `cr-vigente-chip` |
| Acciones | `mat-icon-button` con tooltip | — |
| Empty state | `div.sc-empty-state cr-empty` | — |

### 4.3 Template Snippets Clave

```html
<div class="cr-header">
  <span class="cr-count">{{ rates().length }} tarifas de costo</span>
  <button mat-raised-button color="primary" (click)="showRateForm.set(true)">
    <mat-icon>add</mat-icon> Agregar tarifa
  </button>
</div>

@if (showRateForm()) {
  <div class="sc-card cr-form-card">
    <div class="sc-card__header">
      <mat-icon>monetization_on</mat-icon>
      <span class="sc-card__title">Nueva tarifa de costo</span>
    </div>
    <div class="sc-card__body">
      <form [formGroup]="rateForm" (ngSubmit)="guardarTarifa()">
        <div class="sc-form-grid">

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Miembro del proyecto *</mat-label>
            <mat-select formControlName="usuario">
              @for (m of miembros(); track m.id) {
                <mat-option [value]="m.id">{{ m.nombre }}</mat-option>
              }
            </mat-select>
            @if (rateForm.controls.usuario.hasError('required')) {
              <mat-error>Selecciona un miembro.</mat-error>
            }
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Tarifa por hora *</mat-label>
            <mat-icon matPrefix>attach_money</mat-icon>
            <input matInput type="number" min="0" step="0.01"
              formControlName="tarifa_hora" placeholder="0.00" />
            <span matTextSuffix>/h</span>
            @if (rateForm.controls.tarifa_hora.hasError('required')) {
              <mat-error>La tarifa es obligatoria.</mat-error>
            }
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Moneda</mat-label>
            <mat-select formControlName="moneda">
              @for (m of monedaOptions; track m.value) {
                <mat-option [value]="m.value">{{ m.label }}</mat-option>
              }
            </mat-select>
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Válida desde *</mat-label>
            <input matInput [matDatepicker]="pickerDesde"
              formControlName="fecha_inicio" placeholder="dd/mm/aaaa" />
            <mat-datepicker-toggle matSuffix [for]="pickerDesde" />
            <mat-datepicker #pickerDesde />
            @if (rateForm.controls.fecha_inicio.hasError('required')) {
              <mat-error>La fecha de inicio es obligatoria.</mat-error>
            }
          </mat-form-field>

          <mat-form-field appearance="outline" subscriptSizing="dynamic" floatLabel="always">
            <mat-label>Válida hasta</mat-label>
            <input matInput [matDatepicker]="pickerHasta"
              formControlName="fecha_fin" placeholder="dd/mm/aaaa (opcional)" />
            <mat-datepicker-toggle matSuffix [for]="pickerHasta" />
            <mat-datepicker #pickerHasta />
            <mat-hint>Dejar vacío si la tarifa es indefinida.</mat-hint>
          </mat-form-field>

        </div>
        <div class="form-actions">
          <button mat-stroked-button type="button"
            (click)="showRateForm.set(false)">Cancelar</button>
          <button mat-raised-button color="primary" type="submit"
            [disabled]="rateForm.invalid || saving()">
            @if (saving()) {
              <mat-progress-spinner diameter="18" mode="indeterminate" />
            }
            Guardar tarifa
          </button>
        </div>
      </form>
    </div>
  </div>
}

@if (loading()) { <mat-progress-bar mode="indeterminate" class="cr-progress" /> }

<mat-table [dataSource]="rates()" matSort class="cr-table">

  <ng-container matColumnDef="usuario">
    <mat-header-cell *matHeaderCellDef mat-sort-header>Miembro</mat-header-cell>
    <mat-cell *matCellDef="let row">{{ row.usuario_detail?.nombre }}</mat-cell>
  </ng-container>

  <ng-container matColumnDef="tarifa_hora">
    <mat-header-cell *matHeaderCellDef mat-sort-header class="cr-col-right">
      Tarifa/h
    </mat-header-cell>
    <mat-cell *matCellDef="let row" class="cr-col-right cr-tarifa">
      {{ row.tarifa_hora | currency:row.moneda:'symbol':'1.2-2' }}
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="moneda">
    <mat-header-cell *matHeaderCellDef>Moneda</mat-header-cell>
    <mat-cell *matCellDef="let row">
      <span class="cr-moneda-chip">{{ row.moneda }}</span>
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="fecha_inicio">
    <mat-header-cell *matHeaderCellDef mat-sort-header>Desde</mat-header-cell>
    <mat-cell *matCellDef="let row">
      {{ row.fecha_inicio | date:'dd/MM/yyyy' }}
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="fecha_fin">
    <mat-header-cell *matHeaderCellDef>Hasta</mat-header-cell>
    <mat-cell *matCellDef="let row">
      @if (row.fecha_fin) {
        {{ row.fecha_fin | date:'dd/MM/yyyy' }}
      } @else {
        <mat-chip class="cr-vigente-chip">Vigente</mat-chip>
      }
    </mat-cell>
  </ng-container>

  <ng-container matColumnDef="acciones">
    <mat-header-cell *matHeaderCellDef class="cr-col-acciones"></mat-header-cell>
    <mat-cell *matCellDef="let row" class="cr-col-acciones">
      <button mat-icon-button matTooltip="Editar" (click)="editarTarifa(row)">
        <mat-icon>edit</mat-icon>
      </button>
      <button mat-icon-button color="warn" matTooltip="Eliminar"
        (click)="confirmarEliminar(row)">
        <mat-icon>delete_outline</mat-icon>
      </button>
    </mat-cell>
  </ng-container>

  <mat-header-row *matHeaderRowDef="displayedColumns" />
  <mat-row *matRowDef="let row; columns: displayedColumns;" />
</mat-table>

@if (!loading() && rates().length === 0) {
  <div class="sc-empty-state cr-empty">
    <mat-icon>monetization_on</mat-icon>
    <p class="sc-empty-state__title">Sin tarifas de costo definidas</p>
    <p class="sc-empty-state__subtitle">
      Define las tarifas por hora de los miembros para calcular el costo de mano de obra.
    </p>
    <button mat-raised-button color="primary" (click)="showRateForm.set(true)">
      <mat-icon>add</mat-icon> Agregar tarifa
    </button>
  </div>
}
```

### 4.4 SCSS Variables

```scss
// cost-rates-management.component.scss

.cr-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.cr-count { font-size: 0.875rem; color: var(--sc-text-muted); }
.cr-progress { margin-bottom: -4px; }
.cr-table { width: 100%; border-radius: var(--sc-radius); }
.cr-form-card { margin-bottom: 1rem; }

.cr-tarifa {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  font-weight: 600;
}

.cr-moneda-chip {
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--sc-text-muted);
  background: var(--sc-surface-ground);
  border: 1px solid var(--sc-surface-border);
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
}

.cr-vigente-chip {
  background-color: color-mix(in srgb, var(--sc-success, #66bb6a) 15%, transparent) !important;
  color: var(--sc-success, #66bb6a) !important;
  font-size: 0.6875rem;
  font-weight: 600;
  min-height: 22px;
}

.cr-col-right    { text-align: right !important; justify-content: flex-end !important; }
.cr-col-acciones { width: 96px; justify-content: flex-end !important; }

.cr-empty {
  border: 1px solid var(--sc-surface-border);
  border-top: none;
  border-radius: 0 0 var(--sc-radius) var(--sc-radius);
}
```

---

## 5. BudgetVarianceDashboardComponent

### 5.1 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [mat-card — bvd-status-card]                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  ESTADO PRESUPUESTAL             [chip: DENTRO DEL PRESUPUESTO]   │  │
│  │                                                                   │  │
│  │  ██████████████████████████░░░░░░  $98,500 / $120,000            │  │
│  │  [mat-progress-bar grande, h:16px]   82% ejecutado               │  │
│  │                                                                   │  │
│  │  Umbral de alerta: 80%  ⚠ Se ha superado el umbral               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [div.bvd-evm-grid — 4 columnas]                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │   CPI        │ │   SPI        │ │   CV         │ │   SV         │  │
│  │   1.08       │ │   0.95       │ │  +$4,200     │ │  -$3,100     │  │
│  │  [indicador] │ │  [indicador] │ │  [indicador] │ │  [indicador] │  │
│  │  ● bueno     │ │  ● en riesgo │ │  ● bueno     │ │  ● en riesgo │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │
│                                                                         │
│  [mat-card — bvd-chart-card]                                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Tendencia de costos (últimas 8 semanas)                          │  │
│  │                                                                   │  │
│  │  [div#budget-trend-chart — placeholder para Chart.js]             │  │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░             │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Material Component Mapping

| Elemento UI | Material Component | Clase local |
|---|---|---|
| Tarjeta estado | `mat-card` | `bvd-status-card` |
| Chip estado | `mat-chip` con color dinámico | `bvd-status-chip` |
| Barra progreso grande | `mat-progress-bar mode="determinate"` h:16px | `bvd-main-bar` |
| Aviso umbral | `div.bvd-alert` con `mat-icon warning` | `bvd-alert` |
| Grid EVM | `div.bvd-evm-grid` 4 columnas | `bvd-evm-grid` |
| Tarjeta EVM | `mat-card` | `bvd-evm-card` |
| Indicador color EVM | `span.bvd-evm-dot` con color dinámico | `bvd-evm-dot` |
| Tarjeta chart | `mat-card` | `bvd-chart-card` |
| Canvas Chart.js | `canvas #budgetTrendChart` | `bvd-chart-canvas` |

### 5.3 Template Snippets Clave

```html
<!-- Tarjeta de estado principal -->
<mat-card class="bvd-status-card">
  <mat-card-content>
    <div class="bvd-status-header">
      <span class="bvd-status-title">Estado presupuestal</span>
      <mat-chip
        [style.background-color]="statusColor() + '22'"
        [style.color]="statusColor()"
        class="bvd-status-chip">
        <mat-icon matChipAvatar>{{ statusIcon() }}</mat-icon>
        {{ statusLabel() }}
      </mat-chip>
    </div>

    <div class="bvd-bar-label">
      <span>{{ costoEjecutado() | currency:'COP':'symbol':'1.0-0' }}
        / {{ budget()?.monto_planificado | currency:'COP':'symbol':'1.0-0' }}
      </span>
      <span>{{ porcentajeEjecutado() | number:'1.0-1' }}% ejecutado</span>
    </div>
    <mat-progress-bar
      mode="determinate"
      [value]="porcentajeEjecutado()"
      [color]="progressBarColor()"
      class="bvd-main-bar" />

    @if (superaUmbral()) {
      <div class="bvd-alert">
        <mat-icon>warning</mat-icon>
        <span>
          Se ha superado el umbral de alerta del
          {{ budget()?.umbral_alerta }}%.
        </span>
      </div>
    }
  </mat-card-content>
</mat-card>

<!-- Grid métricas EVM -->
<div class="bvd-evm-grid">
  @for (metric of evmMetrics(); track metric.key) {
    <mat-card class="bvd-evm-card">
      <mat-card-content>
        <span class="bvd-evm-key">{{ metric.label }}</span>
        <span class="bvd-evm-value"
          [style.color]="metric.color">
          {{ metric.value | number:'1.2-2' }}
        </span>
        <span class="bvd-evm-desc">{{ metric.description }}</span>
        <span class="bvd-evm-dot"
          [style.background-color]="metric.color"
          [matTooltip]="metric.tooltip">
        </span>
      </mat-card-content>
    </mat-card>
  }
</div>

<!-- Placeholder Chart.js -->
<mat-card class="bvd-chart-card">
  <mat-card-header>
    <mat-card-title>Tendencia de costos</mat-card-title>
    <mat-card-subtitle>Planificado vs ejecutado por semana</mat-card-subtitle>
  </mat-card-header>
  <mat-card-content>
    <div class="bvd-chart-wrap">
      <canvas #budgetTrendChart class="bvd-chart-canvas"></canvas>
    </div>
  </mat-card-content>
</mat-card>
```

#### Computed de métricas EVM en el componente TS
```typescript
// En el componente — readonly, computed
readonly evmMetrics = computed<EvmMetric[]>(() => {
  const evm = this.evm();
  if (!evm) return [];
  return [
    {
      key: 'cpi',
      label: 'CPI',
      value: evm.cpi,
      description: 'Índice de rendimiento de costo',
      color: evm.cpi >= 1 ? 'var(--budget-success)' : evm.cpi >= 0.8
        ? 'var(--budget-warning)' : 'var(--budget-danger)',
      tooltip: evm.cpi >= 1 ? 'Eficiente en costos' : 'Sobrecosto detectado',
    },
    {
      key: 'spi',
      label: 'SPI',
      value: evm.spi,
      description: 'Índice de rendimiento de cronograma',
      color: evm.spi >= 1 ? 'var(--budget-success)' : evm.spi >= 0.8
        ? 'var(--budget-warning)' : 'var(--budget-danger)',
      tooltip: evm.spi >= 1 ? 'Adelantado en cronograma' : 'Retraso detectado',
    },
    {
      key: 'cv',
      label: 'CV',
      value: evm.cv,
      description: 'Variación de costo',
      color: evm.cv >= 0 ? 'var(--budget-success)' : 'var(--budget-danger)',
      tooltip: evm.cv >= 0 ? 'Bajo presupuesto' : 'Sobre presupuesto',
    },
    {
      key: 'sv',
      label: 'SV',
      value: evm.sv,
      description: 'Variación de cronograma',
      color: evm.sv >= 0 ? 'var(--budget-success)' : 'var(--budget-danger)',
      tooltip: evm.sv >= 0 ? 'Adelantado' : 'Retrasado',
    },
  ];
});
```

### 5.4 SCSS Variables

```scss
// budget-variance-dashboard.component.scss

:host {
  --budget-success: var(--sc-success, #66bb6a);
  --budget-warning: var(--sc-warning, #ffa726);
  --budget-danger:  var(--sc-danger,  #ef5350);
  --budget-info:    var(--sc-primary, #1976d2);
}

.bvd-status-card {
  margin-bottom: 1.25rem;
  border: 1px solid var(--sc-surface-border);
}

.bvd-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.875rem;
}

.bvd-status-title {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sc-text-muted);
}

.bvd-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: var(--sc-text-muted);
  margin-bottom: 0.375rem;
}

.bvd-main-bar {
  height: 16px;
  border-radius: var(--sc-radius);
  margin-bottom: 0.75rem;
}

.bvd-alert {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background-color: color-mix(in srgb, var(--budget-warning) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--budget-warning) 30%, transparent);
  border-radius: var(--sc-radius);
  font-size: 0.875rem;
  color: var(--budget-warning);

  mat-icon { font-size: 1.125rem; width: 1.125rem; height: 1.125rem; }
}

.bvd-evm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.bvd-evm-card {
  border: 1px solid var(--sc-surface-border);
  position: relative;
  overflow: hidden;
}

.bvd-evm-card mat-card-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.875rem 1rem;
}

.bvd-evm-key {
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--sc-text-muted);
}

.bvd-evm-value {
  font-size: 1.75rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.bvd-evm-desc {
  font-size: 0.75rem;
  color: var(--sc-text-muted);
}

.bvd-evm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
}

.bvd-chart-card {
  border: 1px solid var(--sc-surface-border);
  margin-bottom: 1rem;
}

.bvd-chart-wrap {
  position: relative;
  height: 240px;
}

.bvd-chart-canvas {
  width: 100% !important;
  height: 100% !important;
}
```

---

## 6. InvoicePreviewComponent

### 6.1 ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [div.ip-header]                                                        │
│  Vista previa de factura                 [Exportar PDF  mat-raised-btn] │
│                                                                         │
│  [mat-card — ip-invoice-card]                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  PROYECTO: Desarrollo App Móvil           FECHA: 27/03/2026       │  │
│  │  CLIENTE:  Empresa XYZ S.A.S              PERIODO: Ene–Mar 2026   │  │
│  │  ─────────────────────────────────────────────────────────────    │  │
│  │                                                                   │  │
│  │  [mat-table — ip-items-table]                                     │  │
│  │  Descripción         │ Horas/Cant │ Tarifa    │ Subtotal          │  │
│  │  ─────────────────────────────────────────────────────────────    │  │
│  │  Juan A. – Desarrollo│ 40h        │ $45,000/h │ $1,800,000        │  │
│  │  María L. – Diseño   │ 20h        │ $38,000/h │ $760,000          │  │
│  │  Viáticos LATAM      │ 1           │ $380,000  │ $380,000          │  │
│  │  ─────────────────────────────────────────────────────────────    │  │
│  │  [fila total]                              TOTAL: $2,940,000      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [sc-empty-state si no hay items facturables]                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Material Component Mapping

| Elemento UI | Material Component | Clase local |
|---|---|---|
| Header | `div.ip-header` | — |
| Botón exportar | `mat-raised-button color="primary"` con `mat-icon` | — |
| Tarjeta factura | `mat-card` | `ip-invoice-card` |
| Metadata proyecto | `div.ip-meta-grid` | — |
| Tabla items | `mat-table` | `ip-items-table` |
| Fila total | fila especial con clase `ip-total-row` | — |
| Empty state | `div.sc-empty-state ip-empty` | — |

### 6.3 Template Snippets Clave

```html
<div class="ip-header">
  <span class="ip-title">Vista previa de factura</span>
  <button mat-raised-button color="primary"
    [disabled]="exporting() || billableItems().length === 0"
    (click)="exportarPDF()">
    @if (exporting()) {
      <mat-progress-spinner diameter="18" mode="indeterminate" />
    } @else {
      <mat-icon>picture_as_pdf</mat-icon>
    }
    Exportar PDF
  </button>
</div>

@if (loading()) { <mat-progress-bar mode="indeterminate" class="ip-progress" /> }

@if (!loading() && billableItems().length > 0) {
  <mat-card class="ip-invoice-card">
    <mat-card-content>

      <!-- Metadata del proyecto -->
      <div class="ip-meta-grid">
        <div class="ip-meta-item">
          <span class="ip-meta-label">Proyecto</span>
          <span class="ip-meta-value">{{ proyecto()?.nombre }}</span>
        </div>
        <div class="ip-meta-item">
          <span class="ip-meta-label">Fecha emisión</span>
          <span class="ip-meta-value">{{ today | date:'dd/MM/yyyy' }}</span>
        </div>
        <div class="ip-meta-item">
          <span class="ip-meta-label">Cliente</span>
          <span class="ip-meta-value">{{ proyecto()?.cliente_detail?.nombre ?? '—' }}</span>
        </div>
        <div class="ip-meta-item">
          <span class="ip-meta-label">Período</span>
          <span class="ip-meta-value">{{ periodoLabel() }}</span>
        </div>
      </div>

      <mat-divider class="ip-divider" />

      <!-- Tabla de items facturables -->
      <mat-table [dataSource]="billableItems()" class="ip-items-table">

        <ng-container matColumnDef="descripcion">
          <mat-header-cell *matHeaderCellDef>Descripción</mat-header-cell>
          <mat-cell *matCellDef="let row">
            <div class="ip-item-desc">
              <span class="ip-item-name">{{ row.descripcion }}</span>
              <span class="ip-item-type xx-tipo-chip">{{ row.tipo }}</span>
            </div>
          </mat-cell>
        </ng-container>

        <ng-container matColumnDef="cantidad">
          <mat-header-cell *matHeaderCellDef class="ip-col-right">
            Cant.
          </mat-header-cell>
          <mat-cell *matCellDef="let row" class="ip-col-right">
            {{ row.cantidad | number:'1.0-2' }} {{ row.unidad }}
          </mat-cell>
        </ng-container>

        <ng-container matColumnDef="tarifa">
          <mat-header-cell *matHeaderCellDef class="ip-col-right">
            Tarifa
          </mat-header-cell>
          <mat-cell *matCellDef="let row" class="ip-col-right">
            {{ row.tarifa | currency:'COP':'symbol':'1.0-0' }}
          </mat-cell>
        </ng-container>

        <ng-container matColumnDef="subtotal">
          <mat-header-cell *matHeaderCellDef class="ip-col-right">
            Subtotal
          </mat-header-cell>
          <mat-cell *matCellDef="let row" class="ip-col-right ip-subtotal">
            {{ row.subtotal | currency:'COP':'symbol':'1.0-0' }}
          </mat-cell>
        </ng-container>

        <mat-header-row *matHeaderRowDef="displayedColumns" />
        <mat-row *matRowDef="let row; columns: displayedColumns;" />
      </mat-table>

      <!-- Fila de total -->
      <div class="ip-total-row">
        <span class="ip-total-label">TOTAL</span>
        <span class="ip-total-value">
          {{ totalFacturable() | currency:'COP':'symbol':'1.0-0' }}
        </span>
      </div>

    </mat-card-content>
  </mat-card>
}

@if (!loading() && billableItems().length === 0) {
  <div class="sc-empty-state ip-empty">
    <mat-icon>receipt_long</mat-icon>
    <p class="sc-empty-state__title">Sin ítems facturables</p>
    <p class="sc-empty-state__subtitle">
      Registra gastos y horas marcados como "facturable" para generar la vista previa.
    </p>
  </div>
}
```

### 6.4 SCSS Variables

```scss
// invoice-preview.component.scss

.ip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.875rem;
}

.ip-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--sc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ip-progress { margin-bottom: -4px; }

.ip-invoice-card {
  border: 1px solid var(--sc-surface-border);
}

.ip-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.ip-meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.ip-meta-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--sc-text-muted);
}

.ip-meta-value {
  font-size: 0.9375rem;
  font-weight: 500;
}

.ip-divider { margin: 0.75rem 0 0.5rem; }

.ip-items-table { width: 100%; }

.ip-item-desc {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.ip-item-name { font-weight: 500; }

.ip-col-right {
  text-align: right !important;
  justify-content: flex-end !important;
}

.ip-subtotal {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  font-weight: 600;
}

.ip-total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1rem;
  margin-top: 0.25rem;
  background-color: var(--sc-surface-ground);
  border-top: 2px solid var(--sc-primary);
  border-radius: 0 0 var(--sc-radius) var(--sc-radius);
}

.ip-total-label {
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sc-text-muted);
}

.ip-total-value {
  font-size: 1.25rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--sc-primary);
}

.ip-empty {
  border: 1px solid var(--sc-surface-border);
  border-radius: var(--sc-radius);
  margin-top: 1rem;
}
```

---

## 7. Definición de componentes Angular

### 7.1 BudgetManagementComponent

```typescript
// Archivo: budget-management.component.ts
// Selector: app-budget-management

@Component({
  selector: 'app-budget-management',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    // Angular
    ReactiveFormsModule, DecimalPipe, CurrencyPipe, DatePipe,
    // Angular Material
    MatCardModule, MatProgressBarModule, MatTabsModule,
    MatTableModule, MatSortModule, MatChipsModule,
    MatButtonModule, MatIconModule, MatFormFieldModule,
    MatInputModule, MatSelectModule,
    MatProgressSpinnerModule, MatTooltipModule, MatDividerModule,
  ],
})
export class BudgetManagementComponent {
  // Inputs (signals)
  readonly projectId = input.required<string>();

  // Outputs
  readonly budgetApproved = output<Budget>();
  readonly budgetCreated  = output<Budget>();

  // Inyección de dependencias
  private readonly budgetService  = inject(BudgetService);
  private readonly snackBar       = inject(MatSnackBar);
  private readonly dialog         = inject(MatDialog);
  private readonly destroyRef     = inject(DestroyRef);

  // Estado local
  readonly loading           = signal(false);
  readonly loadingRecursos   = signal(false);
  readonly loadingTareas     = signal(false);
  readonly loadingCategorias = signal(false);
  readonly saving            = signal(false);
  readonly showBudgetForm    = signal(false);

  readonly budget         = signal<Budget | null>(null);
  readonly costosRecurso  = signal<CostoBreakdownItem[]>([]);
  readonly costosTarea    = signal<CostoBreakdownItem[]>([]);
  readonly costosCategoria= signal<CostoBreakdownItem[]>([]);

  // Computed
  readonly hasBudget           = computed(() => this.budget() !== null);
  readonly costoEjecutado      = computed(() => this.budget()?.costo_ejecutado ?? 0);
  readonly porcentajeEjecutado = computed(() => {
    const b = this.budget();
    if (!b || b.monto_planificado === 0) return 0;
    return Math.min((b.costo_ejecutado / b.monto_planificado) * 100, 100);
  });
  readonly varianza = computed(() => {
    const b = this.budget();
    if (!b) return 0;
    return b.monto_planificado - b.costo_ejecutado;
  });
  readonly varianzaColor = computed(() => {
    const v = this.varianza();
    if (v > 0) return 'var(--budget-success)';
    if (v === 0) return 'var(--budget-info)';
    return 'var(--budget-danger)';
  });
  readonly progressColor = computed(() => {
    const pct = this.porcentajeEjecutado();
    const umbral = this.budget()?.umbral_alerta ?? 80;
    if (pct >= 100) return 'warn';
    if (pct >= umbral) return 'accent';
    return 'primary';
  });
  readonly isPM = computed(() => /* verificar rol usuario */ false);

  // Columnas tablas
  readonly colsRecurso   = ['nombre', 'planificado', 'ejecutado', 'varianza', 'porcentaje'];
  readonly colsTarea     = ['nombre', 'planificado', 'ejecutado', 'varianza', 'porcentaje'];
  readonly colsCategoria = ['nombre', 'planificado', 'ejecutado', 'varianza', 'porcentaje'];

  // Formulario de presupuesto
  readonly budgetForm = new FormGroup({
    monto_planificado: new FormControl<number | null>(null, [Validators.required, Validators.min(0.01)]),
    moneda:            new FormControl('COP', Validators.required),
    umbral_alerta:     new FormControl(80, [Validators.min(1), Validators.max(100)]),
    notas:             new FormControl(''),
  });

  readonly monedaOptions = [
    { value: 'COP', label: 'COP — Peso colombiano' },
    { value: 'USD', label: 'USD — Dólar americano' },
    { value: 'EUR', label: 'EUR — Euro' },
  ];
}
```

### 7.2 ExpenseListComponent

```typescript
// Archivo: expense-list.component.ts
// Selector: app-expense-list

@Component({
  selector: 'app-expense-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CurrencyPipe, DatePipe,
    MatTableModule, MatSortModule, MatButtonModule, MatIconModule,
    MatChipsModule, MatProgressBarModule, MatTooltipModule,
  ],
})
export class ExpenseListComponent {
  readonly projectId = input.required<string>();

  readonly expenseAdded   = output<Expense>();
  readonly expenseUpdated = output<Expense>();
  readonly expenseDeleted = output<string>();  // id

  private readonly expenseService = inject(ExpenseService);
  private readonly dialog         = inject(MatDialog);
  private readonly snackBar       = inject(MatSnackBar);

  readonly loading  = signal(false);
  readonly expenses = signal<Expense[]>([]);

  readonly displayedColumns = ['fecha', 'categoria', 'descripcion', 'monto', 'facturable', 'pagado_por', 'acciones'];

  // Helpers
  categoryLabel(cat: string): string { /* ... */ return cat; }
  categoryColor(cat: string): string { /* mapeo de categoría → color CSS var */ return 'var(--sc-primary)'; }
}
```

### 7.3 ExpenseFormDialogComponent

```typescript
// Archivo: expense-form-dialog.component.ts
// Selector: app-expense-form-dialog
// Apertura: dialog.open(ExpenseFormDialogComponent, { data: { expense?: Expense, projectId: string }, width: '600px' })

interface ExpenseFormDialogData {
  expense:   Expense | null;
  projectId: string;
}

@Component({
  selector: 'app-expense-form-dialog',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule, DatePipe,
    MatDialogModule, MatButtonModule, MatFormFieldModule, MatInputModule,
    MatSelectModule, MatDatepickerModule, MatCheckboxModule,
    MatIconModule, MatProgressSpinnerModule,
  ],
})
export class ExpenseFormDialogComponent {
  readonly data = inject<ExpenseFormDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef    = inject(MatDialogRef<ExpenseFormDialogComponent>);
  private readonly expenseService = inject(ExpenseService);
  private readonly snackBar     = inject(MatSnackBar);

  readonly saving   = signal(false);
  readonly usuarios = signal<Usuario[]>([]);

  readonly form = new FormGroup({
    categoria:       new FormControl('', Validators.required),
    descripcion:     new FormControl('', [Validators.required, Validators.maxLength(300)]),
    monto:           new FormControl<number | null>(null, [Validators.required, Validators.min(0.01)]),
    fecha:           new FormControl<Date | null>(null, Validators.required),
    pagado_por:      new FormControl<string | null>(null),
    facturable:      new FormControl(false),
    comprobante_url: new FormControl(''),
    notas:           new FormControl(''),
  });

  readonly categoriaOptions = [
    { value: 'labor',      label: 'Mano de obra' },
    { value: 'material',   label: 'Materiales' },
    { value: 'software',   label: 'Software / Licencias' },
    { value: 'viaticos',   label: 'Viáticos' },
    { value: 'consultor',  label: 'Consultoría externa' },
    { value: 'otro',       label: 'Otro' },
  ];
}
```

### 7.4 CostRatesManagementComponent

```typescript
// Archivo: cost-rates-management.component.ts
// Selector: app-cost-rates-management

@Component({
  selector: 'app-cost-rates-management',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule, CurrencyPipe, DatePipe,
    MatTableModule, MatSortModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatDatepickerModule, MatChipsModule, MatProgressBarModule,
    MatProgressSpinnerModule, MatTooltipModule,
  ],
})
export class CostRatesManagementComponent {
  readonly projectId = input.required<string>();

  readonly rateAdded   = output<CostRate>();
  readonly rateUpdated = output<CostRate>();
  readonly rateDeleted = output<string>();

  private readonly costRateService = inject(CostRateService);
  private readonly dialog          = inject(MatDialog);
  private readonly snackBar        = inject(MatSnackBar);

  readonly loading       = signal(false);
  readonly saving        = signal(false);
  readonly showRateForm  = signal(false);
  readonly editingRate   = signal<CostRate | null>(null);
  readonly rates         = signal<CostRate[]>([]);
  readonly miembros      = signal<Usuario[]>([]);

  readonly displayedColumns = ['usuario', 'tarifa_hora', 'moneda', 'fecha_inicio', 'fecha_fin', 'acciones'];

  readonly rateForm = new FormGroup({
    usuario:      new FormControl<string | null>(null, Validators.required),
    tarifa_hora:  new FormControl<number | null>(null, [Validators.required, Validators.min(0.01)]),
    moneda:       new FormControl('COP', Validators.required),
    fecha_inicio: new FormControl<Date | null>(null, Validators.required),
    fecha_fin:    new FormControl<Date | null>(null),
  });

  readonly monedaOptions = [
    { value: 'COP', label: 'COP' },
    { value: 'USD', label: 'USD' },
    { value: 'EUR', label: 'EUR' },
  ];
}
```

### 7.5 BudgetVarianceDashboardComponent

```typescript
// Archivo: budget-variance-dashboard.component.ts
// Selector: app-budget-variance-dashboard

interface EvmMetric {
  key:         string;
  label:       string;
  value:       number;
  description: string;
  color:       string;
  tooltip:     string;
}

@Component({
  selector: 'app-budget-variance-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe, CurrencyPipe,
    MatCardModule, MatProgressBarModule, MatChipsModule,
    MatIconModule, MatButtonModule, MatTooltipModule, MatDividerModule,
  ],
})
export class BudgetVarianceDashboardComponent implements AfterViewInit {
  readonly projectId = input.required<string>();

  private readonly budgetService = inject(BudgetService);

  readonly loading  = signal(false);
  readonly budget   = signal<Budget | null>(null);
  readonly evm      = signal<EvmData | null>(null);
  readonly trendData = signal<BudgetTrendPoint[]>([]);

  // Referencia al canvas de Chart.js
  @ViewChild('budgetTrendChart') chartRef!: ElementRef<HTMLCanvasElement>;

  readonly superaUmbral = computed(() => {
    const b = this.budget();
    if (!b) return false;
    return (b.costo_ejecutado / b.monto_planificado) * 100 >= b.umbral_alerta;
  });

  readonly statusLabel = computed(() => {
    const pct = this.porcentajeEjecutado();
    const umbral = this.budget()?.umbral_alerta ?? 80;
    if (pct >= 100) return 'Sobre presupuesto';
    if (pct >= umbral) return 'En riesgo';
    return 'Dentro del presupuesto';
  });

  readonly statusColor = computed(() => {
    const pct = this.porcentajeEjecutado();
    const umbral = this.budget()?.umbral_alerta ?? 80;
    if (pct >= 100) return 'var(--budget-danger)';
    if (pct >= umbral) return 'var(--budget-warning)';
    return 'var(--budget-success)';
  });

  readonly statusIcon = computed(() => {
    const pct = this.porcentajeEjecutado();
    const umbral = this.budget()?.umbral_alerta ?? 80;
    if (pct >= 100) return 'trending_up';
    if (pct >= umbral) return 'warning';
    return 'check_circle';
  });

  readonly porcentajeEjecutado = computed(() => {
    const b = this.budget();
    if (!b || b.monto_planificado === 0) return 0;
    return (b.costo_ejecutado / b.monto_planificado) * 100;
  });

  readonly progressBarColor = computed(() => {
    const pct = this.porcentajeEjecutado();
    const umbral = this.budget()?.umbral_alerta ?? 80;
    if (pct >= 100) return 'warn';
    if (pct >= umbral) return 'accent';
    return 'primary';
  });

  readonly evmMetrics = computed<EvmMetric[]>(() => {
    // ver snippet TypeScript en sección 5.3
    return [];
  });

  // El chart de tendencia se inicializa en ngAfterViewInit via Chart.js
}
```

### 7.6 InvoicePreviewComponent

```typescript
// Archivo: invoice-preview.component.ts
// Selector: app-invoice-preview

interface BillableItem {
  descripcion: string;
  tipo:        'labor' | 'gasto';
  cantidad:    number;
  unidad:      string;
  tarifa:      number;
  subtotal:    number;
  moneda:      string;
}

@Component({
  selector: 'app-invoice-preview',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CurrencyPipe, DecimalPipe, DatePipe,
    MatCardModule, MatTableModule, MatButtonModule, MatIconModule,
    MatProgressBarModule, MatProgressSpinnerModule,
    MatDividerModule, MatTooltipModule,
  ],
})
export class InvoicePreviewComponent {
  readonly projectId = input.required<string>();

  private readonly invoiceService = inject(InvoiceService);
  private readonly snackBar       = inject(MatSnackBar);

  readonly loading       = signal(false);
  readonly exporting     = signal(false);
  readonly proyecto      = signal<Proyecto | null>(null);
  readonly billableItems = signal<BillableItem[]>([]);

  readonly today = new Date();

  readonly displayedColumns = ['descripcion', 'cantidad', 'tarifa', 'subtotal'];

  readonly totalFacturable = computed(() =>
    this.billableItems().reduce((sum, item) => sum + item.subtotal, 0)
  );

  readonly periodoLabel = computed(() => {
    // Deriva el período de los items
    return '—';
  });
}
```

---

## 8. Integración en proyecto-detail: tab "Presupuesto"

### 8.1 Ubicación en el mat-tab-group

El nuevo tab se inserta entre "Analítica" y "Baselines" (posición 5 del grupo existente), usando `@defer (on viewport)` para carga diferida:

```html
<!-- En proyecto-detail.component.html, dentro de mat-tab-group -->

<!-- Tab: Presupuesto (NUEVO — Feature 7) -->
<mat-tab>
  <ng-template mat-tab-label>
    <mat-icon class="pd-tab-icon">account_balance</mat-icon>
    Presupuesto
    @if (budget()?.aprobado) {
      <mat-icon class="pd-tab-badge-icon pd-tab-badge-icon--ok"
        matTooltip="Presupuesto aprobado">
        verified
      </mat-icon>
    }
  </ng-template>

  <div class="pd-tab-content">
    @defer (on viewport) {

      <!-- Pestañas internas del módulo presupuesto -->
      <mat-tab-group animationDuration="200ms" class="pd-budget-tabs">

        <mat-tab label="Resumen">
          <app-budget-management [projectId]="proyecto()!.id" />
        </mat-tab>

        <mat-tab label="Gastos">
          <app-expense-list [projectId]="proyecto()!.id" />
        </mat-tab>

        <mat-tab label="Tarifas">
          <app-cost-rates-management [projectId]="proyecto()!.id" />
        </mat-tab>

        <mat-tab label="Varianza EVM">
          <app-budget-variance-dashboard [projectId]="proyecto()!.id" />
        </mat-tab>

        <mat-tab label="Pre-factura">
          <app-invoice-preview [projectId]="proyecto()!.id" />
        </mat-tab>

      </mat-tab-group>

    } @placeholder {
      <div class="pd-tab-placeholder">
        <mat-progress-bar mode="indeterminate" />
      </div>
    } @loading (minimum 300ms) {
      <mat-progress-bar mode="indeterminate" />
    }
  </div>
</mat-tab>
```

### 8.2 Imports adicionales en proyecto-detail

```typescript
// Agregar a imports[] de proyecto-detail.component.ts:
BudgetManagementComponent,
ExpenseListComponent,
CostRatesManagementComponent,
BudgetVarianceDashboardComponent,
InvoicePreviewComponent,
```

---

## 9. Estados vacíos — Especificación completa

| Componente | Ícono | Título | Subtítulo | CTA |
|---|---|---|---|---|
| BudgetManagement (sin presupuesto) | `account_balance` | Sin presupuesto definido | Define el presupuesto del proyecto para habilitar el seguimiento de costos. | Definir presupuesto |
| BudgetManagement — tab Por Recurso | `people_outline` | Sin datos de costo por recurso | No hay tarifas de costo o horas registradas para los miembros. | — |
| BudgetManagement — tab Por Tarea | `task_alt` | Sin datos de costo por tarea | Las tareas no tienen horas o gastos asociados aún. | — |
| BudgetManagement — tab Por Categoría | `category` | Sin datos por categoría | Registra gastos con categoría para ver el desglose aquí. | — |
| ExpenseList | `receipt_long` | Sin gastos registrados | Registra los gastos del proyecto para mantener el seguimiento de costos. | Registrar gasto |
| CostRatesManagement | `monetization_on` | Sin tarifas de costo definidas | Define las tarifas por hora de los miembros para calcular el costo de mano de obra. | Agregar tarifa |
| InvoicePreview | `receipt_long` | Sin ítems facturables | Registra gastos y horas marcados como "facturable" para generar la vista previa. | — |

### 9.1 HTML canónico del empty state (patrón del proyecto)

```html
<div class="sc-empty-state [componente]-empty">
  <mat-icon class="sc-empty-state__icon">[icono]</mat-icon>
  <p class="sc-empty-state__title">[Título]</p>
  <p class="sc-empty-state__subtitle">[Subtítulo]</p>
  @if (cta) {
    <button mat-raised-button color="primary" (click)="ctaAction()">
      <mat-icon>add</mat-icon> [Label CTA]
    </button>
  }
</div>
```

El elemento `[componente]-empty` agrega siempre:
```scss
.[componente]-empty {
  border: 1px solid var(--sc-surface-border);
  border-top: none;          // cuando sigue a una tabla
  border-radius: 0 0 var(--sc-radius) var(--sc-radius);
}
// O, si no hay tabla previa:
.[componente]-empty {
  border: 1px solid var(--sc-surface-border);
  border-radius: var(--sc-radius);
  margin-top: 1rem;
}
```

---

## 10. Flujos de navegación entre estados

### 10.1 Flujo global del módulo de presupuesto

```
proyecto-detail → Tab "Presupuesto"
        │
        ▼ @defer carga diferida
  BudgetManagementComponent init
        │
   presupuesto?
   ┌─── NO ──────────────────────────────────────────────┐
   │  sc-empty-state + CTA "Definir presupuesto"         │
   │  → click → showBudgetForm.set(true)                 │
   │  → submit → POST /api/projects/{id}/budget/         │
   │  → snack-success → hasBudget.set(true)              │
   │  → BudgetManagement muestra resumen + tabs           │
   └─────────────────────────────────────────────────────┘
   ┌─── SI ──────────────────────────────────────────────┐
   │  Resumen KPIs                                        │
   │  mat-tab-group desglose: Recurso / Tarea / Categoría │
   │  PM: botón "Aprobar presupuesto"                     │
   │    → ConfirmDialog → approve() → snack-success       │
   └─────────────────────────────────────────────────────┘
```

### 10.2 Flujo CRUD de gastos

```
Tab "Gastos" → ExpenseListComponent
        │
   gastos?
   ┌─── NO ──────────────────────────────────────────────┐
   │  sc-empty-state → click "Registrar gasto"           │
   └─────────────────────────────────────────────────────┘
        │
   click "Registrar gasto" (header o empty state)
        │
        ▼
  dialog.open(ExpenseFormDialogComponent)
        │
  afterClosed: { saved: true, expense }
        │
        ▼
  expenseService.create/update → reload expenses()
  snack-success → expenses() reactualizado
        │
  click "Eliminar fila"
        │
        ▼
  ConfirmDialogComponent
  → confirm → expenseService.delete(id)
  → snack-success → expenses() sin el item
```

### 10.3 Flujo CRUD de tarifas

```
Tab "Tarifas" → CostRatesManagementComponent
        │
  click "Agregar tarifa" → showRateForm.set(true)
  [Formulario inline aparece encima de la tabla]
        │
  submit → costRateService.create(rateForm.value)
  → snack-success → showRateForm.set(false) → reload rates()
        │
  click "Editar" en fila
  → editingRate.set(row) → showRateForm.set(true)
  → formulario pre-rellenado con valores de la tarifa
        │
  submit → costRateService.update(id, rateForm.value)
  → snack-success → reload rates()
```

---

## 11. Checklist de calidad para implementación

Verificar antes de entregar cada componente:

- [ ] `ChangeDetectionStrategy.OnPush` en todos los componentes
- [ ] `inject()` para DI — cero constructor injection
- [ ] `input()` y `output()` — cero `@Input` / `@Output` decoradores
- [ ] `signal()` para estado local — cero propiedades mutables sin signal
- [ ] `computed()` para derivaciones — cero getters con lógica en plantilla
- [ ] `@if` / `@for` — cero `*ngIf` / `*ngFor`
- [ ] `mat-table` (no `table mat-table`), `mat-header-cell` (no `th`)
- [ ] `mat-progress-bar` para loading en listas — cero spinners centrados
- [ ] Empty states con `sc-empty-state` **fuera del mat-table**
- [ ] `mat-form-field appearance="outline"` en todos los campos
- [ ] Errores de validación con `@if` dentro de `mat-form-field`
- [ ] Eliminaciones vía `MatDialog` con `ConfirmDialogComponent`
- [ ] Feedback vía `MatSnackBar` con `panelClass: ['snack-success'|'snack-error']`
- [ ] SCSS usa solo `var(--sc-*)` y `var(--budget-*)` — cero colores hardcodeados
- [ ] Montos monetarios con `| currency` pipe — cero formateo manual
- [ ] Fechas con `| date` pipe — cero `toString()` ni `toLocaleDateString()`
- [ ] `takeUntilDestroyed(this.destroyRef)` en todas las suscripciones
- [ ] Tab "Presupuesto" usa `@defer (on viewport)` en proyecto-detail

---

*Documento generado por UI Designer · ValMen Tech · 2026-03-27*
