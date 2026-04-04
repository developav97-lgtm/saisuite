# PROMPT CLAUDE CODE CLI — FASE 3: BUGS MOBILE MEDIA/BAJA PRIORIDAD
# Módulo Proyectos — Saicloud

**Objetivo:** Corregir los 7 bugs de responsive mobile de **Media y Baja Prioridad** para alcanzar **100% funcionalidad mobile** en todo el Módulo de Proyectos.

**Estimación total:** 8-12 horas  
**Modelo recomendado:** Claude Sonnet 4.6  
**Herramientas:** Browser + Thinking

---

## 📋 BUGS A CORREGIR (7)

### **Media Prioridad (6)**

#### 1. Etiqueta "Float: 2D" sin contexto (1-2h)
**Ubicación:** Detalle de tarea  
**Problema:** Aparece etiqueta "Float: 2D" sin explicación  
**Solución:** Agregar `matTooltip='Holgura disponible (días)'` o cambiar label a "Holgura: 2D"

#### 2. Acordeones de Equipo muy pegados (1-2h)
**Ubicación:** Detalle proyecto → Tab Equipo  
**Problema:** Sin espacio entre elementos  
**Solución:** `mat-expansion-panel` con `margin-bottom: 8px`, padding mínimo 44x44px (touch target)

#### 3. Tabla Baseline comparativa no se ve (1-2h)
**Ubicación:** Detalle proyecto → Tab Baselines → Comparativa  
**Problema:** Tabla no se visualiza correctamente en mobile  
**Solución:** Aplicar `table-responsive`, considerar vista cards en mobile

#### 4. Tabla Escenarios no se ve (1-2h)
**Ubicación:** Detalle proyecto → Tab Escenarios  
**Problema:** Tabla what-if no se visualiza correctamente  
**Solución:** Aplicar `table-responsive`, priorizar columnas esenciales

#### 5. Tablas Admin sin scroll horizontal (2-4h)
**Ubicación:** Administración → Todas las tablas  
**Problema:** Sin scroll horizontal en mobile  
**Solución:** Crear directiva `[appResponsiveTable]` global, aplicar automáticamente

#### 6. Tabla global Terceros sin scroll (1-2h)
**Ubicación:** Administración → Terceros  
**Problema:** Sin scroll horizontal  
**Solución:** Aplicar `table-responsive`, considerar vista cards en mobile

---

### **Baja Prioridad (1)**

#### 7. Cantidad planificada sin formato miles (1-2h)
**Ubicación:** Asignar actividad a tarea  
**Problema:** Muestra "10000" en vez de "10,000"  
**Solución:** Usar pipe `number` de Angular: `{{ cantidad | number:'1.0-2' }}` o directiva custom

---

## 🎯 METODOLOGÍA DE EJECUCIÓN

### PASO 1: Leer Contexto Completo

1. **Leer documentos obligatorios:**
   - `CLAUDE.md` — Reglas del proyecto
   - `CHECKLIST-VALIDACION.md` — Validación 4x4
   - `INFORME_FASE_1_MOBILE.md` — Soluciones ya aplicadas en Fase 1

2. **Reutilizar clase global `.table-responsive`:**
   - Ya existe en `styles.scss` (creada en Fase 1)
   - Aplicar en tablas que faltan

---

## 🔧 IMPLEMENTACIÓN POR BUG

### Bug #1: Etiqueta "Float: 2D" sin contexto

**Archivos a modificar:**
- `tarea-detail.component.html`
- `tarea-detail.component.ts` (si usa signals/computed)

**Opción A: Agregar Tooltip**

```html
<!-- Antes -->
<div class="task-float">
  Float: {{ tarea.float }}D
</div>

<!-- Después -->
<div class="task-float" matTooltip="Holgura disponible (días)" matTooltipPosition="above">
  <mat-icon>schedule</mat-icon>
  Float: {{ tarea.float }}D
</div>
```

**Opción B: Cambiar Label**

```html
<!-- Más explícito -->
<div class="task-slack">
  <mat-icon>hourglass_empty</mat-icon>
  Holgura: {{ tarea.float }} días
</div>
```

**Validación:**
- [ ] Desktop Light: Tooltip aparece en hover ✅
- [ ] Desktop Dark: Tooltip legible ✅
- [ ] Mobile Light: Tap muestra tooltip ✅
- [ ] Mobile Dark: Tooltip contraste adecuado ✅

---

### Bug #2: Acordeones de Equipo muy pegados

**Archivos a modificar:**
- `equipo-tab.component.scss`

**Solución:**

```scss
// equipo-tab.component.scss
.team-accordion {
  mat-expansion-panel {
    margin-bottom: 8px;
    
    @media (max-width: 768px) {
      // Touch targets mínimos
      .mat-expansion-panel-header {
        min-height: 48px;
        padding: 12px 16px;
      }
      
      .mat-expansion-panel-body {
        padding: 16px;
      }
    }
  }
  
  // Último sin margin
  mat-expansion-panel:last-child {
    margin-bottom: 0;
  }
}
```

**Validación:**
- [ ] Desktop Light: Espacio adecuado entre acordeones ✅
- [ ] Desktop Dark: Espacio mantenido ✅
- [ ] Mobile Light: Touch targets ≥ 44x44px ✅
- [ ] Mobile Dark: Touch targets ≥ 44x44px ✅

---

### Bug #3: Tabla Baseline comparativa no se ve

**Archivos a modificar:**
- `baseline-comparativa.component.html`
- `baseline-comparativa.component.scss`

**Solución:**

```html
<!-- baseline-comparativa.component.html -->
<div class="table-responsive">
  <table mat-table [dataSource]="comparativaDataSource">
    <!-- columnas -->
  </table>
</div>

<!-- Mobile: Considerar vista alternativa -->
<div class="baseline-cards" *ngIf="isMobile">
  <mat-card *ngFor="let item of comparativaDataSource">
    <mat-card-header>
      <mat-card-title>{{ item.metric }}</mat-card-title>
    </mat-card-header>
    <mat-card-content>
      <div class="comparison">
        <span class="baseline">Baseline: {{ item.baseline }}</span>
        <span class="actual">Actual: {{ item.actual }}</span>
        <span class="variance" [class.positive]="item.variance > 0">
          Varianza: {{ item.variance }}%
        </span>
      </div>
    </mat-card-content>
  </mat-card>
</div>
```

```scss
// baseline-comparativa.component.scss
.baseline-cards {
  display: none;
  
  @media (max-width: 768px) {
    display: block;
    
    mat-card {
      margin-bottom: 12px;
    }
    
    .comparison {
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      span {
        display: block;
        
        &.positive {
          color: var(--success-color);
        }
        
        &.negative {
          color: var(--error-color);
        }
      }
    }
  }
}

.table-responsive {
  @media (max-width: 768px) {
    display: none;
  }
}
```

**Validación:**
- [ ] Desktop Light/Dark: Tabla se ve correctamente ✅
- [ ] Mobile Light/Dark: Cards se ven correctamente ✅

---

### Bug #4: Tabla Escenarios no se ve

**Archivos a modificar:**
- `escenarios-tab.component.html`
- `escenarios-tab.component.scss`

**Solución:**

```html
<!-- escenarios-tab.component.html -->
<div class="table-responsive">
  <table mat-table [dataSource]="escenariosDataSource">
    <!-- Priorizar columnas esenciales en mobile -->
    <ng-container matColumnDef="nombre">
      <th mat-header-cell *matHeaderCellDef>Nombre</th>
      <td mat-cell *matCellDef="let escenario">{{ escenario.nombre }}</td>
    </ng-container>
    
    <ng-container matColumnDef="descripcion">
      <th mat-header-cell *matHeaderCellDef>Descripción</th>
      <td mat-cell *matCellDef="let escenario">{{ escenario.descripcion }}</td>
    </ng-container>
    
    <ng-container matColumnDef="estado">
      <th mat-header-cell *matHeaderCellDef>Estado</th>
      <td mat-cell *matCellDef="let escenario">
        <span class="status-badge" [class]="escenario.estado">
          {{ escenario.estado }}
        </span>
      </td>
    </ng-container>
    
    <!-- Columnas secundarias ocultas en mobile -->
    <ng-container matColumnDef="creado" class="hide-mobile">
      <th mat-header-cell *matHeaderCellDef>Creado</th>
      <td mat-cell *matCellDef="let escenario">{{ escenario.creado | date:'short' }}</td>
    </ng-container>
    
    <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
    <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
  </table>
</div>
```

```typescript
// escenarios-tab.component.ts
displayedColumns = signal<string[]>([]);

ngOnInit() {
  this.checkViewport();
  window.addEventListener('resize', () => this.checkViewport());
}

checkViewport() {
  const isMobile = window.innerWidth < 768;
  
  if (isMobile) {
    this.displayedColumns.set(['nombre', 'estado']);
  } else {
    this.displayedColumns.set(['nombre', 'descripcion', 'estado', 'creado']);
  }
}
```

```scss
// escenarios-tab.component.scss
@media (max-width: 768px) {
  .hide-mobile {
    display: none !important;
  }
}
```

**Validación:**
- [ ] Desktop: Todas las columnas visibles ✅
- [ ] Mobile: Solo columnas esenciales (nombre, estado) ✅

---

### Bug #5: Tablas Admin sin scroll horizontal

**Archivos a crear:**
- `frontend/src/app/shared/directives/responsive-table.directive.ts`

**Solución: Directiva Global**

```typescript
// responsive-table.directive.ts
import { Directive, ElementRef, OnInit, Renderer2 } from '@angular/core';

@Directive({
  selector: '[appResponsiveTable]',
  standalone: true
})
export class ResponsiveTableDirective implements OnInit {
  
  constructor(
    private el: ElementRef,
    private renderer: Renderer2
  ) {}
  
  ngOnInit() {
    // Crear wrapper div
    const wrapper = this.renderer.createElement('div');
    this.renderer.addClass(wrapper, 'table-responsive');
    
    // Obtener padre del elemento
    const parent = this.el.nativeElement.parentNode;
    
    // Insertar wrapper antes de la tabla
    this.renderer.insertBefore(parent, wrapper, this.el.nativeElement);
    
    // Mover tabla dentro del wrapper
    this.renderer.appendChild(wrapper, this.el.nativeElement);
  }
}
```

**Aplicar en todas las tablas admin:**

```html
<!-- Antes -->
<table mat-table [dataSource]="dataSource">
  ...
</table>

<!-- Después -->
<table mat-table [dataSource]="dataSource" appResponsiveTable>
  ...
</table>
```

**Archivos a modificar:**
```
frontend/src/app/modules/proyectos/admin/
├── proyectos-admin-list/proyectos-admin-list.component.html
├── fases-admin-list/fases-admin-list.component.html
├── tareas-admin-list/tareas-admin-list.component.html
├── actividades-admin-list/actividades-admin-list.component.html
└── terceros-admin-list/terceros-admin-list.component.html (Bug #6)
```

**Validación:**
- [ ] Todas las tablas admin con scroll horizontal en mobile ✅
- [ ] Desktop sin cambios ✅
- [ ] Directiva reutilizable en todo el proyecto ✅

---

### Bug #6: Tabla global Terceros sin scroll

**Archivos a modificar:**
- `terceros-admin-list.component.html` (ya cubierto por directiva del Bug #5)

**Solución adicional: Vista Cards en Mobile (opcional)**

```html
<!-- terceros-admin-list.component.html -->

<!-- Desktop: Tabla -->
<table mat-table [dataSource]="tercerosDataSource" appResponsiveTable *ngIf="!isMobile">
  <!-- columnas -->
</table>

<!-- Mobile: Cards -->
<div class="terceros-cards" *ngIf="isMobile">
  <mat-card *ngFor="let tercero of tercerosDataSource">
    <mat-card-header>
      <mat-card-title>{{ tercero.nombre }}</mat-card-title>
      <mat-card-subtitle>{{ tercero.nit }}</mat-card-subtitle>
    </mat-card-header>
    <mat-card-content>
      <div class="tercero-info">
        <span class="tipo">{{ tercero.tipo }}</span>
        <span class="email">{{ tercero.email }}</span>
        <span class="telefono">{{ tercero.telefono }}</span>
      </div>
    </mat-card-content>
    <mat-card-actions>
      <button mat-icon-button [routerLink]="['/admin/terceros', tercero.id]">
        <mat-icon>visibility</mat-icon>
      </button>
      <button mat-icon-button (click)="editarTercero(tercero)">
        <mat-icon>edit</mat-icon>
      </button>
    </mat-card-actions>
  </mat-card>
</div>
```

```scss
// terceros-admin-list.component.scss
.terceros-cards {
  display: none;
  
  @media (max-width: 768px) {
    display: block;
    
    mat-card {
      margin-bottom: 12px;
      
      .tercero-info {
        display: flex;
        flex-direction: column;
        gap: 6px;
        
        span {
          font-size: 14px;
          
          &.tipo {
            font-weight: 500;
            color: var(--primary-color);
          }
        }
      }
    }
  }
}
```

**Validación:**
- [ ] Desktop: Tabla con directiva responsive ✅
- [ ] Mobile: Cards o tabla con scroll ✅

---

### Bug #7: Cantidad planificada sin formato miles

**Archivos a modificar:**
- `asignar-actividad-dialog.component.html`

**Solución Opción A: Pipe Number (simple)**

```html
<!-- Antes -->
<mat-form-field appearance="outline">
  <mat-label>Cantidad planificada</mat-label>
  <input matInput type="number" [(ngModel)]="cantidad" />
</mat-form-field>

<div class="cantidad-display">
  Cantidad: {{ cantidad }}
</div>

<!-- Después -->
<mat-form-field appearance="outline">
  <mat-label>Cantidad planificada</mat-label>
  <input matInput type="number" [(ngModel)]="cantidad" />
</mat-form-field>

<div class="cantidad-display">
  Cantidad: {{ cantidad | number:'1.0-2' }}
</div>
```

**Solución Opción B: Directiva Custom (avanzado)**

```typescript
// thousand-separator.directive.ts
import { Directive, ElementRef, HostListener, OnInit } from '@angular/core';

@Directive({
  selector: '[appThousandSeparator]',
  standalone: true
})
export class ThousandSeparatorDirective implements OnInit {
  
  private el: HTMLInputElement;
  
  constructor(private elementRef: ElementRef) {
    this.el = this.elementRef.nativeElement;
  }
  
  ngOnInit() {
    this.format(this.el.value);
  }
  
  @HostListener('input', ['$event'])
  onInput(event: any) {
    const value = this.el.value.replace(/[^0-9]/g, '');
    this.format(value);
  }
  
  @HostListener('blur')
  onBlur() {
    this.format(this.el.value);
  }
  
  private format(value: string) {
    if (!value) return;
    
    const numValue = parseInt(value.replace(/[^0-9]/g, ''), 10);
    if (isNaN(numValue)) return;
    
    this.el.value = numValue.toLocaleString('es-CO');
  }
}
```

```html
<!-- Con directiva -->
<input 
  matInput 
  type="text" 
  [(ngModel)]="cantidad" 
  appThousandSeparator 
/>
```

**Validación:**
- [ ] Desktop/Mobile: 10000 → 10,000 ✅
- [ ] Input permite solo números ✅
- [ ] Formato se mantiene al editar ✅

---

## 📝 ORDEN DE EJECUCIÓN RECOMENDADO

### Día 1 (4-5h): Quick Wins

1. Bug #1: Float tooltip (1h) ⚡
2. Bug #2: Acordeones spacing (1h) ⚡
3. Bug #7: Formato miles (1h) ⚡
4. Bug #3: Baseline tabla (1-2h)

### Día 2 (4-7h): Tablas Admin

5. Bug #5: Directiva responsive (2-3h) — **IMPORTANTE**
6. Bug #4: Escenarios tabla (1-2h)
7. Bug #6: Terceros tabla (1-2h)

**Razón del orden:** Empezar por fixes rápidos (1-2h), luego la directiva global (reutilizable), finalmente aplicarla en todas las tablas.

---

## 📦 ENTREGABLES

Al finalizar la Fase 3, debes tener:

1. ✅ **7 bugs mobile corregidos y validados**
2. ✅ **Directiva `[appResponsiveTable]` global creada**
3. ✅ **Informe completo:** `INFORME_FASE_3_MOBILE.md`
4. ✅ **Tareas Notion actualizadas** (estado: Completado)
5. ✅ **Módulo Proyectos 100% responsive mobile** (todos los bugs)

---

## 🎯 CRITERIO DE ÉXITO

La Fase 3 está completa cuando:

- ✅ Los 7 bugs de media/baja prioridad están corregidos
- ✅ Cada bug pasó validación 4x4 (Desktop/Mobile × Light/Dark)
- ✅ Directiva `[appResponsiveTable]` creada y documentada
- ✅ TODAS las tablas del módulo son responsive
- ✅ Sin regresiones en funcionalidad existente
- ✅ Código pusheado a rama `feature/mobile-responsive-fase-3`

---

## ⚠️ REGLAS CRÍTICAS

1. **SIEMPRE reutilizar clase `.table-responsive`**
   - Ya existe en `styles.scss` (Fase 1)
   - NO crear clases duplicadas

2. **SIEMPRE validar 4x4**
   - Desktop/Mobile × Light/Dark
   - NO saltarse validación

3. **SIEMPRE usar touch targets ≥ 44x44px**
   - Acordeones, botones, cards
   - Verificar en mobile

4. **DIRECTIVA reutilizable**
   - Standalone directive
   - Aplicable en cualquier tabla
   - Sin dependencias externas

5. **PRIORIZAR columnas en mobile**
   - Solo esenciales visibles
   - Secundarias ocultas
   - `displayedColumns` dinámico

---

## 📞 REFERENCIAS

- **Clase global:** `styles.scss` → `.table-responsive`
- **Fase 1 soluciones:** `INFORME_FASE_1_MOBILE.md`
- **Checklist validación:** `docs/base-reference/CHECKLIST-VALIDACION.md`
- **Backlog Notion:** https://www.notion.so/0f5116945f4346ffa18fee534371923c
- **Angular Material CDK:** https://material.angular.io/cdk/layout/overview
- **Directivas Angular:** https://angular.dev/guide/directives

---

**¡Ejecuta la Fase 3 y alcanza 100% responsive mobile!** 🚀
