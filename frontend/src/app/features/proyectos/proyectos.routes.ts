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
