/**
 * SaiSuite — LeadsPageComponent Spec
 * Cobertura ≥70% de lógica de componente.
 */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';

import { LeadsPageComponent } from './leads-page.component';
import { CrmService } from '../../services/crm.service';
import { ToastService } from '../../../../core/services/toast.service';
import { CrmLead } from '../../models/crm.model';

const mockLead: CrmLead = {
  id: 'l1', nombre: 'Juan Pérez', empresa: 'Acme', email: 'juan@acme.co',
  telefono: '3001234567', cargo: 'Gerente', fuente: 'manual', score: 50,
  convertido: false, oportunidad: null, asignado_a: null, asignado_a_nombre: null,
  pipeline: null, notas: '', created_at: '2026-01-01', updated_at: '2026-01-01',
};

const pagedResponse = { count: 1, results: [mockLead] };

describe('LeadsPageComponent', () => {
  let fixture: ComponentFixture<LeadsPageComponent>;
  let component: LeadsPageComponent;
  let crmSpy: jasmine.SpyObj<CrmService>;
  let toastSpy: jasmine.SpyObj<ToastService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;

  beforeEach(async () => {
    crmSpy   = jasmine.createSpyObj('CrmService', ['listLeads', 'deleteLead']);
    toastSpy = jasmine.createSpyObj('ToastService', ['error', 'success', 'info']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);

    crmSpy.listLeads.and.returnValue(of(pagedResponse));
    crmSpy.deleteLead.and.returnValue(of(undefined));

    await TestBed.configureTestingModule({
      imports: [LeadsPageComponent, NoopAnimationsModule],
      providers: [
        provideHttpClient(), provideHttpClientTesting(),
        provideRouter([]),
        { provide: CrmService, useValue: crmSpy },
        { provide: ToastService, useValue: toastSpy },
        { provide: MatDialog, useValue: dialogSpy },
      ],
    }).compileComponents();

    fixture   = TestBed.createComponent(LeadsPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('crea el componente', () => {
    expect(component).toBeTruthy();
  });

  it('carga leads en ngOnInit', () => {
    expect(crmSpy.listLeads).toHaveBeenCalled();
    expect(component.leads().length).toBe(1);
    expect(component.total()).toBe(1);
    expect(component.loading()).toBeFalse();
  });

  it('columnas de la tabla definidas', () => {
    expect(component.displayedColumns).toContain('nombre');
    expect(component.displayedColumns).toContain('acciones');
  });

  it('fuenteOpciones tiene opción vacía primero', () => {
    expect(component.fuenteOpciones[0].value).toBe('');
  });

  it('onSearchChange actualiza searchTerm', fakeAsync(() => {
    component.onSearchChange('test');
    expect(component.searchTerm()).toBe('test');
    tick(400);
    expect(crmSpy.listLeads).toHaveBeenCalledTimes(2); // init + debounce
  }));

  it('onFuenteChange actualiza filtroFuente y recarga', () => {
    component.onFuenteChange('manual');
    expect(component.filtroFuente()).toBe('manual');
    expect(crmSpy.listLeads).toHaveBeenCalledTimes(2);
  });

  it('onFuenteChange resetea pageIndex a 0', () => {
    component['pageIndex'].set(2);
    component.onFuenteChange('csv');
    expect(component.pageIndex()).toBe(0);
  });

  it('onPageChange actualiza pageIndex y pageSize', () => {
    component.onPageChange({ pageIndex: 2, pageSize: 50, length: 100 });
    expect(component.pageIndex()).toBe(2);
    expect(component.pageSize()).toBe(50);
    expect(crmSpy.listLeads).toHaveBeenCalledTimes(2);
  });

  it('maneja error al cargar leads', () => {
    crmSpy.listLeads.and.returnValue(throwError(() => new Error('fail')));
    component['loadLeads']();
    expect(toastSpy.error).toHaveBeenCalledWith('Error cargando leads');
    expect(component.loading()).toBeFalse();
  });

  it('openImportDialog llama dialog.open', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of(null) } as never);
    component.openImportDialog();
    expect(dialogSpy.open).toHaveBeenCalled();
  });

  it('openConvertirDialog llama dialog.open', () => {
    dialogSpy.open.and.returnValue({ afterClosed: () => of(null) } as never);
    component.openConvertirDialog(mockLead);
    expect(dialogSpy.open).toHaveBeenCalled();
  });

  it('ngOnDestroy completa destroy$', () => {
    spyOn(component['destroy$'], 'next');
    spyOn(component['destroy$'], 'complete');
    component.ngOnDestroy();
    expect(component['destroy$'].next).toHaveBeenCalled();
    expect(component['destroy$'].complete).toHaveBeenCalled();
  });
});
