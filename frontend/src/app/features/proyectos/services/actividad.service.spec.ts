/**
 * SaiSuite — Tests ActividadService
 * Cubre: list (con filtros y paginación), getById, create, update, delete.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ActividadService } from './actividad.service';
import { ActividadList, ActividadDetail } from '../models/actividad.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockActividadList: ActividadList = {
  id: 'a-1', codigo: 'ACT-001', nombre: 'Excavación',
  tipo: 'material', tipo_display: 'Material',
  unidad_medida: 'm3', costo_unitario_base: '50000.00',
  activo: true, created_at: '2026-01-01T00:00:00Z',
};

const mockActividadDetail: ActividadDetail = {
  ...mockActividadList,
  descripcion: 'Excavación manual',
  saiopen_actividad_id: null,
  sincronizado_con_saiopen: false,
  updated_at: '2026-01-01T00:00:00Z',
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('ActividadService', () => {
  let service: ActividadService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ActividadService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── list ──────────────────────────────────────────────────────────────────

  it('list() GET /api/v1/projects/activities/ con paginación por defecto', () => {
    service.list().subscribe(res => {
      expect(res.count).toBe(1);
      expect(res.results[0].codigo).toBe('ACT-001');
    });
    const req = http.expectOne(r =>
      r.url === '/api/v1/projects/activities/' &&
      r.params.get('page') === '1' &&
      r.params.get('page_size') === '25'
    );
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [mockActividadList] });
  });

  it('list() envía parámetro search', () => {
    service.list('Excavación').subscribe();
    const req = http.expectOne(r => r.params.get('search') === 'Excavación');
    req.flush({ count: 1, next: null, previous: null, results: [mockActividadList] });
  });

  it('list() envía parámetro tipo', () => {
    service.list(undefined, 'mano_obra').subscribe();
    const req = http.expectOne(r => r.params.get('tipo') === 'mano_obra');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('list() no envía parámetro tipo si no se especifica', () => {
    service.list().subscribe();
    const req = http.expectOne(r => r.url === '/api/v1/projects/activities/');
    expect(req.request.params.has('tipo')).toBeFalse();
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('list() envía page y page_size personalizados', () => {
    service.list(undefined, undefined, 3, 10).subscribe();
    const req = http.expectOne(r =>
      r.params.get('page') === '3' && r.params.get('page_size') === '10'
    );
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('list() combina search y tipo simultáneamente', () => {
    service.list('Pintura', 'material').subscribe();
    const req = http.expectOne(r =>
      r.params.get('search') === 'Pintura' && r.params.get('tipo') === 'material'
    );
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  // ── getById ───────────────────────────────────────────────────────────────

  it('getById() GET /api/v1/projects/activities/:id/', () => {
    service.getById('a-1').subscribe(a => {
      expect(a.id).toBe('a-1');
      expect(a.descripcion).toBe('Excavación manual');
    });
    const req = http.expectOne('/api/v1/projects/activities/a-1/');
    expect(req.request.method).toBe('GET');
    req.flush(mockActividadDetail);
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() POST /api/v1/projects/activities/', () => {
    const payload = {
      nombre: 'Nueva Actividad',
      tipo: 'equipo' as const,
      unidad_medida: 'hora',
      costo_unitario_base: '75000',
    };
    service.create(payload).subscribe(a => expect(a.tipo).toBe('material'));
    const req = http.expectOne('/api/v1/projects/activities/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.nombre).toBe('Nueva Actividad');
    req.flush(mockActividadDetail);
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() PATCH /api/v1/projects/activities/:id/', () => {
    service.update('a-1', { costo_unitario_base: '60000' }).subscribe();
    const req = http.expectOne('/api/v1/projects/activities/a-1/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ costo_unitario_base: '60000' });
    req.flush(mockActividadDetail);
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() DELETE /api/v1/projects/activities/:id/', () => {
    service.delete('a-1').subscribe();
    const req = http.expectOne('/api/v1/projects/activities/a-1/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
