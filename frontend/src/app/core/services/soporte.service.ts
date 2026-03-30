import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TenantBasico {
  id: string;
  name: string;
  nit: string;
  plan: string;
}

@Injectable({ providedIn: 'root' })
export class SoporteService {
  private readonly http = inject(HttpClient);

  getTenantsDisponibles(): Observable<TenantBasico[]> {
    return this.http.get<TenantBasico[]>('/api/v1/auth/soporte/tenants/');
  }

  seleccionarTenant(tenantId: string): Observable<{ mensaje: string; tenant: TenantBasico }> {
    return this.http.post<{ mensaje: string; tenant: TenantBasico }>(
      '/api/v1/auth/soporte/seleccionar-tenant/',
      { tenant_id: tenantId },
    );
  }

  liberarTenant(): Observable<{ mensaje: string }> {
    return this.http.post<{ mensaje: string }>('/api/v1/auth/soporte/liberar-tenant/', {});
  }
}
