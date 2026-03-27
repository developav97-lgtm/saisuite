/**
 * SaiSuite — Tests FaseService
 * Cubre: listByProyecto (paginado y array directo), getById, create, update, delete.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { FaseService } from './fase.service';
import { FaseList, FaseDetail } from '../models/fase.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockFaseList: FaseList = {
  id: 'f-1', nombre: 'Fase Inicial', orden: 1,
  porcentaje_avance: '0.00', presupuesto_total: '200000.00',
  activo: true, created_at: '2026-01-01T00:00:00Z',
};

const mockFaseDetail: FaseDetail = {
  ...mockFaseList,
  proyecto: 'p-1',
  descripcion: 'Descripción de prueba',
  fecha_inicio_planificada: '2026-04-01',
  fecha_fin_planificada: '2026-06-30',
  fecha_inicio_real: null, fecha_fin_real: null,
  presupuesto_mano_obra: '200000.00',
  presupuesto_materiales: '0.00',
  presupuesto_subcontratos: '0.00',
  presupuesto_equipos: '0.00',
  presupuesto_otros: '0.00',
  updated_at: '2026-01-01T00:00:00Z',
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('FaseService', () => {
  let service: FaseService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(FaseService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── listByProyecto ────────────────────────────────────────────────────────

  it('listByProyecto() GET /api/v1/projects/:proyectoId/phases/ — respuesta paginada', () => {
    service.listByProyecto('p-1').subscribe(fases => {
      expect(fases.length).toBe(1);
      expect(fases[0].nombre).toBe('Fase Inicial');
    });
    const req = http.expectOne('/api/v1/projects/p-1/phases/');
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [mockFaseList] });
  });

  it('listByProyecto() acepta respuesta directa (array sin paginación)', () => {
    service.listByProyecto('p-1').subscribe(fases => {
      expect(fases.length).toBe(1);
      expect(fases[0].id).toBe('f-1');
    });
    const req = http.expectOne('/api/v1/projects/p-1/phases/');
    req.flush([mockFaseList]);
  });

  it('listByProyecto() retorna array vacío cuando no hay fases', () => {
    service.listByProyecto('p-1').subscribe(fases => {
      expect(fases).toEqual([]);
    });
    const req = http.expectOne('/api/v1/projects/p-1/phases/');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  // ── getById ───────────────────────────────────────────────────────────────

  it('getById() GET /api/v1/projects/phases/:id/', () => {
    service.getById('f-1').subscribe(f => {
      expect(f.id).toBe('f-1');
      expect(f.presupuesto_mano_obra).toBe('200000.00');
    });
    const req = http.expectOne('/api/v1/projects/phases/f-1/');
    expect(req.request.method).toBe('GET');
    req.flush(mockFaseDetail);
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() POST /api/v1/projects/:proyectoId/phases/', () => {
    const payload = {
      nombre: 'Nueva Fase',
      fecha_inicio_planificada: '2026-04-01',
      fecha_fin_planificada: '2026-06-30',
      presupuesto_mano_obra: '100000',
    };
    service.create('p-1', payload).subscribe(f => expect(f.nombre).toBe('Fase Inicial'));
    const req = http.expectOne('/api/v1/projects/p-1/phases/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.nombre).toBe('Nueva Fase');
    req.flush(mockFaseDetail);
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() PATCH /api/v1/projects/phases/:id/', () => {
    service.update('f-1', { nombre: 'Fase Editada' }).subscribe();
    const req = http.expectOne('/api/v1/projects/phases/f-1/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ nombre: 'Fase Editada' });
    req.flush(mockFaseDetail);
  });

  it('update() actualiza porcentaje_avance', () => {
    service.update('f-1', { porcentaje_avance: '50.00' }).subscribe();
    const req = http.expectOne('/api/v1/projects/phases/f-1/');
    expect(req.request.body).toEqual({ porcentaje_avance: '50.00' });
    req.flush(mockFaseDetail);
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() DELETE /api/v1/projects/phases/:id/', () => {
    service.delete('f-1').subscribe();
    const req = http.expectOne('/api/v1/projects/phases/f-1/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
