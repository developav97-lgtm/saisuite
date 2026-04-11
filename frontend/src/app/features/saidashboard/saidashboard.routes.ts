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
  // ── Reportes BI ──────────────────────────────────────────
  {
    path: 'reportes',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/report-list/report-list.component').then(
        m => m.ReportListComponent,
      ),
  },
  {
    path: 'reportes/nuevo',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/report-builder/report-builder.component').then(
        m => m.ReportBuilderComponent,
      ),
  },
  {
    path: 'reportes/:id/edit',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/report-builder/report-builder.component').then(
        m => m.ReportBuilderComponent,
      ),
  },
  {
    path: 'reportes/:id',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/report-viewer/report-viewer.component').then(
        m => m.ReportViewerComponent,
      ),
  },
  // ── Dashboards (catch-all para :id debe ir al final) ───
  {
    path: ':id',
    canActivate: [dashboardLicenseGuard],
    loadComponent: () =>
      import('./components/dashboard-viewer/dashboard-viewer.component').then(
        m => m.DashboardViewerComponent,
      ),
  },
];
