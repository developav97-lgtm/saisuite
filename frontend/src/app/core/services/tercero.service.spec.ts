/**
 * SaiSuite — Tests TerceroService (transversal)
 * Cobertura objetivo: 90%+ en tercero.service.ts
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TerceroService } from './tercero.service';
import { TerceroList, TerceroDetail, TerceroCreate, TerceroDireccion } from '../models/tercero.model';

// ── Datos de prueba ───────────────────────────────────────────────────────────

const mockTerceroList: TerceroList = {
  id: 'abc-123',
  codigo: 'CLI-001',
  tipo_identificacion: 'cc',
  numero_identificacion: '1234567890',
  nombre_completo: 'Juan Pérez',
  tipo_persona: 'natural',
  tipo_tercero: 'cliente',
  email: 'juan@test.com',
  telefono: '3001234567',
  celular: '',
  saiopen_synced: false,
  activo: true,
};

const mockTerceroDetail: TerceroDetail = {
  ...mockTerceroList,
  primer_nombre: 'Juan',
  segundo_nombre: '',
  primer_apellido: 'Pérez',
  segundo_apellido: '',
  razon_social: '',
  saiopen_id: null,
  sai_key: null,
  direcciones: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const mockDireccion: TerceroDireccion = {
  id: 'dir-001',
  tipo: 'principal',
  nombre_sucursal: '',
  pais: 'Colombia',
  departamento: 'Valle del Cauca',
  ciudad: 'Cali',
  direccion_linea1: 'Calle 5 # 12-34',
  direccion_linea2: '',
  codigo_postal: '',
  nombre_contacto: '',
  telefono_contacto: '',
  email_contacto: '',
  saiopen_linea_id: null,
  activa: true,
  es_principal: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

// ── Suite principal ───────────────────────────────────────────────────────────

describe('TerceroService', () => {
  let service: TerceroService;
  let httpMock: HttpTestingController;
  const baseUrl = '/api/v1/terceros';

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        TerceroService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(TerceroService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  // ── Instanciación ────────────────────────────────────────────────────────

  it('debe crearse el servicio', () => {
    expect(service).toBeTruthy();
  });

  // ── list() ───────────────────────────────────────────────────────────────

  describe('list()', () => {

    it('debe retornar lista desde respuesta paginada', () => {
      const paginatedResponse = { count: 1, next: null, previous: null, results: [mockTerceroList] };
      let result: TerceroList[] = [];

      service.list({}).subscribe(t => result = t);

      const req = httpMock.expectOne(`${baseUrl}/`);
      expect(req.request.method).toBe('GET');
      req.flush(paginatedResponse);

      expect(result.length).toBe(1);
      expect(result[0].nombre_completo).toBe('Juan Pérez');
    });

    it('debe retornar lista desde respuesta no paginada (array directo)', () => {
      let result: TerceroList[] = [];

      service.list({}).subscribe(t => result = t);

      const req = httpMock.expectOne(`${baseUrl}/`);
      req.flush([mockTerceroList]);

      expect(result.length).toBe(1);
    });

    it('debe enviar parámetro search en query string', () => {
      service.list({ search: 'Juan' }).subscribe();

      const req = httpMock.expectOne(r => r.url === `${baseUrl}/`);
      expect(req.request.params.get('search')).toBe('Juan');
      req.flush({ count: 0, next: null, previous: null, results: [] });
    });

    it('debe enviar parámetro tipo_tercero en query string', () => {
      service.list({ tipo_tercero: 'cliente' }).subscribe();

      const req = httpMock.expectOne(r => r.url === `${baseUrl}/`);
      expect(req.request.params.get('tipo_tercero')).toBe('cliente');
      req.flush({ count: 0, next: null, previous: null, results: [] });
    });

    it('debe enviar parámetro activo como string', () => {
      service.list({ activo: false }).subscribe();

      const req = httpMock.expectOne(r => r.url === `${baseUrl}/`);
      expect(req.request.params.get('activo')).toBe('false');
      req.flush({ count: 0, next: null, previous: null, results: [] });
    });

    it('debe enviar parámetro page_size en query string', () => {
      service.list({ page_size: 50 }).subscribe();

      const req = httpMock.expectOne(r => r.url === `${baseUrl}/`);
      expect(req.request.params.get('page_size')).toBe('50');
      req.flush({ count: 0, next: null, previous: null, results: [] });
    });

    it('no debe enviar parámetros vacíos u omitidos', () => {
      service.list({}).subscribe();

      const req = httpMock.expectOne(`${baseUrl}/`);
      expect(req.request.params.keys().length).toBe(0);
      req.flush({ count: 0, next: null, previous: null, results: [] });
    });

    it('debe enviar múltiples filtros combinados', () => {
      service.list({ search: 'Ana', tipo_tercero: 'proveedor', activo: true }).subscribe();

      const req = httpMock.expectOne(r => r.url === `${baseUrl}/`);
      expect(req.request.params.get('search')).toBe('Ana');
      expect(req.request.params.get('tipo_tercero')).toBe('proveedor');
      expect(req.request.params.get('activo')).toBe('true');
      req.flush({ count: 0, next: null, previous: null, results: [] });
    });
  });

  // ── get() ────────────────────────────────────────────────────────────────

  describe('get()', () => {

    it('debe obtener detalle de un tercero por ID', () => {
      let result: TerceroDetail | undefined;

      service.get('abc-123').subscribe(t => result = t);

      const req = httpMock.expectOne(`${baseUrl}/abc-123/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockTerceroDetail);

      expect(result?.id).toBe('abc-123');
      expect(result?.nombre_completo).toBe('Juan Pérez');
      expect(result?.direcciones).toEqual([]);
    });
  });

  // ── create() ─────────────────────────────────────────────────────────────

  describe('create()', () => {

    it('debe crear un tercero persona natural', () => {
      const payload: TerceroCreate = {
        tipo_identificacion: 'cc',
        numero_identificacion: '1234567890',
        primer_nombre: 'Juan',
        primer_apellido: 'Pérez',
        tipo_persona: 'natural',
        tipo_tercero: 'cliente',
      };
      let result: TerceroDetail | undefined;

      service.create(payload).subscribe(t => result = t);

      const req = httpMock.expectOne(`${baseUrl}/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(payload);
      req.flush(mockTerceroDetail);

      expect(result?.id).toBe('abc-123');
      expect(result?.codigo).toBe('CLI-001');
    });

    it('debe crear un tercero persona jurídica', () => {
      const payload: TerceroCreate = {
        tipo_identificacion: 'nit',
        numero_identificacion: '900123456',
        razon_social: 'Empresa XYZ S.A.S.',
        tipo_persona: 'juridica',
        tipo_tercero: 'proveedor',
      };

      service.create(payload).subscribe();

      const req = httpMock.expectOne(`${baseUrl}/`);
      expect(req.request.body.tipo_persona).toBe('juridica');
      expect(req.request.body.razon_social).toBe('Empresa XYZ S.A.S.');
      req.flush({ ...mockTerceroDetail, nombre_completo: 'Empresa XYZ S.A.S.' });
    });
  });

  // ── update() ─────────────────────────────────────────────────────────────

  describe('update()', () => {

    it('debe actualizar con PATCH y retornar el detalle actualizado', () => {
      const patch: Partial<TerceroCreate> = { email: 'nuevo@test.com' };
      let result: TerceroDetail | undefined;

      service.update('abc-123', patch).subscribe(t => result = t);

      const req = httpMock.expectOne(`${baseUrl}/abc-123/`);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(patch);
      req.flush({ ...mockTerceroDetail, email: 'nuevo@test.com' });

      expect(result?.email).toBe('nuevo@test.com');
    });

    it('debe enviar solo los campos modificados (PATCH parcial)', () => {
      service.update('abc-123', { telefono: '3009876543' }).subscribe();

      const req = httpMock.expectOne(`${baseUrl}/abc-123/`);
      expect(Object.keys(req.request.body)).toEqual(['telefono']);
      req.flush(mockTerceroDetail);
    });
  });

  // ── delete() ─────────────────────────────────────────────────────────────

  describe('delete()', () => {

    it('debe enviar DELETE al endpoint correcto', () => {
      let completed = false;
      service.delete('abc-123').subscribe(() => completed = true);

      const req = httpMock.expectOne(`${baseUrl}/abc-123/`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);

      expect(completed).toBeTrue();
    });
  });

  // ── addDireccion() ───────────────────────────────────────────────────────

  describe('addDireccion()', () => {

    it('debe crear dirección via POST al endpoint correcto', () => {
      const data: Partial<TerceroDireccion> = {
        tipo: 'principal',
        ciudad: 'Cali',
        departamento: 'Valle del Cauca',
        direccion_linea1: 'Calle 5 # 12-34',
        es_principal: true,
      };
      let result: TerceroDireccion | undefined;

      service.addDireccion('abc-123', data).subscribe(d => result = d);

      const req = httpMock.expectOne(`${baseUrl}/abc-123/direcciones/crear/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(data);
      req.flush(mockDireccion);

      expect(result?.id).toBe('dir-001');
      expect(result?.es_principal).toBeTrue();
    });
  });

  // ── updateDireccion() ────────────────────────────────────────────────────

  describe('updateDireccion()', () => {

    it('debe actualizar dirección via PATCH', () => {
      const patch: Partial<TerceroDireccion> = { ciudad: 'Bogotá' };
      let result: TerceroDireccion | undefined;

      service.updateDireccion('abc-123', 'dir-001', patch).subscribe(d => result = d);

      const req = httpMock.expectOne(`${baseUrl}/abc-123/direcciones/dir-001/`);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(patch);
      req.flush({ ...mockDireccion, ciudad: 'Bogotá' });

      expect(result?.ciudad).toBe('Bogotá');
    });
  });

  // ── deleteDireccion() ────────────────────────────────────────────────────

  describe('deleteDireccion()', () => {

    it('debe eliminar dirección via DELETE al endpoint correcto', () => {
      let completed = false;
      service.deleteDireccion('abc-123', 'dir-001').subscribe(() => completed = true);

      const req = httpMock.expectOne(`${baseUrl}/abc-123/direcciones/dir-001/eliminar/`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);

      expect(completed).toBeTrue();
    });
  });
});
