/**
 * SaiSuite — Tests authInterceptor
 */
import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../auth/auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let controller: HttpTestingController;
  let authService: AuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http        = TestBed.inject(HttpClient);
    controller  = TestBed.inject(HttpTestingController);
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    controller.verify();
    localStorage.clear();
  });

  it('añade Authorization header en rutas protegidas cuando hay token', () => {
    localStorage.setItem('access_token', 'my.access.token');
    http.get('/api/v1/proyectos/').subscribe();
    const req = controller.expectOne('/api/v1/proyectos/');
    expect(req.request.headers.get('Authorization')).toBe('Bearer my.access.token');
    req.flush([]);
  });

  it('no añade Authorization header en ruta pública /login/', () => {
    localStorage.setItem('access_token', 'my.access.token');
    http.post('/api/v1/auth/login/', {}).subscribe();
    const req = controller.expectOne('/api/v1/auth/login/');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('no añade Authorization header en ruta pública /refresh/', () => {
    localStorage.setItem('access_token', 'my.access.token');
    http.post('/api/v1/auth/refresh/', {}).subscribe();
    const req = controller.expectOne('/api/v1/auth/refresh/');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('no añade Authorization header en ruta pública /register/', () => {
    localStorage.setItem('access_token', 'my.access.token');
    http.post('/api/v1/auth/register/', {}).subscribe();
    const req = controller.expectOne('/api/v1/auth/register/');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('no añade Authorization header si no hay access token', () => {
    http.get('/api/v1/proyectos/').subscribe();
    const req = controller.expectOne('/api/v1/proyectos/');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush([]);
  });

  it('redirige a /license-expired en error 402', () => {
    const router = TestBed.inject(Router);
    spyOn(router, 'navigate');
    http.get('/api/v1/proyectos/').subscribe({ error: () => {} });
    const req = controller.expectOne('/api/v1/proyectos/');
    req.flush({ detail: 'Licencia vencida' }, { status: 402, statusText: 'Payment Required' });
    expect(router.navigate).toHaveBeenCalledWith(['/license-expired']);
  });

  it('propaga errores no-401', () => {
    let errorReceived = false;
    http.get('/api/v1/proyectos/').subscribe({ error: () => { errorReceived = true; } });
    const req = controller.expectOne('/api/v1/proyectos/');
    req.flush({ detail: 'Not found' }, { status: 404, statusText: 'Not Found' });
    expect(errorReceived).toBeTrue();
  });

  it('intenta refresh en error 401 en rutas protegidas', () => {
    localStorage.setItem('access_token', 'expired.token');
    localStorage.setItem('refresh_token', 'valid.refresh');

    http.get('/api/v1/proyectos/').subscribe({ error: () => {} });

    // Primera petición → 401
    const req1 = controller.expectOne('/api/v1/proyectos/');
    req1.flush({ detail: 'Token expired' }, { status: 401, statusText: 'Unauthorized' });

    // Intenta refresh
    const refreshReq = controller.expectOne('/api/v1/auth/refresh/');
    refreshReq.flush({ access: 'new.access', refresh: 'new.refresh' });

    // Reintenta la petición original con el nuevo token
    const req2 = controller.expectOne('/api/v1/proyectos/');
    expect(req2.request.headers.get('Authorization')).toBe('Bearer new.access');
    req2.flush([]);
  });

  it('llama logout si el refresh también falla', () => {
    localStorage.setItem('access_token', 'expired.token');
    localStorage.setItem('refresh_token', 'expired.refresh');
    spyOn(authService, 'logout').and.callFake(() => {});

    http.get('/api/v1/proyectos/').subscribe({ error: () => {} });

    const req1 = controller.expectOne('/api/v1/proyectos/');
    req1.flush({ detail: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });

    const refreshReq = controller.expectOne('/api/v1/auth/refresh/');
    refreshReq.flush({ detail: 'Refresh expired' }, { status: 401, statusText: 'Unauthorized' });

    expect(authService.logout).toHaveBeenCalled();
  });
});
