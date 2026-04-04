import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ReportService } from './report.service';
import { CardDataRequest } from '../models/report-filter.model';

describe('ReportService', () => {
  let service: ReportService;
  let http: HttpTestingController;
  const base = '/api/v1/dashboard';

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(ReportService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getCardData() — POST /report/card-data/', () => {
    const req: CardDataRequest = { card_type_code: 'BALANCE_GENERAL', filtros: { fecha_desde: null, fecha_hasta: null } };
    service.getCardData(req).subscribe(res => {
      expect(res.labels).toEqual(['Activo', 'Pasivo']);
    });
    const r = http.expectOne(`${base}/report/card-data/`);
    expect(r.request.method).toBe('POST');
    expect(r.request.body).toEqual(req);
    r.flush({ labels: ['Activo', 'Pasivo'], datasets: [] });
  });

  it('searchTerceros() — GET /filters/terceros/?q=X', () => {
    service.searchTerceros('juan').subscribe();
    const r = http.expectOne(req => req.url === `${base}/filters/terceros/` && req.params.get('q') === 'juan');
    expect(r.request.method).toBe('GET');
    r.flush([]);
  });

  it('getProyectos() — GET /filters/proyectos/', () => {
    service.getProyectos().subscribe();
    http.expectOne(`${base}/filters/proyectos/`).flush([]);
  });

  it('getDepartamentos() — GET /filters/departamentos/', () => {
    service.getDepartamentos().subscribe();
    http.expectOne(`${base}/filters/departamentos/`).flush([]);
  });

  it('getPeriodos() — GET /filters/periodos/', () => {
    service.getPeriodos().subscribe();
    http.expectOne(`${base}/filters/periodos/`).flush([]);
  });
});
