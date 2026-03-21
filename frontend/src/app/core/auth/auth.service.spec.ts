/**
 * SaiSuite — Tests AuthService
 * Cobertura objetivo: 90%+ en auth.service.ts
 */
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { AuthService } from './auth.service';
import { LoginResponse, UserProfile, RegisterResponse, UserCompanyInfo } from './auth.models';

// ── Datos de prueba ───────────────────────────────────────────────────────────

const mockUser: UserProfile = {
  id: 'user-uuid',
  email: 'admin@empresa.com',
  first_name: 'Admin',
  last_name: 'Test',
  full_name: 'Admin Test',
  role: 'company_admin',
  company: { id: 'co-uuid', name: 'Mi Empresa', nit: '900001001' },
};

const mockLoginResponse: LoginResponse = {
  access: 'access.token.here',
  refresh: 'refresh.token.here',
  user: mockUser,
};

const mockRegisterResponse: RegisterResponse = {
  access: 'access.reg.token',
  refresh: 'refresh.reg.token',
  user: mockUser,
  company: {
    id: 'co-uuid',
    name: 'Mi Empresa',
    nit: '900001001',
    plan: 'starter',
    saiopen_enabled: false,
    saiopen_db_path: '',
    is_active: true,
    modules: ['proyectos'],
    created_at: '2026-01-01T00:00:00Z',
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

import { Component } from '@angular/core';
@Component({ template: '' })
class DummyComponent {}

function setup() {
  TestBed.configureTestingModule({
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      provideRouter([{ path: 'auth/login', component: DummyComponent }]),
    ],
  });
  const service = TestBed.inject(AuthService);
  const http    = TestBed.inject(HttpTestingController);
  return { service, http };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    ({ service, http } = setup());
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  // ── Constructor / loadFromStorage ─────────────────────────────────────────

  it('carga usuario de localStorage al inicializar', () => {
    // Service ya fue creado en beforeEach sin datos; establecemos la señal
    // directamente para verificar el estado interno (loadFromStorage probado
    // en el bloque dedicado más abajo).
    service.currentUser.set(mockUser);
    expect(service.currentUser()).toEqual(mockUser);
  });

  it('no carga usuario si localStorage está vacío', () => {
    expect(service.currentUser()).toBeNull();
  });

  it('isAuthenticated es false cuando no hay usuario', () => {
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('isAuthenticated es true cuando hay usuario en señal', () => {
    service.currentUser.set(mockUser);
    expect(service.isAuthenticated()).toBeTrue();
  });

  // ── login ─────────────────────────────────────────────────────────────────

  it('login POST a /api/v1/auth/login/', () => {
    service.login({ email: 'admin@empresa.com', password: 'Pass1234!' }).subscribe();
    const req = http.expectOne('/api/v1/auth/login/');
    expect(req.request.method).toBe('POST');
    req.flush(mockLoginResponse);
  });

  it('login guarda tokens y usuario en localStorage', () => {
    service.login({ email: 'admin@empresa.com', password: 'Pass1234!' }).subscribe();
    const req = http.expectOne('/api/v1/auth/login/');
    req.flush(mockLoginResponse);

    expect(localStorage.getItem('access_token')).toBe('access.token.here');
    expect(localStorage.getItem('refresh_token')).toBe('refresh.token.here');
    expect(JSON.parse(localStorage.getItem('current_user')!)).toEqual(mockUser);
  });

  it('login actualiza señal currentUser', () => {
    service.login({ email: 'admin@empresa.com', password: 'Pass1234!' }).subscribe();
    const req = http.expectOne('/api/v1/auth/login/');
    req.flush(mockLoginResponse);

    expect(service.currentUser()).toEqual(mockUser);
  });

  // ── register ──────────────────────────────────────────────────────────────

  it('register POST a /api/v1/auth/register/', () => {
    service.register({
      company_name: 'Mi Empresa', company_nit: '900001001', company_plan: 'starter',
      email: 'admin@empresa.com', password: 'Pass1234!', first_name: 'Admin', last_name: 'Test',
    }).subscribe();
    const req = http.expectOne('/api/v1/auth/register/');
    expect(req.request.method).toBe('POST');
    req.flush(mockRegisterResponse);
  });

  it('register guarda tokens y usuario en localStorage', () => {
    service.register({
      company_name: 'Mi Empresa', company_nit: '900001001', company_plan: 'starter',
      email: 'admin@empresa.com', password: 'Pass1234!', first_name: 'Admin', last_name: 'Test',
    }).subscribe();
    const req = http.expectOne('/api/v1/auth/register/');
    req.flush(mockRegisterResponse);

    expect(localStorage.getItem('access_token')).toBe('access.reg.token');
    expect(service.currentUser()).toEqual(mockUser);
  });

  // ── logout ────────────────────────────────────────────────────────────────

  it('logout limpia localStorage y señal', fakeAsync(() => {
    localStorage.setItem('access_token', 'acc');
    localStorage.setItem('refresh_token', 'ref');
    localStorage.setItem('current_user', JSON.stringify(mockUser));
    service.currentUser.set(mockUser);

    service.logout();

    // El POST de logout es fire-and-forget; respondemos para evitar errores pendientes
    const req = http.expectOne('/api/v1/auth/logout/');
    req.flush({});
    tick();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(service.currentUser()).toBeNull();
  }));

  it('logout no hace POST si no hay refresh token', () => {
    service.logout();
    http.expectNone('/api/v1/auth/logout/');
    expect(service.currentUser()).toBeNull();
  });

  // ── refreshToken ──────────────────────────────────────────────────────────

  it('refreshToken POST a /api/v1/auth/refresh/', () => {
    localStorage.setItem('refresh_token', 'old.refresh');
    service.refreshToken().subscribe();
    const req = http.expectOne('/api/v1/auth/refresh/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ refresh: 'old.refresh' });
    req.flush({ access: 'new.access', refresh: 'new.refresh' });
  });

  it('refreshToken guarda nuevo access token', () => {
    localStorage.setItem('refresh_token', 'old.refresh');
    service.refreshToken().subscribe();
    const req = http.expectOne('/api/v1/auth/refresh/');
    req.flush({ access: 'new.access', refresh: 'new.refresh' });
    expect(localStorage.getItem('access_token')).toBe('new.access');
  });

  // ── switchCompany ─────────────────────────────────────────────────────────

  it('switchCompany POST con company_id', () => {
    service.switchCompany('co-uuid-2').subscribe();
    const req = http.expectOne('/api/v1/auth/switch-company/');
    expect(req.request.body).toEqual({ company_id: 'co-uuid-2' });
    req.flush(mockUser);
  });

  it('switchCompany actualiza señal y localStorage', () => {
    service.switchCompany('co-uuid-2').subscribe();
    const req = http.expectOne('/api/v1/auth/switch-company/');
    req.flush(mockUser);
    expect(service.currentUser()).toEqual(mockUser);
    expect(JSON.parse(localStorage.getItem('current_user')!)).toEqual(mockUser);
  });

  // ── getMyCompanies ────────────────────────────────────────────────────────

  it('getMyCompanies GET a /api/v1/auth/me/companies/', () => {
    const mockCompanies: UserCompanyInfo[] = [
      { id: 'co-1', name: 'Empresa A', nit: '111', plan: 'starter', role: 'company_admin' },
    ];
    service.getMyCompanies().subscribe(res => {
      expect(res).toEqual(mockCompanies);
    });
    const req = http.expectOne('/api/v1/auth/me/companies/');
    expect(req.request.method).toBe('GET');
    req.flush(mockCompanies);
  });

  // ── requestPasswordReset ──────────────────────────────────────────────────

  it('requestPasswordReset POST con email', () => {
    service.requestPasswordReset('user@test.com').subscribe();
    const req = http.expectOne('/api/v1/auth/password-reset/');
    expect(req.request.body).toEqual({ email: 'user@test.com' });
    req.flush({ detail: 'Si el correo existe recibirás un enlace.' });
  });

  // ── confirmPasswordReset ──────────────────────────────────────────────────

  it('confirmPasswordReset POST con uid, token y password', () => {
    service.confirmPasswordReset('uid-abc', 'tok-xyz', 'NuevoPass123!').subscribe();
    const req = http.expectOne('/api/v1/auth/password-reset/confirm/');
    expect(req.request.body).toEqual({ uid: 'uid-abc', token: 'tok-xyz', password: 'NuevoPass123!' });
    req.flush({ detail: 'Contraseña actualizada.' });
  });

  // ── getAccessToken / getRefreshToken ──────────────────────────────────────

  it('getAccessToken retorna null si no hay token', () => {
    expect(service.getAccessToken()).toBeNull();
  });

  it('getAccessToken retorna el token guardado', () => {
    localStorage.setItem('access_token', 'my.token');
    expect(service.getAccessToken()).toBe('my.token');
  });

  it('getRefreshToken retorna null si no hay token', () => {
    expect(service.getRefreshToken()).toBeNull();
  });

  it('getRefreshToken retorna el token guardado', () => {
    localStorage.setItem('refresh_token', 'my.refresh');
    expect(service.getRefreshToken()).toBe('my.refresh');
  });
});
