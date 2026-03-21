/**
 * SaiSuite — Tests ProyectoFormComponent
 * Cubre: inicialización del formulario, validaciones, modo edición,
 *        guardar (create/update), cancelar, formatDate interno.
 */
import { Component, NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';
import { ProyectoFormComponent } from './proyecto-form.component';
import { ProyectoService } from '../../services/proyecto.service';
import { ProyectoDetail } from '../../models/proyecto.model';
import { AdminService } from '../../../admin/services/admin.service';
import { ConsecutivoService } from '../../../admin/services/consecutivo.service';

@Component({ template: '' })
class DummyComponent {}

// ── Mock data ──────────────────────────────────────────────────────────────────

const mockGerente = { id: 'u-1', email: 'gerente@test.com', full_name: 'Ana García' };

const mockAdminUser = {
  id: 'u-1', email: 'gerente@test.com',
  first_name: 'Ana', last_name: 'García', full_name: 'Ana García',
  role: 'company_admin' as const,
  is_active: true, is_superadmin: false, modules_access: [],
};

const mockProyectoDetail: ProyectoDetail = {
  id: 'p-1', codigo: 'PRY-001', nombre: 'Proyecto Existente',
  tipo: 'obra_civil', estado: 'planificado',
  cliente_id: '900111', cliente_nombre: 'Cliente SA',
  gerente: mockGerente,
  coordinador: null,
  fecha_inicio_planificada: '2026-04-01', fecha_fin_planificada: '2026-12-31',
  fecha_inicio_real: null, fecha_fin_real: null,
  presupuesto_total: '1000000.00', porcentaje_avance: '0.00',
  porcentaje_administracion: '10.00', porcentaje_imprevistos: '5.00', porcentaje_utilidad: '10.00',
  saiopen_proyecto_id: null, sincronizado_con_saiopen: false,
  ultima_sincronizacion: null, fases_count: 0, presupuesto_fases_total: '0.00',
  activo: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
};

// ── Helper para crear el TestBed con o sin id de ruta ─────────────────────────

function createTestBed(routeId: string | null = null) {
  const proyectoService  = jasmine.createSpyObj('ProyectoService', ['getById', 'create', 'update']);
  const adminService     = jasmine.createSpyObj('AdminService', ['listUsers']);
  const consecutivoService = jasmine.createSpyObj('ConsecutivoService', ['list']);
  const snackBar         = jasmine.createSpyObj('MatSnackBar', ['open']);

  proyectoService.getById.and.returnValue(of(mockProyectoDetail));
  proyectoService.create.and.returnValue(of(mockProyectoDetail));
  proyectoService.update.and.returnValue(of(mockProyectoDetail));
  adminService.listUsers.and.returnValue(of([mockAdminUser]));
  consecutivoService.list.and.returnValue(of([]));

  const paramMap = convertToParamMap(routeId ? { id: routeId } : {});
  const activatedRouteMock = { snapshot: { paramMap } };

  return { proyectoService, adminService, consecutivoService, snackBar, activatedRouteMock };
}

// ── Tests modo crear ───────────────────────────────────────────────────────────

describe('ProyectoFormComponent — modo crear', () => {
  let fixture: ComponentFixture<ProyectoFormComponent>;
  let component: ProyectoFormComponent;
  let proyectoService: jasmine.SpyObj<ProyectoService>;
  let router: Router;
  let snackBar: jasmine.SpyObj<MatSnackBar>;

  beforeEach(async () => {
    const deps = createTestBed(null);
    proyectoService = deps.proyectoService;
    snackBar        = deps.snackBar;

    await TestBed.configureTestingModule({
      imports: [ProyectoFormComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: 'proyectos', component: DummyComponent },
          { path: 'proyectos/:id', component: DummyComponent },
        ]),
        provideAnimationsAsync(),
        { provide: ProyectoService, useValue: deps.proyectoService },
        { provide: AdminService, useValue: deps.adminService },
        { provide: ConsecutivoService, useValue: deps.consecutivoService },
        { provide: MatSnackBar, useValue: deps.snackBar },
        { provide: ActivatedRoute, useValue: deps.activatedRouteMock },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    router    = TestBed.inject(Router);
    fixture   = TestBed.createComponent(ProyectoFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('editMode es false en modo crear', () => {
    expect(component.editMode()).toBeFalse();
  });

  it('proyectoId es null en modo crear', () => {
    expect(component.proyectoId()).toBeNull();
  });

  it('formulario es inválido con campos vacíos', () => {
    expect(component.form.valid).toBeFalse();
  });

  it('formulario es válido con todos los campos requeridos', () => {
    component.form.patchValue({
      nombre: 'Nuevo Proyecto', tipo: 'obra_civil',
      cliente_id: '900111', cliente_nombre: 'Cliente SA',
      gerente: 'u-1',
      fecha_inicio_planificada: new Date('2026-04-01'),
      fecha_fin_planificada: new Date('2026-12-31'),
      presupuesto_total: 1000000,
    });
    expect(component.form.valid).toBeTrue();
  });

  it('guardar() no hace nada si el formulario es inválido', () => {
    component.guardar();
    expect(proyectoService.create).not.toHaveBeenCalled();
  });

  it('guardar() llama a create() en modo crear', fakeAsync(() => {
    component.form.patchValue({
      nombre: 'Nuevo', tipo: 'servicios',
      cliente_id: '900111', cliente_nombre: 'CLI',
      gerente: 'u-1',
      fecha_inicio_planificada: new Date('2026-04-01'),
      fecha_fin_planificada: new Date('2026-12-31'),
      presupuesto_total: 500000,
    });
    component.guardar();
    tick(1500); // espera al setTimeout de navigate
    expect(proyectoService.create).toHaveBeenCalled();
    expect(proyectoService.update).not.toHaveBeenCalled();
  }));

  it('saving se establece en false tras error al crear', fakeAsync(() => {
    proyectoService.create.and.returnValue(throwError(() => ({ error: 'Error' })));
    component.form.patchValue({
      nombre: 'Err', tipo: 'servicios',
      cliente_id: '9001', cliente_nombre: 'CLI',
      gerente: 'u-1',
      fecha_inicio_planificada: new Date('2026-04-01'),
      fecha_fin_planificada: new Date('2026-12-31'),
      presupuesto_total: 100000,
    });
    component.guardar();
    tick();
    expect(component.saving()).toBeFalse();
  }));

  it('cancelar() navega a /proyectos sin id', () => {
    const spy = spyOn(router, 'navigate');
    component.cancelar();
    expect(spy).toHaveBeenCalledWith(['/proyectos']);
  });

  it('onClienteSeleccionado() actualiza cliente_id y cliente_nombre en el form', () => {
    component.onClienteSeleccionado({
      numero_identificacion: '900222333',
      nombre_completo: 'Empresa Nueva SAS',
    } as never);
    expect(component.form.controls.cliente_id.value).toBe('900222333');
    expect(component.form.controls.cliente_nombre.value).toBe('Empresa Nueva SAS');
  });

  it('onClienteSeleccionado() limpia campos si se pasa null', () => {
    component.onClienteSeleccionado(null);
    expect(component.form.controls.cliente_id.value).toBe('');
    expect(component.form.controls.cliente_nombre.value).toBe('');
  });

  it('onPresupuestoInput() actualiza presupuesto_total en el form', () => {
    const inputEvent = { target: { value: '1.500.000' } } as unknown as Event;
    component.onPresupuestoInput(inputEvent);
    expect(component.form.controls.presupuesto_total.value).toBe(1500000);
  });
});

// ── Tests modo edición ─────────────────────────────────────────────────────────

describe('ProyectoFormComponent — modo edición', () => {
  let fixture: ComponentFixture<ProyectoFormComponent>;
  let component: ProyectoFormComponent;
  let proyectoService: jasmine.SpyObj<ProyectoService>;
  let router: Router;

  beforeEach(async () => {
    const deps = createTestBed('p-1');
    proyectoService = deps.proyectoService;

    await TestBed.configureTestingModule({
      imports: [ProyectoFormComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'proyectos/:id', component: DummyComponent }]),
        provideAnimationsAsync(),
        { provide: ProyectoService, useValue: deps.proyectoService },
        { provide: AdminService, useValue: deps.adminService },
        { provide: ConsecutivoService, useValue: deps.consecutivoService },
        { provide: MatSnackBar, useValue: deps.snackBar },
        { provide: ActivatedRoute, useValue: deps.activatedRouteMock },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    router    = TestBed.inject(Router);
    fixture   = TestBed.createComponent(ProyectoFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('editMode es true cuando hay id en la ruta', fakeAsync(() => {
    tick();
    expect(component.editMode()).toBeTrue();
  }));

  it('proyectoId contiene el id de la ruta', fakeAsync(() => {
    tick();
    expect(component.proyectoId()).toBe('p-1');
  }));

  it('llama a getById() para cargar el proyecto existente', () => {
    expect(proyectoService.getById).toHaveBeenCalledWith('p-1');
  });

  it('guarda() llama a update() en modo edición', fakeAsync(() => {
    tick();
    component.form.patchValue({
      nombre: 'Editado', tipo: 'obra_civil',
      cliente_id: '900111', cliente_nombre: 'CLI',
      gerente: 'u-1',
      fecha_inicio_planificada: new Date('2026-04-01'),
      fecha_fin_planificada: new Date('2026-12-31'),
      presupuesto_total: 1000000,
    });
    component.guardar();
    tick(1500);
    expect(proyectoService.update).toHaveBeenCalledWith('p-1', jasmine.any(Object));
    expect(proyectoService.create).not.toHaveBeenCalled();
  }));

  it('cancelar() navega a /proyectos/:id en modo edición', fakeAsync(() => {
    tick();
    const spy = spyOn(router, 'navigate');
    component.cancelar();
    expect(spy).toHaveBeenCalledWith(['/proyectos', 'p-1']);
  }));
});
