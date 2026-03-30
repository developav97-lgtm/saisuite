import { HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../../../environments/environment';

/** Prepend API base URL to relative /api requests when not using proxy. */
export const baseUrlInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.url.startsWith('/api') || req.url.startsWith('/health')) {
    const apiBase = environment.apiBaseUrl ?? '';
    if (apiBase) {
      const cloned = req.clone({ url: `${apiBase}${req.url}` });
      return next(cloned);
    }
  }
  return next(req);
};
