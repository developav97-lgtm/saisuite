import { inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { catchError, map, of } from 'rxjs';
import { AuthService } from '../auth/auth.service';

/**
 * Guard que verifica si la empresa del usuario tiene el módulo activo.
 * Uso en rutas:
 *   canActivate: [moduleAccessGuard],
 *   data: { requiredModule: 'proyectos' }
 */
export const moduleAccessGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router      = inject(Router);
  const http        = inject(HttpClient);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/auth/login']);
  }

  const requiredModule = route.data['requiredModule'] as string | undefined;
  if (!requiredModule) return true;

  const user = authService.currentUser();
  if (!user?.company) {
    return router.createUrlTree(['/dashboard']);
  }

  // Verificar acceso via API (la respuesta de /me/ incluye company con módulos)
  return http.get<{ modules: string[] }>(
    `/api/v1/companies/${user.company.id}/`
  ).pipe(
    map(company => {
      if (company.modules.includes(requiredModule)) return true;
      return router.createUrlTree(['/dashboard']);
    }),
    catchError(() => of(router.createUrlTree(['/dashboard']))),
  );
};
