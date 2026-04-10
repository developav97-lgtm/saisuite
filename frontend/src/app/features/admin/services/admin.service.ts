import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AdminUser, AgentTokenInfo, CompanyLicense, CompanySettings, CreateUserDto, UserRole } from '../models/admin.models';
import { LicensePackage, LicenseRequest } from '../models/tenant.model';

export interface ListUsersParams {
  search?: string;
  role?: UserRole | '';
  is_active?: boolean | '';
  page?: number;
  page_size?: number;
}

export interface PaginatedUsers {
  count: number;
  results: AdminUser[];
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly http = inject(HttpClient);

  // ── Users ───────────────────────────────────────────────────────────────

  listUsers(params: ListUsersParams = {}): Observable<PaginatedUsers> {
    let httpParams = new HttpParams();
    if (params.search)    httpParams = httpParams.set('search',    params.search);
    if (params.role)      httpParams = httpParams.set('role',      params.role);
    if (params.is_active !== '' && params.is_active !== undefined)
                          httpParams = httpParams.set('is_active', String(params.is_active));
    if (params.page)      httpParams = httpParams.set('page',      String(params.page));
    if (params.page_size) httpParams = httpParams.set('page_size', String(params.page_size));

    return this.http.get<PaginatedUsers>('/api/v1/auth/users/', { params: httpParams });
  }

  getUser(id: string): Observable<AdminUser> {
    return this.http.get<AdminUser>(`/api/v1/auth/users/${id}/`);
  }

  createUser(data: CreateUserDto): Observable<AdminUser> {
    return this.http.post<AdminUser>('/api/v1/auth/users/', data);
  }

  updateUser(id: string, data: Partial<CreateUserDto> & { rol_granular_id?: number | null }): Observable<AdminUser> {
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

  getMyLicense(): Observable<CompanyLicense> {
    return this.http.get<CompanyLicense>('/api/v1/companies/licenses/me/');
  }

  getMyAIUsage(): Observable<{ messages_used: number; tokens_used: number; tokens_quota: number; tokens_pct: number; total_requests: number }> {
    return this.http.get<{ messages_used: number; tokens_used: number; tokens_quota: number; tokens_pct: number; total_requests: number }>('/api/v1/companies/licenses/me/ai-usage/');
  }

  uploadLogo(file: File): Observable<CompanySettings> {
    const formData = new FormData();
    formData.append('logo', file);
    return this.http.patch<CompanySettings>('/api/v1/companies/me/logo/', formData);
  }

  deleteLogo(): Observable<void> {
    return this.http.delete<void>('/api/v1/companies/me/logo/');
  }

  // ── Agent Tokens ─────────────────────────────────────────────────────────

  getMyAgentTokens(): Observable<AgentTokenInfo[]> {
    return this.http.get<AgentTokenInfo[]>('/api/v1/companies/agent-tokens/me/');
  }

  // ── Catálogo de paquetes (para company-settings) ──────────────────────────

  getAvailablePackages(packageType?: string): Observable<LicensePackage[]> {
    let url = '/api/v1/companies/packages/catalog/';
    if (packageType) url += `?type=${packageType}`;
    return this.http.get<LicensePackage[]>(url);
  }

  // ── Solicitudes de licencia (company_admin) ───────────────────────────────

  getMyLicenseRequests(): Observable<LicenseRequest[]> {
    return this.http.get<LicenseRequest[]>('/api/v1/companies/license-requests/');
  }

  createLicenseRequest(body: { package_id: string; request_type: string; notes?: string }): Observable<LicenseRequest> {
    return this.http.post<LicenseRequest>('/api/v1/companies/license-requests/', body);
  }

  // ── Solicitudes de licencia (superadmin) ─────────────────────────────────

  getAdminLicenseRequests(status?: string): Observable<LicenseRequest[]> {
    const url = status
      ? `/api/v1/admin/tenants/license-requests/?status=${status}`
      : '/api/v1/admin/tenants/license-requests/';
    return this.http.get<LicenseRequest[]>(url);
  }

  approveLicenseRequest(id: string, reviewNotes?: string): Observable<LicenseRequest> {
    return this.http.post<LicenseRequest>(`/api/v1/admin/tenants/license-requests/${id}/approve/`, { review_notes: reviewNotes ?? '' });
  }

  rejectLicenseRequest(id: string, reviewNotes?: string): Observable<LicenseRequest> {
    return this.http.post<LicenseRequest>(`/api/v1/admin/tenants/license-requests/${id}/reject/`, { review_notes: reviewNotes ?? '' });
  }
}
