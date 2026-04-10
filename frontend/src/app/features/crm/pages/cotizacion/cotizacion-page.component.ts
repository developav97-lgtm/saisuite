/**
 * SaiSuite — Cotización Page
 * Editor de cotización con líneas, totales y acciones (enviar, aceptar, rechazar, PDF).
 */
import {
  ChangeDetectionStrategy, Component, OnInit, OnDestroy,
  inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { Subject, takeUntil, switchMap } from 'rxjs';

import { CrmService } from '../../services/crm.service';
import {
  CrmCotizacion, CrmProducto, CrmImpuesto, CrmLineaCotizacionCreate,
} from '../../models/crm.model';
import { ToastService } from '../../../../core/services/toast.service';

@Component({
  selector: 'app-cotizacion-page',
  templateUrl: './cotizacion-page.component.html',
  styleUrl: './cotizacion-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatIconModule, MatFormFieldModule,
    MatInputModule, MatSelectModule, MatTableModule,
    MatProgressBarModule, MatChipsModule, MatTooltipModule, MatDividerModule,
  ],
})
export class CotizacionPageComponent implements OnInit, OnDestroy {
  private readonly crm    = inject(CrmService);
  private readonly route  = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast  = inject(ToastService);
  private readonly fb     = inject(FormBuilder);
  private readonly destroy$ = new Subject<void>();

  readonly cotizacion = signal<CrmCotizacion | null>(null);
  readonly productos  = signal<CrmProducto[]>([]);
  readonly impuestos  = signal<CrmImpuesto[]>([]);
  readonly loading    = signal(false);
  readonly addingLinea = signal(false);

  readonly lineaForm = this.fb.group({
    producto:     [null as string | null],
    descripcion:  ['', Validators.required],
    cantidad:     ['1', [Validators.required, Validators.min(0.01)]],
    vlr_unitario: ['0', [Validators.required, Validators.min(0)]],
    descuento_p:  ['0'],
    impuesto:     [null as string | null],
  });

  readonly lineaColumns = ['descripcion', 'cantidad', 'vlr_unitario', 'descuento_p', 'impuesto', 'total_parcial', 'acciones'];

  ngOnInit(): void {
    this.crm.listProductos().pipe(takeUntil(this.destroy$)).subscribe(p => this.productos.set(p));
    this.crm.listImpuestos().pipe(takeUntil(this.destroy$)).subscribe(i => this.impuestos.set(i));

    this.route.params.pipe(
      takeUntil(this.destroy$),
      switchMap(params => {
        this.loading.set(true);
        return this.crm.getCotizacion(params['id']);
      }),
    ).subscribe({
      next: cot => {
        this.cotizacion.set(cot);
        this.loading.set(false);
      },
      error: () => {
        this.toast.error('Error cargando cotización');
        this.loading.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onProductoChange(productoId: string | null): void {
    if (!productoId) return;
    const prod = this.productos().find(p => p.id === productoId);
    if (prod) {
      this.lineaForm.patchValue({
        descripcion: prod.nombre,
        vlr_unitario: prod.precio_base,
        impuesto: prod.impuesto,
      });
    }
  }

  addLinea(): void {
    if (this.lineaForm.invalid || !this.cotizacion()) return;
    this.addingLinea.set(true);
    const val = this.lineaForm.value;
    const data: CrmLineaCotizacionCreate = {
      producto:     val.producto ?? null,
      descripcion:  val.descripcion!,
      cantidad:     val.cantidad!,
      vlr_unitario: val.vlr_unitario!,
      descuento_p:  val.descuento_p || '0',
      impuesto:     val.impuesto ?? null,
    };
    this.crm.addLinea(this.cotizacion()!.id, data)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.refreshCotizacion();
          this.lineaForm.reset({ cantidad: '1', vlr_unitario: '0', descuento_p: '0' });
          this.addingLinea.set(false);
        },
        error: () => {
          this.toast.error('Error agregando línea');
          this.addingLinea.set(false);
        },
      });
  }

  deleteLinea(lineaId: string): void {
    const cot = this.cotizacion();
    if (!cot) return;
    this.crm.deleteLinea(cot.id, lineaId).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => this.refreshCotizacion(),
      error: () => this.toast.error('Error eliminando línea'),
    });
  }

  enviar(): void {
    this.crm.enviarCotizacion(this.cotizacion()!.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: cot => {
          this.cotizacion.set(cot);
          this.toast.success('Cotización enviada');
        },
        error: (err) => this.toast.error(err?.error?.detail ?? 'Error enviando cotización'),
      });
  }

  aceptar(): void {
    this.crm.aceptarCotizacion(this.cotizacion()!.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: cot => {
          this.cotizacion.set(cot);
          this.toast.success('Cotización aceptada — sincronizando con Saiopen...');
        },
        error: () => this.toast.error('Error aceptando cotización'),
      });
  }

  rechazar(): void {
    this.crm.rechazarCotizacion(this.cotizacion()!.id)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: cot => {
          this.cotizacion.set(cot);
          this.toast.info('Cotización rechazada');
        },
        error: () => this.toast.error('Error rechazando cotización'),
      });
  }

  openPdf(): void {
    const cot = this.cotizacion();
    if (!cot) return;
    window.open(this.crm.getCotizacionPdfUrl(cot.id), '_blank');
  }

  private refreshCotizacion(): void {
    const cot = this.cotizacion();
    if (!cot) return;
    this.crm.getCotizacion(cot.id).pipe(takeUntil(this.destroy$)).subscribe(c => this.cotizacion.set(c));
  }

  formatMoney(val: string): string {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(parseFloat(val || '0'));
  }

  get esBorrador(): boolean {
    return this.cotizacion()?.estado === 'borrador';
  }
}
