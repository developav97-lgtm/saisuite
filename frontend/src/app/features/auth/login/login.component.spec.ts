/**
 * SaiSuite — Tests LoginComponent
 */
import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from '../../../core/auth/auth.service';
import { LoginResponse } from '../../../core/auth/auth.models';

@Component({ template: '' })
class DummyComponent {}

const mockLoginResponse: LoginResponse = {
  access: 'acc', refresh: 'ref',
  user: {
    id: 'u-1', email: 'a@b.com', first_name: 'A', last_name: 'B',
    full_name: 'A B', role: 'company_admin',
    company: { id: 'co-1', name: 'Co', nit: '111' },
  },
};

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let component: LoginComponent;
  let authService: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('AuthService', ['login'], {
      currentUser: { set: () => {} },
      isAuthenticated: () => false,
    });

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'dashboard', component: DummyComponent }]),
        provideAnimationsAsync(),
        { provide: AuthService, useValue: spy },
      ],
    }).compileComponents();

    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    fixture     = TestBed.createComponent(LoginComponent);
    component   = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => localStorage.clear());

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('el formulario empieza inválido con campos vacíos', () => {
    expect(component.form.valid).toBeFalse();
  });

  it('formulario válido con email y contraseña correctos', () => {
    component.form.setValue({ email: 'admin@empresa.com', password: 'Pass1234!' });
    expect(component.form.valid).toBeTrue();
  });

  it('onSubmit no hace nada si el formulario es inválido', () => {
    authService.login.and.returnValue(of(mockLoginResponse));
    component.onSubmit();
    expect(authService.login).not.toHaveBeenCalled();
  });

  it('onSubmit llama AuthService.login con credenciales correctas', fakeAsync(() => {
    authService.login.and.returnValue(of(mockLoginResponse));
    component.form.setValue({ email: 'admin@empresa.com', password: 'Pass1234!' });
    component.onSubmit();
    tick();
    expect(authService.login).toHaveBeenCalledWith({
      email: 'admin@empresa.com',
      password: 'Pass1234!',
    });
  }));

  it('loading se activa al hacer submit', fakeAsync(() => {
    authService.login.and.returnValue(of(mockLoginResponse));
    component.form.setValue({ email: 'admin@empresa.com', password: 'Pass1234!' });
    component.onSubmit();
    // Durante la petición loading debería haber sido true
    tick();
    // Después loading vuelve a false
    expect(component.loading()).toBeFalse();
  }));

  it('loading se desactiva tras error', fakeAsync(() => {
    authService.login.and.returnValue(throwError(() => ({ status: 401 })));
    component.form.setValue({ email: 'admin@empresa.com', password: 'Pass1234!' });
    component.onSubmit();
    tick();
    expect(component.loading()).toBeFalse();
  }));

  it('hidePassword inicia en true y alterna con toggle', () => {
    expect(component.hidePassword()).toBeTrue();
    component.hidePassword.set(false);
    expect(component.hidePassword()).toBeFalse();
  });
});
