/**
 * SaiSuite — Tests authGuard
 */
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { authGuard } from './auth.guard';
import { AuthService } from '../auth/auth.service';
import { UserProfile } from '../auth/auth.models';

const mockUser: UserProfile = {
  id: 'u-1', email: 'a@b.com', first_name: 'A', last_name: 'B',
  full_name: 'A B', role: 'company_admin',
  company: { id: 'co-1', name: 'Co', nit: '111' },
};

function runGuard() {
  const route = {} as ActivatedRouteSnapshot;
  const state = {} as RouterStateSnapshot;
  return TestBed.runInInjectionContext(() => authGuard(route, state));
}

describe('authGuard', () => {
  let authService: AuthService;
  let router: Router;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
      ],
    });
    authService = TestBed.inject(AuthService);
    router      = TestBed.inject(Router);
  });

  afterEach(() => localStorage.clear());

  it('permite el acceso cuando el usuario está autenticado', () => {
    authService.currentUser.set(mockUser);
    const result = runGuard();
    expect(result).toBeTrue();
  });

  it('redirige a /auth/login cuando no está autenticado', () => {
    authService.currentUser.set(null);
    const result = runGuard();
    expect(result).toBeInstanceOf(UrlTree);
    expect((result as UrlTree).toString()).toBe('/auth/login');
  });
});
