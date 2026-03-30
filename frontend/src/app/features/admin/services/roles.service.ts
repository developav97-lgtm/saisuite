import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Permission {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  modulo: string;
  accion: string;
}

export interface RoleSummary {
  id: number;
  nombre: string;
  tipo: 'admin' | 'readonly' | 'custom';
}

export interface Role {
  id: number;
  nombre: string;
  tipo: 'admin' | 'readonly' | 'custom';
  descripcion: string;
  permisos: Permission[];
  es_sistema: boolean;
  usuarios_count: number;
  created_at: string;
  updated_at: string;
}

export interface RoleCreateDto {
  nombre: string;
  descripcion: string;
  permisos_ids: number[];
}

export const TIPO_LABELS: Record<Role['tipo'], string> = {
  admin:    'Administrador',
  readonly: 'Solo Lectura',
  custom:   'Personalizado',
};

export const MODULO_NOMBRES: Record<string, string> = {
  proyectos:    'Proyectos',
  actividades:  'Actividades',
  tareas:       'Tareas',
  timesheets:   'Registro de Horas',
  terceros:     'Terceros',
  admin:        'Administración',
};

@Injectable({ providedIn: 'root' })
export class RolesService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/auth`;

  listar(): Observable<Role[]> {
    return this.http.get<Role[]>(`${this.base}/roles/`);
  }

  obtener(id: number): Observable<Role> {
    return this.http.get<Role>(`${this.base}/roles/${id}/`);
  }

  crear(data: RoleCreateDto): Observable<Role> {
    return this.http.post<Role>(`${this.base}/roles/`, data);
  }

  actualizar(id: number, data: Partial<RoleCreateDto>): Observable<Role> {
    return this.http.patch<Role>(`${this.base}/roles/${id}/`, data);
  }

  eliminar(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/roles/${id}/`);
  }

  obtenerPermisos(): Observable<Permission[]> {
    return this.http.get<Permission[]>(`${this.base}/permissions/`);
  }

  obtenerPermisosAgrupados(): Observable<Record<string, Permission[]>> {
    return this.http.get<Record<string, Permission[]>>(`${this.base}/permissions/by-module/`);
  }
}
