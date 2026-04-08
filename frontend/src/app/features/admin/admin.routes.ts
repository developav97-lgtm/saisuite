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
        path: 'consecutivos',
        loadComponent: () =>
          import('./consecutivos/consecutivo-list.component').then(m => m.ConsecutivoListComponent),
      },
      {
        path: 'proyectos-config',
        loadComponent: () =>
          import('./proyectos-config/proyectos-config.component').then(m => m.ProyectosConfigComponent),
      },
      {
        path: 'roles',
        loadComponent: () =>
          import('./roles/roles-list.component').then(m => m.RolesListComponent),
      },
      {
        path: 'tenants',
        loadComponent: () =>
          import('./tenants/tenant-list/tenant-list.component').then(m => m.TenantListComponent),
      },
      {
        path: 'tenants/nuevo',
        loadComponent: () =>
          import('./tenants/tenant-form/tenant-form.component').then(m => m.TenantFormComponent),
      },
      {
        path: 'tenants/:id',
        loadComponent: () =>
          import('./tenants/tenant-form/tenant-form.component').then(m => m.TenantFormComponent),
      },
      {
        path: 'usuarios-internos',
        loadComponent: () =>
          import('./internal-users/internal-user-list.component').then(m => m.InternalUserListComponent),
      },
      {
        path: 'usuarios-internos/nuevo',
        loadComponent: () =>
          import('./internal-users/internal-user-form.component').then(m => m.InternalUserFormComponent),
      },
      {
        path: 'usuarios-internos/:id',
        loadComponent: () =>
          import('./internal-users/internal-user-form.component').then(m => m.InternalUserFormComponent),
      },
      {
        path: 'packages',
        loadComponent: () =>
          import('./packages/package-catalog.component').then(m => m.PackageCatalogComponent),
      },
      {
        path: 'knowledge-base',
        loadComponent: () =>
          import('./knowledge-base/knowledge-base.component').then(m => m.KnowledgeBaseComponent),
      },
      { path: '', redirectTo: 'usuarios', pathMatch: 'full' },
    ],
  },
];
