# FEATURE-5-UI-WIREFRAMES.md
# Reporting & Analytics — Especificación de Wireframes UI
# SaiSuite · ValMen Tech · Angular Material 18 · Chart.js

**Fecha:** 27 Marzo 2026
**Feature:** #5 — Reporting & Analytics
**Framework UI:** Angular Material (OBLIGATORIO — nunca PrimeNG, Bootstrap ni Tailwind)
**Librería de gráficos:** Chart.js (`npm install chart.js`)
**Referencia canónica de estilo:** `proyecto-list` component

---

## PRERREQUISITOS

Antes de implementar cualquier componente de esta feature, leer:
- `docs/standards/UI-UX-STANDARDS.md` (completo)
- `frontend/src/app/features/proyectos/components/proyecto-list/` (referencia canónica)
- `frontend/src/app/features/proyectos/components/proyecto-detail/` (patrón de tabs)

---

## 1. PROJECT DASHBOARD COMPONENT

### 1.1 Wireframe ASCII — Layout Completo (Desktop 1280px+)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  div.sc-page                                                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ div.sc-page-header                                                      │   │
│  │  h1.sc-page-header__title   Analytics: [Nombre del Proyecto]           │   │
│  │                               [mat-icon-button refresh] [mat-icon-button│   │
│  │                                export_notes "Exportar PDF"]             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ div.pad-filters-card.sc-card   (filtros)                               │   │
│  │  [mat-select "Período"        ] [mat-select "Granularidad"  ]          │   │
│  │  [mat-date-range-input    Rango personalizado                ]          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  @if (loading()) { <mat-progress-bar mode="indeterminate" class="pad-progress"/>}│
│                                                                                 │
│  <!-- KPI Cards — CSS Grid 4 columnas -->                                      │
│  div.pad-kpi-grid                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  mat-card    │  │  mat-card    │  │  mat-card    │  │  mat-card    │       │
│  │ .pad-kpi-card│  │ .pad-kpi-card│  │ .pad-kpi-card│  │.pad-kpi-card │       │
│  │              │  │              │  │              │  │              │       │
│  │ mat-icon     │  │ mat-icon     │  │ mat-icon     │  │ mat-icon     │       │
│  │ task_alt     │  │ schedule     │  │ trending_up  │  │ attach_money │       │
│  │              │  │              │  │              │  │              │       │
│  │ Completud    │  │ On-Time      │  │ Velocidad    │  │ Presupuesto  │       │
│  │ span.pad-kpi │  │ span.pad-kpi │  │ span.pad-kpi │  │ span.pad-kpi │       │
│  │ __value      │  │ __value      │  │ __value      │  │ __value      │       │
│  │   85%        │  │   72%        │  │  12/sem      │  │   -5%        │       │
│  │              │  │              │  │              │  │              │       │
│  │ span semáforo│  │ span semáforo│  │ span semáforo│  │ span semáforo│       │
│  │ .pad-kpi__   │  │ .pad-kpi__   │  │ .pad-kpi__   │  │ .pad-kpi__   │       │
│  │ trend-up     │  │ trend-warn   │  │ trend-up     │  │ trend-danger │       │
│  │ vs período   │  │ vs período   │  │ vs período   │  │ vs período   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                                 │
│  <!-- Gráficos — CSS Grid 2x2 -->                                              │
│  div.pad-charts-grid                                                            │
│  ┌────────────────────────────┐  ┌────────────────────────────┐               │
│  │  mat-card.pad-chart-card   │  │  mat-card.pad-chart-card   │               │
│  │  mat-card-header           │  │  mat-card-header           │               │
│  │    "Burn Down"             │  │    "Velocidad del equipo"  │               │
│  │    mat-icon-button refresh │  │    mat-icon-button refresh │               │
│  │  mat-card-content          │  │  mat-card-content          │               │
│  │  div.pad-chart-container   │  │  div.pad-chart-container   │               │
│  │  ┌──────────────────────┐  │  │  ┌──────────────────────┐  │               │
│  │  │  canvas#burnDown     │  │  │  │  canvas#velocity     │  │               │
│  │  │  (Chart.js Line)     │  │  │  │  (Chart.js Bar)      │  │               │
│  │  └──────────────────────┘  │  │  └──────────────────────┘  │               │
│  └────────────────────────────┘  └────────────────────────────┘               │
│  ┌────────────────────────────┐  ┌────────────────────────────┐               │
│  │  mat-card.pad-chart-card   │  │  mat-card.pad-chart-card   │               │
│  │  mat-card-header           │  │  mat-card-header           │               │
│  │    "Distribución de tareas"│  │    "Utilización de recursos│               │
│  │    mat-icon-button refresh │  │    mat-icon-button refresh │               │
│  │  mat-card-content          │  │  mat-card-content          │               │
│  │  div.pad-chart-container   │  │  div.pad-chart-container   │               │
│  │  ┌──────────────────────┐  │  │  ┌──────────────────────┐  │               │
│  │  │  canvas#taskDist     │  │  │  │  canvas#resourceUtil  │  │               │
│  │  │  (Chart.js Doughnut) │  │  │  │  (Chart.js Bar Horiz)│  │               │
│  │  └──────────────────────┘  │  │  └──────────────────────┘  │               │
│  └────────────────────────────┘  └────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Estructura HTML Angular Material

```html
<!-- app-project-analytics-dashboard -->
<div class="sc-page">

  <!-- Header -->
  <div class="sc-page-header">
    <h1 class="sc-page-header__title">
      Analytics: {{ proyectoNombre() }}
    </h1>
    <div class="pad-header-actions">
      <button mat-icon-button
              matTooltip="Actualizar datos"
              (click)="refresh()"
              [disabled]="loading()"
              aria-label="Actualizar dashboard">
        <mat-icon>refresh</mat-icon>
      </button>
      <button mat-stroked-button
              (click)="exportarPDF()"
              [disabled]="loading()"
              aria-label="Exportar reporte en PDF">
        <mat-icon>picture_as_pdf</mat-icon>
        Exportar PDF
      </button>
    </div>
  </div>

  <!-- Filtros -->
  <div class="pad-filters-card sc-card">
    <mat-form-field appearance="outline" subscriptSizing="dynamic" class="pad-filter">
      <mat-label>Período</mat-label>
      <mat-select [ngModel]="periodoPreset()"
                  (ngModelChange)="periodoPreset.set($event); onPeriodoChange()">
        <mat-option value="current_month">Mes actual</mat-option>
        <mat-option value="last_month">Mes anterior</mat-option>
        <mat-option value="quarter">Trimestre</mat-option>
        <mat-option value="project_life">Duración del proyecto</mat-option>
        <mat-option value="custom">Personalizado</mat-option>
      </mat-select>
    </mat-form-field>

    @if (periodoPreset() === 'custom') {
      <mat-form-field appearance="outline" subscriptSizing="dynamic" class="pad-date-range">
        <mat-label>Rango personalizado</mat-label>
        <mat-date-range-input [rangePicker]="rangePicker">
          <input matStartDate placeholder="Inicio" [ngModel]="fechaInicio()"
                 (ngModelChange)="fechaInicio.set($event)" />
          <input matEndDate placeholder="Fin" [ngModel]="fechaFin()"
                 (ngModelChange)="fechaFin.set($event); onFechaChange()" />
        </mat-date-range-input>
        <mat-datepicker-toggle matIconSuffix [for]="rangePicker" />
        <mat-date-range-picker #rangePicker />
      </mat-form-field>
    }

    <mat-form-field appearance="outline" subscriptSizing="dynamic" class="pad-filter">
      <mat-label>Granularidad</mat-label>
      <mat-select [ngModel]="granularidad()"
                  (ngModelChange)="granularidad.set($event); onGranularidadChange()">
        <mat-option value="week">Semana</mat-option>
        <mat-option value="month">Mes</mat-option>
      </mat-select>
    </mat-form-field>
  </div>

  <!-- Progress bar (loading state) — NUNCA spinner centrado -->
  @if (loading()) {
    <mat-progress-bar mode="indeterminate" class="pad-progress" />
  }

  <!-- KPI Cards -->
  @if (!loading() && kpis()) {
    <div class="pad-kpi-grid" role="region" aria-label="Indicadores clave del proyecto">
      <mat-card class="pad-kpi-card" tabindex="0">
        <mat-card-content>
          <div class="pad-kpi-icon-wrap">
            <mat-icon class="pad-kpi-icon">task_alt</mat-icon>
          </div>
          <span class="pad-kpi-label">Completud</span>
          <span class="pad-kpi-value"
                [class]="kpiSemaforoClass(kpis()!.completud)">
            {{ kpis()!.completud | number:'1.0-1' }}%
          </span>
          <span class="pad-kpi-trend">
            {{ kpis()!.completud_trend > 0 ? '+' : '' }}{{ kpis()!.completud_trend | number:'1.0-1' }}% vs período anterior
          </span>
        </mat-card-content>
      </mat-card>

      <mat-card class="pad-kpi-card" tabindex="0">
        <mat-card-content>
          <div class="pad-kpi-icon-wrap">
            <mat-icon class="pad-kpi-icon">schedule</mat-icon>
          </div>
          <span class="pad-kpi-label">Tareas On-Time</span>
          <span class="pad-kpi-value"
                [class]="kpiSemaforoClass(kpis()!.on_time_pct)">
            {{ kpis()!.on_time_pct | number:'1.0-1' }}%
          </span>
          <span class="pad-kpi-trend">
            {{ kpis()!.tareas_on_time }} de {{ kpis()!.tareas_total }} tareas
          </span>
        </mat-card-content>
      </mat-card>

      <mat-card class="pad-kpi-card" tabindex="0">
        <mat-card-content>
          <div class="pad-kpi-icon-wrap">
            <mat-icon class="pad-kpi-icon">trending_up</mat-icon>
          </div>
          <span class="pad-kpi-label">Velocidad</span>
          <span class="pad-kpi-value pad-kpi-value--neutral">
            {{ kpis()!.velocidad_promedio | number:'1.1-1' }}/sem
          </span>
          <span class="pad-kpi-trend">tareas completadas por semana</span>
        </mat-card-content>
      </mat-card>

      <mat-card class="pad-kpi-card" tabindex="0">
        <mat-card-content>
          <div class="pad-kpi-icon-wrap">
            <mat-icon class="pad-kpi-icon">attach_money</mat-icon>
          </div>
          <span class="pad-kpi-label">Variación Presupuesto</span>
          <span class="pad-kpi-value"
                [class]="presupuestoClass(kpis()!.variacion_presupuesto)">
            {{ kpis()!.variacion_presupuesto > 0 ? '+' : '' }}{{ kpis()!.variacion_presupuesto | number:'1.0-1' }}%
          </span>
          <span class="pad-kpi-trend">
            {{ formatCurrency(kpis()!.gasto_real) }} de {{ formatCurrency(kpis()!.presupuesto_total) }}
          </span>
        </mat-card-content>
      </mat-card>
    </div>
  }

  <!-- Empty state KPIs — cuando no hay datos -->
  @if (!loading() && !kpis()) {
    <div class="sc-empty-state pad-empty">
      <mat-icon>analytics</mat-icon>
      <p>No hay datos analíticos para el período seleccionado.</p>
      <button mat-stroked-button (click)="onPeriodoChange()">
        <mat-icon>refresh</mat-icon> Reintentar
      </button>
    </div>
  }

  <!-- Grid de gráficos 2x2 -->
  @if (!loading() && kpis()) {
    <div class="pad-charts-grid" role="region" aria-label="Gráficos analíticos">

      <!-- Burn Down Chart -->
      <mat-card class="pad-chart-card">
        <mat-card-header>
          <mat-card-title>Burn Down</mat-card-title>
          <mat-card-subtitle>Horas ideales vs reales</mat-card-subtitle>
          <button mat-icon-button class="pad-chart-refresh"
                  matTooltip="Actualizar gráfico"
                  (click)="refreshBurnDown()"
                  aria-label="Actualizar gráfico burn down">
            <mat-icon>refresh</mat-icon>
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="pad-chart-container" role="img" aria-label="Gráfico de burn down del proyecto">
            <canvas #burnDownCanvas id="burnDownChart"></canvas>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Velocity Chart -->
      <mat-card class="pad-chart-card">
        <mat-card-header>
          <mat-card-title>Velocidad del equipo</mat-card-title>
          <mat-card-subtitle>Tareas completadas por semana</mat-card-subtitle>
          <button mat-icon-button class="pad-chart-refresh"
                  matTooltip="Actualizar gráfico"
                  (click)="refreshVelocity()"
                  aria-label="Actualizar gráfico de velocidad">
            <mat-icon>refresh</mat-icon>
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="pad-chart-container" role="img" aria-label="Gráfico de velocidad del equipo por semana">
            <canvas #velocityCanvas id="velocityChart"></canvas>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Task Distribution Chart -->
      <mat-card class="pad-chart-card">
        <mat-card-header>
          <mat-card-title>Distribución de tareas</mat-card-title>
          <mat-card-subtitle>Por estado actual</mat-card-subtitle>
          <button mat-icon-button class="pad-chart-refresh"
                  matTooltip="Actualizar gráfico"
                  (click)="refreshTaskDist()"
                  aria-label="Actualizar gráfico de distribución">
            <mat-icon>refresh</mat-icon>
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="pad-chart-container" role="img" aria-label="Gráfico de distribución de tareas por estado">
            <canvas #taskDistCanvas id="taskDistChart"></canvas>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Resource Utilization Chart -->
      <mat-card class="pad-chart-card">
        <mat-card-header>
          <mat-card-title>Utilización de recursos</mat-card-title>
          <mat-card-subtitle>% de capacidad asignada por persona</mat-card-subtitle>
          <button mat-icon-button class="pad-chart-refresh"
                  matTooltip="Actualizar gráfico"
                  (click)="refreshResourceUtil()"
                  aria-label="Actualizar gráfico de utilización">
            <mat-icon>refresh</mat-icon>
          </button>
        </mat-card-header>
        <mat-card-content>
          <div class="pad-chart-container" role="img" aria-label="Gráfico horizontal de utilización de recursos del equipo">
            <canvas #resourceUtilCanvas id="resourceUtilChart"></canvas>
          </div>
        </mat-card-content>
      </mat-card>

    </div>
  }

</div>
```

### 1.3 SCSS del componente (`project-analytics-dashboard.component.scss`)

```scss
// -- Filtros
.pad-filters-card {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  align-items: center;
  padding: 0.875rem 1rem;
  margin-bottom: 1rem;
}
.pad-filter      { width: 180px; flex-shrink: 0; }
.pad-date-range  { flex: 1; min-width: 260px; }

// -- Progress bar
.pad-progress {
  margin-bottom: -4px;
  border-radius: var(--sc-radius) var(--sc-radius) 0 0;
}

// -- KPI Grid
.pad-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.pad-kpi-card {
  cursor: default;
  transition: box-shadow 200ms ease;
  &:hover { box-shadow: 0 4px 12px rgb(0 0 0 / 0.12); }
}
.pad-kpi-card mat-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.25rem;
  padding: 1.25rem 1rem;
}
.pad-kpi-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--sc-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}
.pad-kpi-icon   { color: var(--sc-primary); font-size: 24px; }
.pad-kpi-label  { font-size: 0.75rem; font-weight: 600; color: var(--sc-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.pad-kpi-value  { font-size: 1.875rem; font-weight: 700; line-height: 1; }
.pad-kpi-trend  { font-size: 0.75rem; color: var(--sc-text-muted); }

// Semáforo de valores KPI
.pad-kpi-value--success { color: #2e7d32; }
.pad-kpi-value--warning { color: #f57f17; }
.pad-kpi-value--danger  { color: #c62828; }
.pad-kpi-value--neutral { color: var(--sc-primary); }

// -- Charts Grid
.pad-charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
.pad-chart-card {
  position: relative;
}
.pad-chart-card mat-card-header {
  padding-right: 48px; // espacio para botón refresh
}
.pad-chart-refresh {
  position: absolute;
  top: 8px;
  right: 8px;
}
.pad-chart-container {
  position: relative;
  height: 280px; // altura fija — evita layout shift
  width: 100%;
}
.pad-chart-container canvas {
  max-height: 100%;
}

// -- Empty state
.pad-empty {
  border: 1px solid var(--sc-surface-border);
  border-radius: var(--sc-radius);
}

// -- Header actions
.pad-header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

// -- Responsive: Tablet (768px)
@media (max-width: 1023px) {
  .pad-kpi-grid     { grid-template-columns: repeat(2, 1fr); }
  .pad-charts-grid  { grid-template-columns: 1fr; }
  .pad-chart-container { height: 240px; }
}

// -- Responsive: Mobile (hasta 639px)
@media (max-width: 639px) {
  .pad-kpi-grid    { grid-template-columns: 1fr; }
  .pad-charts-grid { grid-template-columns: 1fr; }
  .pad-filter      { width: 100%; }
  .pad-date-range  { width: 100%; }
  .pad-chart-container { height: 200px; }
}
```

### 1.4 Estados del componente

| Estado | Comportamiento visual |
|---|---|
| **Loading** | `mat-progress-bar` delgado encima de la sección de KPI cards; cards con `mat-card` muestran skeleton (opacity 0.4). Nunca spinner centrado. |
| **Vacío** | `sc-empty-state` con `mat-icon` `analytics` + mensaje + botón Reintentar. FUERA de la grilla de charts. |
| **Error de red** | `MatSnackBar` con `panelClass: ['snack-error']`, duración 5000ms. El botón refresh queda habilitado. |
| **Refresh parcial** | Solo el gráfico afectado muestra `mat-progress-bar` en su `mat-card-header`. El resto permanece visible. |
| **Dark mode** | Las clases `.dark-theme` en `<body>` propagan via CSS variables `var(--sc-*)`. Los colores de Chart.js se leen desde `getComputedStyle` en el momento de inicializar cada chart. |

### 1.5 Responsive — comportamiento por breakpoint

| Breakpoint | KPI grid | Charts grid | Chart height |
|---|---|---|---|
| Desktop 1280px+ | 4 columnas | 2x2 | 280px |
| Tablet 1024–1279px | 4 columnas | 2x2 | 260px |
| Tablet 768–1023px | 2 columnas | 1 columna | 240px |
| Mobile 640–767px | 2 columnas | 1 columna | 220px |
| Mobile < 640px | 1 columna | 1 columna | 200px |

---

## 2. OVERVIEW DASHBOARD COMPONENT

### 2.1 Wireframe ASCII — Tabla comparativa de proyectos

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  div.sc-page                                                                    │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ div.sc-page-header                                                       │  │
│  │  h1  "Resumen de proyectos"                  [export_notes "Exportar"]  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ div.pod-filters-card.sc-card                                             │  │
│  │  [mat-form-field buscar...] [mat-select Estado] [mat-select Período]    │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  @if (loading()) { mat-progress-bar }                                           │
│                                                                                 │
│  mat-table.pod-table                                                            │
│  ┌──────────┬──────────┬───────────┬──────────┬───────────┬─────────────────┐  │
│  │ Proyecto │ Completud│  On-Time  │Velocidad │Presupuesto│   Acciones      │  │
│  ├──────────┼──────────┼───────────┼──────────┼───────────┼─────────────────┤  │
│  │ Nombre   │ [chip 85%│ [chip 72%]│ 12/sem   │ [chip -5%]│ [ver] [analyt] │  │
│  │ del Proy.│  verde]  │  naranja] │          │  rojo]    │                 │  │
│  ├──────────┼──────────┼───────────┼──────────┼───────────┼─────────────────┤  │
│  │ Proyecto │ [chip 90%│ [chip 88%]│  8/sem   │ [chip +2%]│ [ver] [analyt] │  │
│  │ Beta     │  verde]  │   verde]  │          │  verde]   │                 │  │
│  └──────────┴──────────┴───────────┴──────────┴───────────┴─────────────────┘  │
│                                                                                 │
│  @if (!loading() && proyectos().length === 0) {                                │
│    div.sc-empty-state  icono: "assessment" + mensaje                           │
│  }                                                                              │
│                                                                                 │
│  mat-paginator [server-side]                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Estructura HTML Angular Material

```html
<!-- app-projects-overview-dashboard -->
<div class="sc-page">

  <div class="sc-page-header">
    <h1 class="sc-page-header__title">Resumen de proyectos</h1>
    <button mat-stroked-button (click)="exportarExcel()" aria-label="Exportar tabla a Excel">
      <mat-icon>table_view</mat-icon>
      Exportar Excel
    </button>
  </div>

  <!-- Filtros -->
  <div class="pod-filters-card sc-card">
    <mat-form-field appearance="outline" subscriptSizing="dynamic" class="pod-search">
      <mat-label>Buscar por nombre o código…</mat-label>
      <input matInput [ngModel]="searchText()"
             (ngModelChange)="searchText.set($event)"
             (keyup.enter)="onSearch()" />
      <button mat-icon-button matSuffix (click)="onSearch()" aria-label="Buscar">
        <mat-icon>search</mat-icon>
      </button>
    </mat-form-field>

    <mat-form-field appearance="outline" subscriptSizing="dynamic" class="pod-filter">
      <mat-label>Estado del proyecto</mat-label>
      <mat-select [ngModel]="estadoFilter()"
                  (ngModelChange)="estadoFilter.set($event); onFilterChange()">
        <mat-option value="">Todos</mat-option>
        <mat-option value="planning">Planificación</mat-option>
        <mat-option value="active">Activo</mat-option>
        <mat-option value="on_hold">En pausa</mat-option>
        <mat-option value="completed">Completado</mat-option>
      </mat-select>
    </mat-form-field>

    <mat-form-field appearance="outline" subscriptSizing="dynamic" class="pod-filter">
      <mat-label>Período</mat-label>
      <mat-select [ngModel]="periodoFilter()"
                  (ngModelChange)="periodoFilter.set($event); onFilterChange()">
        <mat-option value="current_month">Mes actual</mat-option>
        <mat-option value="quarter">Trimestre</mat-option>
        <mat-option value="year">Año</mat-option>
        <mat-option value="project_life">Duración del proyecto</mat-option>
      </mat-select>
    </mat-form-field>
  </div>

  @if (loading()) {
    <mat-progress-bar mode="indeterminate" class="pod-progress" />
  }

  <!-- Tabla comparativa -->
  <mat-table [dataSource]="proyectos()"
             matSort
             (matSortChange)="onSort($event)"
             class="pod-table"
             aria-label="Tabla comparativa de KPIs por proyecto">

    <ng-container matColumnDef="nombre">
      <mat-header-cell *matHeaderCellDef mat-sort-header>Proyecto</mat-header-cell>
      <mat-cell *matCellDef="let p">
        <div class="pod-nombre-cell">
          <span class="pod-codigo">{{ p.codigo }}</span>
          <span class="pod-nombre">{{ p.nombre }}</span>
        </div>
      </mat-cell>
    </ng-container>

    <ng-container matColumnDef="completud">
      <mat-header-cell *matHeaderCellDef mat-sort-header class="pod-col-center">
        Completud
      </mat-header-cell>
      <mat-cell *matCellDef="let p" class="pod-col-center">
        <span [class]="'pod-kpi-chip pod-kpi-chip--' + semaforoClass(p.kpis.completud)">
          {{ p.kpis.completud | number:'1.0-0' }}%
        </span>
      </mat-cell>
    </ng-container>

    <ng-container matColumnDef="on_time">
      <mat-header-cell *matHeaderCellDef mat-sort-header class="pod-col-center">
        On-Time
      </mat-header-cell>
      <mat-cell *matCellDef="let p" class="pod-col-center">
        <span [class]="'pod-kpi-chip pod-kpi-chip--' + semaforoClass(p.kpis.on_time_pct)">
          {{ p.kpis.on_time_pct | number:'1.0-0' }}%
        </span>
      </mat-cell>
    </ng-container>

    <ng-container matColumnDef="velocidad">
      <mat-header-cell *matHeaderCellDef mat-sort-header class="pod-col-right">
        Velocidad
      </mat-header-cell>
      <mat-cell *matCellDef="let p" class="pod-col-right">
        {{ p.kpis.velocidad_promedio | number:'1.1-1' }}/sem
      </mat-cell>
    </ng-container>

    <ng-container matColumnDef="presupuesto">
      <mat-header-cell *matHeaderCellDef mat-sort-header class="pod-col-center">
        Presupuesto
      </mat-header-cell>
      <mat-cell *matCellDef="let p" class="pod-col-center">
        <span [class]="'pod-kpi-chip pod-kpi-chip--' + presupuestoClass(p.kpis.variacion_presupuesto)">
          {{ p.kpis.variacion_presupuesto > 0 ? '+' : '' }}{{ p.kpis.variacion_presupuesto | number:'1.0-1' }}%
        </span>
      </mat-cell>
    </ng-container>

    <ng-container matColumnDef="acciones">
      <mat-header-cell *matHeaderCellDef class="pod-col-acciones"></mat-header-cell>
      <mat-cell *matCellDef="let p" class="pod-col-acciones">
        <button mat-icon-button matTooltip="Ver proyecto" (click)="verProyecto(p.id)"
                aria-label="Ver detalle del proyecto {{ p.nombre }}">
          <mat-icon>chevron_right</mat-icon>
        </button>
        <button mat-icon-button matTooltip="Ver analytics" (click)="verAnalytics(p.id)"
                aria-label="Ver analytics del proyecto {{ p.nombre }}">
          <mat-icon>analytics</mat-icon>
        </button>
      </mat-cell>
    </ng-container>

    <mat-header-row *matHeaderRowDef="displayedColumns" />
    <mat-row *matRowDef="let row; columns: displayedColumns;" class="pod-row" />
  </mat-table>

  @if (!loading() && proyectos().length === 0) {
    <div class="sc-empty-state pod-empty">
      <mat-icon>assessment</mat-icon>
      <p>No hay proyectos que coincidan con los filtros seleccionados.</p>
      <button mat-stroked-button (click)="limpiarFiltros()">
        <mat-icon>filter_alt_off</mat-icon> Limpiar filtros
      </button>
    </div>
  }

  <mat-paginator
    [length]="totalCount()"
    [pageSize]="pageSize"
    [pageSizeOptions]="[25, 50, 100]"
    (page)="onPage($event)"
    showFirstLastButtons
    aria-label="Paginación de tabla de proyectos"
  />

</div>
```

### 2.3 Chips de semáforo inline en tabla

```scss
// Chips de KPI con color semáforo — 3 variantes
.pod-kpi-chip {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  white-space: nowrap;

  &--success {
    background: #e8f5e9;
    color: #1b5e20;
  }
  &--warning {
    background: #fff8e1;
    color: #e65100;
  }
  &--danger {
    background: #ffebee;
    color: #b71c1c;
  }
}

// Dark mode
.dark-theme .pod-kpi-chip {
  &--success { background: #1b5e20; color: #e8f5e9; }
  &--warning { background: #e65100; color: #fff8e1; }
  &--danger  { background: #b71c1c; color: #ffebee; }
}
```

### 2.4 Lógica de semáforo (TypeScript)

```typescript
// Umbrales aplicados a % (completud, on-time) y presupuesto
semaforoClass(value: number): 'success' | 'warning' | 'danger' {
  if (value >= 75) return 'success';
  if (value >= 50) return 'warning';
  return 'danger';
}

presupuestoClass(variacion: number): 'success' | 'warning' | 'danger' {
  // variacion positiva = sobre presupuesto (malo)
  if (variacion <= 0)   return 'success';  // en presupuesto o ahorro
  if (variacion <= 10)  return 'warning';  // hasta 10% sobre
  return 'danger';                          // más de 10% sobre
}
```

---

## 3. REPORT BUILDER COMPONENT

### 3.1 Wireframe ASCII — Layout dos columnas

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  div.sc-page                                                                    │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ div.sc-page-header                                                       │  │
│  │  h1  "Constructor de reportes"        [mat-stroked-button "Limpiar"]   │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  div.prb-layout                                                                 │
│  ┌──────────────────────┐  ┌─────────────────────────────────────────────────┐ │
│  │  mat-card.prb-panel  │  │  mat-card.prb-preview                          │ │
│  │  (30% ancho)         │  │  (70% ancho)                                   │ │
│  │                      │  │                                                 │ │
│  │  Filtros del reporte │  │  div.prb-preview-header                        │ │
│  │  ─────────────────── │  │    "Vista previa del reporte"                  │ │
│  │                      │  │    [PDF] [Excel]                                │ │
│  │  Proyectos           │  │  ─────────────────────────────                 │ │
│  │  mat-select multiple │  │                                                 │ │
│  │                      │  │  @if (loading()) { mat-progress-bar }          │ │
│  │  Rango de fechas     │  │                                                 │ │
│  │  mat-date-range-inp. │  │  @if (!filtrosAplicados()) {                   │ │
│  │                      │  │    sc-empty-state                              │ │
│  │  Usuarios            │  │    icono: tune                                 │ │
│  │  mat-select multiple │  │    "Configura los filtros del panel izquierdo" │ │
│  │                      │  │  }                                              │ │
│  │  Métricas            │  │                                                 │ │
│  │  mat-checkbox group  │  │  @if (filtrosAplicados() && !loading()) {      │ │
│  │  [ ] Completud       │  │    div.prb-chart-preview                       │ │
│  │  [ ] On-Time         │  │    canvas (Chart.js)                           │ │
│  │  [ ] Velocidad       │  │    div.prb-tabla-preview                       │ │
│  │  [ ] Presupuesto     │  │    mat-table (datos resumidos)                 │ │
│  │  [ ] Utilización     │  │  }                                              │ │
│  │                      │  │                                                 │ │
│  │  [mat-raised-button  │  │                                                 │ │
│  │   "Generar reporte"] │  │                                                 │ │
│  └──────────────────────┘  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Estructura HTML Angular Material

```html
<!-- app-report-builder -->
<div class="sc-page">

  <div class="sc-page-header">
    <h1 class="sc-page-header__title">Constructor de reportes</h1>
    <button mat-stroked-button (click)="limpiarFiltros()" aria-label="Limpiar todos los filtros">
      <mat-icon>filter_alt_off</mat-icon>
      Limpiar
    </button>
  </div>

  <div class="prb-layout">

    <!-- Panel izquierdo: filtros (30%) -->
    <mat-card class="prb-panel">
      <mat-card-header>
        <mat-card-title>
          <mat-icon>tune</mat-icon>
          Configurar reporte
        </mat-card-title>
      </mat-card-header>
      <mat-card-content>
        <form [formGroup]="filterForm" class="prb-filter-form">

          <!-- Proyectos -->
          <mat-form-field appearance="outline" class="prb-field-full">
            <mat-label>Proyectos</mat-label>
            <mat-select formControlName="proyectos" multiple>
              @for (p of proyectosDisponibles(); track p.id) {
                <mat-option [value]="p.id">{{ p.nombre }}</mat-option>
              }
            </mat-select>
            @if (filterForm.get('proyectos')?.hasError('required')) {
              <mat-error>Selecciona al menos un proyecto</mat-error>
            }
          </mat-form-field>

          <!-- Rango de fechas -->
          <mat-form-field appearance="outline" class="prb-field-full">
            <mat-label>Rango de fechas</mat-label>
            <mat-date-range-input formGroupName="fechas" [rangePicker]="reportPicker">
              <input matStartDate formControlName="inicio" placeholder="Inicio" />
              <input matEndDate formControlName="fin" placeholder="Fin" />
            </mat-date-range-input>
            <mat-datepicker-toggle matIconSuffix [for]="reportPicker" />
            <mat-date-range-picker #reportPicker />
            @if (filterForm.get('fechas.inicio')?.hasError('matStartDateInvalid')) {
              <mat-error>Fecha de inicio inválida</mat-error>
            }
            @if (filterForm.get('fechas.fin')?.hasError('matEndDateInvalid')) {
              <mat-error>Fecha de fin inválida</mat-error>
            }
          </mat-form-field>

          <!-- Usuarios -->
          <mat-form-field appearance="outline" class="prb-field-full">
            <mat-label>Usuarios del equipo</mat-label>
            <mat-select formControlName="usuarios" multiple>
              @for (u of usuariosDisponibles(); track u.id) {
                <mat-option [value]="u.id">{{ u.full_name || u.email }}</mat-option>
              }
            </mat-select>
          </mat-form-field>

          <!-- Métricas a incluir -->
          <div class="prb-metricas-group" role="group" aria-labelledby="metricas-label">
            <span id="metricas-label" class="prb-metricas-label">Métricas a incluir</span>
            <mat-checkbox formControlName="metricaCompletud">Completud del proyecto</mat-checkbox>
            <mat-checkbox formControlName="metricaOnTime">Cumplimiento on-time</mat-checkbox>
            <mat-checkbox formControlName="metricaVelocidad">Velocidad del equipo</mat-checkbox>
            <mat-checkbox formControlName="metricaPresupuesto">Variación de presupuesto</mat-checkbox>
            <mat-checkbox formControlName="metricaUtilizacion">Utilización de recursos</mat-checkbox>
          </div>

          <div class="prb-form-actions">
            <button mat-raised-button color="primary"
                    type="button"
                    [disabled]="filterForm.invalid || loading()"
                    (click)="generarReporte()"
                    aria-label="Generar vista previa del reporte">
              @if (loading()) {
                <mat-progress-spinner diameter="18" mode="indeterminate" />
              }
              Generar reporte
            </button>
          </div>

        </form>
      </mat-card-content>
    </mat-card>

    <!-- Panel derecho: preview (70%) -->
    <mat-card class="prb-preview">
      <mat-card-header>
        <mat-card-title>Vista previa</mat-card-title>
        @if (reporteGenerado()) {
          <div class="prb-export-actions">
            <button mat-stroked-button (click)="exportarPDF()" aria-label="Exportar a PDF">
              <mat-icon>picture_as_pdf</mat-icon> PDF
            </button>
            <button mat-stroked-button (click)="exportarExcel()" aria-label="Exportar a Excel">
              <mat-icon>table_view</mat-icon> Excel
            </button>
          </div>
        }
      </mat-card-header>
      <mat-card-content>

        @if (loading()) {
          <mat-progress-bar mode="indeterminate" class="prb-progress" />
        }

        @if (!filtrosAplicados() && !loading()) {
          <div class="sc-empty-state prb-empty">
            <mat-icon>tune</mat-icon>
            <p>Configura los filtros en el panel izquierdo y presiona "Generar reporte".</p>
          </div>
        }

        @if (filtrosAplicados() && !loading() && reporteGenerado()) {
          <div class="prb-chart-preview"
               role="img"
               aria-label="Vista previa del gráfico del reporte">
            <canvas #previewCanvas id="previewChart"></canvas>
          </div>

          <mat-table [dataSource]="reporteData()"
                     class="prb-preview-table"
                     aria-label="Tabla de resumen del reporte">
            <!-- columnas dinámicas según métricas seleccionadas -->
          </mat-table>
        }

      </mat-card-content>
    </mat-card>

  </div>
</div>
```

### 3.3 SCSS del Report Builder

```scss
.prb-layout {
  display: grid;
  grid-template-columns: 30% 1fr;
  gap: 1rem;
  align-items: start;
}
.prb-panel { height: fit-content; }
.prb-filter-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.prb-field-full { width: 100%; }
.prb-metricas-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.prb-metricas-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--sc-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 0.25rem;
}
.prb-form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}
.prb-chart-preview {
  position: relative;
  height: 280px;
  margin-bottom: 1.5rem;
}
.prb-progress { margin-bottom: 1rem; }
.prb-empty {
  border: 1px solid var(--sc-surface-border);
  border-radius: var(--sc-radius);
}
.prb-export-actions {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
}
.prb-preview-table { width: 100%; }

// Responsive — tablet: dos columnas comprimidas
@media (max-width: 1023px) {
  .prb-layout { grid-template-columns: 35% 1fr; }
}
// Responsive — mobile: una columna, panel filtros primero
@media (max-width: 767px) {
  .prb-layout { grid-template-columns: 1fr; }
  .prb-chart-preview { height: 200px; }
}
```

---

## 4. INTEGRACION TAB ANALYTICS EN PROYECTO-DETAIL

### 4.1 Modificación de `proyecto-detail.component.html`

Agregar un nuevo tab al final del `mat-tab-group` existente (después del tab "Equipo"):

```html
<!-- Tab 9: Analytics — lazy load del componente -->
<mat-tab label="Analytics">
  <div class="pd-tab-content">
    @defer (on viewport) {
      <app-project-analytics-dashboard
        [proyectoId]="p.id"
        [proyectoNombre]="p.nombre"
      />
    } @placeholder {
      <div class="pd-tab-placeholder">
        <mat-icon>analytics</mat-icon>
        <p>Cargando analytics…</p>
      </div>
    } @loading (minimum 300ms) {
      <mat-progress-bar mode="indeterminate" />
    }
  </div>
</mat-tab>
```

### 4.2 Estrategia de carga diferida

- Se usa `@defer (on viewport)` de Angular 18: el componente analytics solo se instancia cuando el usuario activa el tab y el contenedor es visible.
- Esto evita peticiones HTTP al cargar el proyecto si el usuario nunca accede a Analytics.
- El `@placeholder` es suficiente para orientar al usuario sin layout shift.
- El `@loading (minimum 300ms)` previene flicker con `mat-progress-bar` delgado.

### 4.3 Input del componente analytics

```typescript
// project-analytics-dashboard.component.ts
readonly proyectoId    = input.required<string>();
readonly proyectoNombre = input.required<string>();
```

---

## 5. ESTADOS Y TRANSICIONES GLOBALES

### 5.1 Matriz de estados por sección

| Sección | Loading | Vacío | Error | Parcial |
|---|---|---|---|---|
| KPI Cards | Skeleton opacity 0.4 en `mat-card` | `sc-empty-state` con `mat-icon analytics` | `snack-error` + cards con `--` | `mat-progress-bar` en header |
| Burn Down | `mat-progress-bar` en card header | Card muestra "Sin datos de horas" con `mat-icon show_chart` | `snack-error` | Datos anteriores visible |
| Velocity | Idem | "Sin semanas con tareas completadas" con `mat-icon speed` | `snack-error` | Datos anteriores visible |
| Task Dist | Idem | "Sin tareas en el período" con `mat-icon inbox` | `snack-error` | Datos anteriores visible |
| Resource | Idem | "Sin asignaciones en el período" con `mat-icon people_outline` | `snack-error` | Datos anteriores visible |
| Overview Table | `mat-progress-bar` arriba de tabla | `sc-empty-state` con `mat-icon assessment` | `snack-error` | — |
| Report Builder | `mat-progress-spinner` en botón | `sc-empty-state` con `mat-icon tune` en preview | `snack-error` | — |

### 5.2 Botón refresh en header de cada chart card

```html
<!-- Patrón consistente para todos los mat-card de gráficos -->
<mat-card-header>
  <mat-card-title>{{ titulo }}</mat-card-title>
  <mat-card-subtitle>{{ subtitulo }}</mat-card-subtitle>
  <button mat-icon-button
          class="pad-chart-refresh"
          [matTooltip]="'Actualizar ' + titulo"
          (click)="onRefresh.emit()"
          [disabled]="loading()"
          [attr.aria-label]="'Actualizar gráfico de ' + titulo">
    <mat-icon>refresh</mat-icon>
  </button>
</mat-card-header>
```

### 5.3 Feedback de acciones

```typescript
// Exportar PDF exitoso
this.snackBar.open('Reporte PDF generado correctamente.', 'Cerrar', {
  duration: 3000,
  panelClass: ['snack-success']
});

// Error al cargar datos
this.snackBar.open('Error al cargar los datos analíticos. Intenta de nuevo.', 'Cerrar', {
  duration: 5000,
  panelClass: ['snack-error']
});

// Datos actualizados
this.snackBar.open('Dashboard actualizado.', 'Cerrar', {
  duration: 2000,
  panelClass: ['snack-success']
});
```

---

## 6. CHECKLIST DE COMPONENTES — PRE-ENTREGA

Aplicar a cada componente de Feature #5 antes de hacer PR:

- [ ] Usa `sc-page`, `sc-page-header`, filtros en `sc-card` (si aplica)
- [ ] Loading usa `mat-progress-bar` (no spinner) en listados y secciones
- [ ] Empty state con `sc-empty-state` FUERA del `mat-table` / grilla
- [ ] SCSS usa variables CSS `var(--sc-*)`, sin colores hardcodeados
- [ ] No hay `*ngIf` / `*ngFor` — todo con `@if` / `@for`
- [ ] No hay `any` en TypeScript — `unknown` con narrowing si aplica
- [ ] `ChangeDetectionStrategy.OnPush` en todos los componentes
- [ ] Feedback con `MatSnackBar` con `panelClass` correcto, nunca `alert()`
- [ ] `aria-label` en todos los canvas de Chart.js
- [ ] `role="img"` en contenedores de gráficos
- [ ] `aria-label` en botones icon-only
- [ ] Inputs tipados con `input()` (no `@Input()`)
- [ ] Signals con `signal()` / `computed()` para estado local
- [ ] Servicios inyectados con `inject()` (no constructor)

---

## 7. RUTAS Y ESTRUCTURA DE ARCHIVOS

```
frontend/src/app/features/proyectos/
├── components/
│   ├── project-analytics-dashboard/       # Feature #5
│   │   ├── project-analytics-dashboard.component.ts
│   │   ├── project-analytics-dashboard.component.html
│   │   └── project-analytics-dashboard.component.scss
│   ├── projects-overview-dashboard/       # Feature #5
│   │   ├── projects-overview-dashboard.component.ts
│   │   ├── projects-overview-dashboard.component.html
│   │   └── projects-overview-dashboard.component.scss
│   └── report-builder/                    # Feature #5
│       ├── report-builder.component.ts
│       ├── report-builder.component.html
│       └── report-builder.component.scss
├── models/
│   └── analytics.model.ts                 # Interfaces TS para Feature #5
└── services/
    └── analytics.service.ts               # Llamadas API analytics
```

### Rutas sugeridas

```typescript
// Dentro del módulo lazy de proyectos
{
  path: 'analytics',
  loadComponent: () => import('./components/projects-overview-dashboard/projects-overview-dashboard.component')
    .then(m => m.ProjectsOverviewDashboardComponent)
},
{
  path: ':id/analytics',
  loadComponent: () => import('./components/project-analytics-dashboard/project-analytics-dashboard.component')
    .then(m => m.ProjectAnalyticsDashboardComponent)
},
{
  path: 'reportes',
  loadComponent: () => import('./components/report-builder/report-builder.component')
    .then(m => m.ReportBuilderComponent)
}
```
