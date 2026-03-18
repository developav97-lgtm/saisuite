import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { LoginRequest, LoginResponse, TokenRefreshResponse, UserProfile } from './auth.models';

const ACCESS_KEY  = 'access_token';
const REFRESH_KEY = 'refresh_token';
const USER_KEY    = 'current_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http   = inject(HttpClient);
  private readonly router = inject(Router);

  readonly currentUser     = signal<UserProfile | null>(null);
  readonly isAuthenticated = computed(() => !!this.currentUser());

  constructor() {
    this.loadFromStorage();
  }

  login(credentials: LoginRequest): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>('/api/v1/auth/login/', credentials)
      .pipe(tap(res => this.saveTokens(res)));
  }

  logout(): void {
    const refresh = this.getRefreshToken();
    if (refresh) {
      this.http
        .post('/api/v1/auth/logout/', { refresh })
        .subscribe({ error: () => {} });
    }
    this.clearStorage();
    this.router.navigate(['/auth/login']);
  }

  refreshToken(): Observable<TokenRefreshResponse> {
    return this.http
      .post<TokenRefreshResponse>('/api/v1/auth/refresh/', { refresh: this.getRefreshToken() })
      .pipe(tap(tokens => localStorage.setItem(ACCESS_KEY, tokens.access)));
  }

  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  private saveTokens(res: LoginResponse): void {
    localStorage.setItem(ACCESS_KEY, res.access);
    localStorage.setItem(REFRESH_KEY, res.refresh);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this.currentUser.set(res.user);
  }

  private clearStorage(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this.currentUser.set(null);
  }

  private loadFromStorage(): void {
    const raw = localStorage.getItem(USER_KEY);
    if (raw) {
      this.currentUser.set(JSON.parse(raw) as UserProfile);
    }
  }
}
