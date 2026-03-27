/**
 * SaiSuite — ConfiguracionProyectoService
 * Consume GET/PATCH /api/v1/projects/config/
 */
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ConfiguracionProyecto } from '../models/configuracion-proyecto.model';

@Injectable({ providedIn: 'root' })
export class ConfiguracionProyectoService {
  private readonly http   = inject(HttpClient);
  private readonly apiUrl = '/api/v1/projects/config';

  obtener(): Observable<ConfiguracionProyecto> {
    return this.http.get<ConfiguracionProyecto>(`${this.apiUrl}/`);
  }

  actualizar(data: Partial<ConfiguracionProyecto>): Observable<ConfiguracionProyecto> {
    return this.http.patch<ConfiguracionProyecto>(`${this.apiUrl}/`, data);
  }
}
