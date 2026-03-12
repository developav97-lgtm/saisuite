// frontend/src/app/app.routes.ts
import { Routes } from '@angular/router';
import { ShellComponent } from './core/components/shell/shell.component';

export const routes: Routes = [
    // ── Rutas PÚBLICAS (sin shell — login, recuperar contraseña) ────
    {
        path: 'auth',
        loadChildren: () =>
            import('./features/auth/auth.routes').then(m => m.AUTH_ROUTES),
    },

    // ── Rutas PRIVADAS dentro del shell (autenticadas) ───────────────
    {
        path: '',
        component: ShellComponent,
        // canActivate: [authGuard],  ← descomentar cuando exista el guard
        children: [
            {
                path: 'dashboard',
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
            // Configuración
            {
                path: 'configuracion',
                loadChildren: () =>
                    import('./features/configuracion/configuracion.routes').then(m => m.CONFIGURACION_ROUTES),
            },
            // Redirect por defecto al dashboard
            { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
        ],
    },

    // Fallback
    { path: '**', redirectTo: 'dashboard' },
];