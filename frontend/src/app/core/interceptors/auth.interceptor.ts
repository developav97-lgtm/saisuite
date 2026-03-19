import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { BehaviorSubject, throwError } from 'rxjs';
import { catchError, filter, switchMap, take } from 'rxjs/operators';
import { AuthService } from '../auth/auth.service';
import { TokenRefreshResponse } from '../auth/auth.models';

/** Rutas que nunca deben llevar el header Authorization. */
const PUBLIC_ROUTES = [
  '/api/v1/auth/login/',
  '/api/v1/auth/refresh/',
  '/api/v1/auth/register/',
];

// Module-level state for serializing concurrent refresh attempts
const isRefreshing$ = new BehaviorSubject<boolean>(false);
const refreshToken$ = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getAccessToken();

  const isPublic = PUBLIC_ROUTES.some(route => req.url.includes(route));

  // No adjuntar token en rutas públicas — SimpleJWT rechaza requests con
  // tokens expirados incluso cuando el endpoint tiene permission_classes = [AllowAny].
  const cloned = token && !isPublic
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(cloned).pipe(
    catchError((error: HttpErrorResponse) => {
      const isAuthRoute = PUBLIC_ROUTES.some(route => req.url.includes(route));

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
