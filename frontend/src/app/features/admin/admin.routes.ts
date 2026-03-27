import { Routes } from '@angular/router';
import { quickAccessGuard } from '../../shared/guards/quick-access.guard';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    children: [
      {
        path: 'usuarios',
        loadComponent: () =>
          import('./user-list/user-list.component').then(m => m.UserListComponent),
      },
      {
        path: 'usuarios/nuevo',
        canActivate: [quickAccessGuard],
        loadComponent: () =>
          import('./user-form/user-form.component').then(m => m.UserFormComponent),
      },
      {
        path: 'usuarios/:id',
        canActivate: [quickAccessGuard],
        loadComponent: () =>
          import('./user-form/user-form.component').then(m => m.UserFormComponent),
      },
      {
        path: 'empresa',
        loadComponent: () =>
          import('./company-settings/company-settings.component').then(m => m.CompanySettingsComponent),
      },
      {
        path: 'modulos',
        loadComponent: () =>
          import('./modules/modules.component').then(m => m.ModulesComponent),
      },
      {
        path: 'consecutivos',
        loadComponent: () =>
          import('./consecutivos/consecutivo-list.component').then(m => m.ConsecutivoListComponent),
      },
      {
        path: 'proyectos-config',
        loadComponent: () =>
          import('./proyectos-config/proyectos-config.component').then(m => m.ProyectosConfigComponent),
      },
      { path: '', redirectTo: 'usuarios', pathMatch: 'full' },
    ],
  },
];
