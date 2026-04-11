import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ReportShareDialogComponent, ReportShareDialogData } from './report-share-dialog.component';

describe('ReportShareDialogComponent', () => {
  let component: ReportShareDialogComponent;
  let fixture: ComponentFixture<ReportShareDialogComponent>;
  let httpMock: HttpTestingController;

  const mockData: ReportShareDialogData = {
    reportId: '123',
    reportTitle: 'Test Report',
    existingShares: [
      { user_id: 'u2', email: 'user2@test.com', full_name: 'User Two', puede_editar: false, creado_en: '2026-01-01' },
    ],
    currentUserId: 'u1',
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReportShareDialogComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideNoopAnimations(),
        { provide: MAT_DIALOG_DATA, useValue: mockData },
        { provide: MatDialogRef, useValue: { close: jasmine.createSpy('close') } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportShareDialogComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    fixture.detectChanges();
    const req = httpMock.expectOne(r => r.url.includes('/api/v1/auth/users/'));
    req.flush({ results: [
      { id: 'u1', email: 'me@test.com', full_name: 'Me' },
      { id: 'u2', email: 'user2@test.com', full_name: 'User Two' },
      { id: 'u3', email: 'user3@test.com', full_name: 'User Three' },
    ] });
    expect(component).toBeTruthy();
  });

  it('should load existing shares', () => {
    fixture.detectChanges();
    httpMock.expectOne(r => r.url.includes('/api/v1/auth/users/')).flush({ results: [] });
    expect(component.shares().length).toBe(1);
    expect(component.shares()[0].email).toBe('user2@test.com');
  });

  it('should filter out current user and already shared users from available list', () => {
    fixture.detectChanges();
    const req = httpMock.expectOne(r => r.url.includes('/api/v1/auth/users/'));
    req.flush({ results: [
      { id: 'u1', email: 'me@test.com', full_name: 'Me' },
      { id: 'u2', email: 'user2@test.com', full_name: 'User Two' },
      { id: 'u3', email: 'user3@test.com', full_name: 'User Three' },
    ] });

    const available = component.availableUsers();
    expect(available.length).toBe(1);
    expect(available[0].id).toBe('u3');
  });

  it('should add a share and update lists', () => {
    fixture.detectChanges();
    httpMock.expectOne(r => r.url.includes('/api/v1/auth/users/')).flush({ results: [
      { id: 'u3', email: 'user3@test.com', full_name: 'User Three' },
    ] });

    component.selectedUserId = 'u3';
    component.puedeEditar = true;
    component.addShare();

    const req = httpMock.expectOne(r => r.url.includes('/share/'));
    req.flush({
      user_id: 'u3', email: 'user3@test.com', full_name: 'User Three',
      puede_editar: true, creado_en: '2026-01-02',
    });

    expect(component.shares().length).toBe(2);
    expect(component.selectedUserId).toBe('');
  });

  it('should revoke a share', () => {
    fixture.detectChanges();
    httpMock.expectOne(r => r.url.includes('/api/v1/auth/users/')).flush({ results: [] });

    component.revokeShare('u2');

    const req = httpMock.expectOne(r => r.url.includes('/share/u2/'));
    req.flush(null);

    expect(component.shares().length).toBe(0);
  });

  it('should display dialog title with report name', () => {
    fixture.detectChanges();
    httpMock.expectOne(r => r.url.includes('/api/v1/auth/users/')).flush({ results: [] });

    const title = fixture.nativeElement.querySelector('[mat-dialog-title]');
    expect(title.textContent).toContain('Test Report');
  });
});
