/**
 * SaiSuite — Tests ActividadProyectoService
 * Cubre: listByProyecto (con y sin faseId), asignar, update, desasignar.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ActividadProyectoService } from './actividad-proyecto.service';
import { ActividadProyecto } from '../models/actividad.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockActividadProyecto: ActividadProyecto = {
  id: 'ap-1', proyecto: 'p-1', actividad: 'a-1',
  actividad_codigo: 'ACT-001', actividad_nombre: 'Excavación',
  actividad_unidad_medida: 'm3', actividad_tipo: 'material',
  fase: 'f-1', fase_nombre: 'Fase Inicial',
  cantidad_planificada: '10.00', cantidad_ejecutada: '0.00',
  costo_unitario: '50000.00', presupuesto_total: '500000.00',
  porcentaje_avance: '0.00', created_at: '2026-01-01T00:00:00Z',
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('ActividadProyectoService', () => {
  let service: ActividadProyectoService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ActividadProyectoService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── listByProyecto ────────────────────────────────────────────────────────

  it('listByProyecto() GET /api/v1/proyectos/:id/actividades/ — respuesta paginada', () => {
    service.listByProyecto('p-1').subscribe(items => {
      expect(items.length).toBe(1);
      expect(items[0].actividad_codigo).toBe('ACT-001');
    });
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/');
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [mockActividadProyecto] });
  });

  it('listByProyecto() acepta respuesta directa (array sin paginación)', () => {
    service.listByProyecto('p-1').subscribe(items => {
      expect(items.length).toBe(1);
      expect(items[0].id).toBe('ap-1');
    });
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/');
    req.flush([mockActividadProyecto]);
  });

  it('listByProyecto() envía filtro por fase cuando se especifica', () => {
    service.listByProyecto('p-1', 'f-1').subscribe(items => {
      expect(items.length).toBe(1);
    });
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/?fase=f-1');
    req.flush([mockActividadProyecto]);
  });

  it('listByProyecto() sin faseId no envía parámetro fase', () => {
    service.listByProyecto('p-1').subscribe();
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/');
    expect(req.request.url).not.toContain('fase=');
    req.flush([]);
  });

  // ── asignar ───────────────────────────────────────────────────────────────

  it('asignar() POST /api/v1/proyectos/:id/actividades/', () => {
    const payload = {
      actividad: 'a-1',
      fase: 'f-1',
      cantidad_planificada: '10.00',
      costo_unitario: '50000.00',
    };
    service.asignar('p-1', payload).subscribe(ap => expect(ap.id).toBe('ap-1'));
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.actividad).toBe('a-1');
    req.flush(mockActividadProyecto);
  });

  it('asignar() permite omitir costo_unitario (backend usa costo_unitario_base)', () => {
    const payload = { actividad: 'a-1', cantidad_planificada: '5.00' };
    service.asignar('p-1', payload).subscribe();
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/');
    expect(req.request.body).not.toEqual(jasmine.objectContaining({ costo_unitario: jasmine.anything() }));
    req.flush(mockActividadProyecto);
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() PATCH /api/v1/proyectos/:id/actividades/:apId/', () => {
    service.update('p-1', 'ap-1', { cantidad_ejecutada: '7.00' }).subscribe();
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/ap-1/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ cantidad_ejecutada: '7.00' });
    req.flush({ ...mockActividadProyecto, cantidad_ejecutada: '7.00' });
  });

  // ── desasignar ────────────────────────────────────────────────────────────

  it('desasignar() DELETE /api/v1/proyectos/:id/actividades/:apId/', () => {
    service.desasignar('p-1', 'ap-1').subscribe();
    const req = http.expectOne('/api/v1/proyectos/p-1/actividades/ap-1/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
