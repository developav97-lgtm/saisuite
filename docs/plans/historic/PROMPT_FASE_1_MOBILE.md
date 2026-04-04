# PROMPT CLAUDE CODE CLI — FASE 1: QUICK WINS MOBILE
# Módulo Proyectos — Saicloud

**Objetivo:** Arreglar los 6 bugs de responsive mobile de **Alta Prioridad** para tener el Módulo de Proyectos 100% funcional en dispositivos móviles.

**Estimación total:** 10-16 horas  
**Modelo recomendado:** Claude Sonnet 4.6  
**Herramientas:** Browser + Thinking + Multi-agent

---

## 📋 BUGS A CORREGIR (6)

### 1. Pestañas de Tareas sin scroll horizontal (1-2h)
**Ubicación:** Detalle proyecto → Tab Tareas  
**Problema:** No se puede acceder a pestañas del fondo en mobile  
**Solución:** `overflow-x: auto` en mat-tab-labels

### 2. Filtros de proyectos no responsive (2-4h)
**Ubicación:** Lista de proyectos → Filtros  
**Problema:** Controles se salen del viewport  
**Solución:** Panel vertical con media query, mat-expansion-panel

### 3. Pestaña Fases sin scroll horizontal (1-2h)
**Ubicación:** Detalle proyecto → Tab Fases  
**Problema:** Tabla se corta  
**Solución:** Wrapper con class `table-responsive`

### 4. Tabla Terceros sin scroll horizontal (1-2h)
**Ubicación:** Detalle proyecto → Tab Terceros  
**Problema:** Nombres cortados  
**Solución:** Class `table-responsive`, ocultar columnas secundarias

### 5. Gantt mobile (4-8h) ⚠️ MÁS COMPLEJO
**Ubicación:** Detalle proyecto → Tab Gantt  
**Problema:** Colores no visibles, flechas no se ven, botones no se ajustan  
**Solución:** Zoom específico mobile, verificar dhtmlx-gantt responsive

### 6. Tabla Presupuesto sin scroll (2-4h)
**Ubicación:** Detalle proyecto → Tab Presupuesto (todas secciones)  
**Problema:** Tablas se salen sin scroll  
**Solución:** `table-responsive` en todas las secciones

---

## 🎯 METODOLOGÍA DE EJECUCIÓN

### PASO 1: Leer Contexto y Checklist

1. **Leer `CHECKLIST-VALIDACION.md`** completo
2. **Leer backlog en Notion:** https://www.notion.so/0f5116945f4346ffa18fee534371923c
3. **Entender el proyecto:**
   - Stack: Django 5 + Angular 18 + PostgreSQL 16
   - UI: Angular Material (NO PrimeNG)
   - Temas: Light + Dark mode

### PASO 2: Setup de Validación

```bash
# Asegurar que el servidor esté corriendo
cd /ruta/proyecto/saicloud
docker-compose up -d  # Si usa Docker

# O manualmente:
# Terminal 1 - Backend
source venv/bin/activate
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
ng serve
```

**Abrir navegador:**
- http://localhost:4200
- Login con usuario de prueba
- Navegar a Módulo Proyectos

### PASO 3: Validación Inicial (Baseline)

Para CADA uno de los 6 bugs:

1. **Abrir Chrome DevTools** (F12)
2. **Modo Responsive** (Cmd+Shift+M)
3. **Configurar viewport:** iPhone SE (375x667)
4. **Navegar a la ubicación del bug**
5. **Reproducir el problema** en:
   - Tema Claro
   - Tema Oscuro
6. **Capturar el estado actual** (anotar el problema específico)

### PASO 4: Implementar Fixes (Por Bug)

Para cada bug, ejecutar en ESTE ORDEN:

#### A. Análisis del Código
```bash
# Localizar el componente Angular afectado
# Ejemplo para bug #1 (Pestañas Tareas):
cd frontend/src/app/modules/proyectos/components
ls -la
# Identificar: proyecto-detalle.component.ts o tareas-tab.component.ts
```

**Usar `view` tool para leer:**
- Component TypeScript
- Component HTML
- Component SCSS
- Verificar si ya existe class `table-responsive` en global styles

#### B. Aplicar Fix

**Para bugs de scroll horizontal (#1, #3, #4, #6):**

1. Crear/verificar class global `table-responsive`:

```scss
// frontend/src/styles.scss o theme.scss
.table-responsive {
  display: block;
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch; // Smooth scroll iOS
  
  @media (max-width: 768px) {
    max-width: 100vw;
  }
  
  table {
    width: 100%;
    min-width: 600px; // Ajustar según tabla
  }
}

// Para tabs con scroll horizontal
.mat-tab-labels {
  @media (max-width: 768px) {
    overflow-x: auto !important;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }
}
```

2. Aplicar en componente HTML:

```html
<!-- Antes -->
<table mat-table [dataSource]="dataSource">
  ...
</table>

<!-- Después -->
<div class="table-responsive">
  <table mat-table [dataSource]="dataSource">
    ...
  </table>
</div>
```

**Para bug #2 (Filtros no responsive):**

1. Crear panel colapsable en mobile:

```html
<!-- Desktop -->
<div class="filters-desktop" *ngIf="!isMobile">
  <mat-form-field>
    <mat-label>Estado</mat-label>
    <mat-select [(ngModel)]="filtros.estado">
      <mat-option value="todos">Todos</mat-option>
      <!-- opciones -->
    </mat-select>
  </mat-form-field>
  
  <mat-form-field>
    <mat-label>Fase</mat-label>
    <mat-select [(ngModel)]="filtros.fase">
      <!-- opciones -->
    </mat-select>
  </mat-form-field>
  
  <!-- más filtros -->
</div>

<!-- Mobile -->
<mat-expansion-panel *ngIf="isMobile" class="filters-mobile">
  <mat-expansion-panel-header>
    <mat-panel-title>
      <mat-icon>filter_list</mat-icon>
      Filtros
    </mat-panel-title>
  </mat-expansion-panel-header>
  
  <div class="filters-mobile-content">
    <mat-form-field style="width: 100%; margin-bottom: 16px;">
      <mat-label>Estado</mat-label>
      <mat-select [(ngModel)]="filtros.estado">
        <mat-option value="todos">Todos</mat-option>
        <!-- opciones -->
      </mat-select>
    </mat-form-field>
    
    <mat-form-field style="width: 100%; margin-bottom: 16px;">
      <mat-label>Fase</mat-label>
      <mat-select [(ngModel)]="filtros.fase">
        <!-- opciones -->
      </mat-select>
    </mat-form-field>
    
    <!-- más filtros con width: 100% -->
  </div>
</mat-expansion-panel>
```

2. Agregar lógica en TypeScript:

```typescript
// component.ts
export class ProyectosListaComponent implements OnInit, OnDestroy {
  isMobile = false;
  private resizeSubscription?: Subscription;
  
  ngOnInit() {
    this.checkViewport();
    
    // Escuchar cambios de viewport
    this.resizeSubscription = fromEvent(window, 'resize')
      .pipe(debounceTime(200))
      .subscribe(() => this.checkViewport());
  }
  
  ngOnDestroy() {
    this.resizeSubscription?.unsubscribe();
  }
  
  private checkViewport() {
    this.isMobile = window.innerWidth < 768;
  }
}
```

**Para bug #5 (Gantt mobile - COMPLEJO):**

1. Identificar librería Gantt usada (dhtmlx-gantt, ng-gantt, custom)
2. Verificar documentación responsive de la librería
3. Aplicar configuración mobile:

```typescript
// Ejemplo con dhtmlx-gantt
gantt.config.scale_unit = this.isMobile ? "day" : "week";
gantt.config.date_scale = this.isMobile ? "%d %M" : "%d %M %Y";
gantt.config.min_column_width = this.isMobile ? 50 : 70;

// Botones responsive
if (this.isMobile) {
  // Usar mat-icon-button en vez de mat-button
}
```

4. Ajustar colores para mobile (verificar contraste):

```scss
// gantt.component.scss
.gantt-mobile {
  @media (max-width: 768px) {
    .gantt_task_line {
      border: 2px solid var(--primary-color);
      background: var(--primary-light);
    }
    
    .gantt_link_arrow {
      border-color: var(--accent-color);
      width: 3px; // Más grueso para visibilidad
    }
  }
}
```

#### C. Validar el Fix (CHECKLIST COMPLETO)

Para CADA bug corregido, validar en **4 combinaciones:**

1. **Desktop Light:**
   - Abrir http://localhost:4200
   - Viewport: 1920x1080
   - Tema: Claro
   - Verificar: ¿El fix NO rompió desktop?

2. **Desktop Dark:**
   - Cambiar a tema oscuro
   - Verificar: ¿Sigue funcionando correctamente?

3. **Mobile Light:**
   - DevTools Responsive: iPhone SE (375x667)
   - Tema: Claro
   - Verificar: ✅ ¿Bug corregido?
   - Verificar: ✅ ¿Scroll funciona?
   - Verificar: ✅ ¿Touch targets adecuados?

4. **Mobile Dark:**
   - Tema: Oscuro
   - Verificar: ✅ ¿Bug corregido en dark mode?
   - Verificar: ✅ ¿Contraste adecuado?

**Checklist de validación por bug:**

```markdown
## Bug #X: [Nombre]

### Desktop Light ✅/❌
- Navegación: ✅
- No rompe layout desktop: ✅

### Desktop Dark ✅/❌
- Contraste: ✅
- No rompe layout desktop: ✅

### Mobile Light ✅/❌
- Bug corregido: ✅
- Scroll funciona: ✅
- Touch targets: ✅
- Layout no roto: ✅

### Mobile Dark ✅/❌
- Bug corregido: ✅
- Contraste adecuado: ✅
- Scroll funciona: ✅

### Estado: ✅ APROBADO / ❌ REVISAR
```

#### D. Actualizar Base de Datos Notion

Después de corregir CADA bug:

```bash
# Actualizar tarea en Notion
# Estado: "Por hacer" → "Completado"
# Agregar comentario con:
# - Fecha de fix
# - Archivos modificados
# - Validación 4x4 completa
```

### PASO 5: Documentar Cambios

Al final de la fase, generar:

**1. INFORME_FASE_1_MOBILE.md**

```markdown
# Informe Fase 1: Quick Wins Mobile

**Fecha:** 2026-03-31  
**Bugs corregidos:** 6/6  
**Tiempo total:** X horas

## Bugs Corregidos

### 1. Pestañas Tareas sin scroll
- Archivos: `tareas-tab.component.html`, `styles.scss`
- Cambios: Agregado class `mat-tab-labels` con overflow-x
- Validación: ✅ 4x4 completa

[... para cada bug]

## Archivos Modificados
- `frontend/src/styles.scss` — Agregada class `.table-responsive`
- `frontend/src/app/modules/proyectos/components/proyecto-detalle/proyecto-detalle.component.ts` — Agregado `isMobile`
[... lista completa]

## Próximos Pasos
- Fase 2: Funcionalidades Alta Prioridad
```

**2. Actualizar tareas en Notion:**
- Cambiar estado a "Completado"
- Agregar comentarios con detalles

---

## ⚠️ REGLAS CRÍTICAS

### 1. NUNCA saltarse la validación 4x4
Cada bug DEBE validarse en las 4 combinaciones ANTES de marcarlo como completado.

### 2. NUNCA romper desktop por arreglar mobile
Siempre verificar que el fix NO afecta negativamente la vista desktop.

### 3. NUNCA hardcodear breakpoints inconsistentes
Usar SIEMPRE:
- Mobile: `< 768px`
- Tablet: `768px - 1024px`
- Desktop: `> 1024px`

### 4. NUNCA usar `!important` sin justificación
Si necesitas `!important`, documenta POR QUÉ.

### 5. SIEMPRE usar variables CSS del tema
```scss
// ❌ MAL
color: #000;
background: #fff;

// ✅ BIEN
color: var(--text-primary);
background: var(--background-primary);
```

---

## 🚀 ORDEN DE EJECUCIÓN RECOMENDADO

**Día 1 (4-6h):**
1. Bug #1: Pestañas Tareas (1-2h) ⚡
2. Bug #3: Pestaña Fases (1-2h) ⚡
3. Bug #4: Tabla Terceros (1-2h) ⚡

**Día 2 (4-6h):**
4. Bug #2: Filtros responsive (2-4h)
5. Bug #6: Tabla Presupuesto (2-4h)

**Día 3 (4-8h):**
6. Bug #5: Gantt mobile (4-8h) ⚠️

**Razón del orden:** Empezar por los más rápidos (quick wins) para generar momentum, dejar el Gantt (más complejo) para el final.

---

## 📦 ENTREGABLES

Al finalizar la Fase 1, debes tener:

1. ✅ **6 bugs mobile corregidos y validados**
2. ✅ **Informe completo** (`INFORME_FASE_1_MOBILE.md`)
3. ✅ **Tareas Notion actualizadas** (estado: Completado)
4. ✅ **Módulo Proyectos 100% funcional en mobile**
5. ✅ **Sin regresiones en desktop**

---

## 🎯 CRITERIO DE ÉXITO

La Fase 1 está completa cuando:

- ✅ Los 6 bugs de alta prioridad están corregidos
- ✅ Cada bug pasó validación 4x4 (Desktop/Mobile × Light/Dark)
- ✅ No hay regresiones en desktop
- ✅ No hay nuevos bugs introducidos
- ✅ Código pusheado a rama `feature/mobile-responsive-fase-1`
- ✅ Pull request creado y documentado

---

## 📞 REFERENCIAS

- **Checklist validación:** `CHECKLIST-VALIDACION.md`
- **Backlog Notion:** https://www.notion.so/0f5116945f4346ffa18fee534371923c
- **Módulo Proyectos:** https://www.notion.so/327ee9c3690a81f296a2ec384b557049
- **Angular Material Responsive:** https://material.angular.io/cdk/layout/overview
- **Touch Targets:** https://web.dev/accessible-tap-targets/

---

**¡Ejecuta la Fase 1 y prepara el módulo para producción mobile!** 🚀
