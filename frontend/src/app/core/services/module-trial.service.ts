import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ModuleTrialStatus, ModuleTrial } from '../../features/admin/models/tenant.model';

@Injectable({ providedIn: 'root' })
export class ModuleTrialService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/companies/modules`;

  /**
   * Retorna el estado de acceso al módulo para la empresa del usuario autenticado.
   * Usado por company_admin y guards de módulo.
   */
  getStatus(moduleCode: string): Observable<ModuleTrialStatus> {
    return this.http.get<ModuleTrialStatus>(`${this.base}/${moduleCode}/trial/status/`);
  }

  /**
   * Activa un trial de 14 días para el módulo indicado.
   * Solo company_admin puede llamar este endpoint.
   */
  activateTrial(moduleCode: string): Observable<ModuleTrial> {
    return this.http.post<ModuleTrial>(`${this.base}/${moduleCode}/trial/activate/`, {});
  }
}
