import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CardCatalogService } from './card-catalog.service';

describe('CardCatalogService', () => {
  let service: CardCatalogService;
  let http: HttpTestingController;
  const base = '/api/v1/dashboard/catalog';

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(CardCatalogService);
    http    = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('getCards() — GET /catalog/cards/', () => {
    service.getCards().subscribe(res => expect(res).toEqual([]));
    http.expectOne(`${base}/cards/`).flush([]);
  });

  it('getCategories() — GET /catalog/categories/', () => {
    service.getCategories().subscribe(res => expect(res).toEqual([]));
    http.expectOne(`${base}/categories/`).flush([]);
  });
});
