import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { LicensePackage, LicensePackageWriteRequest, PackageType } from '../models/tenant.model';

const BASE = '/api/v1/admin/packages';

@Injectable({ providedIn: 'root' })
export class PackageService {
  private readonly http = inject(HttpClient);

  listPackages(packageType?: PackageType): Observable<LicensePackage[]> {
    let params = new HttpParams();
    if (packageType) params = params.set('package_type', packageType);
    return this.http.get<LicensePackage[]>(`${BASE}/`, { params });
  }

  getPackage(id: string): Observable<LicensePackage> {
    return this.http.get<LicensePackage>(`${BASE}/${id}/`);
  }

  createPackage(data: LicensePackageWriteRequest): Observable<LicensePackage> {
    return this.http.post<LicensePackage>(`${BASE}/`, data);
  }

  updatePackage(id: string, data: Partial<LicensePackageWriteRequest>): Observable<LicensePackage> {
    return this.http.patch<LicensePackage>(`${BASE}/${id}/`, data);
  }

  deletePackage(id: string): Observable<void> {
    return this.http.delete<void>(`${BASE}/${id}/`);
  }
}
