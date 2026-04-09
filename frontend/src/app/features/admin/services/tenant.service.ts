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
  LicensePackageItem,
  MonthlyLicenseSnapshot,
  AIUsageSummary,
  AIUsagePerUser,
  AgentTokenInfo,
  ModuleTrial,
  ModuleTrialStatus,
  LicensePriceCalculatorLine,
  LicensePriceResult,
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

  updateTenant(id: string, data: Partial<{ name: string; saiopen_enabled: boolean }>): Observable<Tenant> {
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

  // ── Paquetes de licencia ──────────────────────────────────────────────────

  getLicensePackages(tenantId: string): Observable<LicensePackageItem[]> {
    return this.http.get<LicensePackageItem[]>(`${BASE}/${tenantId}/license/packages/`);
  }

  addLicensePackage(tenantId: string, packageId: string, quantity = 1): Observable<LicensePackageItem> {
    return this.http.post<LicensePackageItem>(`${BASE}/${tenantId}/license/packages/`, { package_id: packageId, quantity });
  }

  removeLicensePackage(tenantId: string, itemId: string): Observable<void> {
    return this.http.delete<void>(`${BASE}/${tenantId}/license/packages/${itemId}/`);
  }

  // ── Snapshots mensuales ───────────────────────────────────────────────────

  getLicenseSnapshots(tenantId: string): Observable<MonthlyLicenseSnapshot[]> {
    return this.http.get<MonthlyLicenseSnapshot[]>(`${BASE}/${tenantId}/license/snapshots/`);
  }

  // ── Uso IA ────────────────────────────────────────────────────────────────

  getAIUsage(tenantId: string): Observable<AIUsageSummary> {
    return this.http.get<AIUsageSummary>(`${BASE}/${tenantId}/license/ai-usage/`);
  }

  getAIUsageByUser(tenantId: string): Observable<AIUsagePerUser[]> {
    return this.http.get<AIUsagePerUser[]>(`${BASE}/${tenantId}/license/ai-usage/by-user/`);
  }

  // ── Tokens del agente ─────────────────────────────────────────────────────

  getAgentTokens(tenantId: string): Observable<AgentTokenInfo[]> {
    return this.http.get<AgentTokenInfo[]>(`${BASE}/${tenantId}/agent-tokens/`);
  }

  createAgentToken(tenantId: string, label: string): Observable<AgentTokenInfo> {
    return this.http.post<AgentTokenInfo>(`${BASE}/${tenantId}/agent-tokens/`, { label });
  }

  revokeAgentToken(tenantId: string, tokenId: string): Observable<void> {
    return this.http.post<void>(`${BASE}/${tenantId}/agent-tokens/${tokenId}/revoke/`, {});
  }

  // ── Trials de módulo (superadmin) ─────────────────────────────────────────

  getModuleTrialStatus(tenantId: string, moduleCode: string): Observable<ModuleTrialStatus> {
    return this.http.get<ModuleTrialStatus>(`${BASE}/${tenantId}/modules/${moduleCode}/trial/status/`);
  }

  activateModuleTrial(tenantId: string, moduleCode: string): Observable<ModuleTrial> {
    return this.http.post<ModuleTrial>(`${BASE}/${tenantId}/modules/${moduleCode}/trial/activate/`, {});
  }

  // ── Calculadora de precio de licencia ─────────────────────────────────────

  calculateLicensePrice(
    lines: LicensePriceCalculatorLine[],
    period: 'monthly' | 'annual' = 'monthly'
  ): Observable<LicensePriceResult> {
    return this.http.post<LicensePriceResult>(
      `/api/v1/admin/tenants/license/calculate-total/`,
      { lines, period }
    );
  }
}
