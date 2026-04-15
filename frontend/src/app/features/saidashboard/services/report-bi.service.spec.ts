import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ReportBIService } from './report-bi.service';
import { ReportBICreateRequest, ReportBIExecuteRequest } from '../models/report-bi.model';

describe('ReportBIService', () => {
  let service: ReportBIService;
  let http: HttpTestingController;
  const base = '/api/v1/dashboard/reportes';

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(ReportBIService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── CRUD ──────────────────────────────────────────────────

  it('list() — GET /', () => {
    service.list().subscribe(items => {
      expect(items).toEqual([]);
    });
    http.expectOne(`${base}/`).flush([]);
  });

  it('getById() — GET /:id', () => {
    service.getById('r1').subscribe(r => {
      expect(r.id).toBe('r1');
    });
    http.expectOne(`${base}/r1/`).flush({ id: 'r1' });
  });

  it('create() — POST /', () => {
    const payload: ReportBICreateRequest = {
      titulo: 'Test Report',
      fuentes: ['gl'],
    };
    service.create(payload).subscribe();
    const req = http.expectOne(`${base}/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.titulo).toBe('Test Report');
    req.flush({ id: 'new-1' });
  });

  it('update() — PUT /:id', () => {
    service.update('r1', { titulo: 'Updated' }).subscribe();
    const req = http.expectOne(`${base}/r1/`);
    expect(req.request.method).toBe('PUT');
    req.flush({ id: 'r1' });
  });

  it('delete() — DELETE /:id', () => {
    service.delete('r1').subscribe();
    const req = http.expectOne(`${base}/r1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  // ── Actions ───────────────────────────────────────────────

  it('execute() — POST /:id/execute/', () => {
    service.execute('r1').subscribe(result => {
      expect(result).toBeTruthy();
    });
    const req = http.expectOne(`${base}/r1/execute/`);
    expect(req.request.method).toBe('POST');
    req.flush({ columns: ['col1'], rows: [], total_count: 0 });
  });

  it('preview() — POST /preview/', () => {
    const data: ReportBIExecuteRequest = {
      fuentes: ['gl'],
      campos_config: [{ source: 'gl', field: 'debito', role: 'metric', aggregation: 'SUM', label: 'Débito' }],
    };
    service.preview(data).subscribe(result => {
      expect(result).toBeTruthy();
    });
    const req = http.expectOne(`${base}/preview/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.fuentes).toEqual(['gl']);
    req.flush({ columns: ['debito'], rows: [], total_count: 5 });
  });

  it('toggleFavorite() — POST /:id/toggle-favorite/', () => {
    service.toggleFavorite('r1').subscribe(res => {
      expect(res.es_favorito).toBeTrue();
    });
    const req = http.expectOne(`${base}/r1/toggle-favorite/`);
    expect(req.request.method).toBe('POST');
    req.flush({ es_favorito: true });
  });

  // ── Share ─────────────────────────────────────────────────

  it('share() — POST /:id/share/', () => {
    service.share('r1', { user_id: 'u1', puede_editar: false }).subscribe();
    const req = http.expectOne(`${base}/r1/share/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('revokeShare() — DELETE /:id/share/:userId/', () => {
    service.revokeShare('r1', 'u1').subscribe();
    const req = http.expectOne(`${base}/r1/share/u1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  // ── Export ───────────────────────────────────────────────

  it('exportPdf() — POST /:id/export-pdf/', () => {
    service.exportPdf('r1').subscribe(blob => {
      expect(blob).toBeTruthy();
    });
    const req = http.expectOne(`${base}/r1/export-pdf/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.responseType).toBe('blob');
    req.flush(new Blob(['pdf content']));
  });

  // ── Metadata ──────────────────────────────────────────────

  it('getTemplates() — GET /templates/', () => {
    service.getTemplates().subscribe(items => {
      expect(items.length).toBe(1);
    });
    http.expectOne(`${base}/templates/`).flush([{ id: 't1' }]);
  });

  it('getSources() — GET /meta/sources/', () => {
    service.getSources().subscribe(sources => {
      expect(sources.length).toBe(2);
    });
    http.expectOne(`${base}/meta/sources/`).flush([
      { code: 'gl', label: 'GL', description: '', icon: '' },
      { code: 'cartera', label: 'Cartera', description: '', icon: '' },
    ]);
  });

  it('getFields() — GET /meta/fields/?source=gl', () => {
    service.getFields('gl').subscribe(data => {
      expect(data['Valores']).toBeDefined();
    });
    const req = http.expectOne(r => r.url === `${base}/meta/fields/` && r.params.get('source') === 'gl');
    expect(req.request.method).toBe('GET');
    req.flush({ Valores: [{ field: 'debito', label: 'Débito', type: 'decimal', role: 'metric' }] });
  });

  it('getFilters() — GET /meta/filters/?source=gl', () => {
    service.getFilters('gl').subscribe(filters => {
      expect(filters.length).toBe(1);
    });
    const req = http.expectOne(r => r.url === `${base}/meta/filters/` && r.params.get('source') === 'gl');
    expect(req.request.method).toBe('GET');
    req.flush([{ field: 'periodo', label: 'Período', type: 'multi_select' }]);
  });

  it('getJoins() — GET /meta/joins/', () => {
    service.getJoins().subscribe(joins => {
      expect(joins.length).toBe(1);
      expect(joins[0].source_a).toBe('facturacion');
    });
    http.expectOne(`${base}/meta/joins/`).flush([
      { source_a: 'facturacion', source_b: 'facturacion_detalle', description: 'FK', type: 'fk' },
    ]);
  });

  it('duplicate() — POST /:id/duplicate/', () => {
    service.duplicate('rep-id', { titulo: 'Mi copia' }).subscribe(r => {
      expect(r.titulo).toBe('Mi copia');
    });
    const req = http.expectOne(`${base}/rep-id/duplicate/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ titulo: 'Mi copia' });
    req.flush({ id: 'new-id', titulo: 'Mi copia' });
  });
});
