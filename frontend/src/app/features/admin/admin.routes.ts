import { Routes } from '@angular/router';

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
        loadComponent: () =>
          import('./user-form/user-form.component').then(m => m.UserFormComponent),
      },
      {
        path: 'usuarios/:id',
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
      { path: '', redirectTo: 'usuarios', pathMatch: 'full' },
    ],
  },
];
