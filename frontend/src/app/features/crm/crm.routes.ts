/**
 * SaiSuite — CRM Routes
 * Lazy-loaded at /crm. Protegido por moduleAccessGuard + permissionGuard.
 */
import { Routes } from '@angular/router';

export const CRM_ROUTES: Routes = [
  // Entrada por defecto → Dashboard CRM
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  // Dashboard CRM
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./pages/dashboard/crm-dashboard-page.component').then(m => m.CrmDashboardPageComponent),
  },
  // Kanban / Pipeline
  {
    path: 'kanban',
    loadComponent: () =>
      import('./pages/kanban/kanban-page.component').then(m => m.KanbanPageComponent),
  },
  // Leads
  {
    path: 'leads',
    loadComponent: () =>
      import('./pages/leads/leads-page.component').then(m => m.LeadsPageComponent),
  },
  // Lead form — nuevo
  {
    path: 'leads/nuevo',
    loadComponent: () =>
      import('./pages/lead-form/lead-form-page.component').then(m => m.LeadFormPageComponent),
  },
  // Lead detail
  {
    path: 'leads/:id',
    loadComponent: () =>
      import('./pages/lead-detail/lead-detail-page.component').then(m => m.LeadDetailPageComponent),
  },
  // Lead form — editar
  {
    path: 'leads/:id/editar',
    loadComponent: () =>
      import('./pages/lead-form/lead-form-page.component').then(m => m.LeadFormPageComponent),
  },
  // Oportunidad form — nueva
  {
    path: 'oportunidades/nueva',
    loadComponent: () =>
      import('./pages/oportunidad-form/oportunidad-form-page.component').then(
        m => m.OportunidadFormPageComponent,
      ),
  },
  // Oportunidad form — editar
  {
    path: 'oportunidades/:id/editar',
    loadComponent: () =>
      import('./pages/oportunidad-form/oportunidad-form-page.component').then(
        m => m.OportunidadFormPageComponent,
      ),
  },
  // Oportunidad detail
  {
    path: 'oportunidades/:id',
    loadComponent: () =>
      import('./pages/oportunidad-detail/oportunidad-detail-page.component').then(
        m => m.OportunidadDetailPageComponent,
      ),
  },
  // Agenda
  {
    path: 'agenda',
    loadComponent: () =>
      import('./pages/agenda/crm-agenda-page.component').then(m => m.CrmAgendaPageComponent),
  },
  // Cotización detail
  {
    path: 'cotizaciones/:id',
    loadComponent: () =>
      import('./pages/cotizacion/cotizacion-page.component').then(m => m.CotizacionPageComponent),
  },
];
