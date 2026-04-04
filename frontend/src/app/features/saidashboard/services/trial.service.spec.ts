import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TrialService } from './trial.service';
import { TrialStatus } from '../models/trial.model';

describe('TrialService', () => {
  let service: TrialService;
  let http: HttpTestingController;
  const base = '/api/v1/dashboard/trial';

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(TrialService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getStatus() — GET /trial/status/', () => {
    const mockStatus: TrialStatus = {
      tiene_acceso: true,
      tipo_acceso: 'trial',
      dias_restantes: 10,
      expira_en: '2026-04-17',
    };
    service.getStatus().subscribe(res => {
      expect(res.tipo_acceso).toBe('trial');
      expect(res.dias_restantes).toBe(10);
    });
    http.expectOne(`${base}/status/`).flush(mockStatus);
  });

  it('activate() — POST /trial/activate/', () => {
    service.activate().subscribe(res => {
      expect(res.esta_activo).toBeTrue();
      expect(res.dias_restantes).toBe(14);
    });
    const req = http.expectOne(`${base}/activate/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({});
    req.flush({ module_code: 'dashboard', iniciado_en: '2026-04-03', expira_en: '2026-04-17', esta_activo: true, dias_restantes: 14 });
  });
});
