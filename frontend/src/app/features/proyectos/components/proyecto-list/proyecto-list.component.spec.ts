/**
 * SaiSuite — Tests ProyectoListComponent
 * Cubre: carga inicial, señales de estado, filtros, navegación, eliminar.
 */
import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError, Subject } from 'rxjs';
import { ProyectoListComponent } from './proyecto-list.component';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoList } from '../../models/proyecto.model';

@Component({ template: '' })
class DummyComponent {}

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockGerente = { id: 'u-1', email: 'g@test.com', full_name: 'Gerente' };

const mockProyecto: ProyectoList = {
  id: 'p-1', codigo: 'PRY-001', nombre: 'Proyecto Test',
  tipo: 'obra_civil', estado: 'planificado',
  cliente_nombre: 'Cliente SA', gerente: mockGerente,
  fecha_inicio_planificada: '2026-04-01', fecha_fin_planificada: '2026-12-31',
  presupuesto_total: '1000000.00', porcentaje_avance: '25.00',
  activo: true, created_at: '2026-01-01T00:00:00Z',
};

const mockPaginatedResponse = {
  count: 1, next: null, previous: null, results: [mockProyecto],
};

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('ProyectoListComponent', () => {
  let fixture: ComponentFixture<ProyectoListComponent>;
  let component: ProyectoListComponent;
  let proyectoService: jasmine.SpyObj<ProyectoService>;
  let router: Router;
  let dialog: jasmine.SpyObj<MatDialog>;
  let snackBar: jasmine.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    proyectoService = jasmine.createSpyObj('ProyectoService', ['list', 'delete']);
    dialog          = jasmine.createSpyObj('MatDialog', ['open']);
    snackBar        = jasmine.createSpyObj('MatSnackBar', ['open']);

    proyectoService.list.and.returnValue(of(mockPaginatedResponse));
    proyectoService.delete.and.returnValue(of(undefined));

    await TestBed.configureTestingModule({
      imports: [ProyectoListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'proyectos', component: DummyComponent }]),
        provideAnimationsAsync(),
        { provide: ProyectoService, useValue: proyectoService },
        { provide: MatDialog, useValue: dialog },
        { provide: MatSnackBar, useValue: snackBar },
      ],
    }).compileComponents();

    router   = TestBed.inject(Router);
    fixture  = TestBed.createComponent(ProyectoListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('llama a ProyectoService.list() en ngOnInit', () => {
    expect(proyectoService.list).toHaveBeenCalled();
  });

  it('carga proyectos y los almacena en la señal', fakeAsync(() => {
    tick();
    expect(component.proyectos().length).toBe(1);
    expect(component.proyectos()[0].codigo).toBe('PRY-001');
  }));

  it('actualiza totalCount con el count de la respuesta', fakeAsync(() => {
    tick();
    expect(component.totalCount()).toBe(1);
  }));

  it('loading se establece en false tras carga exitosa', fakeAsync(() => {
    tick();
    expect(component.loading()).toBeFalse();
  }));

  it('loading se establece en false tras error de carga', fakeAsync(() => {
    proyectoService.list.and.returnValue(throwError(() => ({ status: 500 })));
    component.loadProyectos(0, 25);
    tick();
    expect(component.loading()).toBeFalse();
  }));

  it('muestra snackBar de error si falla la carga', fakeAsync(() => {
    proyectoService.list.and.returnValue(throwError(() => ({ status: 500 })));
    component.loadProyectos(0, 25);
    tick();
    expect(snackBar.open).toHaveBeenCalledWith(
      'No se pudieron cargar los proyectos.', 'Cerrar',
      jasmine.objectContaining({ duration: 4000 })
    );
  }));

  it('onSearch() recarga desde página 0', () => {
    component.onSearch();
    expect(proyectoService.list).toHaveBeenCalledTimes(2); // ngOnInit + onSearch
  });

  it('onFilterChange() recarga desde página 0', () => {
    component.onFilterChange();
    expect(proyectoService.list).toHaveBeenCalledTimes(2);
  });

  it('verDetalle() navega a /proyectos/:id', () => {
    const spy = spyOn(router, 'navigate');
    component.verDetalle('p-1');
    expect(spy).toHaveBeenCalledWith(['/proyectos', 'p-1']);
  });

  it('nuevoProyecto() navega a /proyectos/nuevo', () => {
    const spy = spyOn(router, 'navigate');
    component.nuevoProyecto();
    expect(spy).toHaveBeenCalledWith(['/proyectos', 'nuevo']);
  });

  it('confirmarEliminar() abre MatDialog de confirmación', () => {
    const afterClosedSubject = new Subject<boolean>();
    dialog.open.and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() } as never);
    component.confirmarEliminar(mockProyecto);
    expect(dialog.open).toHaveBeenCalled();
  });

  it('elimina el proyecto si el usuario confirma en el dialog', fakeAsync(() => {
    const afterClosedSubject = new Subject<boolean>();
    dialog.open.and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() } as never);
    component.confirmarEliminar(mockProyecto);
    afterClosedSubject.next(true);
    tick();
    expect(proyectoService.delete).toHaveBeenCalledWith('p-1');
  }));

  it('no llama a delete si el usuario cancela el dialog', fakeAsync(() => {
    const afterClosedSubject = new Subject<boolean>();
    dialog.open.and.returnValue({ afterClosed: () => afterClosedSubject.asObservable() } as never);
    component.confirmarEliminar(mockProyecto);
    afterClosedSubject.next(false);
    tick();
    expect(proyectoService.delete).not.toHaveBeenCalled();
  }));

  // ── Métodos de utilidad ────────────────────────────────────────────────────

  it('formatCurrency() formatea string numérico a formato COP', () => {
    const result = component.formatCurrency('1000000');
    expect(result).toContain('1');
    expect(typeof result).toBe('string');
  });

  it('formatCurrency() retorna el valor original si no es un número válido', () => {
    expect(component.formatCurrency('no-es-numero')).toBe('no-es-numero');
  });

  it('estadoLabel() retorna la etiqueta correcta para un estado válido', () => {
    expect(component.estadoLabel('planificado')).toBe('Planificado');
    expect(component.estadoLabel('en_ejecucion')).toBe('En ejecución');
  });

  it('estadoLabel() retorna el estado original si no está en el mapa', () => {
    expect(component.estadoLabel('desconocido')).toBe('desconocido');
  });

  it('estadoClass() retorna clase CSS con el estado', () => {
    expect(component.estadoClass('borrador')).toContain('borrador');
    expect(component.estadoClass('planificado')).toContain('planificado');
  });
});
