# Feature #5 — QA Report
**Fecha:** 2026-03-27
**Revisor:** EvidenceQA — Evidence Collector
**Metodología:** Revisión estática de código (sin acceso a browser/screenshots)
**Archivos revisados:** 11 archivos (4 backend, 7 frontend)

---

## Issues Encontrados

### ISSUE-01: Fuga de memoria — suscripción manual sin unsubscribe en `forkJoin` — Severidad: ALTA

**Archivo:** `frontend/src/app/features/proyectos/components/analytics/project-analytics-dashboard/project-analytics-dashboard.component.ts:84-102`

**Descripción:**
El componente hace una suscripción manual a `forkJoin(...)` en `loadData()` sin almacenar la suscripción para cancelarla en `ngOnDestroy`. Si el usuario navega fuera del componente mientras la carga está en progreso, el callback `next` se ejecutará igualmente (set de signals, buildCharts), provocando un error de operación en componente destruido y el riesgo de memory leak por la referencia viva. `forkJoin` completa automáticamente, pero `loadData()` puede ser llamado manualmente via el botón "Actualizar datos" — generando múltiples suscripciones simultáneas sin control.

**Evidencia — código exacto con el problema:**
```typescript
// project-analytics-dashboard.component.ts:84
forkJoin({
  kpis: this.analyticsService.getKPIs(id),
  ...
}).subscribe({        // <-- suscripción manual sin Subscription almacenada
  next: (data) => {
    this.kpis.set(data.kpis);
    ...
    setTimeout(() => this.buildCharts(), 0);  // <-- puede ejecutarse en componente destruido
  },
  ...
});
```

La regla del proyecto (`CLAUDE.md`) lo exige explícitamente: "Nunca suscripción manual sin `unsubscribe`. Usar `async pipe` en el template."

**Fix recomendado:**
Agregar `private loadSubscription?: Subscription;` y en `ngOnDestroy()` llamar `this.loadSubscription?.unsubscribe()`. Alternativamente, usar `takeUntilDestroyed(this.destroyRef)` con `inject(DestroyRef)`.

---

### ISSUE-02: Desajuste de tipos en `analytics.model.ts` — campo `prioridad` — Severidad: ALTA

**Archivo:** `frontend/src/app/features/proyectos/models/analytics.model.ts:83`

**Descripción:**
La interfaz `TimelineTask` declara `prioridad` como `string`, pero el serializer Django `TimelineTaskSerializer` lo declara como `serializers.IntegerField`. El backend retorna un entero; el frontend espera un string. Esto viola el contrato backend-frontend y puede causar fallos silenciosos en comparaciones o display de prioridad.

**Evidencia:**

Backend — `analytics_serializers.py:153`:
```python
prioridad = serializers.IntegerField(read_only=True)
```

Frontend — `analytics.model.ts:83`:
```typescript
prioridad: string;   // <-- debería ser: number
```

**Fix recomendado:**
Cambiar `prioridad: string` a `prioridad: number` en la interfaz `TimelineTask`.

---

### ISSUE-03: Desajuste de campos — `ResourceUtilization` omite `user_email` — Severidad: MEDIA

**Archivo:** `frontend/src/app/features/proyectos/models/analytics.model.ts:55-62`

**Descripción:**
El serializer Django `ResourceUtilizationSerializer` incluye el campo `user_email` (`serializers.EmailField`). La interfaz TypeScript `ResourceUtilization` no declara ese campo. Aunque TypeScript no romperá en tiempo de compilación (campos extra del JSON son ignorados), el campo está disponible desde el backend pero inaccesible de forma tipada desde el frontend, lo que viola el principio de que el model TS "espeja exactamente el serializer" (`CLAUDE.md`, paso 7).

**Evidencia:**

Backend — `analytics_serializers.py:117-118`:
```python
user_email = serializers.EmailField(read_only=True)
```

Frontend — `analytics.model.ts:55-62`:
```typescript
export interface ResourceUtilization {
  user_id: string;
  user_name: string;
  // user_email FALTA   <-- campo presente en backend, ausente en modelo TS
  assigned_hours: number;
  registered_hours: number;
  capacity_hours: number;
  utilization_percentage: number;
}
```

**Fix recomendado:**
Agregar `user_email: string;` a la interfaz `ResourceUtilization`.

---

### ISSUE-04: Desajuste de tipos en respuesta del servicio — `getVelocity` y `getBurnRate` — Severidad: ALTA

**Archivo:** `frontend/src/app/features/proyectos/services/analytics.service.ts:30-44`

**Descripción:**
Los métodos `getVelocity()` y `getBurnRate()` declaran que retornan `Observable<VelocityDataPoint[]>` y `Observable<BurnRateDataPoint[]>` respectivamente. Sin embargo, el backend NO retorna un array directo: retorna un objeto envolvente `{ periods: number, data: [...] }` serializado por `VelocityResponseSerializer` y `BurnRateResponseSerializer`. El `HttpClient` deserializará el objeto completo, no el array interior. Esto causará que `data.velocity` en el `forkJoin` del componente sea el objeto `{ periods, data }` en lugar de `VelocityDataPoint[]`, rompiendo `velocityData.set(data.velocity)` (línea 88 del componente) y el chart de velocidad.

**Evidencia:**

Backend — `analytics_views.py:154-158`:
```python
response_data = {
    'periods': periods,
    'data': data_points,  # <-- el array está anidado bajo 'data'
}
serializer = VelocityResponseSerializer(response_data)
return Response(serializer.data)  # retorna { periods: 8, data: [...] }
```

Frontend — `analytics.service.ts:30-35`:
```typescript
getVelocity(projectId: string, periods = 8): Observable<VelocityDataPoint[]> {
  // ...
  return this.http.get<VelocityDataPoint[]>(...)  // tipo incorrecto: el JSON es { periods, data }
}
```

Frontend — `analytics.service.ts:38-44`:
```typescript
getBurnRate(projectId: string, periods = 8): Observable<BurnRateDataPoint[]> {
  return this.http.get<BurnRateDataPoint[]>(...)  // tipo incorrecto: el JSON es { periods, data }
}
```

El modelo `analytics.model.ts` no define interfaces para `VelocityResponse` ni `BurnRateResponse` (el objeto envolvente), agravando el problema.

**Fix recomendado:**
Crear interfaces `VelocityResponse { periods: number; data: VelocityDataPoint[]; }` y `BurnRateResponse { periods: number; data: BurnRateDataPoint[]; }`. Actualizar las firmas de `getVelocity` y `getBurnRate` para retornar esos tipos. En el componente, acceder a `.data` del objeto recibido al hacer `velocityData.set(data.velocity.data)`.

---

### ISSUE-05: `@defer (on viewport)` es incorrecto para un tab de Material — Severidad: MEDIA

**Archivo:** `frontend/src/app/features/proyectos/components/proyecto-detail/proyecto-detail.component.html:257`

**Descripción:**
El tab "Analytics" usa `@defer (on viewport)` dentro de `<mat-tab>`. El contenido de un `mat-tab` que no está activo está presente en el DOM pero con `display: none`. El trigger `on viewport` de Angular 18 usa `IntersectionObserver` sobre el elemento placeholder. Cuando un tab de Material no está activo, el placeholder tiene `display: none` y nunca intersecta el viewport, por lo que el componente de analytics NUNCA se cargará a menos que el tab sea activado Y el usuario haga scroll. El resultado práctico es que la carga nunca se dispara cuando el usuario cambia al tab Analytics.

**Evidencia:**
```html
<!-- proyecto-detail.component.html:254-264 -->
<mat-tab label="Analytics">
  <div class="pd-tab-content">
    @defer (on viewport) {           <!-- problema: el placeholder no es visible hasta que el tab ya está activo -->
      <app-project-analytics-dashboard [projectId]="p.id" />
    } @placeholder {
      <div class="sc-loading-state" style="height: 200px;">
        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
      </div>
    }
  </div>
</mat-tab>
```

El trigger correcto para carga lazy en tabs de Material es `on interaction` (cuando el usuario hace click en el tab) o `on idle`.

**Fix recomendado:**
Cambiar `@defer (on viewport)` por `@defer (on interaction)` o `@defer (on idle)` para garantizar que el componente cargue cuando el tab sea seleccionado.

---

### ISSUE-06: Hardcoded colors en SCSS — viola estándar `var(--sc-*)` — Severidad: BAJA

**Archivo:** `frontend/src/app/features/proyectos/components/analytics/project-analytics-dashboard/project-analytics-dashboard.component.scss:55-64`

**Descripción:**
Los modificadores de estado `.pad-kpi__trend--up`, `--warn` y `--danger` usan colores hexadecimales hardcodeados en lugar de variables `var(--sc-*)`. El estándar del proyecto (`CLAUDE.md`) exige: "SCSS: variables `var(--sc-*)` siempre, sin colores hardcodeados."

**Evidencia — código exacto:**
```scss
/* project-analytics-dashboard.component.scss:54-65 */
&--up {
  color: #4caf50;    /* <-- hardcoded, debería ser var(--sc-success) o similar */
}

&--warn {
  color: #ffc107;    /* <-- hardcoded */
}

&--danger {
  color: #f44336;    /* <-- hardcoded */
}
```

Además, en el archivo `.ts`, los colores de los gráficos Chart.js también están hardcodeados (`#9E9E9E`, `#1976d2`, `#4CAF50`, `#F44336`, etc.) en las líneas 163, 171, 179, etc. Aunque los chart colors son razonables de hardcodear (Chart.js no conoce CSS vars), los colores de estado en SCSS sí deben respetar el sistema de diseño.

**Fix recomendado:**
Reemplazar `#4caf50`, `#ffc107`, `#f44336` por variables del sistema (`var(--sc-success, #4caf50)`, etc.) para consistencia con el tema y soporte de dark mode.

---

### ISSUE-07: `TaskDistribution` omite campo `cancelled` en `percentages` — Severidad: MEDIA

**Archivo:** `frontend/src/app/features/proyectos/models/analytics.model.ts:20-28`

**Descripción:**
La interfaz `TaskDistribution.percentages` no incluye el campo `cancelled`, pero el serializer Django `TaskDistributionPercentagesSerializer` sí lo incluye, y el servicio `get_task_distribution()` lo calcula y retorna. La interfaz también omite `cancelled` en el nivel raíz del objeto (solo tiene `todo`, `in_progress`, `in_review`, `completed`, `blocked`, `total`, `percentages`), cuando el backend retorna además `cancelled: number`.

**Evidencia:**

Backend — `analytics_serializers.py:34-41`:
```python
class TaskDistributionPercentagesSerializer(serializers.Serializer):
    todo        = serializers.FloatField(read_only=True)
    in_progress = serializers.FloatField(read_only=True)
    in_review   = serializers.FloatField(read_only=True)
    completed   = serializers.FloatField(read_only=True)
    blocked     = serializers.FloatField(read_only=True)
    cancelled   = serializers.FloatField(read_only=True)  # <-- presente en backend
```

Frontend — `analytics.model.ts:20-28`:
```typescript
export interface TaskDistribution {
  todo: number;
  in_progress: number;
  in_review: number;
  completed: number;
  blocked: number;
  // cancelled FALTA en el nivel raíz y en percentages
  total: number;
  percentages: {
    todo: number;
    in_progress: number;
    in_review: number;
    completed: number;
    blocked: number;
    // cancelled FALTA aquí también
  };
}
```

**Fix recomendado:**
Agregar `cancelled: number;` tanto al nivel raíz de `TaskDistribution` como dentro de `percentages`.

---

## Verificaciones Pasadas

- **Multi-tenancy backend**: Todas las funciones de servicio reciben y filtran por `company_id`. Las views recuperan el proyecto con `get_object_or_404(Project, id=project_pk, company=company, activo=True)` antes de llamar al servicio, garantizando el aislamiento por empresa.
- **Permission class**: Todos los 9 `APIView` declaran `permission_classes = [CanAccessProyectos]`. Ninguna view queda sin protección.
- **Content-Disposition del Excel**: La view `ExportExcelView` retorna `response['Content-Disposition'] = 'attachment; filename="analytics_report.xlsx"'` correctamente en la línea 542.
- **URLs bajo prefijo correcto**: Los analytics se registran bajo `/api/v1/projects/<uuid>/analytics/...` que coincide con el `baseUrl = '/api/v1/projects'` del servicio Angular. No hay desajuste de prefijo.
- **`destroyCharts()` en `ngOnDestroy`**: El componente llama `this.destroyCharts()` en `ngOnDestroy()` (línea 71). Los gráficos Chart.js se limpian correctamente al destruir el componente.
- **Ausencia de `any` en TypeScript**: No se encontró ningún `any` en los archivos revisados. Todos usan tipos explícitos o `unknown`.
- **`ChangeDetectionStrategy.OnPush`**: Aplicado correctamente en `ProjectAnalyticsDashboardComponent` (línea 32) y `ProyectoDetailComponent` (línea 26).
- **Sintaxis Angular 18**: El template usa `@if`, `@for`, `@defer` correctamente. No hay `*ngIf` ni `*ngFor`.
- **`MatSnackBar` con panelClass correcto**: Ambos usos usan `panelClass: ['snack-error']` y `['snack-success']` según el estándar.
- **Serializers sin lógica de negocio**: Los serializers de analytics son declarativos puros, no contienen lógica de cálculo.
- **`compare_projects` filtra multi-tenant**: La función `compare_projects` fuerza `company_id=company_id` en el queryset de proyectos (línea 663-666), impidiendo acceso cross-tenant aunque `project_ids` contenga UUIDs de otras empresas.
- **Logging consistente**: Todas las funciones de servicio usan `logger.info(...)` con `extra={}`. No hay `print()`.
- **`TimelinePhase` serializer nullable**: `start_actual` y `end_actual` tienen `allow_null=True` en `TimelinePhaseSerializer`. El servicio puede retornar `None` para esos campos.

---

## Resumen

| Severidad | Cantidad | Issues |
|-----------|----------|--------|
| CRÍTICA   | 0        | —      |
| ALTA      | 3        | ISSUE-01, ISSUE-02, ISSUE-04 |
| MEDIA     | 3        | ISSUE-03, ISSUE-05, ISSUE-07 |
| BAJA      | 1        | ISSUE-06 |
| **Total** | **7**    | |

**Listo para producción: NO**

### Prioridad de corrección antes de merge

1. **ISSUE-04** — El tipo incorrecto de `getVelocity`/`getBurnRate` provocará que los gráficos de velocidad y burn rate nunca rendericen datos reales. Bug funcional garantizado.
2. **ISSUE-05** — El `@defer (on viewport)` en un tab Material hace que el componente analytics nunca cargue cuando el usuario navega al tab. Bug funcional garantizado.
3. **ISSUE-01** — Suscripción sin unsubscribe: viola el estándar del proyecto y puede provocar comportamiento inesperado en navegación rápida.
4. **ISSUE-02** — Tipo `prioridad: string` vs `number`: viola strict TypeScript y puede causar bugs silenciosos.
5. **ISSUE-07** — Campo `cancelled` faltante en model TS: datos reales del backend no representados en el tipo.
6. **ISSUE-03** — Campo `user_email` faltante en `ResourceUtilization`: información disponible inaccesible de forma tipada.
7. **ISSUE-06** — Colores hardcodeados: viola estándar de diseño, bajo riesgo funcional pero rompe consistencia de dark mode.

---

**QA Agent:** EvidenceQA
**Evidencia:** Revisión estática de código — sin acceso a browser
**Fecha:** 2026-03-27
**Archivos revisados:** 11 (analytics_services.py, analytics_views.py, analytics_serializers.py, urls.py, analytics.model.ts, analytics.service.ts, project-analytics-dashboard.component.ts/html/scss, proyecto-detail.component.ts/html)
