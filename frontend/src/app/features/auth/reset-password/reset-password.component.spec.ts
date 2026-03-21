/**
 * SaiSuite — Tests ResetPasswordComponent
 */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { of, throwError } from 'rxjs';
import { ResetPasswordComponent } from './reset-password.component';
import { AuthService } from '../../../core/auth/auth.service';

function makeRoute(uid = 'uid-abc', token = 'tok-xyz') {
  return {
    snapshot: {
      queryParamMap: {
        get: (key: string) => (key === 'uid' ? uid : key === 'token' ? token : null),
      },
    },
  };
}

describe('ResetPasswordComponent', () => {
  let fixture: ComponentFixture<ResetPasswordComponent>;
  let component: ResetPasswordComponent;
  let authService: jasmine.SpyObj<AuthService>;

  async function setup(uid = 'uid-abc', token = 'tok-xyz') {
    const spy = jasmine.createSpyObj('AuthService', ['confirmPasswordReset', 'logout']);

    await TestBed.configureTestingModule({
      imports: [ResetPasswordComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        provideAnimationsAsync(),
        { provide: AuthService, useValue: spy },
        { provide: ActivatedRoute, useValue: makeRoute(uid, token) },
      ],
    }).compileComponents();

    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    fixture     = TestBed.createComponent(ResetPasswordComponent);
    component   = fixture.componentInstance;
    fixture.detectChanges();
  }

  afterEach(() => localStorage.clear());

  it('se crea correctamente', async () => {
    await setup();
    expect(component).toBeTruthy();
  });

  it('empieza con loading=false y done=false', async () => {
    await setup();
    expect(component.loading()).toBeFalse();
    expect(component.done()).toBeFalse();
  });

  it('formulario inválido con contraseñas vacías', async () => {
    await setup();
    expect(component.form.valid).toBeFalse();
  });

  it('formulario válido con contraseñas que cumplen mínimo', async () => {
    await setup();
    component.form.setValue({ password: 'NuevoPass1!', password2: 'NuevoPass1!' });
    expect(component.form.valid).toBeTrue();
  });

  it('onSubmit no actúa si el form es inválido', async () => {
    await setup();
    component.onSubmit();
    expect(authService.confirmPasswordReset).not.toHaveBeenCalled();
  });

  it('onSubmit muestra snackbar si las contraseñas no coinciden', async () => {
    await setup();
    component.form.setValue({ password: 'NuevoPass1!', password2: 'DiferentePass1!' });
    // No debe llamar al servicio
    authService.confirmPasswordReset.and.returnValue(of({ detail: 'Ok' }));
    component.onSubmit();
    expect(authService.confirmPasswordReset).not.toHaveBeenCalled();
  });

  it('onSubmit llama confirmPasswordReset con uid, token y password', fakeAsync(async () => {
    await setup('uid-123', 'tok-456');
    authService.confirmPasswordReset.and.returnValue(of({ detail: 'Contraseña actualizada.' }));
    component.form.setValue({ password: 'NuevoPass1!', password2: 'NuevoPass1!' });
    component.onSubmit();
    tick();
    expect(authService.confirmPasswordReset).toHaveBeenCalledWith('uid-123', 'tok-456', 'NuevoPass1!');
  }));

  it('done pasa a true tras reset exitoso', fakeAsync(async () => {
    await setup();
    authService.confirmPasswordReset.and.returnValue(of({ detail: 'Ok' }));
    component.form.setValue({ password: 'NuevoPass1!', password2: 'NuevoPass1!' });
    component.onSubmit();
    tick();
    expect(component.done()).toBeTrue();
    expect(component.loading()).toBeFalse();
  }));

  it('loading se desactiva tras error', fakeAsync(async () => {
    await setup();
    authService.confirmPasswordReset.and.returnValue(
      throwError(() => ({ error: { detail: 'Token inválido.' } }))
    );
    component.form.setValue({ password: 'NuevoPass1!', password2: 'NuevoPass1!' });
    component.onSubmit();
    tick();
    expect(component.loading()).toBeFalse();
    expect(component.done()).toBeFalse();
  }));

  it('hidePassword inicia en true', async () => {
    await setup();
    expect(component.hidePassword()).toBeTrue();
  });
});
