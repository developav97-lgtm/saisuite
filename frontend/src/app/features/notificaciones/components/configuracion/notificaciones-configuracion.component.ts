import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RouterLink } from '@angular/router';

import { NotificacionesService } from '../../../../core/services/notificaciones.service';
import { PreferenciaNotificacion, TipoNotificacion } from '../../../../shared/models/notificacion.model';
import { ToastService } from '../../../../core/services/toast.service';

interface TipoMeta {
  tipo: TipoNotificacion;
  label: string;
  icon: string;
}

const TIPOS_META: TipoMeta[] = [
  { tipo: 'comentario',           label: 'Comentarios',        icon: 'comment' },
  { tipo: 'mencion',              label: 'Menciones',          icon: 'alternate_email' },
  { tipo: 'asignacion',           label: 'Asignaciones',       icon: 'person_add' },
  { tipo: 'cambio_estado',        label: 'Cambios de estado',  icon: 'sync' },
  { tipo: 'vencimiento',          label: 'Vencimientos',       icon: 'schedule' },
  { tipo: 'aprobacion',           label: 'Aprobaciones',       icon: 'task_alt' },
  { tipo: 'sistema',              label: 'Sistema',            icon: 'info' },
];

@Component({
  selector: 'app-notificaciones-configuracion',
  standalone: true,
  imports: [
    RouterLink,
    MatCardModule,
    MatSlideToggleModule,
    MatSelectModule,
    MatCheckboxModule,
    MatIconModule,
    MatButtonModule,
    MatDividerModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './notificaciones-configuracion.component.html',
  styleUrl: './notificaciones-configuracion.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificacionesConfiguracionComponent implements OnInit {
  private readonly svc      = inject(NotificacionesService);
  private readonly toast       = inject(ToastService);

  preferencias = signal<PreferenciaNotificacion[]>([]);
  cargando     = signal(true);

  readonly tiposMeta = TIPOS_META;

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.svc.obtenerPreferencias().subscribe({
      next: prefs => { this.preferencias.set(prefs); this.cargando.set(false); },
      error: ()   => this.cargando.set(false),
    });
  }

  getPref(tipo: string): PreferenciaNotificacion | undefined {
    return this.preferencias().find(p => p.tipo === tipo);
  }

  patch(tipo: string, datos: Partial<PreferenciaNotificacion>): void {
    this.svc.actualizarPreferencia(tipo, datos).subscribe({
      next: updated => {
        this.preferencias.update(list =>
          list.map(p => p.tipo === tipo ? { ...p, ...updated } : p),
        );
        this.toast.success('Guardado');
      },
    });
  }
}
