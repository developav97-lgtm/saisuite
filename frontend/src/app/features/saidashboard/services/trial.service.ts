import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TrialStatus, TrialActivateResponse } from '../models/trial.model';

@Injectable({ providedIn: 'root' })
export class TrialService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/dashboard/trial';

  getStatus(): Observable<TrialStatus> {
    return this.http.get<TrialStatus>(`${this.baseUrl}/status/`);
  }

  activate(): Observable<TrialActivateResponse> {
    return this.http.post<TrialActivateResponse>(`${this.baseUrl}/activate/`, {});
  }
}
