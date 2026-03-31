# Checklist de Validación Obligatorio
# Saicloud — Multi-plataforma y Multi-tema

**Versión:** 1.0  
**Fecha:** 31 de Marzo de 2026  
**Aplicable a:** TODAS las features, componentes, y módulos de Saicloud

---

## 🎯 Propósito

Garantizar que **TODA** funcionalidad implementada en Saicloud funcione correctamente en:
- ✅ **Desktop** (1920x1080 y superior)
- ✅ **Mobile** (375x667 - iPhone SE, 360x800 - Android)
- ✅ **Tema Claro** (light mode)
- ✅ **Tema Oscuro** (dark mode)

**Regla de oro:** Una funcionalidad NO está completa hasta que pase este checklist en las 4 combinaciones.

---

## 📋 Checklist de Validación (OBLIGATORIO)

### ✅ Pre-requisito: Antes de Validar

- [ ] **Código implementado** (backend + frontend)
- [ ] **Tests unitarios PASS** (pytest + Karma)
- [ ] **Servidor corriendo** (Django en puerto 8000, Angular en puerto 4200)
- [ ] **Datos de prueba cargados** (fixtures o manual)

---

### 🖥️ VALIDACIÓN DESKTOP

#### Tema Claro (Light Mode)

- [ ] **Navegación:** Todos los links y botones funcionan
- [ ] **Formularios:** Todos los campos visibles y editables
- [ ] **Tablas:** Todas las columnas visibles, scroll horizontal si es necesario
- [ ] **Modales/Diálogos:** Se abren correctamente, no se cortan
- [ ] **Gráficos/Charts:** Se visualizan correctamente con colores adecuados
- [ ] **Imágenes/Iconos:** Se cargan y tienen contraste adecuado
- [ ] **Tooltips/Hints:** Aparecen en hover, son legibles
- [ ] **Validaciones:** Mensajes de error visibles y claros
- [ ] **Estados de carga:** Spinners/skeletons funcionan
- [ ] **Notificaciones:** Toast/snackbar aparecen correctamente

#### Tema Oscuro (Dark Mode)

- [ ] **Contraste:** Todos los textos legibles sobre fondos oscuros
- [ ] **Colores:** Paleta oscura aplicada (no inversión simple)
- [ ] **Bordes:** Visibles pero no invasivos
- [ ] **Iconos:** Colores ajustados para modo oscuro
- [ ] **Gráficos:** Colores adaptados (evitar negro sobre negro)
- [ ] **Formularios:** Inputs con borde visible
- [ ] **Estados hover/focus:** Visibles en modo oscuro
- [ ] **Imágenes:** Contraste adecuado o filtros aplicados
- [ ] **Sombras:** Ajustadas para modo oscuro (más sutiles)
- [ ] **Links:** Color diferenciado del texto normal

---

### 📱 VALIDACIÓN MOBILE (375px - 768px)

#### Tema Claro (Light Mode)

- [ ] **Responsive layout:** Todo el contenido visible sin zoom
- [ ] **Menú/Sidebar:** Hamburger menu funcional o drawer lateral
- [ ] **Tablas:** Scroll horizontal O vista de cards alternativa
- [ ] **Formularios:** Campos apilados verticalmente, width: 100%
- [ ] **Botones:** Tamaño mínimo 44x44px (touch target)
- [ ] **Pestañas/Tabs:** Scroll horizontal si son muchas
- [ ] **Modales:** Ocupan 100% del viewport o son scrollables
- [ ] **Gráficos:** Escalados correctamente, controles ajustados
- [ ] **Filtros:** Panel colapsable o drawer lateral
- [ ] **Espaciado:** Elementos no pegados, margin/padding adecuado
- [ ] **Tipografía:** Tamaño de fuente legible (mínimo 14px)
- [ ] **Scroll:** Funciona correctamente (vertical + horizontal donde se necesite)
- [ ] **Touch targets:** Separación mínima 8px entre botones
- [ ] **Orientación:** Funciona en portrait (preferido) y landscape

#### Tema Oscuro (Dark Mode)

- [ ] **Todos los checks de Tema Claro Mobile** ✅
- [ ] **Contraste mobile:** Textos legibles en pantallas pequeñas
- [ ] **Bordes:** Visibles en modo oscuro mobile
- [ ] **Estados touch:** Feedback visual al tocar (ripple, highlight)
- [ ] **Colores de estado:** Error/warning/success visibles

---

### 🔄 VALIDACIÓN DE TRANSICIONES

**Cambio de Tema (Light ↔ Dark):**
- [ ] **Sin recarga:** Transición suave sin recargar página
- [ ] **Persistencia:** Preferencia guardada (localStorage + backend)
- [ ] **Consistencia:** Todos los componentes cambian simultáneamente
- [ ] **Sin glitches:** No hay parpadeos o elementos que no cambian

**Cambio de Viewport (Desktop ↔ Mobile):**
- [ ] **Breakpoints:** Transiciones suaves en 768px, 1024px, 1440px
- [ ] **Elementos ocultos/visibles:** Se muestran/ocultan correctamente
- [ ] **Reorganización:** Layouts se ajustan sin romper
- [ ] **Scroll reset:** No aparecen scroll bars innecesarios

---

## 🛠️ Herramientas de Validación

### Chrome DevTools (Recomendado)

```bash
# Abrir DevTools: F12 o Cmd+Opt+I (Mac)

# Responsive Mode: Cmd+Shift+M (Mac) o Ctrl+Shift+M (Windows)
# Presets recomendados:
- iPhone SE (375x667)
- Pixel 5 (393x851)
- iPad (768x1024)
- Desktop (1920x1080)

# Cambiar tema:
# Opción 1: Toggle en app (botón light/dark)
# Opción 2: DevTools > Rendering > Emulate CSS prefers-color-scheme
```

### Validación Automatizada (Futuro)

```typescript
// E2E Test con Playwright
test.describe('Multi-platform validation', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'desktop', width: 1920, height: 1080 }
  ];
  
  const themes = ['light', 'dark'];
  
  for (const viewport of viewports) {
    for (const theme of themes) {
      test(`should work on ${viewport.name} with ${theme} theme`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await page.goto('/proyectos');
        await page.click(`[data-theme="${theme}"]`);
        
        // Assertions específicas
        await expect(page.locator('table')).toBeVisible();
        // ... más validaciones
      });
    }
  }
});
```

---

## 📝 Registro de Validación

Para cada feature completada, documentar:

```markdown
## Feature: [Nombre de la funcionalidad]

**Fecha validación:** 2026-03-31  
**Validado por:** Claude Code CLI / Desarrollador

### Desktop Light ✅
- Navegación: ✅
- Formularios: ✅
- Tablas: ✅
[...]

### Desktop Dark ✅
- Contraste: ✅
- Colores: ✅
[...]

### Mobile Light ✅
- Responsive: ✅
- Touch targets: ✅
[...]

### Mobile Dark ✅
- Contraste mobile: ✅
- Estados touch: ✅
[...]

### Observaciones
- Tabla de presupuesto requiere scroll horizontal en mobile
- Tema oscuro: ajustado color de iconos en gráfico Gantt

### Estado Final: ✅ APROBADO
```

---

## 🚨 Criterios de Rechazo

Una funcionalidad NO puede considerarse completa si:

❌ **No funciona en mobile** (responsive roto, scroll bloqueado, elementos cortados)  
❌ **No funciona en algún tema** (contraste ilegible, colores incorrectos, bordes invisibles)  
❌ **Touch targets < 44x44px** en mobile  
❌ **Tablas sin scroll horizontal** en mobile (a menos que tenga vista alternativa de cards)  
❌ **Texto ilegible** por falta de contraste  
❌ **Elementos superpuestos** en cualquier viewport  
❌ **Funcionalidad core inaccesible** en mobile  

---

## 🔧 Fixes Comunes

### Problema: Tabla sin scroll horizontal en mobile

**Solución:**
```scss
// global-styles.scss o component.scss
.table-responsive {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch; // iOS smooth scroll
  
  @media (max-width: 768px) {
    display: block;
    width: 100%;
  }
}
```

```html
<div class="table-responsive">
  <table mat-table [dataSource]="dataSource">
    <!-- columnas -->
  </table>
</div>
```

### Problema: Contraste insuficiente en dark mode

**Solución:**
```scss
// Usar variables CSS del tema
.card-title {
  color: var(--text-primary); // NO hardcodear #000 o #fff
}

// Material theming
@use '@angular/material' as mat;

$dark-theme: mat.define-dark-theme(( /* config */ ));

.dark-mode {
  @include mat.all-component-themes($dark-theme);
}
```

### Problema: Touch targets muy pequeños

**Solución:**
```scss
// Aplicar a botones/iconos en mobile
@media (max-width: 768px) {
  button, .icon-button {
    min-width: 44px;
    min-height: 44px;
    padding: 8px;
  }
  
  // Separación entre botones
  button + button {
    margin-left: 8px;
  }
}
```

### Problema: Filtros no caben en mobile

**Solución:**
```html
<!-- Desktop: inline -->
<div class="filters" *ngIf="!isMobile">
  <mat-form-field>...</mat-form-field>
  <mat-form-field>...</mat-form-field>
</div>

<!-- Mobile: expansion panel -->
<mat-expansion-panel *ngIf="isMobile">
  <mat-expansion-panel-header>
    Filtros
  </mat-expansion-panel-header>
  <div class="filters-mobile">
    <mat-form-field style="width: 100%">...</mat-form-field>
    <mat-form-field style="width: 100%">...</mat-form-field>
  </div>
</mat-expansion-panel>
```

```typescript
// component.ts
isMobile = false;

ngOnInit() {
  this.checkViewport();
  window.addEventListener('resize', () => this.checkViewport());
}

checkViewport() {
  this.isMobile = window.innerWidth < 768;
}
```

---

## 📚 Recursos

- **Angular Material Theming:** https://material.angular.io/guide/theming
- **Responsive Breakpoints:** Bootstrap estándar (576, 768, 992, 1200, 1400)
- **WCAG Contrast:** https://webaim.org/resources/contrastchecker/
- **Touch Target Size:** https://web.dev/accessible-tap-targets/

---

## ✅ Integración con Metodología Saicloud

Este checklist se integra en:

- **Fase 6: Protección de Ventana** → Validar multi-plataforma antes de avanzar
- **Fase 7: Revisión Final** → Checklist completo obligatorio
- **Fase 9: Validación UI/UX** → Énfasis en temas y responsive

**Archivo de referencia:** `CHECKLIST-VALIDACION.md`  
**Ubicación:** `/docs/base-reference/`

---

## 🎉 Beneficios

✅ **Experiencia de usuario consistente** en todas las plataformas  
✅ **Menos bugs reportados** en producción  
✅ **Documentación de validación** clara y trazable  
✅ **Ahorro de tiempo** al detectar issues temprano  
✅ **Producto profesional** desde el primer día  

---

**Última actualización:** 31 de Marzo de 2026  
**Mantenido por:** Equipo Saicloud — ValMen Tech
