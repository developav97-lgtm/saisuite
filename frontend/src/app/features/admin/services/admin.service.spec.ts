/**
 * SaiSuite — Tests AdminService (companies/licencias)
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { AdminService } from './admin.service';
import { AdminUser, CompanySettings, CompanyLicense } from '../models/admin.models';

// ── Mock data ─────────────────────────────────────────────────────────────────

const mockUser: AdminUser = {
  id: 'u-1', email: 'a@b.com', first_name: 'A', last_name: 'B',
  full_name: 'A B', role: 'company_admin',
  is_active: true, is_superadmin: false, modules_access: [],
};

const mockSettings: CompanySettings = {
  id: 'co-1', name: 'Mi Empresa', nit: '900001001',
  plan: 'starter', saiopen_enabled: false, is_active: true,
  modules: [{ id: 'm-1', module: 'proyectos', is_active: true }],
  created_at: '2026-01-01T00:00:00Z',
};

const mockLicense: CompanyLicense = {
  id: 'lic-1', plan: 'starter', status: 'active',
  starts_at: '2026-01-01', expires_at: '2026-12-31',
  max_users: 10, days_until_expiry: 285, is_expired: false,
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AdminService', () => {
  let service: AdminService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(AdminService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── Users ─────────────────────────────────────────────────────────────────

  it('listUsers() GET /api/v1/auth/users/ — respuesta paginada', () => {
    service.listUsers().subscribe(users => {
      expect(users.length).toBe(1);
      expect(users[0].email).toBe('a@b.com');
    });
    const req = http.expectOne('/api/v1/auth/users/');
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [mockUser] });
  });

  it('listUsers() acepta respuesta directa (sin paginación)', () => {
    service.listUsers().subscribe(users => {
      expect(users.length).toBe(1);
    });
    const req = http.expectOne('/api/v1/auth/users/');
    req.flush([mockUser]);
  });

  it('getUser() GET /api/v1/auth/users/:id/', () => {
    service.getUser('u-1').subscribe(u => expect(u.id).toBe('u-1'));
    const req = http.expectOne('/api/v1/auth/users/u-1/');
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });

  it('createUser() POST a /api/v1/auth/users/', () => {
    const dto = {
      email: 'new@co.com', first_name: 'N', last_name: 'U',
      role: 'viewer' as const, password: 'Pass1!', modules_access: [],
    };
    service.createUser(dto).subscribe(u => expect(u.email).toBe('a@b.com'));
    const req = http.expectOne('/api/v1/auth/users/');
    expect(req.request.method).toBe('POST');
    req.flush(mockUser);
  });

  it('updateUser() PATCH a /api/v1/auth/users/:id/', () => {
    service.updateUser('u-1', { first_name: 'Juan' }).subscribe();
    const req = http.expectOne('/api/v1/auth/users/u-1/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ first_name: 'Juan' });
    req.flush(mockUser);
  });

  it('deactivateUser() PATCH con is_active=false', () => {
    service.deactivateUser('u-1').subscribe();
    const req = http.expectOne('/api/v1/auth/users/u-1/');
    expect(req.request.body).toEqual({ is_active: false });
    req.flush(mockUser);
  });

  it('activateUser() PATCH con is_active=true', () => {
    service.activateUser('u-1').subscribe();
    const req = http.expectOne('/api/v1/auth/users/u-1/');
    expect(req.request.body).toEqual({ is_active: true });
    req.flush(mockUser);
  });

  // ── Company ───────────────────────────────────────────────────────────────

  it('getCompanySettings() GET /api/v1/companies/me/', () => {
    service.getCompanySettings().subscribe(s => expect(s.name).toBe('Mi Empresa'));
    const req = http.expectOne('/api/v1/companies/me/');
    expect(req.request.method).toBe('GET');
    req.flush(mockSettings);
  });

  it('activateModule() POST con company y module', () => {
    service.activateModule('co-1', 'ventas').subscribe();
    const req = http.expectOne('/api/v1/companies/co-1/modules/activate/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ module: 'ventas' });
    req.flush({});
  });

  it('deactivateModule() POST con company y module', () => {
    service.deactivateModule('co-1', 'cobros').subscribe();
    const req = http.expectOne('/api/v1/companies/co-1/modules/deactivate/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ module: 'cobros' });
    req.flush({});
  });

  // ── License ───────────────────────────────────────────────────────────────

  it('getMyLicense() GET /api/v1/companies/licenses/me/', () => {
    service.getMyLicense().subscribe(lic => {
      expect(lic.status).toBe('active');
      expect(lic.days_until_expiry).toBe(285);
    });
    const req = http.expectOne('/api/v1/companies/licenses/me/');
    expect(req.request.method).toBe('GET');
    req.flush(mockLicense);
  });
});
