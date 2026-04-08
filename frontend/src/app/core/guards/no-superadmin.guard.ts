import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';

export const noSuperAdminGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.currentUser();
  // SuperAdmins should not access module routes — redirect to their area
  if (user?.is_superadmin || user?.role === 'valmen_admin') {
    return router.createUrlTree(['/admin/tenants']);
  }
  return true;
};
