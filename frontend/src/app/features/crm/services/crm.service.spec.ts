/**
 * SaiSuite — CrmService Tests
 * Cobertura 100% de todos los métodos HTTP del servicio.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

import { CrmService } from './crm.service';
import {
  CrmPipeline, CrmEtapa, KanbanColumna,
  CrmLead, CrmOportunidad, CrmActividad, CrmTimelineEvent,
  CrmCotizacion, CrmLineaCotizacion, CrmProducto, CrmImpuesto,
  CrmLeadScoringRule, CrmDashboard, CrmForecast,
} from '../models/crm.model';

const BASE = '/api/v1/crm';

// ─── Fixtures ────────────────────────────────────────────────────────────────

const mockEtapa: CrmEtapa = {
  id: 'e1', nombre: 'Prospecto', orden: 1, color: '#000',
  probabilidad: '10', es_ganado: false, es_perdido: false,
};

const mockPipeline: CrmPipeline = {
  id: 'p1', nombre: 'Ventas', es_default: true, etapas: [mockEtapa], created_at: '2026-01-01',
};

const mockKanban: KanbanColumna = {
  etapa_id: 'e1', etapa_nombre: 'Prospecto', color: '#000', probabilidad: '10',
  es_ganado: false, es_perdido: false, oportunidades: [],
  total_count: 0, total_valor: '0',
};

const mockLead: CrmLead = {
  id: 'l1', nombre: 'Juan', email: 'j@t.co', telefono: '', empresa: '', cargo: '',
  fuente: 'manual', score: 0, convertido: false, oportunidad: null,
  asignado_a: null, asignado_a_nombre: null, pipeline: null, notas: '',
  created_at: '2026-01-01', updated_at: '2026-01-01',
};

const mockOportunidad: CrmOportunidad = {
  id: 'o1', titulo: 'Oport1', pipeline: 'p1', pipeline_nombre: 'Ventas',
  etapa: 'e1', etapa_nombre: 'Prospecto', etapa_color: '#000',
  valor_esperado: '1000', probabilidad: '10', valor_ponderado: '100',
  fecha_cierre_estimada: null,
  contacto: null, contacto_nombre: null, asignado_a: null, asignado_a_nombre: null,
  ganada_en: null, perdida_en: null, motivo_perdida: '',
  proxima_actividad_fecha: null, proxima_actividad_tipo: null,
  created_at: '2026-01-01', updated_at: '2026-01-01',
};

const mockActividad: CrmActividad = {
  id: 'a1', oportunidad: 'o1', tipo: 'llamada', titulo: 'Llamada', descripcion: '',
  fecha_programada: '2026-04-20T10:00:00Z', completada: false,
  asignado_a: null, asignado_a_nombre: null, resultado: '', created_at: '2026-01-01',
};

const mockTimeline: CrmTimelineEvent = {
  id: 't1', tipo: 'nota', descripcion: 'Nota test',
  usuario_nombre: null, metadata: {}, created_at: '2026-01-01',
};

const mockCotizacion: CrmCotizacion = {
  id: 'c1', numero_interno: 'COT-001', titulo: 'Cot 1', oportunidad: 'o1',
  estado: 'borrador', contacto: null, contacto_nombre: null,
  validez_dias: 30, fecha_vencimiento: null,
  subtotal: '0', descuento_adicional_p: '0', descuento_adicional_val: '0',
  total_iva: '0', total: '0', notas: '', terminos: '',
  sai_key: null, saiopen_synced: false, lineas: [],
  created_at: '2026-01-01', updated_at: '2026-01-01',
};

const mockLinea: CrmLineaCotizacion = {
  id: 'li1', conteo: 1, producto: null, descripcion: 'Desc',
  cantidad: '1', vlr_unitario: '100', descuento_p: '0',
  impuesto: null, iva_valor: '0', total_parcial: '100',
};

const mockProducto: CrmProducto = {
  id: 'pr1', nombre: 'Prod', codigo: 'P01', descripcion: '',
  precio_base: '100', unidad_venta: 'UND',
  impuesto: null, impuesto_nombre: null, impuesto_porcentaje: null,
};

const mockImpuesto: CrmImpuesto = { id: 'im1', nombre: 'IVA 19%', porcentaje: '19' };

const mockScoringRule: CrmLeadScoringRule = {
  id: 'sr1', nombre: 'Tiene email', campo: 'email', operador: 'not_empty',
  valor: '', puntos: 10, orden: 1, activa: true,
};

const mockDashboard: CrmDashboard = {
  total_leads: 10, leads_nuevos_mes: 5, oportunidades_activas: 3,
  valor_total_activo: '50000', tasa_conversion: '20', forecast: '30000',
  funnel: [], rendimiento_vendedores: [],
};

const mockForecast: CrmForecast = {
  total_forecast: '40000', total_valor_esperado: '60000', detalle: [],
};

// ─── Suite ───────────────────────────────────────────────────────────────────

describe('CrmService', () => {
  let service: CrmService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [CrmService, provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(CrmService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── Pipelines ───────────────────────────────────────────────────────────────

  it('listPipelines — GET /pipelines/', () => {
    service.listPipelines().subscribe(r => expect(r).toEqual([mockPipeline]));
    http.expectOne(`${BASE}/pipelines/`).flush([mockPipeline]);
  });

  it('createPipeline — POST /pipelines/', () => {
    service.createPipeline({ nombre: 'Ventas' }).subscribe(r => expect(r.id).toBe('p1'));
    const req = http.expectOne(`${BASE}/pipelines/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockPipeline);
  });

  it('updatePipeline — PATCH /pipelines/:id/', () => {
    service.updatePipeline('p1', { nombre: 'Actualizado' }).subscribe(r => expect(r.id).toBe('p1'));
    const req = http.expectOne(`${BASE}/pipelines/p1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockPipeline);
  });

  it('deletePipeline — DELETE /pipelines/:id/', () => {
    service.deletePipeline('p1').subscribe();
    const req = http.expectOne(`${BASE}/pipelines/p1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('getKanban — GET /pipelines/:id/kanban/', () => {
    service.getKanban('p1').subscribe(r => expect(r).toEqual([mockKanban]));
    http.expectOne(`${BASE}/pipelines/p1/kanban/`).flush([mockKanban]);
  });

  // ── Etapas ──────────────────────────────────────────────────────────────────

  it('createEtapa — POST /pipelines/:id/etapas/', () => {
    service.createEtapa('p1', { nombre: 'Cierre' }).subscribe(r => expect(r.id).toBe('e1'));
    const req = http.expectOne(`${BASE}/pipelines/p1/etapas/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockEtapa);
  });

  it('updateEtapa — PATCH /etapas/:id/', () => {
    service.updateEtapa('e1', { nombre: 'Nuevo' }).subscribe(r => expect(r.id).toBe('e1'));
    const req = http.expectOne(`${BASE}/etapas/e1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockEtapa);
  });

  it('deleteEtapa — DELETE /etapas/:id/', () => {
    service.deleteEtapa('e1').subscribe();
    const req = http.expectOne(`${BASE}/etapas/e1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('reordenarEtapas — POST /pipelines/:id/etapas/reordenar/', () => {
    service.reordenarEtapas('p1', [{ id: 'e1', orden: 1 }]).subscribe();
    const req = http.expectOne(`${BASE}/pipelines/p1/etapas/reordenar/`);
    expect(req.request.method).toBe('POST');
    req.flush(null);
  });

  // ── Leads ───────────────────────────────────────────────────────────────────

  it('listLeads — GET /leads/ sin params', () => {
    service.listLeads().subscribe(r => expect(r.results).toEqual([mockLead]));
    http.expectOne(`${BASE}/leads/`).flush({ count: 1, results: [mockLead] });
  });

  it('listLeads — GET /leads/ con params', () => {
    service.listLeads({ search: 'Juan', fuente: 'manual', convertido: false, page: 2, page_size: 20 }).subscribe();
    const req = http.expectOne(r => r.url === `${BASE}/leads/`);
    expect(req.request.params.get('search')).toBe('Juan');
    expect(req.request.params.get('fuente')).toBe('manual');
    expect(req.request.params.get('convertido')).toBe('false');
    expect(req.request.params.get('page')).toBe('2');
    req.flush({ count: 0, results: [] });
  });

  it('listLeads — GET /leads/ con asignado_a, pipeline, ordering', () => {
    service.listLeads({ asignado_a: 'u1', pipeline: 'p1', ordering: '-score' }).subscribe();
    const req = http.expectOne(r => r.url === `${BASE}/leads/`);
    expect(req.request.params.get('asignado_a')).toBe('u1');
    expect(req.request.params.get('pipeline')).toBe('p1');
    expect(req.request.params.get('ordering')).toBe('-score');
    req.flush({ count: 0, results: [] });
  });

  it('getLead — GET /leads/:id/', () => {
    service.getLead('l1').subscribe(r => expect(r.id).toBe('l1'));
    http.expectOne(`${BASE}/leads/l1/`).flush(mockLead);
  });

  it('createLead — POST /leads/', () => {
    const data = { nombre: 'Juan', email: 'j@t.co', fuente: 'manual' as const };
    service.createLead(data).subscribe(r => expect(r.id).toBe('l1'));
    const req = http.expectOne(`${BASE}/leads/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockLead);
  });

  it('updateLead — PATCH /leads/:id/', () => {
    service.updateLead('l1', { nombre: 'Nuevo' }).subscribe(r => expect(r.id).toBe('l1'));
    const req = http.expectOne(`${BASE}/leads/l1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockLead);
  });

  it('deleteLead — DELETE /leads/:id/', () => {
    service.deleteLead('l1').subscribe();
    const req = http.expectOne(`${BASE}/leads/l1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('convertirLead — POST /leads/:id/convertir/', () => {
    service.convertirLead('l1', { etapa_id: 'e1', valor_esperado: '500' }).subscribe(r => expect(r.id).toBe('o1'));
    const req = http.expectOne(`${BASE}/leads/l1/convertir/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockOportunidad);
  });

  it('asignarLead — POST /leads/:id/asignar/', () => {
    service.asignarLead('l1', 'u1').subscribe(r => expect(r.id).toBe('l1'));
    const req = http.expectOne(`${BASE}/leads/l1/asignar/`);
    expect(req.request.body).toEqual({ usuario_id: 'u1' });
    req.flush(mockLead);
  });

  it('importarLeads — POST /leads/importar/', () => {
    const registros = [{ nombre: 'X', email: 'x@t.co' }];
    service.importarLeads(registros).subscribe(r => expect(r.creados).toBe(1));
    const req = http.expectOne(`${BASE}/leads/importar/`);
    expect(req.request.body).toEqual({ registros });
    req.flush({ creados: 1, errores: [] });
  });

  // ── Scoring Rules ────────────────────────────────────────────────────────────

  it('listScoringRules — GET /scoring-rules/', () => {
    service.listScoringRules().subscribe(r => expect(r).toEqual([mockScoringRule]));
    http.expectOne(`${BASE}/scoring-rules/`).flush([mockScoringRule]);
  });

  it('createScoringRule — POST /scoring-rules/', () => {
    service.createScoringRule({ campo: 'email', puntos: 10 }).subscribe(r => expect(r.id).toBe('sr1'));
    const req = http.expectOne(`${BASE}/scoring-rules/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockScoringRule);
  });

  it('updateScoringRule — PATCH /scoring-rules/:id/', () => {
    service.updateScoringRule('sr1', { puntos: 20 }).subscribe(r => expect(r.id).toBe('sr1'));
    const req = http.expectOne(`${BASE}/scoring-rules/sr1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockScoringRule);
  });

  it('deleteScoringRule — DELETE /scoring-rules/:id/', () => {
    service.deleteScoringRule('sr1').subscribe();
    const req = http.expectOne(`${BASE}/scoring-rules/sr1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  // ── Oportunidades ────────────────────────────────────────────────────────────

  it('listOportunidades — GET /oportunidades/ sin params', () => {
    service.listOportunidades().subscribe(r => expect(r.results).toEqual([mockOportunidad]));
    http.expectOne(`${BASE}/oportunidades/`).flush({ count: 1, results: [mockOportunidad] });
  });

  it('listOportunidades — GET /oportunidades/ con params', () => {
    service.listOportunidades({ pipeline: 'p1', etapa: 'e1', asignado_a: 'u1', ordering: '-created_at', page: 1, page_size: 10 }).subscribe();
    const req = http.expectOne(r => r.url === `${BASE}/oportunidades/`);
    expect(req.request.params.get('pipeline')).toBe('p1');
    expect(req.request.params.get('ordering')).toBe('-created_at');
    req.flush({ count: 0, results: [] });
  });

  it('listOportunidades — GET /oportunidades/ con search', () => {
    service.listOportunidades({ search: 'test' }).subscribe();
    const req = http.expectOne(r => r.url === `${BASE}/oportunidades/`);
    expect(req.request.params.get('search')).toBe('test');
    req.flush({ count: 0, results: [] });
  });

  it('getOportunidad — GET /oportunidades/:id/', () => {
    service.getOportunidad('o1').subscribe(r => expect(r.id).toBe('o1'));
    http.expectOne(`${BASE}/oportunidades/o1/`).flush(mockOportunidad);
  });

  it('createOportunidad — POST /oportunidades/', () => {
    const data = { titulo: 'Oport1', pipeline: 'p1', etapa: 'e1', valor_esperado: '1000', probabilidad: '10' };
    service.createOportunidad(data).subscribe(r => expect(r.id).toBe('o1'));
    const req = http.expectOne(`${BASE}/oportunidades/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockOportunidad);
  });

  it('updateOportunidad — PATCH /oportunidades/:id/', () => {
    service.updateOportunidad('o1', { titulo: 'Nuevo' }).subscribe(r => expect(r.id).toBe('o1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockOportunidad);
  });

  it('deleteOportunidad — DELETE /oportunidades/:id/', () => {
    service.deleteOportunidad('o1').subscribe();
    const req = http.expectOne(`${BASE}/oportunidades/o1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('moverEtapa — POST /oportunidades/:id/mover-etapa/', () => {
    service.moverEtapa('o1', 'e2').subscribe(r => expect(r.id).toBe('o1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/mover-etapa/`);
    expect(req.request.body).toEqual({ etapa_id: 'e2' });
    req.flush(mockOportunidad);
  });

  it('ganarOportunidad — POST /oportunidades/:id/ganar/', () => {
    service.ganarOportunidad('o1').subscribe(r => expect(r.id).toBe('o1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/ganar/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockOportunidad);
  });

  it('perderOportunidad — POST /oportunidades/:id/perder/', () => {
    service.perderOportunidad('o1', 'Precio alto').subscribe(r => expect(r.id).toBe('o1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/perder/`);
    expect(req.request.body).toEqual({ motivo: 'Precio alto' });
    req.flush(mockOportunidad);
  });

  it('getTimeline — GET /oportunidades/:id/timeline/', () => {
    service.getTimeline('o1').subscribe(r => expect(r).toEqual([mockTimeline]));
    http.expectOne(`${BASE}/oportunidades/o1/timeline/`).flush([mockTimeline]);
  });

  it('agregarNota — POST /oportunidades/:id/notas/', () => {
    service.agregarNota('o1', 'Nota').subscribe(r => expect(r.id).toBe('t1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/notas/`);
    expect(req.request.body).toEqual({ descripcion: 'Nota' });
    req.flush(mockTimeline);
  });

  it('enviarEmail — POST /oportunidades/:id/enviar-email/', () => {
    const data = { destinatario: 'x@t.co', asunto: 'Asunto', cuerpo: 'Cuerpo' };
    service.enviarEmail('o1', data).subscribe();
    const req = http.expectOne(`${BASE}/oportunidades/o1/enviar-email/`);
    expect(req.request.body).toEqual(data);
    req.flush(null);
  });

  // ── Actividades ──────────────────────────────────────────────────────────────

  it('listActividades — GET /oportunidades/:id/actividades/', () => {
    service.listActividades('o1').subscribe(r => expect(r).toEqual([mockActividad]));
    http.expectOne(`${BASE}/oportunidades/o1/actividades/`).flush([mockActividad]);
  });

  it('createActividad — POST /oportunidades/:id/actividades/', () => {
    const data = { tipo: 'llamada' as const, titulo: 'Llamada', descripcion: '', fecha_programada: '2026-04-20T10:00:00Z' };
    service.createActividad('o1', data).subscribe(r => expect(r.id).toBe('a1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/actividades/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockActividad);
  });

  it('updateActividad — PATCH /actividades/:id/', () => {
    service.updateActividad('a1', { titulo: 'Nuevo' }).subscribe(r => expect(r.id).toBe('a1'));
    const req = http.expectOne(`${BASE}/actividades/a1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockActividad);
  });

  it('completarActividad — POST /actividades/:id/completar/', () => {
    service.completarActividad('a1', 'Completada OK').subscribe(r => expect(r.id).toBe('a1'));
    const req = http.expectOne(`${BASE}/actividades/a1/completar/`);
    expect(req.request.body).toEqual({ resultado: 'Completada OK' });
    req.flush(mockActividad);
  });

  // ── Cotizaciones ─────────────────────────────────────────────────────────────

  it('listCotizaciones — GET /oportunidades/:id/cotizaciones/', () => {
    service.listCotizaciones('o1').subscribe(r => expect(r).toEqual([mockCotizacion]));
    http.expectOne(`${BASE}/oportunidades/o1/cotizaciones/`).flush([mockCotizacion]);
  });

  it('getCotizacion — GET /cotizaciones/:id/', () => {
    service.getCotizacion('c1').subscribe(r => expect(r.id).toBe('c1'));
    http.expectOne(`${BASE}/cotizaciones/c1/`).flush(mockCotizacion);
  });

  it('createCotizacion — POST /oportunidades/:id/cotizaciones/crear/', () => {
    service.createCotizacion('o1', { titulo: 'Cot 1' }).subscribe(r => expect(r.id).toBe('c1'));
    const req = http.expectOne(`${BASE}/oportunidades/o1/cotizaciones/crear/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockCotizacion);
  });

  it('updateCotizacion — PATCH /cotizaciones/:id/', () => {
    service.updateCotizacion('c1', { titulo: 'Nuevo' }).subscribe(r => expect(r.id).toBe('c1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockCotizacion);
  });

  it('deleteCotizacion — DELETE /cotizaciones/:id/', () => {
    service.deleteCotizacion('c1').subscribe();
    const req = http.expectOne(`${BASE}/cotizaciones/c1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('enviarCotizacion — POST /cotizaciones/:id/enviar/', () => {
    service.enviarCotizacion('c1', 'dest@t.co').subscribe(r => expect(r.id).toBe('c1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/enviar/`);
    expect(req.request.body).toEqual({ email_destino: 'dest@t.co' });
    req.flush(mockCotizacion);
  });

  it('enviarCotizacion — POST sin emailDestino', () => {
    service.enviarCotizacion('c1').subscribe(r => expect(r.id).toBe('c1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/enviar/`);
    expect(req.request.body).toEqual({ email_destino: undefined });
    req.flush(mockCotizacion);
  });

  it('aceptarCotizacion — POST /cotizaciones/:id/aceptar/', () => {
    service.aceptarCotizacion('c1').subscribe(r => expect(r.id).toBe('c1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/aceptar/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockCotizacion);
  });

  it('rechazarCotizacion — POST /cotizaciones/:id/rechazar/', () => {
    service.rechazarCotizacion('c1').subscribe(r => expect(r.id).toBe('c1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/rechazar/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockCotizacion);
  });

  it('getCotizacionPdfUrl — retorna URL sin HTTP call', () => {
    const url = service.getCotizacionPdfUrl('c1');
    expect(url).toBe(`${BASE}/cotizaciones/c1/pdf/`);
  });

  // ── Líneas ───────────────────────────────────────────────────────────────────

  it('addLinea — POST /cotizaciones/:id/lineas/', () => {
    const data = { descripcion: 'Desc', cantidad: '1', vlr_unitario: '100' };
    service.addLinea('c1', data).subscribe(r => expect(r.id).toBe('li1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/lineas/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockLinea);
  });

  it('updateLinea — PATCH /cotizaciones/:cid/lineas/:lid/', () => {
    service.updateLinea('c1', 'li1', { cantidad: '2' }).subscribe(r => expect(r.id).toBe('li1'));
    const req = http.expectOne(`${BASE}/cotizaciones/c1/lineas/li1/`);
    expect(req.request.method).toBe('PATCH');
    req.flush(mockLinea);
  });

  it('deleteLinea — DELETE /cotizaciones/:cid/lineas/:lid/', () => {
    service.deleteLinea('c1', 'li1').subscribe();
    const req = http.expectOne(`${BASE}/cotizaciones/c1/lineas/li1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  // ── Catálogo ─────────────────────────────────────────────────────────────────

  it('listProductos — GET /productos/ sin params', () => {
    service.listProductos().subscribe(r => expect(r).toEqual([mockProducto]));
    http.expectOne(`${BASE}/productos/`).flush([mockProducto]);
  });

  it('listProductos — GET /productos/ con params', () => {
    service.listProductos({ search: 'prod', grupo: 'G1', clase: 'C1' }).subscribe();
    const req = http.expectOne(r => r.url === `${BASE}/productos/`);
    expect(req.request.params.get('search')).toBe('prod');
    expect(req.request.params.get('grupo')).toBe('G1');
    expect(req.request.params.get('clase')).toBe('C1');
    req.flush([]);
  });

  it('listImpuestos — GET /impuestos/', () => {
    service.listImpuestos().subscribe(r => expect(r).toEqual([mockImpuesto]));
    http.expectOne(`${BASE}/impuestos/`).flush([mockImpuesto]);
  });

  // ── Dashboard ────────────────────────────────────────────────────────────────

  it('getDashboard — GET /dashboard/', () => {
    service.getDashboard().subscribe(r => expect(r.leads_nuevos_mes).toBe(5));
    http.expectOne(`${BASE}/dashboard/`).flush(mockDashboard);
  });

  it('getForecast — GET /dashboard/forecast/', () => {
    service.getForecast().subscribe(r => expect(r.total_forecast).toBe('40000'));
    http.expectOne(`${BASE}/dashboard/forecast/`).flush(mockForecast);
  });
});
