/**
 * SaiSuite — Tests ProyectoService
 * Cubre: list (con parámetros), getById, create, update, delete,
 *        cambiarEstado, getEstadoFinanciero.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ProyectoService } from './proyecto.service';
import { ProyectoList, ProyectoDetail, EstadoFinanciero } from '../models/proyecto.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockGerente = { id: 'u-1', email: 'gerente@test.com', full_name: 'Gerente Test' };

const mockProyectoList: ProyectoList = {
  id: 'p-1', codigo: 'PRY-001', nombre: 'Proyecto Test',
  tipo: 'obra_civil', estado: 'planificado',
  cliente_nombre: 'Cliente SA', gerente: mockGerente,
  fecha_inicio_planificada: '2026-04-01', fecha_fin_planificada: '2026-12-31',
  presupuesto_total: '1000000.00', porcentaje_avance: '0.00',
  activo: true, created_at: '2026-01-01T00:00:00Z',
};

const mockProyectoDetail: ProyectoDetail = {
  ...mockProyectoList,
  cliente_id: '900111222',
  coordinador: null,
  fecha_inicio_real: null, fecha_fin_real: null,
  porcentaje_administracion: '10.00',
  porcentaje_imprevistos: '5.00',
  porcentaje_utilidad: '10.00',
  saiopen_proyecto_id: null, sincronizado_con_saiopen: false,
  ultima_sincronizacion: null,
  fases_count: 0, presupuesto_fases_total: '0.00',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockEstadoFinanciero: EstadoFinanciero = {
  presupuesto_total: '1000000.00', presupuesto_costos: '800000.00',
  precio_venta_aiu: '1000000.00', costo_ejecutado: '0.00',
  porcentaje_avance_fisico: '0.00', porcentaje_avance_financiero: '0.00',
  desviacion_presupuesto: '0.00',
  desglose_presupuesto: { mano_obra: '0', materiales: '0', subcontratos: '0', equipos: '0', otros: '0' },
  aiu: { porcentaje_administracion: '10', porcentaje_imprevistos: '5', porcentaje_utilidad: '10', valor_aiu: '200000' },
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('ProyectoService', () => {
  let service: ProyectoService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ProyectoService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── list ──────────────────────────────────────────────────────────────────

  it('list() GET /api/v1/projects/ sin parámetros', () => {
    service.list().subscribe(res => {
      expect(res.count).toBe(1);
      expect(res.results[0].codigo).toBe('PRY-001');
    });
    const req = http.expectOne(r => r.url === '/api/v1/projects/');
    expect(req.request.method).toBe('GET');
    req.flush({ count: 1, next: null, previous: null, results: [mockProyectoList] });
  });

  it('list() envía parámetro search', () => {
    service.list({ search: 'Torre' }).subscribe();
    const req = http.expectOne(r => r.params.get('search') === 'Torre');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('list() envía parámetro estado', () => {
    service.list({ estado: 'planificado' }).subscribe();
    const req = http.expectOne(r => r.params.get('estado') === 'planificado');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('list() envía parámetro tipo', () => {
    service.list({ tipo: 'servicios' }).subscribe();
    const req = http.expectOne(r => r.params.get('tipo') === 'servicios');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('list() envía parámetros de paginación', () => {
    service.list({ page: 2, page_size: 10 }).subscribe();
    const req = http.expectOne(r =>
      r.params.get('page') === '2' && r.params.get('page_size') === '10'
    );
    req.flush({ count: 10, next: null, previous: null, results: [] });
  });

  // ── getById ───────────────────────────────────────────────────────────────

  it('getById() GET /api/v1/projects/:id/', () => {
    service.getById('p-1').subscribe(p => {
      expect(p.id).toBe('p-1');
      expect(p.fases_count).toBe(0);
    });
    const req = http.expectOne('/api/v1/projects/p-1/');
    expect(req.request.method).toBe('GET');
    req.flush(mockProyectoDetail);
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() POST /api/v1/projects/', () => {
    const payload = {
      nombre: 'Nuevo Proyecto', tipo: 'servicios' as const,
      cliente_id: '9001', cliente_nombre: 'Cliente Test',
      gerente: 'u-1',
      fecha_inicio_planificada: '2026-04-01',
      fecha_fin_planificada: '2026-12-31',
      presupuesto_total: '500000',
    };
    service.create(payload).subscribe(p => expect(p.nombre).toBe('Proyecto Test'));
    const req = http.expectOne('/api/v1/projects/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body.nombre).toBe('Nuevo Proyecto');
    req.flush(mockProyectoDetail);
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() PATCH /api/v1/projects/:id/', () => {
    service.update('p-1', { nombre: 'Editado' }).subscribe();
    const req = http.expectOne('/api/v1/projects/p-1/');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ nombre: 'Editado' });
    req.flush(mockProyectoDetail);
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() DELETE /api/v1/projects/:id/', () => {
    service.delete('p-1').subscribe();
    const req = http.expectOne('/api/v1/projects/p-1/');
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });

  // ── cambiarEstado ─────────────────────────────────────────────────────────

  it('cambiarEstado() POST /api/v1/projects/:id/cambiar-estado/ con forzar=false', () => {
    service.cambiarEstado('p-1', 'planificado').subscribe(p =>
      expect(p.estado).toBe('planificado')
    );
    const req = http.expectOne('/api/v1/projects/p-1/cambiar-estado/');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ nuevo_estado: 'planificado', forzar: false });
    req.flush({ ...mockProyectoDetail, estado: 'planificado' });
  });

  it('cambiarEstado() envía forzar=true cuando se especifica', () => {
    service.cambiarEstado('p-1', 'en_ejecucion', true).subscribe();
    const req = http.expectOne('/api/v1/projects/p-1/cambiar-estado/');
    expect(req.request.body.forzar).toBeTrue();
    req.flush(mockProyectoDetail);
  });

  // ── getEstadoFinanciero ───────────────────────────────────────────────────

  it('getEstadoFinanciero() GET /api/v1/projects/:id/estado-financiero/', () => {
    service.getEstadoFinanciero('p-1').subscribe(ef => {
      expect(ef.presupuesto_total).toBe('1000000.00');
      expect(ef.aiu.porcentaje_administracion).toBe('10');
    });
    const req = http.expectOne('/api/v1/projects/p-1/estado-financiero/');
    expect(req.request.method).toBe('GET');
    req.flush(mockEstadoFinanciero);
  });
});
