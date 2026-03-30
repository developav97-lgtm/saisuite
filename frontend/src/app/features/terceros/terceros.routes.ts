import { Routes } from '@angular/router';
import { quickAccessGuard } from '../../shared/guards/quick-access.guard';
import { permissionGuard } from '../../core/guards/permission.guard';

export const TERCEROS_ROUTES: Routes = [
  {
    path: '',
    canActivate: [permissionGuard('terceros.view')],
    loadComponent: () =>
      import('./pages/tercero-list-page/tercero-list-page.component').then(
        m => m.TerceroListPageComponent,
      ),
  },
  {
    path: 'nuevo',
    canActivate: [quickAccessGuard, permissionGuard('terceros.create')],
    loadComponent: () =>
      import('./pages/tercero-form/tercero-form.component').then(
        m => m.TerceroFormComponent,
      ),
  },
  {
    path: ':id/editar',
    canActivate: [quickAccessGuard, permissionGuard('terceros.edit')],
    loadComponent: () =>
      import('./pages/tercero-form/tercero-form.component').then(
        m => m.TerceroFormComponent,
      ),
  },
];
