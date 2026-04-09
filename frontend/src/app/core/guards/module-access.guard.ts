import { inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from '../auth/auth.service';
import { ModuleTrialService } from '../services/module-trial.service';

/**
 * Guard que verifica si la empresa del usuario tiene el módulo activo.
 * Flujo:
 *   1. Si el módulo está en license.modules_included → permite acceso
 *   2. Si hay trial activo → permite acceso
 *   3. En cualquier otro caso → redirige a /acceso-modulo?module=<code>
 *
 * Uso en rutas:
 *   canActivate: [moduleAccessGuard],
 *   data: { requiredModule: 'proyectos' }
 */
export const moduleAccessGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService    = inject(AuthService);
  const moduleTrialSvc = inject(ModuleTrialService);
  const router         = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/auth/login']);
  }

  const requiredModule = route.data['requiredModule'] as string | undefined;
  if (!requiredModule) return true;

  const user = authService.currentUser();
  if (!user?.company) {
    return router.createUrlTree(['/dashboard']);
  }

  // Verificación local rápida: módulo en la licencia
  const modulesIncluded = user.company.license?.modules_included ?? [];
  if (modulesIncluded.includes(requiredModule)) return true;

  // Módulo no en licencia → verificar trial via API
  const lockedTree = router.createUrlTree(['/acceso-modulo'], {
    queryParams: { module: requiredModule },
  });

  return moduleTrialSvc.getStatus(requiredModule).pipe(
    map(status => (status.tiene_acceso ? true : lockedTree)),
    catchError(() => of(lockedTree)),
  );
};
