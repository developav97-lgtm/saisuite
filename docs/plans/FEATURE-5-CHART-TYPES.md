# FEATURE-5-CHART-TYPES.md
# Reporting & Analytics — Especificación de Tipos de Gráfico
# SaiSuite · ValMen Tech · Chart.js · Angular 18

**Fecha:** 27 Marzo 2026
**Feature:** #5 — Reporting & Analytics
**Librería:** Chart.js (`npm install chart.js`)
**Instalación:** solo `chart.js`. No instalar `ng2-charts` ni `chart.js-plugin-*` innecesarios.

---

## 1. CONFIGURACION GLOBAL DE CHART.JS

### 1.1 Instalación y registro

```bash
npm install chart.js
```

```typescript
// src/main.ts — registrar una sola vez al arranque de la app
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);
```

Solo se registra en `main.ts`. Nunca por componente para no duplicar el registro.

### 1.2 Defaults globales — `analytics-chart.defaults.ts`

```typescript
// frontend/src/app/features/proyectos/services/analytics-chart.defaults.ts

import { Chart } from 'chart.js';

export function applyChartDefaults(): void {
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size   = 12;
  Chart.defaults.color       = '#6b7280'; // --sc-text-muted en light mode
  Chart.defaults.responsive  = true;
  Chart.defaults.maintainAspectRatio = false; // altura controlada por CSS
  Chart.defaults.animation   = false;          // desactivar para actualizaciones frecuentes
  Chart.defaults.plugins.tooltip.padding  = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 6;
  Chart.defaults.plugins.tooltip.displayColors = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.padding  = 16;
}
```

Llamar `applyChartDefaults()` en `main.ts` inmediatamente después de `Chart.register(...)`.

### 1.3 Estrategia de dark mode

Los colores de Chart.js no reaccionan a CSS variables automáticamente porque se leen en el momento de crear el chart. La estrategia es:

1. El `ThemeService` expone un signal `isDark = signal<boolean>(false)`.
2. Cada componente que contiene un chart escucha `effect(() => { if (this.themeService.isDark()) this.rebuildCharts(); })`.
3. `rebuildCharts()` destruye los chart instances existentes y los recrea leyendo los colores actuales con `this.getChartColors()`.

```typescript
// Leer colores desde CSS en tiempo de ejecución
private getChartColors(): ChartColorPalette {
  const style = getComputedStyle(document.documentElement);
  return {
    primary:        style.getPropertyValue('--sc-primary').trim()        || '#1976d2',
    primaryLight:   style.getPropertyValue('--sc-primary-light').trim()  || '#e3f2fd',
    textMuted:      style.getPropertyValue('--sc-text-muted').trim()     || '#6b7280',
    surfaceBorder:  style.getPropertyValue('--sc-surface-border').trim() || '#e5e7eb',
  };
}
```

### 1.4 Estrategia de destroy/recreate vs `chart.update()`

| Caso | Método | Razón |
|---|---|---|
| Cambio de período o filtros | `chart.destroy()` + recrear | Los labels del eje X cambian completamente |
| Refresh de datos con mismos labels | `chart.data.datasets[n].data = newData; chart.update('none')` | Evita re-render completo; `'none'` omite animación |
| Toggle dark mode | `chart.destroy()` + recrear | Los colores requieren releer CSS vars |
| Cambio de granularidad (semana/mes) | `chart.destroy()` + recrear | Cantidad de puntos cambia |

```typescript
// Patrón de destrucción segura
private destroyChart(chart: Chart | null): void {
  if (chart) {
    chart.destroy();
  }
}
```

### 1.5 Estrategia con OnPush y signals

```typescript
// En el componente con ChangeDetectionStrategy.OnPush
private readonly cdRef = inject(ChangeDetectorRef);

// Cuando los datos llegan del servicio (observable → signal)
private readonly analytics = toSignal(
  this.analyticsService.getProjectAnalytics(this.proyectoId()),
  { initialValue: null }
);

// Efecto para redibujar charts cuando cambian los datos
constructor() {
  effect(() => {
    const data = this.analytics();
    if (data) {
      // Los charts usan ViewChild + ElementRef, no están en el template directamente
      // por lo que no necesitamos markForCheck para ellos
      this.buildCharts(data);
      // Solo si hay bindings en el template que dependen de signals
      this.cdRef.markForCheck();
    }
  });
}
```

**Regla:** Los `canvas` de Chart.js se manipulan imperativamente con `ViewChild`. `markForCheck()` solo es necesario cuando hay bindings en el template (como `kpis()`) que cambian después de una operación async.

---

## 2. BURN DOWN CHART (Line Chart)

### 2.1 Descripción para el usuario

El burn down muestra cuántas horas de trabajo quedan en el proyecto:
- **Línea ideal** (punteada): cómo deberían consumirse las horas en ritmo uniforme.
- **Línea estimada** (sólida): plan original basado en horas estimadas por tarea.
- **Línea real** (rellena): horas restantes según el trabajo registrado.

Si la línea real está por encima de la ideal, el proyecto va retrasado. Si está por debajo, va adelantado.

### 2.2 Interfaz de datos

```typescript
// analytics.model.ts
export interface BurnDownPoint {
  fecha: string;       // ISO 8601 date, eje X
  horas_ideales:    number;
  horas_estimadas:  number;
  horas_restantes:  number; // línea real
}

export interface BurnDownData {
  proyecto_id:  string;
  fecha_inicio: string;
  fecha_fin:    string;
  puntos:       BurnDownPoint[];
  total_horas_estimadas: number;
}
```

### 2.3 Configuración Chart.js

```typescript
import { ChartConfiguration, ChartType } from 'chart.js';

function buildBurnDownConfig(
  data: BurnDownData,
  colors: ChartColorPalette
): ChartConfiguration<'line'> {

  const labels = data.puntos.map(p => {
    const d = new Date(p.fecha);
    return d.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
  });

  return {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Horas ideales',
          data: data.puntos.map(p => p.horas_ideales),
          borderColor: colors.textMuted,
          backgroundColor: 'transparent',
          borderDash: [6, 4],
          borderWidth: 2,
          pointRadius: 0,
          tension: 0,
        },
        {
          label: 'Horas estimadas',
          data: data.puntos.map(p => p.horas_estimadas),
          borderColor: '#1976d2',   // --color-estimated
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.2,
        },
        {
          label: 'Horas reales',
          data: data.puntos.map(p => p.horas_restantes),
          borderColor: '#0d47a1',   // --color-actual (más oscuro)
          backgroundColor: 'rgba(13, 71, 161, 0.08)',
          fill: true,
          borderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          tension: 0.2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
        },
        tooltip: {
          callbacks: {
            title: (items) => {
              // Mostrar fecha completa en tooltip
              const idx = items[0].dataIndex;
              const d = new Date(data.puntos[idx].fecha);
              return d.toLocaleDateString('es-CO', {
                weekday: 'short', day: 'numeric', month: 'long'
              });
            },
            label: (item) => {
              const value = item.parsed.y;
              return ` ${item.dataset.label}: ${value.toFixed(1)} h`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: colors.surfaceBorder },
          ticks: {
            color: colors.textMuted,
            maxTicksLimit: 10,
            maxRotation: 0,
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: colors.surfaceBorder },
          ticks: {
            color: colors.textMuted,
            callback: (value) => `${value} h`,
          },
          title: {
            display: true,
            text: 'Horas restantes',
            color: colors.textMuted,
          },
        },
      },
    },
  };
}
```

### 2.4 Paleta de colores del Burn Down

| Línea | Color light | Color dark | Variable |
|---|---|---|---|
| Ideal (punteada) | `#9e9e9e` | `#616161` | `--color-ideal` |
| Estimada | `#1976d2` | `#42a5f5` | `--color-estimated` |
| Real (rellena) | `#0d47a1` | `#1565c0` | `--color-actual` |

---

## 3. VELOCITY CHART (Bar Chart)

### 3.1 Descripción para el usuario

Muestra cuántas tareas completó el equipo cada semana. Permite identificar semanas de alta y baja productividad. La línea de media (simulada con `borderColor` en una barra invisible) da contexto al rendimiento relativo.

### 3.2 Interfaz de datos

```typescript
export interface VelocityPoint {
  semana_label: string;   // "Sem 1", "Sem 2" o "12 ene"
  semana_inicio: string;  // ISO date
  semana_fin:    string;  // ISO date
  tareas_completadas: number;
}

export interface VelocityData {
  proyecto_id: string;
  periodo:     string;
  puntos:      VelocityPoint[];
  velocidad_media: number;
}
```

### 3.3 Configuración Chart.js

```typescript
function buildVelocityConfig(
  data: VelocityData,
  colors: ChartColorPalette
): ChartConfiguration<'bar'> {

  const velocidades = data.puntos.map(p => p.tareas_completadas);
  const media       = data.velocidad_media;

  // Color por barra: verde si >= media, rojo si cae por debajo
  const barColors = velocidades.map(v =>
    v >= media ? 'rgba(46, 125, 50, 0.85)' : 'rgba(198, 40, 40, 0.85)'
  );
  const barBorderColors = velocidades.map(v =>
    v >= media ? '#1b5e20' : '#b71c1c'
  );

  return {
    type: 'bar',
    data: {
      labels: data.puntos.map(p => p.semana_label),
      datasets: [
        {
          label: 'Tareas completadas',
          data: velocidades,
          backgroundColor: barColors,
          borderColor:     barBorderColors,
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const idx  = items[0].dataIndex;
              const p    = data.puntos[idx];
              const ini  = new Date(p.semana_inicio).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
              const fin  = new Date(p.semana_fin).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
              return `${p.semana_label}  (${ini} – ${fin})`;
            },
            label: (item) => {
              const v = item.parsed.y;
              const diff = (v - media).toFixed(1);
              const sign = v >= media ? '+' : '';
              return [
                ` ${v} tareas completadas`,
                ` ${sign}${diff} vs media (${media.toFixed(1)})`,
              ];
            },
          },
        },
        // Anotación de media — usando el plugin annotation si se instala,
        // o como dataset auxiliar tipo 'line' con borderDash
        annotation: undefined, // NO incluir sin instalar @chartjs-plugin-annotation
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: colors.textMuted },
        },
        y: {
          beginAtZero: true,
          grid: { color: colors.surfaceBorder },
          ticks: {
            color: colors.textMuted,
            stepSize: 1,
            precision: 0,
          },
          title: {
            display: true,
            text: 'Tareas completadas',
            color: colors.textMuted,
          },
        },
      },
    },
  };
}
```

### 3.4 Línea de media sin plugin externo

Para dibujar la línea de media sin instalar `@chartjs-plugin-annotation`, agregar un segundo dataset de tipo `line`:

```typescript
// Agregar como segundo dataset en el array datasets:
{
  type: 'line' as const,
  label: `Media (${data.velocidad_media.toFixed(1)} tareas)`,
  data: data.puntos.map(() => data.velocidad_media),
  borderColor: '#f57f17',
  borderDash: [6, 3],
  borderWidth: 2,
  pointRadius: 0,
  fill: false,
  order: 0, // se dibuja encima de las barras
}
```

---

## 4. TASK DISTRIBUTION CHART (Donut Chart)

### 4.1 Descripción para el usuario

Muestra la distribución de tareas según su estado actual. Ayuda a identificar si hay muchas tareas bloqueadas o estancadas en revisión.

### 4.2 Estados y colores de los segmentos

Los colores son los mismos que los chips de estado en el resto de la aplicación (chips en `tarea-list`, badges en `tarea-kanban`). Consistencia visual global.

```typescript
// Mapeado directo desde los estados de Task en el backend
export const TASK_STATUS_COLORS: Record<string, string> = {
  todo:        '#9e9e9e',  // gris      — --color-todo
  in_progress: '#1976d2',  // azul      — --color-in-progress
  in_review:   '#f59e0b',  // ámbar     — --color-in-review
  completed:   '#2e7d32',  // verde     — --color-completed
  blocked:     '#c62828',  // rojo      — --color-blocked
};

export const TASK_STATUS_COLORS_DARK: Record<string, string> = {
  todo:        '#757575',
  in_progress: '#42a5f5',
  in_review:   '#fbbf24',
  completed:   '#4caf50',
  blocked:     '#ef5350',
};

export const TASK_STATUS_LABELS: Record<string, string> = {
  todo:        'Por hacer',
  in_progress: 'En progreso',
  in_review:   'En revisión',
  completed:   'Completadas',
  blocked:     'Bloqueadas',
};
```

### 4.3 Interfaz de datos

```typescript
export interface TaskDistributionItem {
  estado:  string;
  label:   string;
  count:   number;
  pct:     number;  // porcentaje del total, 0-100
}

export interface TaskDistributionData {
  proyecto_id:  string;
  total_tareas: number;
  distribucion: TaskDistributionItem[];
}
```

### 4.4 Configuración Chart.js

```typescript
function buildTaskDistConfig(
  data: TaskDistributionData,
  isDark: boolean
): ChartConfiguration<'doughnut'> {

  const colors = isDark ? TASK_STATUS_COLORS_DARK : TASK_STATUS_COLORS;
  const visibleItems = data.distribucion.filter(d => d.count > 0);

  return {
    type: 'doughnut',
    data: {
      labels: visibleItems.map(d => TASK_STATUS_LABELS[d.estado] ?? d.label),
      datasets: [{
        data:            visibleItems.map(d => d.count),
        backgroundColor: visibleItems.map(d => colors[d.estado] ?? '#9e9e9e'),
        borderColor:     isDark ? '#1e1e1e' : '#ffffff',
        borderWidth: 3,
        hoverBorderWidth: 4,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      cutout: '65%',  // grosor del donut
      plugins: {
        legend: {
          position: 'right',
          labels: {
            padding: 14,
            boxWidth: 12,
            generateLabels: (chart) => {
              const ds  = chart.data.datasets[0];
              return (chart.data.labels as string[]).map((label, i) => ({
                text:            `${label}  (${visibleItems[i].count})`,
                fillStyle:       (ds.backgroundColor as string[])[i],
                strokeStyle:     (ds.borderColor as string),
                lineWidth:       1,
                hidden:          false,
                index:           i,
              }));
            },
          },
        },
        tooltip: {
          callbacks: {
            label: (item) => {
              const count = item.parsed;
              const pct   = visibleItems[item.dataIndex].pct.toFixed(1);
              return ` ${count} tareas (${pct}%)`;
            },
          },
        },
      },
    },
    plugins: [
      // Plugin inline para texto central del donut
      {
        id: 'doughnutCenter',
        afterDraw(chart) {
          const { ctx, chartArea: { top, left, width, height } } = chart;
          ctx.save();
          const cx = left + width  / 2;
          const cy = top  + height / 2;
          // Número grande
          ctx.font = `bold 28px Inter, system-ui, sans-serif`;
          ctx.fillStyle = isDark ? '#f9fafb' : '#111827';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(String(data.total_tareas), cx, cy - 8);
          // Etiqueta pequeña
          ctx.font = `12px Inter, system-ui, sans-serif`;
          ctx.fillStyle = isDark ? '#9ca3af' : '#6b7280';
          ctx.fillText('tareas', cx, cy + 14);
          ctx.restore();
        },
      },
    ],
  };
}
```

### 4.5 Posición de leyenda según breakpoint

```typescript
// Ajustar posición de leyenda en mobile
const legendPosition: 'right' | 'bottom' =
  window.innerWidth < 640 ? 'bottom' : 'right';
```

---

## 5. RESOURCE UTILIZATION CHART (Horizontal Bar Chart)

### 5.1 Descripción para el usuario

Una barra horizontal por miembro del equipo muestra qué porcentaje de su capacidad semanal está asignado. Ordenado de mayor a menor utilización. Una línea de referencia en el 100% marca el límite de capacidad.

### 5.2 Interfaz de datos

```typescript
export interface ResourceUtilizationItem {
  usuario_id:    string;
  usuario_nombre: string;
  horas_capacidad:  number;
  horas_asignadas:  number;
  porcentaje:       number;  // horas_asignadas / horas_capacidad * 100
}

export interface ResourceUtilizationData {
  proyecto_id:  string;
  periodo:      string;
  recursos:     ResourceUtilizationItem[];  // ya ordenados por porcentaje desc desde API
}
```

### 5.3 Umbral de colores

| Rango | Color (light) | Color (dark) | Significado |
|---|---|---|---|
| < 70% | `rgba(46, 125, 50, 0.85)` | `rgba(76, 175, 80, 0.85)` | Capacidad disponible |
| 70% – 90% | `rgba(245, 127, 23, 0.85)` | `rgba(251, 192, 45, 0.85)` | Carga alta |
| > 90% | `rgba(198, 40, 40, 0.85)` | `rgba(239, 83, 80, 0.85)` | Sobreasignado / riesgo |

### 5.4 Configuración Chart.js

```typescript
function buildResourceUtilConfig(
  data: ResourceUtilizationData,
  isDark: boolean,
  colors: ChartColorPalette
): ChartConfiguration<'bar'> {

  const recursos = data.recursos;

  const barColors = recursos.map(r => {
    const pct = r.porcentaje;
    if (isDark) {
      if (pct <= 70) return 'rgba(76, 175, 80, 0.85)';
      if (pct <= 90) return 'rgba(251, 192, 45, 0.85)';
      return 'rgba(239, 83, 80, 0.85)';
    }
    if (pct <= 70) return 'rgba(46, 125, 50, 0.85)';
    if (pct <= 90) return 'rgba(245, 127, 23, 0.85)';
    return 'rgba(198, 40, 40, 0.85)';
  });

  return {
    type: 'bar',
    data: {
      labels: recursos.map(r => {
        // Nombre corto para eje Y
        const parts = r.usuario_nombre.trim().split(' ');
        return parts.length > 1
          ? `${parts[0]} ${parts[1].charAt(0)}.`
          : parts[0];
      }),
      datasets: [
        {
          label: 'Utilización (%)',
          data:            recursos.map(r => Math.min(r.porcentaje, 120)), // cap visual en 120%
          backgroundColor: barColors,
          borderColor:     barColors.map(c => c.replace('0.85', '1')),
          borderWidth: 1,
          borderRadius: 3,
          borderSkipped: false,
        },
      ],
    },
    options: {
      indexAxis: 'y',  // barras horizontales
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              return recursos[items[0].dataIndex].usuario_nombre;
            },
            label: (item) => {
              const r   = recursos[item.dataIndex];
              const pct = r.porcentaje.toFixed(1);
              return [
                ` ${pct}% de capacidad asignada`,
                ` ${r.horas_asignadas.toFixed(1)} de ${r.horas_capacidad.toFixed(1)} horas`,
              ];
            },
          },
        },
        // Línea de referencia en 100% como segundo dataset
        annotation: undefined,
      },
      scales: {
        x: {
          min: 0,
          max: 120,
          grid: { color: colors.surfaceBorder },
          ticks: {
            color: colors.textMuted,
            callback: (value) => `${value}%`,
            stepSize: 20,
          },
          title: {
            display: true,
            text: 'Porcentaje de capacidad',
            color: colors.textMuted,
          },
        },
        y: {
          grid: { display: false },
          ticks: { color: colors.textMuted },
        },
      },
    },
  };
}
```

### 5.5 Línea de referencia en 100% (sin plugin externo)

```typescript
// Agregar como segundo dataset en el array datasets:
{
  type: 'line' as const,
  label: 'Capacidad máxima (100%)',
  data: recursos.map(() => 100),
  borderColor: isDark ? '#ef5350' : '#c62828',
  borderDash: [4, 4],
  borderWidth: 2,
  pointRadius: 0,
  fill: false,
  xAxisID: 'x',
  yAxisID: 'y',
}
```

---

## 6. PALETA DE COLORES GLOBAL

### 6.1 Variables SCSS para estados de tarea

Agregar al archivo global `styles.scss` (o al design token file):

```scss
// -- Estados de tarea (consistentes con chips en tarea-list/tarea-kanban)
:root {
  --color-todo:        #9e9e9e;
  --color-in-progress: #1976d2;
  --color-in-review:   #f59e0b;
  --color-completed:   #2e7d32;
  --color-blocked:     #c62828;

  // KPI thresholds
  --color-kpi-success: #2e7d32;   // > 75%
  --color-kpi-warning: #f57f17;   // 50–75%
  --color-kpi-danger:  #c62828;   // < 50%

  // Chart lines (Burn Down)
  --color-ideal:     #9e9e9e;
  --color-estimated: #1976d2;
  --color-actual:    #0d47a1;

  // Resource utilization thresholds
  --color-util-ok:   rgba(46, 125, 50, 0.85);    // < 70%
  --color-util-warn: rgba(245, 127, 23, 0.85);   // 70–90%
  --color-util-over: rgba(198, 40, 40, 0.85);    // > 90%
}

// Dark mode overrides
.dark-theme {
  --color-todo:        #757575;
  --color-in-progress: #42a5f5;
  --color-in-review:   #fbbf24;
  --color-completed:   #4caf50;
  --color-blocked:     #ef5350;

  --color-kpi-success: #4caf50;
  --color-kpi-warning: #ffb300;
  --color-kpi-danger:  #ef5350;

  --color-ideal:     #757575;
  --color-estimated: #42a5f5;
  --color-actual:    #1565c0;

  --color-util-ok:   rgba(76, 175, 80, 0.85);
  --color-util-warn: rgba(251, 192, 45, 0.85);
  --color-util-over: rgba(239, 83, 80, 0.85);
}
```

### 6.2 Tabla de referencia completa de colores

| Nombre | Light mode | Dark mode | Contexto |
|---|---|---|---|
| Todo | `#9e9e9e` | `#757575` | Chips tarea, donut |
| En progreso | `#1976d2` | `#42a5f5` | Chips tarea, donut, burn down estimado |
| En revisión | `#f59e0b` | `#fbbf24` | Chips tarea, donut |
| Completada | `#2e7d32` | `#4caf50` | Chips tarea, donut, KPI success |
| Bloqueada | `#c62828` | `#ef5350` | Chips tarea, donut, KPI danger |
| KPI success | `#2e7d32` | `#4caf50` | > 75% completud / on-time |
| KPI warning | `#f57f17` | `#ffb300` | 50–75% |
| KPI danger | `#c62828` | `#ef5350` | < 50% |
| Ideal | `#9e9e9e` | `#757575` | Burn down línea ideal |
| Estimado | `#1976d2` | `#42a5f5` | Burn down línea estimada |
| Real | `#0d47a1` | `#1565c0` | Burn down línea real |
| Velocidad media | `#f57f17` | `#ffb300` | Línea de referencia velocity |
| Util OK | `rgba(46,125,50,0.85)` | `rgba(76,175,80,0.85)` | < 70% uso |
| Util warn | `rgba(245,127,23,0.85)` | `rgba(251,192,45,0.85)` | 70–90% uso |
| Util over | `rgba(198,40,40,0.85)` | `rgba(239,83,80,0.85)` | > 90% uso |

---

## 7. RESPONSIVIDAD DE GRAFICOS

### 7.1 Regla fundamental: altura fija en CSS

```scss
// En el componente SCSS — altura fija para evitar layout shift
.pad-chart-container {
  position: relative;
  height: 280px;  // desktop
  width:  100%;
}

@media (max-width: 1023px) {
  .pad-chart-container { height: 240px; }
}

@media (max-width: 767px) {
  .pad-chart-container { height: 200px; }
}
```

```typescript
// En el canvas — NUNCA usar width/height en el elemento HTML
// Chart.js lee el contenedor CSS gracias a maintainAspectRatio: false
```

### 7.2 Simplificación de leyenda en mobile

```typescript
// Adaptar la configuración del chart según viewport
private getLegendConfig(chartType: string): object {
  const isMobile = window.innerWidth < 640;
  return {
    position: (chartType === 'doughnut' && isMobile) ? 'bottom' : 'right',
    labels: {
      font: { size: isMobile ? 10 : 12 },
      padding: isMobile ? 8 : 14,
      boxWidth: isMobile ? 8 : 12,
    },
  };
}
```

### 7.3 Comportamiento por chart en mobile

| Chart | Desktop | Tablet (768px) | Mobile (< 640px) |
|---|---|---|---|
| Burn Down | Todos los puntos | Max 10 ticks en X | Max 6 ticks en X |
| Velocity | Todas las semanas | Todas | Labels a 45° si > 8 semanas |
| Task Dist | Leyenda a la derecha | Leyenda a la derecha | Leyenda abajo |
| Resource | Todos los usuarios | Todos | Solo top 5 por utilización |

```typescript
// Para Resource en mobile: mostrar solo top 5
const recursos = isMobile
  ? data.recursos.slice(0, 5)   // ya ordenados desc
  : data.recursos;
```

---

## 8. PERFORMANCE

### 8.1 Configuración base para actualizaciones frecuentes

```typescript
// En Chart.defaults (aplicado globalmente en main.ts)
Chart.defaults.animation = false;  // sin animaciones en modo datos en vivo
```

### 8.2 Cuándo usar `chart.update()` vs destruir y recrear

```typescript
// CASO 1: Solo cambian los valores, los labels son iguales
// → usar chart.update('none') — más eficiente
chart.data.datasets[0].data = nuevosValores;
chart.update('none'); // 'none' = sin animación

// CASO 2: Cambian labels (período diferente, granularidad)
// → destruir y recrear completamente
this.destroyChart(this.burnDownChart);
this.burnDownChart = new Chart(canvas, nuevaConfig);

// CASO 3: Toggle dark mode
// → siempre destruir y recrear (los colores son estáticos en la config)
this.rebuildAllCharts();
```

### 8.3 Estrategia de destrucción en `ngOnDestroy`

```typescript
// Implementar en el componente para evitar memory leaks
ngOnDestroy(): void {
  this.destroyChart(this.burnDownChart);
  this.destroyChart(this.velocityChart);
  this.destroyChart(this.taskDistChart);
  this.destroyChart(this.resourceUtilChart);
}

private destroyChart(chart: Chart | null): void {
  chart?.destroy();
}
```

### 8.4 Lazy init: crear charts solo cuando el canvas es visible

```typescript
// Usar @defer en el template (ver sección de Wireframes)
// El effect() que crea los charts se dispara después del @defer,
// garantizando que el canvas ya está en el DOM

ngAfterViewInit(): void {
  // Los ViewChild se resuelven aquí — seguro crear charts
  this.initCharts();
}

// O con signal + effect si el componente está dentro de @defer
constructor() {
  effect(() => {
    const data = this.analytics();
    if (data && this.canvasRef()?.nativeElement) {
      this.buildCharts(data);
    }
  });
}
```

### 8.5 Costo estimado por operación

| Operación | Tiempo estimado | Método recomendado |
|---|---|---|
| Primera inicialización de 4 charts | ~120ms | `ngAfterViewInit` + lazy load con `@defer` |
| Actualización de datos (mismos labels) | ~5ms por chart | `chart.update('none')` |
| Cambio de período (labels nuevos) | ~40ms por chart | Destroy + recrear |
| Toggle dark mode (4 charts) | ~160ms | `rebuildAllCharts()` |

---

## 9. ACCESIBILIDAD — WCAG AA

### 9.1 Atributos ARIA en canvas

```html
<!-- Todo canvas de Chart.js debe tener role y aria-label -->
<div class="pad-chart-container"
     role="img"
     [attr.aria-label]="ariaLabelBurnDown()">
  <canvas #burnDownCanvas></canvas>
</div>
```

```typescript
// Generar aria-label dinámico con datos reales
readonly ariaLabelBurnDown = computed(() => {
  const data = this.burnDownData();
  if (!data) return 'Gráfico de burn down — sin datos';
  return `Gráfico de burn down del proyecto. ${data.total_horas_estimadas} horas estimadas totales. Período: ${data.fecha_inicio} a ${data.fecha_fin}.`;
});
```

### 9.2 Tabla de datos accesible como alternativa

Para usuarios que usan lectores de pantalla, complementar cada chart con una tabla visualmente oculta pero disponible:

```html
<!-- Visible solo para lectores de pantalla -->
<table class="cdk-visually-hidden" aria-label="Datos del burn down">
  <thead>
    <tr>
      <th scope="col">Fecha</th>
      <th scope="col">Horas ideales</th>
      <th scope="col">Horas estimadas</th>
      <th scope="col">Horas reales</th>
    </tr>
  </thead>
  <tbody>
    @for (punto of burnDownData()?.puntos; track punto.fecha) {
      <tr>
        <td>{{ punto.fecha | date:'dd/MM/yyyy' }}</td>
        <td>{{ punto.horas_ideales | number:'1.1-1' }} h</td>
        <td>{{ punto.horas_estimadas | number:'1.1-1' }} h</td>
        <td>{{ punto.horas_restantes | number:'1.1-1' }} h</td>
      </tr>
    }
  </tbody>
</table>
```

### 9.3 Ratio de contraste en colores KPI

Los chips de semáforo deben cumplir WCAG AA (4.5:1 para texto pequeño):

| Combinación | Ratio aproximado | Cumple AA |
|---|---|---|
| Texto `#1b5e20` sobre `#e8f5e9` | 7.5:1 | Si |
| Texto `#e65100` sobre `#fff8e1` | 5.1:1 | Si |
| Texto `#b71c1c` sobre `#ffebee` | 7.8:1 | Si |

Dark mode:

| Combinación | Ratio aproximado | Cumple AA |
|---|---|---|
| Texto `#e8f5e9` sobre `#1b5e20` | 7.5:1 | Si |
| Texto `#fff8e1` sobre `#e65100` | 5.1:1 | Si |
| Texto `#ffebee` sobre `#b71c1c` | 7.8:1 | Si |

### 9.4 Navegación por teclado

- Todos los botones de refresh tienen `aria-label` explícito.
- Las KPI cards tienen `tabindex="0"` para permitir navegación.
- Los `mat-select` de filtros son nativamente accesibles via Angular Material.
- Los botones de exportar PDF/Excel tienen `aria-label` descriptivos.

---

## 10. ARCHIVO DE TIPOS TS — `analytics.model.ts`

```typescript
// frontend/src/app/features/proyectos/models/analytics.model.ts

export interface ProjectKpis {
  completud:            number;   // 0-100
  completud_trend:      number;   // delta vs período anterior
  on_time_pct:          number;   // 0-100
  tareas_on_time:       number;
  tareas_total:         number;
  velocidad_promedio:   number;   // tareas/semana
  variacion_presupuesto: number;  // % sobre/bajo presupuesto
  gasto_real:           number;
  presupuesto_total:    number;
}

export interface BurnDownPoint {
  fecha:            string;
  horas_ideales:    number;
  horas_estimadas:  number;
  horas_restantes:  number;
}

export interface BurnDownData {
  proyecto_id:           string;
  fecha_inicio:          string;
  fecha_fin:             string;
  puntos:                BurnDownPoint[];
  total_horas_estimadas: number;
}

export interface VelocityPoint {
  semana_label:       string;
  semana_inicio:      string;
  semana_fin:         string;
  tareas_completadas: number;
}

export interface VelocityData {
  proyecto_id:      string;
  periodo:          string;
  puntos:           VelocityPoint[];
  velocidad_media:  number;
}

export interface TaskDistributionItem {
  estado: string;
  label:  string;
  count:  number;
  pct:    number;
}

export interface TaskDistributionData {
  proyecto_id:  string;
  total_tareas: number;
  distribucion: TaskDistributionItem[];
}

export interface ResourceUtilizationItem {
  usuario_id:      string;
  usuario_nombre:  string;
  horas_capacidad: number;
  horas_asignadas: number;
  porcentaje:      number;
}

export interface ResourceUtilizationData {
  proyecto_id: string;
  periodo:     string;
  recursos:    ResourceUtilizationItem[];
}

export interface ProjectAnalytics {
  kpis:        ProjectKpis;
  burn_down:   BurnDownData;
  velocity:    VelocityData;
  task_dist:   TaskDistributionData;
  resource_util: ResourceUtilizationData;
}

// Para el overview dashboard (tabla comparativa)
export interface ProjectKpiRow {
  id:     string;
  codigo: string;
  nombre: string;
  estado: string;
  kpis:   ProjectKpis;
}

export interface ProjectKpiPeriod {
  value: 'current_month' | 'last_month' | 'quarter' | 'year' | 'project_life';
  label: string;
}

export interface ChartColorPalette {
  primary:       string;
  primaryLight:  string;
  textMuted:     string;
  surfaceBorder: string;
}
```

---

## 11. CHECKLIST PRE-IMPLEMENTACION DE CHARTS

Antes de codificar cada chart component:

- [ ] `Chart.register(...registerables)` está en `main.ts`, no en el componente
- [ ] `maintainAspectRatio: false` en todas las configuraciones
- [ ] `animation: false` en todas las configuraciones
- [ ] Canvas tiene `role="img"` en su contenedor `div`
- [ ] Canvas tiene `aria-label` descriptivo y dinámico
- [ ] Tabla `cdk-visually-hidden` con datos para lectores de pantalla
- [ ] `ngOnDestroy` destruye todos los chart instances
- [ ] Dark mode reactivo via `ThemeService` signal + `effect()`
- [ ] Colores leídos desde CSS variables en runtime, no hardcodeados en el componente
- [ ] Altura del contenedor fija en CSS (no en el canvas)
- [ ] Sin `@chartjs-plugin-annotation` — líneas de referencia como dataset auxiliar
- [ ] Responsive: simplificación en mobile (leyenda, max items)
