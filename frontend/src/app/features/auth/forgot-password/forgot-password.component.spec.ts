/**
 * SaiSuite — Tests ForgotPasswordComponent
 */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { of, throwError } from 'rxjs';
import { ForgotPasswordComponent } from './forgot-password.component';
import { AuthService } from '../../../core/auth/auth.service';

describe('ForgotPasswordComponent', () => {
  let fixture: ComponentFixture<ForgotPasswordComponent>;
  let component: ForgotPasswordComponent;
  let authService: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    const spy = jasmine.createSpyObj('AuthService', ['requestPasswordReset']);

    await TestBed.configureTestingModule({
      imports: [ForgotPasswordComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        provideAnimationsAsync(),
        { provide: AuthService, useValue: spy },
      ],
    }).compileComponents();

    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    fixture     = TestBed.createComponent(ForgotPasswordComponent);
    component   = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('empieza con loading=false y sent=false', () => {
    expect(component.loading()).toBeFalse();
    expect(component.sent()).toBeFalse();
  });

  it('formulario inválido con email vacío', () => {
    expect(component.form.valid).toBeFalse();
  });

  it('formulario válido con email correcto', () => {
    component.form.setValue({ email: 'user@empresa.com' });
    expect(component.form.valid).toBeTrue();
  });

  it('onSubmit no llama al servicio si el form es inválido', () => {
    component.onSubmit();
    expect(authService.requestPasswordReset).not.toHaveBeenCalled();
  });

  it('onSubmit llama requestPasswordReset con el email', fakeAsync(() => {
    authService.requestPasswordReset.and.returnValue(of({ detail: 'Ok' }));
    component.form.setValue({ email: 'user@empresa.com' });
    component.onSubmit();
    tick();
    expect(authService.requestPasswordReset).toHaveBeenCalledWith('user@empresa.com');
  }));

  it('sent pasa a true tras respuesta exitosa', fakeAsync(() => {
    authService.requestPasswordReset.and.returnValue(of({ detail: 'Ok' }));
    component.form.setValue({ email: 'user@empresa.com' });
    component.onSubmit();
    tick();
    expect(component.sent()).toBeTrue();
    expect(component.loading()).toBeFalse();
  }));

  it('sent pasa a true incluso con error (respuesta genérica)', fakeAsync(() => {
    authService.requestPasswordReset.and.returnValue(throwError(() => ({ status: 500 })));
    component.form.setValue({ email: 'user@empresa.com' });
    component.onSubmit();
    tick();
    expect(component.sent()).toBeTrue();
    expect(component.loading()).toBeFalse();
  }));
});
