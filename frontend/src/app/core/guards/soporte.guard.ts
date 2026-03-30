import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../auth/auth.service';

export const soporteGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.currentUser();
  if (user?.is_staff && !user.is_superadmin) {
    return true;
  }
  return router.createUrlTree(['/dashboard']);
};
