import { Routes } from '@angular/router';

export const PROYECTOS_ROUTES: Routes = [
  {
    path: '',
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
    loadComponent: () =>
      import('./components/tarea-form/tarea-form.component').then(
        (m) => m.TareaFormComponent
      ),
  },
  {
    path: 'tareas/:id',
    loadComponent: () =>
      import('./components/tarea-detail/tarea-detail.component').then(
        (m) => m.TareaDetailComponent
      ),
  },
  {
    path: 'tareas/:id/editar',
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
    path: 'nuevo',
    loadComponent: () =>
      import('./components/proyecto-form/proyecto-form.component').then(
        (m) => m.ProyectoFormComponent
      ),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./components/proyecto-detail/proyecto-detail.component').then(
        (m) => m.ProyectoDetailComponent
      ),
  },
  {
    path: ':id/editar',
    loadComponent: () =>
      import('./components/proyecto-form/proyecto-form.component').then(
        (m) => m.ProyectoFormComponent
      ),
  },
];
