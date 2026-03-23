/**
 * SaiSuite — Tests TareaTagService
 * Cubre: list, create, update, delete.
 */
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TareaTagService } from './tarea-tag.service';
import { TareaTag } from '../models/tarea.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockTag: TareaTag = {
  id: 'tag-1',
  company: 'company-1',
  nombre: 'Bug',
  color: 'red',
  created_at: '2026-03-22T10:00:00Z',
  updated_at: '2026-03-22T10:00:00Z',
};

const BASE = '/api/v1/proyectos/tags';

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('TareaTagService', () => {
  let service: TareaTagService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(TareaTagService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ── list ──────────────────────────────────────────────────────────────────

  it('list() GET /tags/', () => {
    service.list().subscribe(tags => {
      expect(tags.length).toBe(1);
      expect(tags[0].nombre).toBe('Bug');
      expect(tags[0].color).toBe('red');
    });

    const req = http.expectOne(`${BASE}/`);
    expect(req.request.method).toBe('GET');
    req.flush([mockTag]);
  });

  // ── create ────────────────────────────────────────────────────────────────

  it('create() POST /tags/', () => {
    service.create({ nombre: 'Feature', color: 'blue' }).subscribe(tag => {
      expect(tag.id).toBe('tag-1');
    });

    const req = http.expectOne(`${BASE}/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ nombre: 'Feature', color: 'blue' });
    req.flush({ ...mockTag, nombre: 'Feature', color: 'blue' });
  });

  // ── update ────────────────────────────────────────────────────────────────

  it('update() PATCH /tags/{id}/', () => {
    service.update('tag-1', { color: 'green' }).subscribe(tag => {
      expect(tag.color).toBe('green');
    });

    const req = http.expectOne(`${BASE}/tag-1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ color: 'green' });
    req.flush({ ...mockTag, color: 'green' });
  });

  // ── delete ────────────────────────────────────────────────────────────────

  it('delete() DELETE /tags/{id}/', () => {
    service.delete('tag-1').subscribe();

    const req = http.expectOne(`${BASE}/tag-1/`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
