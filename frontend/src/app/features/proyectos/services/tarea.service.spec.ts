/**
 * SaiSuite — Tests TareaService
 * Cubre: list (con y sin filtros), listByProyecto, getById, create, update,
 *        delete, agregarFollower, quitarFollower, cambiarEstado,
 *        getMisTareas, getVencidas, getSubtareas.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TareaService } from './tarea.service';
import { Tarea, TareaCreateDTO } from '../models/tarea.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockTarea: Tarea = {
  id: 't-1',
  codigo: 'TASK-00001',
  nombre: 'Tarea de prueba',
  descripcion: '',
  proyecto: 'p-1',
  fase: null,
  tarea_padre: null,
  responsable: null,
  followers: [],
  prioridad: 2,
  tags: [],
  fecha_inicio: null,
  fecha_fin: null,
  fecha_limite: null,
  estado: 'por_hacer',
  porcentaje_completado: 0,
  horas_estimadas: 0,
  horas_registradas: 0,
  es_recurrente: false,
  frecuencia_recurrencia: null,
  proxima_generacion: null,
  es_vencida: false,
  tiene_subtareas: false,
  nivel_jerarquia: 0,
  created_at: '2026-03-22T10:00:00Z',
  updated_at: '2026-03-22T10:00:00Z',
};

const BASE = '/api/v1/projects/tasks';

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('TareaService', () => {
  let service: TareaService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(TareaService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── list ──────────────────────────────────────────────────────────────────

  it('list() GET sin filtros', () => {
    service.list().subscribe(tareas => {
      expect(tareas.length).toBe(1);
      expect(tareas[0].codigo).toBe('TASK-00001');
    });

    const req = http.expectOne(r => r.url === `${BASE}/` && r.method === 'GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush([mockTarea]);
  });

  it('list() envía filtro estado', () => {
    service.list({ estado: 'en_progreso' }).subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` && r.params.get('estado') === 'en_progreso'
    );
    req.flush([]);
  });

  it('list() envía filtro prioridad como string', () => {
    service.list({ prioridad: 3 }).subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` && r.params.get('prioridad') === '3'
    );
    req.flush([]);
  });

  it('list() omite filtros undefined/null/vacíos', () => {
    service.list({ estado: undefined, search: '' }).subscribe();

    const req = http.expectOne(r => r.url === `${BASE}/`);
    expect(req.request.params.has('estado')).toBeFalse();
    expect(req.request.params.has('search')).toBeFalse();
    req.flush([]);
  });

  // ── listByProyecto ────────────────────────────────────────────────────────

  it('listByProyecto() agrega filtro proyecto', () => {
    service.listByProyecto('p-1').subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` && r.params.get('proyecto') === 'p-1'
    );
    req.flush([mockTarea]);
  });

  it('listByProyecto() combina proyecto con otros filtros', () => {
    service.listByProyecto('p-1', { estado: 'bloqueada' }).subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` &&
      r.params.get('proyecto') === 'p-1' &&
      r.params.get('estado') === 'bloqueada'
    );
    req.flush([]);
  });

  // ── getById ───────────────────────────────────────────────────────────────

  it('getById() GET /tareas/{id}/', () => {
    service.getById('t-1').subscribe(t => {
      expect(t.id).toBe('t-1');
      expect(t.codigo).toBe('TASK-00001');
    });

    const req = http.expectOne(`${BASE}/t-1/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockTarea);
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() POST /tareas/', () => {
    const payload: TareaCreateDTO = {
      nombre: 'Nueva tarea',
      proyecto: 'p-1',
      prioridad: 2,
    };

    service.create(payload).subscribe(t => expect(t.id).toBe('t-1'));

    const req = http.expectOne(`${BASE}/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ ...mockTarea, nombre: payload.nombre });
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() PATCH /tareas/{id}/', () => {
    service.update('t-1', { nombre: 'Editada' }).subscribe();

    const req = http.expectOne(`${BASE}/t-1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ nombre: 'Editada' });
    req.flush({ ...mockTarea, nombre: 'Editada' });
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() DELETE /tareas/{id}/', () => {
    service.delete('t-1').subscribe();

    const req = http.expectOne(`${BASE}/t-1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });

  // ── agregarFollower ───────────────────────────────────────────────────────

  it('agregarFollower() POST /tareas/{id}/agregar-follower/', () => {
    service.agregarFollower('t-1', 'u-1').subscribe(res => {
      expect(res.followers_count).toBe(2);
    });

    const req = http.expectOne(`${BASE}/t-1/agregar-follower/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ user_id: 'u-1' });
    req.flush({ message: 'Follower agregado', followers_count: 2 });
  });

  // ── quitarFollower ────────────────────────────────────────────────────────

  it('quitarFollower() DELETE /tareas/{id}/quitar-follower/{user_id}/', () => {
    service.quitarFollower('t-1', 'u-1').subscribe(res => {
      expect(res.followers_count).toBe(1);
    });

    const req = http.expectOne(`${BASE}/t-1/quitar-follower/u-1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush({ message: 'Follower removido', followers_count: 1 });
  });

  // ── cambiarEstado ─────────────────────────────────────────────────────────

  it('cambiarEstado() POST /tareas/{id}/cambiar-estado/', () => {
    service.cambiarEstado('t-1', 'completada').subscribe(t => {
      expect(t.estado).toBe('completada');
    });

    const req = http.expectOne(`${BASE}/t-1/cambiar-estado/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ estado: 'completada' });
    req.flush({ ...mockTarea, estado: 'completada', porcentaje_completado: 100 });
  });

  // ── getMisTareas ──────────────────────────────────────────────────────────

  it('getMisTareas() agrega solo_mis_tareas=true', () => {
    service.getMisTareas().subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` && r.params.get('solo_mis_tareas') === 'true'
    );
    req.flush([]);
  });

  // ── getVencidas ───────────────────────────────────────────────────────────

  it('getVencidas() agrega vencidas=true', () => {
    service.getVencidas().subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` && r.params.get('vencidas') === 'true'
    );
    req.flush([]);
  });

  // ── getSubtareas ──────────────────────────────────────────────────────────

  it('getSubtareas() filtra por tarea_padre', () => {
    service.getSubtareas('t-1').subscribe();

    const req = http.expectOne(r =>
      r.url === `${BASE}/` && r.params.get('tarea_padre') === 't-1'
    );
    req.flush([]);
  });
});
