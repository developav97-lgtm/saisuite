import {
  ChangeDetectionStrategy, Component, OnInit,
  inject, signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatSnackBar } from '@angular/material/snack-bar';
import { TerceroService } from '../../../../core/services/tercero.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import {
  TerceroList,
  TipoIdentificacion, TipoTercero,
  TIPO_IDENTIFICACION_LABELS, TIPO_TERCERO_LABELS,
} from '../../../../core/models/tercero.model';

@Component({
  selector: 'app-tercero-list-page',
  templateUrl: './tercero-list-page.component.html',
  styleUrl: './tercero-list-page.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatTableModule, MatButtonModule, MatIconModule,
    MatFormFieldModule, MatInputModule, MatSelectModule,
    MatTooltipModule, MatDialogModule, MatProgressBarModule,
    MatChipsModule,
  ],
})
export class TerceroListPageComponent implements OnInit {
  private readonly service  = inject(TerceroService);
  private readonly router   = inject(Router);
  private readonly dialog   = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  readonly terceros   = signal<TerceroList[]>([]);
  readonly loading    = signal(false);
  readonly searchText = signal('');
  readonly tipoFilter = signal<TipoTercero | ''>('');

  readonly displayedColumns = ['nombre_completo', 'numero_identificacion', 'tipo_tercero', 'contacto', 'acciones'];

  readonly tipoTerceroOptions: { value: TipoTercero | ''; label: string }[] = [
    { value: '',              label: 'Todos'          },
    { value: 'cliente',       label: 'Cliente'        },
    { value: 'proveedor',     label: 'Proveedor'      },
    { value: 'subcontratista',label: 'Subcontratista' },
    { value: 'interventor',   label: 'Interventor'    },
    { value: 'consultor',     label: 'Consultor'      },
    { value: 'empleado',      label: 'Empleado'       },
    { value: 'otro',          label: 'Otro'           },
  ];

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.service.list({
      search:       this.searchText() || undefined,
      tipo_tercero: this.tipoFilter() || undefined,
    }).subscribe({
      next: (data) => { this.terceros.set(data); this.loading.set(false); },
      error: () => {
        this.snackBar.open('Error al cargar terceros.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        this.loading.set(false);
      },
    });
  }

  onSearch(): void { this.load(); }
  onFilter(): void { this.load(); }

  nuevo(): void {
    this.router.navigate(['/terceros/nuevo']);
  }

  editar(t: TerceroList): void {
    this.router.navigate(['/terceros', t.id, 'editar']);
  }

  confirmarEliminar(t: TerceroList): void {
    const ref = this.dialog.open(ConfirmDialogComponent, {
      data: {
        header:      'Eliminar tercero',
        message:     `¿Eliminar "${t.nombre_completo}"? Solo se desactivará.`,
        acceptLabel: 'Eliminar',
        acceptColor: 'warn',
      },
      width: '400px',
    });
    ref.afterClosed().subscribe((confirmed: boolean) => {
      if (!confirmed) return;
      this.service.delete(t.id).subscribe({
        next: () => {
          this.load();
          this.snackBar.open('Tercero eliminado.', 'Cerrar', { duration: 3000, panelClass: ['snack-success'] });
        },
        error: () => {
          this.snackBar.open('No se pudo eliminar.', 'Cerrar', { duration: 4000, panelClass: ['snack-error'] });
        },
      });
    });
  }

  getTipoTerceroLabel(tipo: string): string {
    return TIPO_TERCERO_LABELS[tipo as TipoTercero] ?? tipo;
  }

  getTipoIdentificacionLabel(tipo: string): string {
    return TIPO_IDENTIFICACION_LABELS[tipo as TipoIdentificacion] ?? tipo;
  }
}
