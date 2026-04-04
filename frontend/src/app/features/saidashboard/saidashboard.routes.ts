import { Routes } from '@angular/router';
import { dashboardLicenseGuard } from './guards/dashboard-license.guard';

export const SAIDASHBOARD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./components/dashboard-list/dashboard-list.component').then(
        m => m.DashboardListComponent,
      ),
  },
  {
    path: 'nuevo',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/dashboard-builder/dashboard-builder.component').then(
        m => m.DashboardBuilderComponent,
      ),
  },
  {
    path: 'builder/:id',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/dashboard-builder/dashboard-builder.component').then(
        m => m.DashboardBuilderComponent,
      ),
  },
  {
    path: ':id',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/dashboard-viewer/dashboard-viewer.component').then(
        m => m.DashboardViewerComponent,
      ),
  },
];
