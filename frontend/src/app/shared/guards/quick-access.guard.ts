import { inject } from '@angular/core';
import { CanActivateFn } from '@angular/router';
import { QuickAccessNavigatorService } from '../services/quick-access-navigator.service';

/**
 * Guard que intercepta navegaciones cuando un QuickAccessDialog está activo.
 * Retorna false (cancela la navegación del router) y le pasa la URL al dialog.
 */
export const quickAccessGuard: CanActivateFn = (_route, state) => {
  const navigator = inject(QuickAccessNavigatorService);
  if (navigator.tryIntercept(state.url)) {
    return false; // navegación absorbida por el dialog
  }
  return true;
};
