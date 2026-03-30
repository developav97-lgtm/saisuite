import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';

/**
 * Guard de licencia.
 * Verifica que la empresa del usuario autenticado tenga una licencia activa.
 * Si no tiene licencia válida → redirige a /license-expired.
 *
 * Excepciones (siempre pasan):
 * - Superadmins (is_superadmin = true)
 * - Staff (is_staff = true)
 */
export const licenseGuard: CanActivateFn = () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  const user = auth.currentUser();
  if (!user) {
    return router.createUrlTree(['/auth/login']);
  }

  // Superadmin y staff siempre pasan
  if (user.is_superadmin || user.is_staff) {
    return true;
  }

  const license = user.company?.license;

  // Sin empresa asignada — no bloquear (el backend maneja este caso)
  if (!user.company) {
    return true;
  }

  // Sin licencia o licencia inválida → bloquear
  if (!license || !license.is_active_and_valid) {
    return router.createUrlTree(['/license-expired']);
  }

  return true;
};
