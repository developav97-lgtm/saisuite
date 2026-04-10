// frontend/src/app/app.routes.ts
import { Routes } from '@angular/router';
import { ShellComponent } from './core/components/shell/shell.component';
import { authGuard } from './core/guards/auth.guard';
import { licenseGuard } from './core/guards/license.guard';
import { noSuperAdminGuard } from './core/guards/no-superadmin.guard';
import { moduleAccessGuard } from './core/guards/module-access.guard';

export const routes: Routes = [
    // ── Rutas PÚBLICAS (sin shell — login, recuperar contraseña) ────
    {
        path: 'auth',
        loadChildren: () =>
            import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES),
    },

    // ── Selector de tenant para usuario soporte (sin shell propio) ──
    {
        path: 'seleccionar-tenant',
        canActivate: [authGuard],
        loadComponent: () =>
            import('./features/soporte/selector-tenant/selector-tenant.component')
                .then(m => m.SelectorTenantComponent),
    },

    // ── Rutas PRIVADAS dentro del shell (autenticadas) ───────────────
    {
        path: '',
        component: ShellComponent,
        canActivate: [authGuard, licenseGuard],
        children: [
            {
                path: 'dashboard',
                canActivate: [noSuperAdminGuard],
                loadChildren: () =>
                    import('./features/dashboard/dashboard.routes').then(m => m.DASHBOARD_ROUTES),
            },
            // SaiVentas
            {
                path: 'ventas',
                loadChildren: () =>
                    import('./features/ventas/ventas.routes').then(m => m.VENTAS_ROUTES),
            },
            // SaiCobros
            {
                path: 'cobros',
                loadChildren: () =>
                    import('./features/cobros/cobros.routes').then(m => m.COBROS_ROUTES),
            },
            // Configuración — redirige a admin
            { path: 'configuracion', redirectTo: '/admin/empresa', pathMatch: 'full' },
            // Proyectos
            {
                path: 'proyectos',
                canActivate: [moduleAccessGuard],
                data: { requiredModule: 'proyectos' },
                loadChildren: () =>
                    import('./features/proyectos/proyectos.routes').then(m => m.PROYECTOS_ROUTES),
            },
            // Terceros — catálogo transversal
            {
                path: 'terceros',
                loadChildren: () =>
                    import('./features/terceros/terceros.routes').then(m => m.TERCEROS_ROUTES),
            },
            // Notificaciones
            {
                path: 'notificaciones',
                loadComponent: () =>
                    import('./features/notificaciones/notificaciones-list.component').then(
                        m => m.NotificacionesListComponent
                    ),
            },
            {
                path: 'notificaciones/configuracion',
                loadComponent: () =>
                    import('./features/notificaciones/components/configuracion/notificaciones-configuracion.component').then(
                        m => m.NotificacionesConfiguracionComponent
                    ),
            },
            // SaiDashboard — BI financiero
            {
                path: 'saidashboard',
                canActivate: [noSuperAdminGuard, moduleAccessGuard],
                data: { requiredModule: 'dashboard' },
                loadChildren: () =>
                    import('./features/saidashboard/saidashboard.routes').then(m => m.SAIDASHBOARD_ROUTES),
            },
            // Admin — gestión de empresa, usuarios y módulos
            {
                path: 'admin',
                loadChildren: () =>
                    import('./features/admin/admin.routes').then(m => m.ADMIN_ROUTES),
            },
                    // Módulo bloqueado (sin licencia / sin trial)
            {
                path: 'acceso-modulo',
                loadComponent: () =>
                    import('./shared/components/module-locked/module-locked.component').then(
                        m => m.ModuleLockedComponent
                    ),
            },
            // Redirect por defecto al dashboard
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
        ],
    },

    // Licencia vencida / bloqueada
    {
        path: 'license-expired',
        loadComponent: () =>
            import('./features/license-expired/license-expired.component').then(m => m.LicenseExpiredComponent),
    },

    // Fallback
    { path: '**', redirectTo: '/auth/login' },
];
