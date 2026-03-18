import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { BehaviorSubject, throwError } from 'rxjs';
import { catchError, filter, switchMap, take } from 'rxjs/operators';
import { AuthService } from '../auth/auth.service';
import { TokenRefreshResponse } from '../auth/auth.models';

const AUTH_ROUTES = ['/api/v1/auth/login/', '/api/v1/auth/refresh/'];

// Module-level state for serializing concurrent refresh attempts
const isRefreshing$ = new BehaviorSubject<boolean>(false);
const refreshToken$ = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getAccessToken();

  const cloned = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(cloned).pipe(
    catchError((error: HttpErrorResponse) => {
      const isAuthRoute = AUTH_ROUTES.some(route => req.url.includes(route));

      if (error.status !== 401 || isAuthRoute) {
        return throwError(() => error);
      }

      if (isRefreshing$.getValue()) {
        return refreshToken$.pipe(
          filter((t): t is string => t !== null),
          take(1),
          switchMap(newToken => {
            const retried = req.clone({ setHeaders: { Authorization: `Bearer ${newToken}` } });
            return next(retried);
          }),
        );
      }

      isRefreshing$.next(true);
      refreshToken$.next(null);

      return authService.refreshToken().pipe(
        switchMap((tokens: TokenRefreshResponse) => {
          isRefreshing$.next(false);
          refreshToken$.next(tokens.access);
          const retried = req.clone({ setHeaders: { Authorization: `Bearer ${tokens.access}` } });
          return next(retried);
        }),
        catchError(refreshError => {
          isRefreshing$.next(false);
          authService.logout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
