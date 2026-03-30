import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';

/**
 * Guard de permisos granulares.
 *
 * Uso en rutas:
 *   {
 *     path: 'nuevo',
 *     canActivate: [permissionGuard('proyectos.create')],
 *     loadComponent: ...
 *   }
 *
 * Superadmin y staff siempre tienen acceso.
 * Si el usuario no tiene el permiso → redirige a la ruta padre (quita el último segmento).
 */
export function permissionGuard(codigo: string): CanActivateFn {
  return (route, state) => {
    const auth   = inject(AuthService);
    const router = inject(Router);
    const user   = auth.currentUser();

    if (!user) return router.createUrlTree(['/auth/login']);

    // Superadmin y soporte siempre pasan
    if (user.is_superadmin || user.is_superuser || user.is_staff) return true;

    const permisos = user.rol_granular?.permisos ?? [];
    const tiene    = permisos.some(p => p.codigo === codigo);

    if (tiene) return true;

    // Redirigir al padre (ej: /proyectos/nuevo → /proyectos)
    const segments = state.url.split('/').filter(Boolean);
    const parentUrl = segments.length > 1
      ? '/' + segments.slice(0, -1).join('/')
      : '/dashboard';

    return router.createUrlTree([parentUrl]);
  };
}
