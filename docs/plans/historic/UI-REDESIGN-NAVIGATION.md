# UI Redesign — Navegación por Módulos
# SaiSuite · ValMen Tech
# Fecha: 2026-03-26

---

## Resumen ejecutivo

Este documento especifica la nueva arquitectura de navegación de SaiSuite post-login.
El objetivo es introducir un **landing de módulos** que reemplace la navegación actual
(sidebar global con todos los items de todos los módulos) por un modelo donde:

1. Al hacer login el usuario llega a un **selector de módulos** (cards).
2. Al entrar a un módulo (ej: Proyectos) el **sidebar muestra solo los ítems de ese módulo**.
3. Las vistas de Tasks incluyen un **toggle Kanban/Lista** persistido en localStorage.
4. La lista de Proyectos incorpora una **vista Cards** con métricas.

### Restricciones absolutas (no negociables)
- **Angular Material únicamente**: `mat-card`, `mat-icon`, `mat-sidenav`, `mat-toolbar`, etc.
- **NUNCA** PrimeNG (`p-card`, `p-button`, etc.) — prohibido por DEC-011.
- **NUNCA** Bootstrap ni Tailwind.
- Iconos: Material Icons con `mat-icon`.
- Variables CSS: `var(--sc-*)` siempre, sin colores hardcodeados.
- Dark mode: clase `.dark-theme` en `<body>`, gestionada por `ThemeService`.
- Sintaxis Angular 18: `@if` / `@for` / `@switch` — nunca `*ngIf` / `*ngFor`.
- `ChangeDetectionStrategy.OnPush` en todos los componentes.

---

## 1. Componentes a crear

| Selector | Archivo | Descripción |
|---|---|---|
| `app-module-launcher` | `features/modules/components/module-launcher/` | Landing post-login — grid de módulos |
| `app-module-card` | `features/modules/components/module-card/` | Card individual de módulo (activo / coming-soon) |
| `app-proyectos-sidebar` | `features/proyectos/components/proyectos-sidebar/` | Sidebar contextual del módulo Proyectos |
| `app-task-view-toggle` | `features/proyectos/components/task-view-toggle/` | Toggle Kanban / Lista con persistencia localStorage |
| `app-proyecto-card` | `features/proyectos/components/proyecto-card/` | Card de proyecto con métricas (progreso, horas, tareas) |
| `app-proyectos-card-list` | `features/proyectos/components/proyectos-card-list/` | Grid responsivo de proyecto-cards |

### Archivos a modificar

| Archivo | Cambio |
|---|---|
| `frontend/src/app/app.routes.ts` | Agregar ruta `/modulos` (landing) y redirect post-login |
| `frontend/src/app/core/components/shell/shell.component.html` | Soporte para sidebar contextual (slot de contenido dinámico) |
| `frontend/src/app/core/components/sidebar/sidebar.component.ts` | Cargar `navSections` según módulo activo desde `ModuleContextService` |
| `frontend/src/app/features/proyectos/components/proyecto-list/proyecto-list.component.html` | Agregar toggle tabla/cards |
| `frontend/src/styles.scss` | Agregar variables CSS nuevas `--sc-module-*` |

---

## 2. Wireframes ASCII

### 2.1 Landing de módulos (post-login)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TOPBAR: Logo SaiCloud                            [ThemeToggle] [Avatar] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                         Bienvenido, Juan                                 │
│                    ¿A qué módulo quieres acceder?                       │
│                                                                          │
│   ┌─────────────────────┐   ┌─────────────────────┐                    │
│   │  [work]             │   │  [people]            │                    │
│   │                     │   │                      │                    │
│   │  Gestión de         │   │  CRM                 │                    │
│   │  Proyectos          │   │                      │                    │
│   │                     │   │  Próximamente        │  (coming soon)     │
│   │  ► Abrir módulo     │   │                      │                    │
│   └─────────────────────┘   └─────────────────────┘                    │
│                                                                          │
│   ┌─────────────────────┐   ┌─────────────────────┐                    │
│   │  [support_agent]    │   │  [account_balance]   │                    │
│   │                     │   │                      │                    │
│   │  Soporte            │   │  Finanzas            │                    │
│   │                     │   │                      │                    │
│   │  Próximamente       │   │  Próximamente        │  (coming soon)     │
│   └─────────────────────┘   └─────────────────────┘                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Layout con sidebar contextual (módulo Proyectos activo)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  TOPBAR: [☰] SaiCloud > Proyectos                  [Theme] [Avatar]      │
├──────────┬───────────────────────────────────────────────────────────────┤
│          │                                                                │
│ SIDEBAR  │  CONTENIDO PRINCIPAL (router-outlet)                          │
│          │                                                                │
│ ← Módulos│  ┌──────────────────────────────────────────────────────┐    │
│          │  │ sc-page-header                                        │    │
│ ─────    │  │  h1: Proyectos              [+ Nuevo Proyecto]        │    │
│          │  └──────────────────────────────────────────────────────┘    │
│ [home]   │                                                                │
│ Dashboard│  ┌─────────────── Filtros (sc-card) ────────────────────┐    │
│          │  │ [Buscar…]   [Estado ▼]   [Tipo ▼]   [Tabla | Cards]  │    │
│ [list]   │  └──────────────────────────────────────────────────────┘    │
│ Proyectos│                                                                │
│          │  ┌──── mat-table ──────────────────────────────────────┐     │
│ [task_alt│  │  CÓDIGO │ NOMBRE │ ESTADO │ CLIENTE │ FECHA │ ...   │     │
│ Tareas   │  ├─────────────────────────────────────────────────────┤     │
│ [▤][≡]   │  │  PRY-001  Migración BD  En ejecución  SAI S.A  ...  │     │
│          │  └──────────────────────────────────────────────────────┘    │
│ [contacts│                                                                │
│ Terceros │  [◄◄] [◄] 1–25 de 48  [►] [►►]                              │
│          │                                                                │
│ [timer]  │                                                                │
│ Mis Horas│                                                                │
│          │                                                                │
│ ─────    │                                                                │
│ [ValMen] │                                                                │
│ v1.0.0   │                                                                │
└──────────┴───────────────────────────────────────────────────────────────┘
```

### 2.3 Toggle Kanban / Lista

```
┌──────────────────────────────────────────────────────────────────────────┐
│  sc-page-header                                                           │
│    h1: Tareas                         [mat-button-toggle-group]           │
│                                       ┌──────────┬──────────┐            │
│                                       │ [▤] Lista│[▦]Kanban │            │
│                                       └──────────┴──────────┘            │
│  @if (view === 'list') { <app-tareas-list /> }                            │
│  @if (view === 'kanban') { <app-tareas-kanban /> }                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Vista Cards de Proyectos

```
┌──────────────────────────────────────────────────────────────────────────┐
│  [Tabla] [Cards]  ← mat-button-toggle-group en el header de filtros      │
│                                                                           │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐ │
│  │ PRY-001            │  │ PRY-002            │  │ PRY-003            │ │
│  │ Migración a la nube│  │ App Móvil          │  │ ERP v2             │ │
│  │ [En ejecución]     │  │ [Planificado]      │  │ [Borrador]         │ │
│  │                    │  │                    │  │                    │ │
│  │ Cliente: SAI S.A.S │  │ Cliente: ValMen    │  │ Cliente: TechCorp  │ │
│  │                    │  │                    │  │                    │ │
│  │ ████████████░░ 75% │  │ ░░░░░░░░░░░░░░  0% │  │ ████░░░░░░░░░ 30% │ │
│  │                    │  │                    │  │                    │ │
│  │ Tareas: 15/20      │  │ Tareas: 0/8        │  │ Tareas: 6/20       │ │
│  │ Horas:  120/160    │  │ Horas:  0/80       │  │ Horas:  45/150     │ │
│  │                    │  │                    │  │                    │ │
│  │            [►]     │  │            [►]     │  │            [►]     │ │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Variables CSS nuevas

Agregar en `frontend/src/styles.scss` dentro de `:root` y `body.dark-theme`:

```scss
// ── Colores de módulos ─────────────────────────────────────────────────
:root {
  /* Proyectos — azul principal */
  --sc-module-blue-bg:     #e8f0fe;
  --sc-module-blue-icon:   #1565c0;
  --sc-module-blue-border: #b3c6f5;

  /* CRM — teal */
  --sc-module-teal-bg:     #e0f7f4;
  --sc-module-teal-icon:   #00796b;
  --sc-module-teal-border: #b2dfdb;

  /* Soporte — naranja */
  --sc-module-orange-bg:   #fff3e0;
  --sc-module-orange-icon: #e65100;
  --sc-module-orange-border: #ffe0b2;

  /* Finanzas — verde */
  --sc-module-green-bg:    #f1f8e9;
  --sc-module-green-icon:  #2e7d32;
  --sc-module-green-border: #dcedc8;

  /* Coming soon — gris neutro */
  --sc-module-muted-bg:    var(--sc-surface-ground);
  --sc-module-muted-icon:  var(--sc-text-light);
  --sc-module-muted-border: var(--sc-surface-border);
}

body.dark-theme {
  --sc-module-blue-bg:     #0d2137;
  --sc-module-blue-icon:   #90caf9;
  --sc-module-blue-border: #1e3a5f;

  --sc-module-teal-bg:     #003d35;
  --sc-module-teal-icon:   #80cbc4;
  --sc-module-teal-border: #00695c;

  --sc-module-orange-bg:   #2d1600;
  --sc-module-orange-icon: #ffb74d;
  --sc-module-orange-border: #4e2200;

  --sc-module-green-bg:    #0a1f0a;
  --sc-module-green-icon:  #a5d6a7;
  --sc-module-green-border: #1b5e20;

  --sc-module-muted-bg:    var(--sc-surface-ground);
  --sc-module-muted-icon:  var(--sc-text-light);
  --sc-module-muted-border: var(--sc-surface-border);
}
```

---

## 4. Nuevo servicio: ModuleContextService

**Ruta:** `frontend/src/app/core/services/module-context.service.ts`

```typescript
// frontend/src/app/core/services/module-context.service.ts
import { Injectable, signal } from '@angular/core';

export type ModuleId = 'proyectos' | 'crm' | 'soporte' | 'finanzas' | null;

@Injectable({ providedIn: 'root' })
export class ModuleContextService {
  readonly activeModule = signal<ModuleId>(null);

  setModule(id: ModuleId): void {
    this.activeModule.set(id);
  }

  clearModule(): void {
    this.activeModule.set(null);
  }
}
```

---

## 5. Componente: app-module-launcher

**Ruta:** `frontend/src/app/features/modules/components/module-launcher/`

### 5.1 Template HTML

```html
<!-- module-launcher.component.html -->
<div class="ml-page">

  <div class="ml-hero">
    <h1 class="ml-hero__title">Bienvenido, {{ userName() }}</h1>
    <p class="ml-hero__subtitle">¿A qué módulo quieres acceder?</p>
  </div>

  <div class="ml-grid">
    @for (mod of modules; track mod.id) {
      <app-module-card
        [module]="mod"
        (selected)="onModuleSelect($event)"
      />
    }
  </div>

</div>
```

### 5.2 TypeScript

```typescript
// module-launcher.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  signal,
  computed,
} from '@angular/core';
import { Router } from '@angular/router';
import { ModuleCardComponent, ModuleConfig } from '../module-card/module-card.component';
import { ModuleContextService } from '../../../../core/services/module-context.service';
import { AuthService } from '../../../../core/auth/auth.service';

@Component({
  selector: 'app-module-launcher',
  standalone: true,
  imports: [ModuleCardComponent],
  templateUrl: './module-launcher.component.html',
  styleUrl: './module-launcher.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModuleLauncherComponent {
  private readonly router = inject(Router);
  private readonly moduleContext = inject(ModuleContextService);
  private readonly authService = inject(AuthService);

  readonly userName = computed(() => {
    const user = this.authService.currentUser();
    return user?.first_name || user?.email || 'Usuario';
  });

  readonly modules: ModuleConfig[] = [
    {
      id: 'proyectos',
      label: 'Gestión de Proyectos',
      description: 'Proyectos, tareas, equipos y seguimiento de horas.',
      icon: 'work',
      route: '/proyectos',
      colorVar: 'blue',
      available: true,
    },
    {
      id: 'crm',
      label: 'CRM',
      description: 'Clientes, oportunidades y pipeline de ventas.',
      icon: 'people',
      route: '/crm',
      colorVar: 'teal',
      available: false,
    },
    {
      id: 'soporte',
      label: 'Soporte',
      description: 'Tickets, SLA y base de conocimiento.',
      icon: 'support_agent',
      route: '/soporte',
      colorVar: 'orange',
      available: false,
    },
    {
      id: 'finanzas',
      label: 'Finanzas',
      description: 'Facturación, cobros y reportes financieros.',
      icon: 'account_balance',
      route: '/finanzas',
      colorVar: 'green',
      available: false,
    },
  ];

  onModuleSelect(mod: ModuleConfig): void {
    if (!mod.available) return;
    this.moduleContext.setModule(mod.id as never);
    this.router.navigate([mod.route]);
  }
}
```

### 5.3 SCSS

```scss
// module-launcher.component.scss
.ml-page {
  padding: 2.5rem 2rem;
  max-width: 960px;
  margin: 0 auto;
}

.ml-hero {
  text-align: center;
  margin-bottom: 2.5rem;

  &__title {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--sc-text-color);
    margin: 0 0 0.5rem;
    letter-spacing: -0.02em;
  }

  &__subtitle {
    font-size: 1rem;
    color: var(--sc-text-muted);
    margin: 0;
  }
}

.ml-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.25rem;

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
}
```

---

## 6. Componente: app-module-card

**Ruta:** `frontend/src/app/features/modules/components/module-card/`

### 6.1 Interfaz

```typescript
export interface ModuleConfig {
  id: string;
  label: string;
  description: string;
  icon: string;          // Material Icon name
  route: string;
  colorVar: 'blue' | 'teal' | 'orange' | 'green';
  available: boolean;
}
```

### 6.2 Template HTML

```html
<!-- module-card.component.html -->
<mat-card
  class="mc-card"
  [class.mc-card--available]="module().available"
  [class.mc-card--muted]="!module().available"
  [class]="'mc-card mc-card--' + module().colorVar"
  (click)="onClick()"
  [attr.role]="module().available ? 'button' : null"
  [attr.tabindex]="module().available ? 0 : null"
  [attr.aria-label]="module().available
    ? 'Abrir módulo ' + module().label
    : module().label + ', próximamente'"
  (keydown.enter)="onClick()"
  (keydown.space)="onClick(); $event.preventDefault()"
>
  <mat-card-content class="mc-content">

    <div class="mc-icon-wrap">
      <mat-icon class="mc-icon">{{ module().icon }}</mat-icon>
    </div>

    <h2 class="mc-title">{{ module().label }}</h2>
    <p class="mc-description">{{ module().description }}</p>

    @if (module().available) {
      <div class="mc-cta">
        <span>Abrir módulo</span>
        <mat-icon class="mc-cta__arrow">arrow_forward</mat-icon>
      </div>
    } @else {
      <div class="mc-badge">
        <mat-icon class="mc-badge__icon">schedule</mat-icon>
        <span>Próximamente</span>
      </div>
    }

  </mat-card-content>
</mat-card>
```

### 6.3 TypeScript

```typescript
// module-card.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  input,
  output,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { ModuleConfig } from './module-card.model';

@Component({
  selector: 'app-module-card',
  standalone: true,
  imports: [MatCardModule, MatIconModule],
  templateUrl: './module-card.component.html',
  styleUrl: './module-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModuleCardComponent {
  readonly module = input.required<ModuleConfig>();
  readonly selected = output<ModuleConfig>();

  onClick(): void {
    if (this.module().available) {
      this.selected.emit(this.module());
    }
  }
}
```

### 6.4 SCSS

```scss
// module-card.component.scss
.mc-card {
  cursor: default;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  border: 1px solid var(--sc-surface-border) !important;
  min-height: 200px;

  // ── Colores por módulo ────────────────────────────────────
  &--blue   { --mc-bg: var(--sc-module-blue-bg);   --mc-icon-color: var(--sc-module-blue-icon);   --mc-border: var(--sc-module-blue-border);   }
  &--teal   { --mc-bg: var(--sc-module-teal-bg);   --mc-icon-color: var(--sc-module-teal-icon);   --mc-border: var(--sc-module-teal-border);   }
  &--orange { --mc-bg: var(--sc-module-orange-bg); --mc-icon-color: var(--sc-module-orange-icon); --mc-border: var(--sc-module-orange-border); }
  &--green  { --mc-bg: var(--sc-module-green-bg);  --mc-icon-color: var(--sc-module-green-icon);  --mc-border: var(--sc-module-green-border);  }

  // ── Estado disponible ─────────────────────────────────────
  &--available {
    cursor: pointer;
    border-color: var(--mc-border) !important;
    background: var(--mc-bg) !important;

    &:hover {
      transform: translateY(-3px);
      box-shadow: var(--sc-shadow-md) !important;
    }

    &:focus-visible {
      outline: 2px solid var(--sc-primary);
      outline-offset: 2px;
    }
  }

  // ── Estado coming soon ────────────────────────────────────
  &--muted {
    opacity: 0.65;
    background: var(--sc-module-muted-bg) !important;
    border-color: var(--sc-module-muted-border) !important;
  }
}

.mc-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1.5rem !important;
}

.mc-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(255,255,255,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.25rem;
  border: 1px solid var(--mc-border, var(--sc-surface-border));
}

.mc-icon {
  font-size: 1.5rem !important;
  width: 1.5rem !important;
  height: 1.5rem !important;
  color: var(--mc-icon-color, var(--sc-primary));
}

.mc-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--sc-text-color);
  margin: 0;
  letter-spacing: -0.01em;
}

.mc-description {
  font-size: 0.8125rem;
  color: var(--sc-text-muted);
  margin: 0;
  line-height: 1.4;
  flex: 1;
}

.mc-cta {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--mc-icon-color, var(--sc-primary));
  margin-top: 0.5rem;

  &__arrow {
    font-size: 1rem !important;
    width: 1rem !important;
    height: 1rem !important;
    transition: transform 0.15s ease;
  }

  .mc-card--available:hover & .mc-cta__arrow {
    transform: translateX(3px);
  }
}

.mc-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--sc-text-muted);
  background: var(--sc-surface-border);
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  width: fit-content;
  margin-top: 0.5rem;

  &__icon {
    font-size: 0.875rem !important;
    width: 0.875rem !important;
    height: 0.875rem !important;
  }
}
```

---

## 7. Componente: app-proyectos-sidebar

**Ruta:** `frontend/src/app/features/proyectos/components/proyectos-sidebar/`

Este componente NO reemplaza el `SidebarComponent` global. En su lugar, el `SidebarComponent`
existente leerá los `navSections` desde `ModuleContextService` cuando hay un módulo activo.

### 7.1 Modificación a SidebarComponent

En `sidebar.component.ts`, cambiar la forma en que `navSections` se calcula:

```typescript
// Agregar en sidebar.component.ts
import { ModuleContextService } from '../../services/module-context.service';
import { computed, inject } from '@angular/core';

// Dentro de la clase:
private readonly moduleContext = inject(ModuleContextService);

readonly navSections = computed<NavSection[]>(() => {
  const mod = this.moduleContext.activeModule();
  if (mod === 'proyectos') return this.proyectosNav;
  return this.globalNav;    // nav actual (dashboard + módulos + catálogos + sistema)
});

private readonly proyectosNav: NavSection[] = [
  {
    items: [
      {
        label: '← Módulos',
        icon: 'apps',
        route: '/modulos',
      },
    ],
  },
  {
    sectionLabel: 'Proyectos',
    items: [
      { label: 'Dashboard',  icon: 'home',         route: '/proyectos/dashboard' },
      { label: 'Proyectos',  icon: 'list',          route: '/proyectos' },
      { label: 'Tareas',     icon: 'task_alt',      route: '/proyectos/tareas' },
      { label: 'Terceros',   icon: 'contacts',      route: '/terceros' },
      { label: 'Mis Horas',  icon: 'timer',         route: '/proyectos/mis-horas' },
    ],
  },
  {
    sectionLabel: 'Config',
    items: [
      { label: 'Configuración', icon: 'tune', route: '/proyectos/configuracion' },
    ],
  },
];

private readonly globalNav: NavSection[] = [
  // ... contenido actual de navSections (sin cambios)
];
```

**Nota:** El item `← Módulos` navega a `/modulos` y limpia el módulo activo en el guard o resolver.

---

## 8. Componente: app-task-view-toggle

**Ruta:** `frontend/src/app/features/proyectos/components/task-view-toggle/`

### 8.1 Template HTML

```html
<!-- task-view-toggle.component.html -->
<mat-button-toggle-group
  class="tvt-toggle"
  [value]="currentView()"
  (change)="onViewChange($event.value)"
  hideSingleSelectionIndicator
  aria-label="Cambiar vista de tareas"
>
  <mat-button-toggle value="list" aria-label="Vista lista">
    <mat-icon>view_list</mat-icon>
  </mat-button-toggle>
  <mat-button-toggle value="kanban" aria-label="Vista Kanban">
    <mat-icon>view_kanban</mat-icon>
  </mat-button-toggle>
</mat-button-toggle-group>
```

### 8.2 TypeScript

```typescript
// task-view-toggle.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  output,
  signal,
} from '@angular/core';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';

export type TaskView = 'list' | 'kanban';
const STORAGE_KEY = 'sc_task_view';

@Component({
  selector: 'app-task-view-toggle',
  standalone: true,
  imports: [MatButtonToggleModule, MatIconModule],
  templateUrl: './task-view-toggle.component.html',
  styleUrl: './task-view-toggle.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TaskViewToggleComponent implements OnInit {
  readonly viewChanged = output<TaskView>();
  readonly currentView = signal<TaskView>('list');

  ngOnInit(): void {
    const stored = localStorage.getItem(STORAGE_KEY) as TaskView | null;
    if (stored === 'list' || stored === 'kanban') {
      this.currentView.set(stored);
      this.viewChanged.emit(stored);
    }
  }

  onViewChange(view: TaskView): void {
    this.currentView.set(view);
    localStorage.setItem(STORAGE_KEY, view);
    this.viewChanged.emit(view);
  }
}
```

### 8.3 SCSS

```scss
// task-view-toggle.component.scss
.tvt-toggle {
  // Hereda estilos de mat-button-toggle-group globales del tema M3
  // Solo ajustes de tamaño para integrarse en el sc-page-header
  .mat-button-toggle {
    height: 36px;
    line-height: 36px;

    .mat-icon {
      font-size: 1.125rem !important;
      width: 1.125rem !important;
      height: 1.125rem !important;
    }
  }
}
```

---

## 9. Componente: app-proyecto-card

**Ruta:** `frontend/src/app/features/proyectos/components/proyecto-card/`

### 9.1 Template HTML

```html
<!-- proyecto-card.component.html -->
<mat-card class="pc-card" (click)="verDetalle()" role="button" tabindex="0"
  [attr.aria-label]="'Ver proyecto ' + proyecto().nombre"
  (keydown.enter)="verDetalle()" (keydown.space)="verDetalle(); $event.preventDefault()">

  <mat-card-content class="pc-content">

    <!-- Header: código + estado -->
    <div class="pc-header">
      <span class="pc-codigo">{{ proyecto().codigo }}</span>
      <span [class]="estadoClass()">{{ estadoLabel() }}</span>
    </div>

    <!-- Nombre -->
    <h2 class="pc-nombre">{{ proyecto().nombre }}</h2>

    <!-- Cliente -->
    <p class="pc-cliente">
      <mat-icon class="pc-meta-icon">business</mat-icon>
      {{ proyecto().cliente_nombre }}
    </p>

    <!-- Progreso -->
    <div class="pc-progress-section">
      <div class="pc-progress-header">
        <span class="pc-progress-label">Progreso</span>
        <span class="pc-progress-pct">{{ progressPct() }}%</span>
      </div>
      <mat-progress-bar
        mode="determinate"
        [value]="progressPct()"
        class="pc-progress-bar"
      />
    </div>

    <!-- Métricas -->
    <div class="pc-metrics">
      <div class="pc-metric">
        <mat-icon class="pc-metric__icon">task_alt</mat-icon>
        <span class="pc-metric__value">{{ proyecto().tareas_completadas }}/{{ proyecto().tareas_total }}</span>
        <span class="pc-metric__label">tareas</span>
      </div>
      <div class="pc-metric">
        <mat-icon class="pc-metric__icon">timer</mat-icon>
        <span class="pc-metric__value">{{ proyecto().horas_registradas }}/{{ proyecto().horas_estimadas }}</span>
        <span class="pc-metric__label">horas</span>
      </div>
    </div>

    <!-- Fecha fin -->
    @if (proyecto().fecha_fin_planificada) {
      <p class="pc-fecha">
        <mat-icon class="pc-meta-icon">calendar_today</mat-icon>
        {{ proyecto().fecha_fin_planificada | date: 'dd/MM/yyyy' }}
      </p>
    }

  </mat-card-content>
</mat-card>
```

### 9.2 TypeScript

```typescript
// proyecto-card.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  output,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { ProyectoList } from '../../models/proyecto.model';

@Component({
  selector: 'app-proyecto-card',
  standalone: true,
  imports: [MatCardModule, MatIconModule, MatProgressBarModule, DatePipe],
  templateUrl: './proyecto-card.component.html',
  styleUrl: './proyecto-card.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProyectoCardComponent {
  readonly proyecto = input.required<ProyectoList>();
  readonly detailClick = output<string>();

  readonly progressPct = computed<number>(() => {
    const p = this.proyecto();
    if (!p.tareas_total || p.tareas_total === 0) return 0;
    return Math.round((p.tareas_completadas / p.tareas_total) * 100);
  });

  readonly estadoClass = computed<string>(() => {
    const estado = this.proyecto().estado;
    return `sc-status-chip sc-status-chip--${estado}`;
  });

  readonly estadoLabel = computed<string>(() => {
    const labels: Record<string, string> = {
      borrador:      'Borrador',
      planificado:   'Planificado',
      en_ejecucion:  'En ejecución',
      suspendido:    'Suspendido',
      cerrado:       'Cerrado',
      cancelado:     'Cancelado',
    };
    return labels[this.proyecto().estado] ?? this.proyecto().estado;
  });

  verDetalle(): void {
    this.detailClick.emit(this.proyecto().id);
  }
}
```

### 9.3 SCSS

```scss
// proyecto-card.component.scss
.pc-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  height: 100%;

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--sc-shadow-md) !important;
  }

  &:focus-visible {
    outline: 2px solid var(--sc-primary);
    outline-offset: 2px;
  }
}

.pc-content {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 1.25rem !important;
  height: 100%;
}

.pc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.pc-codigo {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--sc-primary);
  background: var(--sc-primary-light);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.pc-nombre {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--sc-text-color);
  margin: 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pc-cliente {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8125rem;
  color: var(--sc-text-muted);
  margin: 0;
}

.pc-meta-icon {
  font-size: 0.875rem !important;
  width: 0.875rem !important;
  height: 0.875rem !important;
}

.pc-progress-section {
  margin-top: auto;
}

.pc-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.3rem;
}

.pc-progress-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--sc-text-muted);
}

.pc-progress-pct {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--sc-primary);
}

.pc-progress-bar {
  border-radius: 4px;
  height: 6px;
}

.pc-metrics {
  display: flex;
  gap: 1rem;
}

.pc-metric {
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &__icon {
    font-size: 0.875rem !important;
    width: 0.875rem !important;
    height: 0.875rem !important;
    color: var(--sc-text-muted);
  }

  &__value {
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--sc-text-color);
  }

  &__label {
    font-size: 0.75rem;
    color: var(--sc-text-muted);
  }
}

.pc-fecha {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  color: var(--sc-text-muted);
  margin: 0;
}
```

---

## 10. Componente: app-proyectos-card-list

**Ruta:** `frontend/src/app/features/proyectos/components/proyectos-card-list/`

### 10.1 Template HTML

```html
<!-- proyectos-card-list.component.html -->
@if (loading()) {
  <mat-progress-bar mode="indeterminate" class="pcl-progress" />
}

@if (!loading() && proyectos().length === 0) {
  <div class="sc-empty-state pcl-empty">
    <mat-icon>work_outline</mat-icon>
    <p>No hay proyectos que coincidan con los filtros.</p>
    <button mat-raised-button color="primary" (click)="nuevo.emit()">
      <mat-icon>add</mat-icon> Nuevo proyecto
    </button>
  </div>
}

@if (!loading() && proyectos().length > 0) {
  <div class="pcl-grid">
    @for (p of proyectos(); track p.id) {
      <app-proyecto-card
        [proyecto]="p"
        (detailClick)="detailClick.emit($event)"
      />
    }
  </div>
}
```

### 10.2 TypeScript

```typescript
// proyectos-card-list.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  input,
  output,
} from '@angular/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { ProyectoCardComponent } from '../proyecto-card/proyecto-card.component';
import { ProyectoList } from '../../models/proyecto.model';

@Component({
  selector: 'app-proyectos-card-list',
  standalone: true,
  imports: [MatProgressBarModule, MatIconModule, MatButtonModule, ProyectoCardComponent],
  templateUrl: './proyectos-card-list.component.html',
  styleUrl: './proyectos-card-list.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProyectosCardListComponent {
  readonly proyectos = input.required<ProyectoList[]>();
  readonly loading = input(false);
  readonly detailClick = output<string>();
  readonly nuevo = output<void>();
}
```

### 10.3 SCSS

```scss
// proyectos-card-list.component.scss
.pcl-progress {
  margin-bottom: 1rem;
  border-radius: var(--sc-radius);
}

.pcl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.25rem;

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
}

.pcl-empty {
  border: 1px solid var(--sc-surface-border);
  border-radius: var(--sc-radius);
}
```

---

## 11. Modificación: proyecto-list — Toggle Tabla/Cards

Agregar un `mat-button-toggle-group` en el header de filtros del componente
`proyecto-list.component.html` para alternar entre la tabla y la vista cards.

### 11.1 Cambio en el template (sección de filtros)

```html
<!-- Dentro de .pl-filters-card, agregar al final: -->
<mat-button-toggle-group
  class="pl-view-toggle"
  [value]="viewMode()"
  (change)="viewMode.set($event.value)"
  hideSingleSelectionIndicator
  aria-label="Cambiar vista"
>
  <mat-button-toggle value="table" aria-label="Vista tabla">
    <mat-icon>table_rows</mat-icon>
  </mat-button-toggle>
  <mat-button-toggle value="cards" aria-label="Vista cards">
    <mat-icon>grid_view</mat-icon>
  </mat-button-toggle>
</mat-button-toggle-group>
```

### 11.2 Cambio condicional en el cuerpo

```html
<!-- Reemplazar el bloque de mat-table + empty state + paginator por: -->

@if (viewMode() === 'table') {
  <!-- mat-table actual — sin cambios -->
  @if (loading()) { <mat-progress-bar mode="indeterminate" class="pl-progress" /> }
  <mat-table ...>...</mat-table>
  @if (!loading() && proyectos().length === 0) { ... empty state ... }
  <mat-paginator ... />
}

@if (viewMode() === 'cards') {
  <app-proyectos-card-list
    [proyectos]="proyectos()"
    [loading]="loading()"
    (detailClick)="verDetalle($event)"
    (nuevo)="nuevoProyecto()"
  />
}
```

### 11.3 Cambio en el TypeScript del componente

```typescript
// Agregar en proyecto-list.component.ts
readonly viewMode = signal<'table' | 'cards'>('table');
```

---

## 12. Modificaciones al routing

### 12.1 app.routes.ts — agregar ruta `/modulos`

```typescript
// Agregar dentro de las rutas hijas del ShellComponent:
{
  path: 'modulos',
  loadComponent: () =>
    import('./features/modules/components/module-launcher/module-launcher.component')
      .then(m => m.ModuleLauncherComponent),
},

// Cambiar el redirect por defecto:
{ path: '', redirectTo: 'modulos', pathMatch: 'full' },
```

### 12.2 Guard para limpiar contexto de módulo al ir a /modulos

```typescript
// En ModuleLauncherComponent.ngOnInit:
ngOnInit(): void {
  this.moduleContext.clearModule();
}
```

---

## 13. Accesibilidad

| Elemento | Atributo | Valor |
|---|---|---|
| `app-module-card` (disponible) | `role="button"`, `tabindex="0"` | Navegable con teclado |
| `app-module-card` (coming soon) | Sin `role` ni `tabindex` | No interactivo |
| `app-module-card` | `aria-label` | "Abrir módulo Proyectos" |
| `app-proyecto-card` | `role="button"`, `tabindex="0"` | Navegable con teclado |
| `app-task-view-toggle` | `aria-label` en group | "Cambiar vista de tareas" |
| Cards con teclado | `keydown.enter` + `keydown.space` | Activar con Enter y Space |
| `mat-progress-bar` en cards | `aria-label="Progreso del proyecto"` | Lectura por screen reader |

---

## 14. Orden de implementación

Seguir el orden de CLAUDE.md (sección 5):

```
1.  Crear ModuleContextService                          (core/services)
2.  Crear ModuleConfig interface + ModuleCardComponent  (features/modules)
3.  Crear ModuleLauncherComponent                       (features/modules)
4.  Agregar ruta /modulos en app.routes.ts
5.  Modificar SidebarComponent para leer navSections computed
6.  Crear TaskViewToggleComponent                       (features/proyectos)
7.  Crear ProyectoCardComponent                         (features/proyectos)
8.  Crear ProyectosCardListComponent                    (features/proyectos)
9.  Modificar proyecto-list.component (toggle + imports)
10. Agregar variables CSS nuevas en styles.scss
```

---

## 15. Checklist de conformidad (DEC-011 + UI-UX-STANDARDS)

- [ ] Solo Angular Material — cero PrimeNG, Bootstrap, Tailwind
- [ ] `ChangeDetectionStrategy.OnPush` en todos los componentes nuevos
- [ ] `input()` / `output()` signals (no decoradores `@Input` / `@Output`)
- [ ] `@if` / `@for` / `@switch` — ningún `*ngIf` / `*ngFor`
- [ ] Variables `var(--sc-*)` — ningún color hardcodeado
- [ ] Dark mode funciona con `.dark-theme` en `<body>`
- [ ] `mat-progress-bar` (no spinner) para estados de carga en listas
- [ ] Empty state `sc-empty-state` FUERA del `mat-table`
- [ ] Cards y toggle accesibles con teclado (Enter, Space, tabindex, aria-label)
- [ ] Ningún `any` en TypeScript
- [ ] `localStorage` para persistir toggle Kanban/Lista
- [ ] Module card "coming soon" no es interactiva (sin role/tabindex)
- [ ] Feedback de navegación con `MatSnackBar` si aplica (no `alert()`)
