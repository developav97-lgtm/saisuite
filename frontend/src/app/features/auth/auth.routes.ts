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
    { path: '', redirectTo: 'login', pathMatch: 'full' },
];