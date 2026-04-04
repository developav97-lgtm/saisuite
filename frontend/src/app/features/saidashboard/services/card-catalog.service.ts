import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CardCatalogItem, CategoryWithCards } from '../models/card-catalog.model';

@Injectable({ providedIn: 'root' })
export class CardCatalogService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/dashboard/catalog';

  getCards(): Observable<CardCatalogItem[]> {
    return this.http.get<CardCatalogItem[]>(`${this.baseUrl}/cards/`);
  }

  getCategories(): Observable<CategoryWithCards[]> {
    return this.http.get<CategoryWithCards[]>(`${this.baseUrl}/categories/`);
  }
}
