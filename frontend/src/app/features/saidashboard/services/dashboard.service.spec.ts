import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { DashboardService } from './dashboard.service';
import { DashboardCreate, CardLayoutRequest, ShareRequest } from '../models/dashboard.model';

describe('DashboardService', () => {
  let service: DashboardService;
  let http: HttpTestingController;
  const base = '/api/v1/dashboard';

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service  = TestBed.inject(DashboardService);
    http     = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── Dashboard CRUD ──────────────────────────────────────────

  it('list() — GET /', () => {
    service.list().subscribe();
    http.expectOne(`${base}/`).flush([]);
  });

  it('getById() — GET /:id', () => {
    service.getById('abc').subscribe();
    http.expectOne(`${base}/abc/`).flush({});
  });

  it('create() — POST /', () => {
    const payload: DashboardCreate = { titulo: 'Test', descripcion: '' };
    service.create(payload).subscribe();
    const req = http.expectOne(`${base}/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('update() — PUT /:id', () => {
    service.update('abc', { titulo: 'Updated' }).subscribe();
    const req = http.expectOne(`${base}/abc/`);
    expect(req.request.method).toBe('PUT');
    req.flush({});
  });

  it('delete() — DELETE /:id', () => {
    service.delete('abc').subscribe();
    const req = http.expectOne(`${base}/abc/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('setDefault() — POST /:id/set-default/', () => {
    service.setDefault('abc').subscribe();
    const req = http.expectOne(`${base}/abc/set-default/`);
    expect(req.request.method).toBe('POST');
    req.flush({ success: true });
  });

  it('toggleFavorite() — POST /:id/toggle-favorite/', () => {
    service.toggleFavorite('abc').subscribe(res => {
      expect(res.es_favorito).toBeTrue();
    });
    http.expectOne(`${base}/abc/toggle-favorite/`).flush({ es_favorito: true });
  });

  it('getSharedWithMe() — GET /compartidos-conmigo/', () => {
    service.getSharedWithMe().subscribe();
    http.expectOne(`${base}/compartidos-conmigo/`).flush([]);
  });

  // ── Cards ───────────────────────────────────────────────────

  it('getCards() — GET /:dashboardId/cards/', () => {
    service.getCards('d1').subscribe();
    http.expectOne(`${base}/d1/cards/`).flush([]);
  });

  it('addCard() — POST /:dashboardId/cards/', () => {
    service.addCard('d1', { card_type_code: 'BALANCE', chart_type: 'kpi', pos_x: 0, pos_y: 0, width: 4, height: 2 }).subscribe();
    const req = http.expectOne(`${base}/d1/cards/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('updateCard() — PUT /:dashboardId/cards/:cardId/', () => {
    service.updateCard('d1', '42', { width: 6 }).subscribe();
    const req = http.expectOne(`${base}/d1/cards/42/`);
    expect(req.request.method).toBe('PUT');
    req.flush({});
  });

  it('deleteCard() — DELETE /:dashboardId/cards/:cardId/', () => {
    service.deleteCard('d1', '42').subscribe();
    const req = http.expectOne(`${base}/d1/cards/42/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('saveLayout() — POST /:dashboardId/cards/layout/', () => {
    const layout: CardLayoutRequest = { layout: [] };
    service.saveLayout('d1', layout).subscribe();
    const req = http.expectOne(`${base}/d1/cards/layout/`);
    expect(req.request.method).toBe('POST');
    req.flush(layout);
  });

  // ── Share ───────────────────────────────────────────────────

  it('share() — POST /:dashboardId/share/', () => {
    const data: ShareRequest = { user_id: 'u1', puede_editar: false };
    service.share('d1', data).subscribe();
    const req = http.expectOne(`${base}/d1/share/`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('revokeShare() — DELETE /:dashboardId/share/:userId/', () => {
    service.revokeShare('d1', 'u1').subscribe();
    const req = http.expectOne(`${base}/d1/share/u1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
