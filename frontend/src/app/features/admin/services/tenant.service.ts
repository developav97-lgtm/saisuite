import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Tenant,
  TenantLicense,
  TenantCreateRequest,
  LicenseWriteRequest,
  LicensePayment,
  LicensePaymentRequest,
  LicenseHistory,
  LicenseRenewal,
} from '../models/tenant.model';

const BASE = '/api/v1/admin/tenants';

@Injectable({ providedIn: 'root' })
export class TenantService {
  private readonly http = inject(HttpClient);

  // ── Tenants ──────────────────────────────────────────────────────────────

  listTenants(): Observable<Tenant[]> {
    return this.http.get<Tenant[]>(`${BASE}/`);
  }

  getTenant(id: string): Observable<Tenant> {
    return this.http.get<Tenant>(`${BASE}/${id}/`);
  }

  createTenant(data: TenantCreateRequest): Observable<Tenant> {
    return this.http.post<Tenant>(`${BASE}/`, data);
  }

  updateTenant(id: string, data: Partial<{ name: string; plan: string; saiopen_enabled: boolean }>): Observable<Tenant> {
    return this.http.patch<Tenant>(`${BASE}/${id}/`, data);
  }

  setTenantActive(id: string, is_active: boolean): Observable<{ id: string; is_active: boolean }> {
    return this.http.post<{ id: string; is_active: boolean }>(`${BASE}/${id}/activate/`, { is_active });
  }

  // ── Licencias ─────────────────────────────────────────────────────────────

  getLicense(tenantId: string): Observable<TenantLicense> {
    return this.http.get<TenantLicense>(`${BASE}/${tenantId}/license/`);
  }

  createLicense(tenantId: string, data: LicenseWriteRequest): Observable<TenantLicense> {
    return this.http.post<TenantLicense>(`${BASE}/${tenantId}/license/`, data);
  }

  updateLicense(tenantId: string, data: Partial<LicenseWriteRequest>): Observable<TenantLicense> {
    return this.http.patch<TenantLicense>(`${BASE}/${tenantId}/license/`, data);
  }

  getLicenseHistory(tenantId: string): Observable<LicenseHistory[]> {
    return this.http.get<LicenseHistory[]>(`${BASE}/${tenantId}/license/history/`);
  }

  addPayment(tenantId: string, data: LicensePaymentRequest): Observable<LicensePayment> {
    return this.http.post<LicensePayment>(`${BASE}/${tenantId}/license/payments/`, data);
  }

  // ── Renovaciones ──────────────────────────────────────────────────────────

  getRenewal(tenantId: string): Observable<LicenseRenewal | null> {
    return this.http.get<LicenseRenewal | null>(`/api/v1/admin/tenants/${tenantId}/license/renewal/`);
  }

  createRenewal(tenantId: string, period: string): Observable<LicenseRenewal> {
    return this.http.post<LicenseRenewal>(
      `/api/v1/admin/tenants/${tenantId}/license/renewal/`,
      { period }
    );
  }

  confirmRenewal(tenantId: string, notes = ''): Observable<LicenseRenewal> {
    return this.http.post<LicenseRenewal>(
      `/api/v1/admin/tenants/${tenantId}/license/renewal/confirm/`,
      { notes }
    );
  }

  cancelRenewal(tenantId: string): Observable<LicenseRenewal> {
    return this.http.post<LicenseRenewal>(
      `/api/v1/admin/tenants/${tenantId}/license/renewal/cancel/`,
      {}
    );
  }
}
