// frontend/src/app/features/auth/auth.routes.ts
import { Routes } from '@angular/router';
import { LoginComponent } from './login/login.component';
import { RegisterComponent } from './register/register.component';

export const AUTH_ROUTES: Routes = [
    { path: 'login',          component: LoginComponent },
    { path: 'register',       component: RegisterComponent },
    {
      path: 'forgot-password',
      loadComponent: () => import('./forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent),
    },
    {
      path: 'reset-password',
      loadComponent: () => import('./reset-password/reset-password.component').then(m => m.ResetPasswordComponent),
    },
    {
      path: 'activar',
      loadComponent: () => import('./activate-account/activate-account.component').then(m => m.ActivateAccountComponent),
    },
    { path: '', redirectTo: 'login', pathMatch: 'full' },
];