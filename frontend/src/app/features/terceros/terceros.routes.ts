import { Routes } from '@angular/router';

export const TERCEROS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/tercero-list-page/tercero-list-page.component').then(
        m => m.TerceroListPageComponent,
      ),
  },
  {
    path: 'nuevo',
    loadComponent: () =>
      import('./pages/tercero-form/tercero-form.component').then(
        m => m.TerceroFormComponent,
      ),
  },
  {
    path: ':id/editar',
    loadComponent: () =>
      import('./pages/tercero-form/tercero-form.component').then(
        m => m.TerceroFormComponent,
      ),
  },
];
