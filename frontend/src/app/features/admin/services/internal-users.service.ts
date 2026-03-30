import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface InternalUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_superadmin: boolean;
  is_staff: boolean;
  is_active: boolean;
  tipo_usuario: 'superadmin' | 'soporte';
}

export interface InternalUserCreate {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superadmin: boolean;
}

export interface InternalUserUpdate {
  first_name?: string;
  last_name?: string;
  is_staff?: boolean;
  is_superadmin?: boolean;
  is_active?: boolean;
  password?: string;
}

@Injectable({ providedIn: 'root' })
export class InternalUsersService {
  private readonly http = inject(HttpClient);

  list(): Observable<InternalUser[]> {
    return this.http.get<InternalUser[]>('/api/v1/auth/internal-users/');
  }

  get(id: string): Observable<InternalUser> {
    return this.http.get<InternalUser>(`/api/v1/auth/internal-users/${id}/`);
  }

  create(data: InternalUserCreate): Observable<InternalUser> {
    return this.http.post<InternalUser>('/api/v1/auth/internal-users/', data);
  }

  update(id: string, data: InternalUserUpdate): Observable<InternalUser> {
    return this.http.patch<InternalUser>(`/api/v1/auth/internal-users/${id}/`, data);
  }
}
