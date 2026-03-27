import { Routes } from '@angular/router';
import { quickAccessGuard } from '../../shared/guards/quick-access.guard';

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
    canActivate: [quickAccessGuard],
    loadComponent: () =>
      import('./pages/tercero-form/tercero-form.component').then(
        m => m.TerceroFormComponent,
      ),
  },
  {
    path: ':id/editar',
    canActivate: [quickAccessGuard],
    loadComponent: () =>
      import('./pages/tercero-form/tercero-form.component').then(
        m => m.TerceroFormComponent,
      ),
  },
];
