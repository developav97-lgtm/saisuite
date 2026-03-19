import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { AdminUser, CompanySettings, CreateUserDto } from '../models/admin.models';

interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  // ── Users ───────────────────────────────────────────────────────────────

  listUsers(): Observable<AdminUser[]> {
    return this.http.get<Paginated<AdminUser>>('/api/v1/auth/users/')
      .pipe(map(r => r.results ?? (r as unknown as AdminUser[])));
  }

  getUser(id: string): Observable<AdminUser> {
    return this.http.get<AdminUser>(`/api/v1/auth/users/${id}/`);
  }

  createUser(data: CreateUserDto): Observable<AdminUser> {
    return this.http.post<AdminUser>('/api/v1/auth/users/', data);
  }

  updateUser(id: string, data: Partial<CreateUserDto>): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`/api/v1/auth/users/${id}/`, data);
  }

  deactivateUser(id: string): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`/api/v1/auth/users/${id}/`, { is_active: false });
  }

  activateUser(id: string): Observable<AdminUser> {
    return this.http.patch<AdminUser>(`/api/v1/auth/users/${id}/`, { is_active: true });
  }

  // ── Company ─────────────────────────────────────────────────────────────

  getCompanySettings(): Observable<CompanySettings> {
    return this.http.get<CompanySettings>('/api/v1/companies/me/');
  }

  activateModule(companyId: string, module: string): Observable<void> {
    return this.http.post<void>(`/api/v1/companies/${companyId}/modules/activate/`, { module });
  }

  deactivateModule(companyId: string, module: string): Observable<void> {
    return this.http.post<void>(`/api/v1/companies/${companyId}/modules/deactivate/`, { module });
  }
}
