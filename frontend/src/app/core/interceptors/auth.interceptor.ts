// frontend/src/app/core/interceptors/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';

// Interceptor funcional — formato Angular 17+ standalone
// Se registra en app.config.ts con withInterceptors([authInterceptor])
export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const token = localStorage.getItem('access_token');

    if (token) {
        const cloned = req.clone({
            setHeaders: { Authorization: `Bearer ${token}` },
        });
        return next(cloned);
    }

    return next(req);
};