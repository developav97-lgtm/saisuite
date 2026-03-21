/**
 * SaiSuite — Tests HitoListComponent
 * Cubre: carga inicial, señales, computed porcentajeUsado,
 *        formulario de nuevo hito, validaciones, confirmarGenerarFactura.
 *
 * Nota: HitoListComponent importa MatDialogModule, por lo que MatDialog es
 * provisto por el propio módulo. Se usa spyOn sobre la instancia real.
 */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError, Subject } from 'rxjs';
import { HitoListComponent } from './hito-list.component';
import { HitoService } from '../../services/hito.service';
import { FaseService } from '../../services/fase.service';
import { Hito } from '../../models/hito.model';
import { FaseList } from '../../models/fase.model';

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockHito: Hito = {
  id: 'h-1', proyecto: 'p-1',
  fase: 'f-1', fase_nombre: 'Fase Inicial',
  nombre: 'Hito Entrega 1',
  descripcion: 'Primera entrega parcial',
  porcentaje_proyecto: '25.00',
  valor_facturar: '250000.00',
  facturable: true, facturado: false,
  documento_factura: null, fecha_facturacion: null,
  created_at: '2026-01-01T00:00:00Z',
};

const mockHitoFacturado: Hito = {
  ...mockHito, id: 'h-2', nombre: 'Hito Facturado',
  facturado: true, documento_factura: 'FAC-001',
  fecha_facturacion: '2026-03-01',
};

const mockFaseList: FaseList = {
  id: 'f-1', nombre: 'Fase Inicial', orden: 1,
  porcentaje_avance: '0.00', presupuesto_total: '200000.00',
  activo: true, created_at: '2026-01-01T00:00:00Z',
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('HitoListComponent', () => {
  let fixture: ComponentFixture<HitoListComponent>;
  let component: HitoListComponent;
  let hitoService: jasmine.SpyObj<HitoService>;
  let faseService: jasmine.SpyObj<FaseService>;
  let snackBar: jasmine.SpyObj<MatSnackBar>;
  // dialog se obtiene desde la instancia del componente (provisto por su MatDialogModule)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let componentDialog: any;

  beforeEach(async () => {
    hitoService = jasmine.createSpyObj('HitoService', ['list', 'create', 'generarFactura']);
    faseService = jasmine.createSpyObj('FaseService', ['listByProyecto']);
    snackBar    = jasmine.createSpyObj('MatSnackBar', ['open']);

    hitoService.list.and.returnValue(of([mockHito]));
    faseService.listByProyecto.and.returnValue(of([mockFaseList]));
    hitoService.create.and.returnValue(of(mockHito));
    hitoService.generarFactura.and.returnValue(of(mockHitoFacturado));

    await TestBed.configureTestingModule({
      imports: [HitoListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideAnimationsAsync(),
        { provide: HitoService, useValue: hitoService },
        { provide: FaseService, useValue: faseService },
        { provide: MatSnackBar, useValue: snackBar },
      ],
    }).compileComponents();

    fixture   = TestBed.createComponent(HitoListComponent);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('proyectoId', 'p-1');
    fixture.detectChanges();
    // Obtener la instancia privada del dialog que usa el componente
    componentDialog = (component as never as Record<string, unknown>)['dialog'];
  });

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('llama a HitoService.list() con proyectoId en ngOnInit', () => {
    expect(hitoService.list).toHaveBeenCalledWith('p-1');
  });

  it('llama a FaseService.listByProyecto() con proyectoId en ngOnInit', () => {
    expect(faseService.listByProyecto).toHaveBeenCalledWith('p-1');
  });

  it('almacena hitos en la señal', fakeAsync(() => {
    tick();
    expect(component.hitos().length).toBe(1);
    expect(component.hitos()[0].nombre).toBe('Hito Entrega 1');
  }));

  it('almacena fases en la señal', fakeAsync(() => {
    tick();
    expect(component.fases().length).toBe(1);
    expect(component.fases()[0].nombre).toBe('Fase Inicial');
  }));

  it('loading se establece en false tras carga exitosa', fakeAsync(() => {
    tick();
    expect(component.loading()).toBeFalse();
  }));

  it('loading se establece en false tras error de carga', fakeAsync(() => {
    hitoService.list.and.returnValue(throwError(() => ({ status: 500 })));
    component.loadHitos();
    tick();
    expect(component.loading()).toBeFalse();
  }));

  // ── porcentajeUsado ────────────────────────────────────────────────────────

  it('porcentajeUsado() calcula la suma de porcentajes de todos los hitos', fakeAsync(() => {
    tick();
    expect(component.porcentajeUsado()).toBe(25);
  }));

  it('porcentajeUsado() retorna 0 cuando no hay hitos', () => {
    component.hitos.set([]);
    expect(component.porcentajeUsado()).toBe(0);
  });

  it('porcentajeUsado() suma múltiples hitos', () => {
    component.hitos.set([
      { ...mockHito, porcentaje_proyecto: '30.00' },
      { ...mockHito, id: 'h-2', porcentaje_proyecto: '20.00' },
    ]);
    expect(component.porcentajeUsado()).toBe(50);
  });

  // ── formulario ────────────────────────────────────────────────────────────

  it('el formulario de hito es inválido con campos vacíos', () => {
    expect(component.form.valid).toBeFalse();
  });

  it('el formulario es válido con nombre, porcentaje y valor_facturar', () => {
    component.form.patchValue({
      nombre: 'Hito 2',
      porcentaje_proyecto: 30,
      valor_facturar: 300000,
      facturable: true,
    });
    expect(component.form.valid).toBeTrue();
  });

  it('porcentaje_proyecto rechaza valores menores a 0.01', () => {
    component.form.controls.nombre.setValue('Test');
    component.form.controls.porcentaje_proyecto.setValue(0);
    component.form.controls.valor_facturar.setValue(100);
    expect(component.form.controls.porcentaje_proyecto.hasError('min')).toBeTrue();
  });

  it('porcentaje_proyecto rechaza valores mayores a 100', () => {
    component.form.controls.porcentaje_proyecto.setValue(101);
    expect(component.form.controls.porcentaje_proyecto.hasError('max')).toBeTrue();
  });

  it('crearHito() no hace nada si el formulario es inválido', () => {
    component.crearHito();
    expect(hitoService.create).not.toHaveBeenCalled();
  });

  it('crearHito() muestra error si el porcentaje excede el disponible', fakeAsync(() => {
    tick(); // carga hitos con 25% usado → disponible = 75%
    component.form.patchValue({
      nombre: 'Excede', porcentaje_proyecto: 80,
      valor_facturar: 100000, facturable: true,
    });
    component.crearHito();
    expect(snackBar.open).toHaveBeenCalledWith(
      jasmine.stringContaining('disponible'),
      'Cerrar', jasmine.any(Object)
    );
    expect(hitoService.create).not.toHaveBeenCalled();
  }));

  // ── confirmarGenerarFactura ────────────────────────────────────────────────

  it('confirmarGenerarFactura() muestra snackBar si el hito ya fue facturado', () => {
    component.confirmarGenerarFactura(mockHitoFacturado);
    expect(snackBar.open).toHaveBeenCalledWith(
      'Este hito ya fue facturado.', 'Cerrar', jasmine.any(Object)
    );
  });

  it('confirmarGenerarFactura() abre MatDialog para hito no facturado', () => {
    const afterClosedSubject = new Subject<boolean>();
    spyOn(componentDialog, 'open').and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() });
    component.confirmarGenerarFactura(mockHito);
    expect(componentDialog.open).toHaveBeenCalled();
    afterClosedSubject.next(false);
  });

  it('genera factura si el usuario confirma en el dialog', fakeAsync(() => {
    const afterClosedSubject = new Subject<boolean>();
    spyOn(componentDialog, 'open').and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() });
    component.confirmarGenerarFactura(mockHito);
    afterClosedSubject.next(true);
    tick();
    expect(hitoService.generarFactura).toHaveBeenCalledWith('p-1', 'h-1');
  }));

  it('no genera factura si el usuario cancela el dialog', fakeAsync(() => {
    const afterClosedSubject = new Subject<boolean>();
    spyOn(componentDialog, 'open').and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() });
    component.confirmarGenerarFactura(mockHito);
    afterClosedSubject.next(false);
    tick();
    expect(hitoService.generarFactura).not.toHaveBeenCalled();
  }));

  it('actualiza el hito en la señal tras facturar exitosamente', fakeAsync(() => {
    tick(); // carga hitos → lista: [mockHito con id='h-1']
    // generarFactura debe devolver el mismo hito con id 'h-1' marcado como facturado
    const hitoFacturadoMismoId: Hito = { ...mockHito, facturado: true, documento_factura: 'FAC-001' };
    hitoService.generarFactura.and.returnValue(of(hitoFacturadoMismoId));
    const afterClosedSubject = new Subject<boolean>();
    spyOn(componentDialog, 'open').and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() });
    component.confirmarGenerarFactura(mockHito);
    afterClosedSubject.next(true);
    tick();
    const hitoActualizado = component.hitos().find(h => h.id === 'h-1');
    expect(hitoActualizado).toBeTruthy();
    expect(hitoActualizado?.facturado).toBeTrue();
  }));

  // ── Métodos de utilidad ────────────────────────────────────────────────────

  it('formatCurrency() formatea string numérico a moneda colombiana', () => {
    const result = component.formatCurrency('250000');
    expect(typeof result).toBe('string');
    expect(result).not.toBe('');
  });

  it('formatDate() formatea una fecha ISO correctamente', () => {
    const result = component.formatDate('2026-04-01');
    expect(result).toBeTruthy();
    expect(result).not.toBe('—');
  });

  it('formatDate() retorna "—" si la fecha es null', () => {
    expect(component.formatDate(null)).toBe('—');
  });
});
