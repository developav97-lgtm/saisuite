import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, catchError, of } from 'rxjs';
import { TrialService } from '../services/trial.service';

/**
 * Guard that checks if the user has access to the SaiDashboard module
 * (either via active license or trial). If not, redirects to the
 * dashboard list which will show the trial activation banner.
 */
export const dashboardLicenseGuard: CanActivateFn = () => {
  const trialService = inject(TrialService);
  const router = inject(Router);

  return trialService.getStatus().pipe(
    map(status => {
      if (status.tiene_acceso) {
        return true;
      }
      // Redirect to the module landing page which shows the trial banner
      return router.createUrlTree(['/saidashboard']);
    }),
    catchError(() => {
      // On error, allow access — the component will handle the error state
      return of(true);
    }),
  );
};
