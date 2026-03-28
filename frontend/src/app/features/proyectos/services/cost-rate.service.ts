import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ResourceCostRate, ResourceCostRateWrite } from '../models/budget.model';

@Injectable({ providedIn: 'root' })
export class CostRateService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/projects';

  getRates(userId?: string): Observable<ResourceCostRate[]> {
    let params = new HttpParams();
    if (userId) params = params.set('user_id', userId);
    return this.http.get<ResourceCostRate[]>(
      `${this.base}/resources/cost-rates/`,
      { params },
    );
  }

  getRate(rateId: string): Observable<ResourceCostRate> {
    return this.http.get<ResourceCostRate>(
      `${this.base}/resources/cost-rates/${rateId}/`,
    );
  }

  createRate(data: ResourceCostRateWrite): Observable<ResourceCostRate> {
    return this.http.post<ResourceCostRate>(
      `${this.base}/resources/cost-rates/`,
      data,
    );
  }

  updateRate(rateId: string, data: Partial<ResourceCostRateWrite>): Observable<ResourceCostRate> {
    return this.http.patch<ResourceCostRate>(
      `${this.base}/resources/cost-rates/${rateId}/`,
      data,
    );
  }

  deleteRate(rateId: string): Observable<void> {
    return this.http.delete<void>(
      `${this.base}/resources/cost-rates/${rateId}/`,
    );
  }
}
