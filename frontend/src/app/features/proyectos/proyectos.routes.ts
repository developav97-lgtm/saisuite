import { Routes } from '@angular/router';
import { permissionGuard } from '../../core/guards/permission.guard';

export const PROYECTOS_ROUTES: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  {
    // Dashboard — home del módulo
    path: 'dashboard',
    loadComponent: () =>
      import('./components/proyecto-dashboard/proyecto-dashboard.component').then(
        (m) => m.ProyectoDashboardComponent
      ),
  },
  {
    // Lista completa de proyectos
    path: 'lista',
    loadComponent: () =>
      import('./components/proyecto-list/proyecto-list.component').then(
        (m) => m.ProyectoListComponent
      ),
  },
  {
    // Debe ir ANTES de :id para que no sea capturado como UUID
    path: 'tareas',
    loadComponent: () =>
      import('./components/tarea-list/tarea-list.component').then(
        (m) => m.TareaListComponent
      ),
  },
  {
    path: 'tareas/kanban',
    loadComponent: () =>
      import('./components/tarea-kanban/tarea-kanban.component').then(
        (m) => m.TareaKanbanComponent
      ),
  },
  {
    path: 'tareas/nueva',
    canActivate: [permissionGuard('tareas.create')],
    loadComponent: () =>
      import('./components/tarea-form/tarea-form.component').then(
        (m) => m.TareaFormComponent
      ),
  },
  {
    path: 'tareas/:id',
    canActivate: [permissionGuard('tareas.view')],
    loadComponent: () =>
      import('./components/tarea-detail/tarea-detail.component').then(
        (m) => m.TareaDetailComponent
      ),
  },
  {
    path: 'tareas/:id/editar',
    canActivate: [permissionGuard('tareas.edit')],
    loadComponent: () =>
      import('./components/tarea-form/tarea-form.component').then(
        (m) => m.TareaFormComponent
      ),
  },
  {
    path: 'configuracion',
    loadComponent: () =>
      import('./components/configuracion/configuracion.component').then(
        (m) => m.ConfiguracionComponent
      ),
  },
  {
    // Vista cards — debe ir ANTES de :id
    path: 'cards',
    loadComponent: () =>
      import('./components/proyecto-cards/proyecto-cards.component').then(
        (m) => m.ProyectoCardsComponent
      ),
  },
  {
    // Debe ir ANTES de :id para que no sea capturado como UUID
    path: 'actividades',
    loadComponent: () =>
      import('./components/actividad-list/actividad-list.component').then(
        (m) => m.ActividadListComponent
      ),
  },
  {
    // Debe ir ANTES de :id para que no sea capturado como UUID
    path: 'timesheets',
    loadComponent: () =>
      import('./components/timesheet-semanal/timesheet-semanal.component').then(
        (m) => m.TimesheetSemanalComponent
      ),
  },
  {
    // Vista "Mis Tareas" — debe ir ANTES de :id
    path: 'mis-tareas',
    loadComponent: () =>
      import('./components/tarea-list/tarea-list.component').then(
        (m) => m.TareaListComponent
      ),
    data: { misTareas: true },
  },
  {
    // Gestión de plantillas — debe ir ANTES de :id
    path: 'plantillas',
    canActivate: [permissionGuard('proyectos.create')],
    loadComponent: () =>
      import('./components/plantillas-page/plantillas-page.component').then(
        (m) => m.PlantillasPageComponent
      ),
  },
  {
    path: 'nuevo',
    canActivate: [permissionGuard('proyectos.create')],
    loadComponent: () =>
      import('./components/proyecto-form/proyecto-form.component').then(
        (m) => m.ProyectoFormComponent
      ),
  },
  {
    path: ':id',
    canActivate: [permissionGuard('proyectos.view')],
    loadComponent: () =>
      import('./components/proyecto-detail/proyecto-detail.component').then(
        (m) => m.ProyectoDetailComponent
      ),
  },
  {
    path: ':id/editar',
    canActivate: [permissionGuard('proyectos.edit')],
    loadComponent: () =>
      import('./components/proyecto-form/proyecto-form.component').then(
        (m) => m.ProyectoFormComponent
      ),
  },
];
