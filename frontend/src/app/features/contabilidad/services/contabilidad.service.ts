import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface MovimientoContable {
  conteo: number;
  auxiliar: string;
  auxiliar_nombre: string;
  titulo_codigo: number | null;
  titulo_nombre: string;
  cuenta_codigo: number | null;
  cuenta_nombre: string;
  tercero_id: string;
  tercero_nombre: string;
  debito: string;
  credito: string;
  tipo: string;
  invc: string;
  descripcion: string;
  fecha: string;
  periodo: string;
  proyecto_codigo: string | null;
  proyecto_nombre: string;
  sincronizado_en: string;
}

export interface GLListResponse {
  count: number;
  results: MovimientoContable[];
}

export interface GLFiltros {
  periodo?: string;
  titulo_codigo?: number | string;
  tercero_id?: string;
  tipo?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

@Injectable({ providedIn: 'root' })
export class ContabilidadService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/contabilidad`;

  getMovimientos(filtros: GLFiltros = {}): Observable<GLListResponse> {
    let params = new HttpParams();
    if (filtros.periodo)       params = params.set('periodo', filtros.periodo);
    if (filtros.titulo_codigo) params = params.set('titulo_codigo', String(filtros.titulo_codigo));
    if (filtros.tercero_id)    params = params.set('tercero_id', filtros.tercero_id);
    if (filtros.tipo)          params = params.set('tipo', filtros.tipo);
    if (filtros.fecha_inicio)  params = params.set('fecha_inicio', filtros.fecha_inicio);
    if (filtros.fecha_fin)     params = params.set('fecha_fin', filtros.fecha_fin);
    if (filtros.search)        params = params.set('search', filtros.search);
    if (filtros.page)          params = params.set('page', String(filtros.page));
    if (filtros.page_size)     params = params.set('page_size', String(filtros.page_size));

    return this.http.get<GLListResponse>(`${this.base}/movimientos/`, { params });
  }
}
