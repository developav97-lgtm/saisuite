import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  input,
  signal,
  computed,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { debounceTime, distinctUntilChanged, Subject, switchMap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DestroyRef } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';

import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/auth/auth.service';
import { ComentariosService } from '../../services/comentarios.service';
import { Comentario, ComentarioAutor, Respuesta } from '../../models/comentario.model';
import { ToastService } from '../../../core/services/toast.service';

interface MencionSugerencia {
  id: string;
  full_name: string;
  email: string;
}

@Component({
  selector: 'app-comentarios-thread',
  standalone: true,
  imports: [
    FormsModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
  ],
  templateUrl: './comentarios-thread.component.html',
  styleUrl: './comentarios-thread.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComentariosThreadComponent implements OnInit {
  /** Nombre del modelo Django. Ej: 'tarea' */
  readonly contentTypeModel = input.required<string>();
  /** UUID del objeto relacionado */
  readonly objectId = input.required<string>();

  private readonly svc        = inject(ComentariosService);
  private readonly authSvc    = inject(AuthService);
  private readonly toast       = inject(ToastService);
  private readonly http       = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);

  comentarios  = signal<Comentario[]>([]);
  cargando     = signal(false);
  enviando     = signal(false);

  textoNuevo     = '';
  respondiendo   = signal<string | null>(null);
  textoRespuesta = '';
  editandoId     = signal<string | null>(null);
  textoEdicion   = '';

  // ── Menciones autocomplete ────────────────────────────────────────────────
  sugerencias          = signal<MencionSugerencia[]>([]);
  mostrarSugerencias   = signal(false);
  private mencSearch$  = new Subject<string>();
  private _mencOffset  = 0;   // posición del @ activo en el textarea

  readonly usuarioActual = computed(() => this.authSvc.currentUser());

  ngOnInit(): void {
    this.cargarComentarios();
    this._iniciarMenciones();
  }

  private _iniciarMenciones(): void {
    this.mencSearch$
      .pipe(
        debounceTime(200),
        distinctUntilChanged(),
        switchMap(q =>
          this.http.get<MencionSugerencia[]>(
            `${environment.apiUrl}/auth/users/menciones/`,
            { params: q ? { q } : {} }
          )
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({ next: r => this.sugerencias.set(r), error: () => this.sugerencias.set([]) });
  }

  onTextareaInput(event: Event, campo: 'nuevo' | 'respuesta'): void {
    const ta  = event.target as HTMLTextAreaElement;
    const pos = ta.selectionStart ?? 0;
    const txt = ta.value.substring(0, pos);
    const idx = txt.lastIndexOf('@');

    if (idx !== -1) {
      const fragmento = txt.substring(idx + 1);
      // Solo si no hay espacio después del @ (seguimos escribiendo la mención)
      if (!/\s/.test(fragmento)) {
        this._mencOffset = idx;
        this.mostrarSugerencias.set(true);
        this.mencSearch$.next(fragmento);
        return;
      }
    }
    this.mostrarSugerencias.set(false);
  }

  seleccionarMencion(sug: MencionSugerencia, campo: 'nuevo' | 'respuesta'): void {
    const emailPrefix = sug.email.split('@')[0];
    if (campo === 'nuevo') {
      this.textoNuevo =
        this.textoNuevo.substring(0, this._mencOffset) +
        `@${emailPrefix} ` +
        this.textoNuevo.substring(this._mencOffset + this.textoNuevo.length - this._mencOffset);
      // Reemplazo correcto: solo hasta el cursor actual
      const actual  = this.textoNuevo;
      const pre     = actual.substring(0, this._mencOffset);
      const post    = actual.substring(this._mencOffset).replace(/^@[\w.]*/, '');
      this.textoNuevo = `${pre}@${emailPrefix} ${post}`;
    } else {
      const actual  = this.textoRespuesta;
      const pre     = actual.substring(0, this._mencOffset);
      const post    = actual.substring(this._mencOffset).replace(/^@[\w.]*/, '');
      this.textoRespuesta = `${pre}@${emailPrefix} ${post}`;
    }
    this.mostrarSugerencias.set(false);
    this.sugerencias.set([]);
  }

  cargarComentarios(): void {
    this.cargando.set(true);
    this.svc.listar({
      content_type_model: this.contentTypeModel(),
      object_id: this.objectId(),
    }).subscribe({
      next: r  => { this.comentarios.set(r.results); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }

  // ── Nuevo comentario raíz ──────────────────────────────────────────────────

  enviarComentario(): void {
    const texto = this.textoNuevo.trim();
    if (!texto) return;
    this.enviando.set(true);
    this.svc.crear({
      content_type_model: this.contentTypeModel(),
      object_id: this.objectId(),
      texto,
    }).subscribe({
      next: nuevo => {
        this.comentarios.update(list => [...list, nuevo]);
        this.textoNuevo = '';
        this.enviando.set(false);
      },
      error: () => {
        this.toast.error('No se pudo enviar el comentario.');
        this.enviando.set(false);
      },
    });
  }

  // ── Respuesta ──────────────────────────────────────────────────────────────

  replyTo(id: string): void {
    this.respondiendo.set(this.respondiendo() === id ? null : id);
    this.textoRespuesta = '';
    this.editandoId.set(null);
  }

  enviarRespuesta(padre: Comentario): void {
    const texto = this.textoRespuesta.trim();
    if (!texto) return;
    this.enviando.set(true);
    this.svc.crear({
      content_type_model: this.contentTypeModel(),
      object_id: this.objectId(),
      texto,
      padre: padre.id,
    }).subscribe({
      next: actualizado => {
        // El backend devuelve el padre actualizado con la nueva respuesta incluida
        this.comentarios.update(list =>
          list.map(c => c.id === actualizado.id ? actualizado : c)
        );
        this.textoRespuesta = '';
        this.respondiendo.set(null);
        this.enviando.set(false);
      },
      error: () => {
        this.toast.error('No se pudo enviar la respuesta.');
        this.enviando.set(false);
      },
    });
  }

  // ── Edición ───────────────────────────────────────────────────────────────

  iniciarEdicion(id: string, textoActual: string): void {
    this.editandoId.set(id);
    this.textoEdicion = textoActual;
    this.respondiendo.set(null);
  }

  cancelarEdicion(): void {
    this.editandoId.set(null);
    this.textoEdicion = '';
  }

  guardarEdicion(comentarioId: string, esPadre: boolean, padreId?: string): void {
    const texto = this.textoEdicion.trim();
    if (!texto) return;
    this.svc.editar(comentarioId, texto).subscribe({
      next: editado => {
        if (esPadre) {
          this.comentarios.update(list =>
            list.map(c => c.id === comentarioId ? editado : c)
          );
        } else {
          // Actualizar respuesta dentro del comentario padre
          this.comentarios.update(list =>
            list.map(c => {
              if (c.id !== padreId) return c;
              return {
                ...c,
                respuestas: c.respuestas.map(r =>
                  r.id === comentarioId
                    ? { ...r, texto: editado.texto, editado: true, editado_en: editado.editado_en }
                    : r
                ),
              };
            })
          );
        }
        this.cancelarEdicion();
      },
      error: () =>
        this.toast.error('No se pudo editar el comentario.'),
    });
  }

  // ── Eliminación ───────────────────────────────────────────────────────────

  eliminarComentario(id: string, esPadre: boolean, padreId?: string): void {
    this.svc.eliminar(id).subscribe({
      next: () => {
        if (esPadre) {
          this.comentarios.update(list => list.filter(c => c.id !== id));
        } else {
          this.comentarios.update(list =>
            list.map(c => {
              if (c.id !== padreId) return c;
              return { ...c, respuestas: c.respuestas.filter(r => r.id !== id) };
            })
          );
        }
      },
      error: () =>
        this.toast.error('No se pudo eliminar el comentario.'),
    });
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  esPropio(autor: ComentarioAutor): boolean {
    return this.usuarioActual()?.id === autor.id;
  }

  getInitial(autor: ComentarioAutor): string {
    return (autor.full_name || autor.email || '?').charAt(0).toUpperCase();
  }

  getInitialUser(): string {
    const u = this.usuarioActual();
    return (u?.full_name || u?.email || '?').charAt(0).toUpperCase();
  }

  formatTiempo(fecha: string): string {
    const diff  = Date.now() - new Date(fecha).getTime();
    const min   = Math.floor(diff / 60_000);
    const horas = Math.floor(diff / 3_600_000);
    const dias  = Math.floor(diff / 86_400_000);
    if (min < 1)    return 'Ahora';
    if (min < 60)   return `Hace ${min}m`;
    if (horas < 24) return `Hace ${horas}h`;
    if (dias < 7)   return `Hace ${dias}d`;
    return new Date(fecha).toLocaleDateString('es-CO');
  }

  /** Convierte @usuario en <span> resaltado */
  formatTexto(texto: string): string {
    return texto.replace(
      /@(\w+)/g,
      '<span class="ct-mention">@$1</span>',
    );
  }

  onEnterComentario(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.enviarComentario();
    }
  }

  onEnterRespuesta(event: KeyboardEvent, padre: Comentario): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.enviarRespuesta(padre);
    }
  }

  trackById(_: number, item: Comentario | Respuesta): string {
    return item.id;
  }
}
