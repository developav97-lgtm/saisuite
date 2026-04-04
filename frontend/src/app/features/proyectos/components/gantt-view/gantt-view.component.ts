import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  inject,
  input,
  signal,
} from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';
import { FormsModule } from '@angular/forms';
import Gantt, { type FrappeGanttTask, type ViewMode } from 'frappe-gantt';
import { ProyectoService } from '../../services/proyecto.service';
import { TareaService } from '../../services/tarea.service';
import { SchedulingService } from '../../services/scheduling.service';
import { BaselineService } from '../../services/baseline.service';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { TareaDialogComponent, TareaDialogResult } from '../tarea-dialog/tarea-dialog.component';
import type { ProjectBaselineList } from '../../models/baseline.model';
import { ToastService } from '../../../../core/services/toast.service';

/**
 * Convierte un UUID (con guiones) en un ID seguro para atributos SVG/HTML.
 * frappe-gantt usa el id como atributo `id` en elementos SVG; un UUID con
 * guiones es válido en HTML pero frappe-gantt lo pasa a selectores CSS donde
 * los guiones en el primer carácter causan InvalidCharacterError.
 * Prefijo "g_" garantiza que comienza con letra y los guiones se convierten a
 * underscores, produciendo un identificador CSS y SVG completamente seguro.
 */
function uuidToGanttId(uuid: string): string {
  return 'g_' + uuid.replace(/-/g, '_');
}

@Component({
  selector: 'app-gantt-view',
  templateUrl: './gantt-view.component.html',
  styleUrl: './gantt-view.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonToggleModule,
    MatButtonModule,
    MatDialogModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatChipsModule,
  ],
})
export class GanttViewComponent implements AfterViewInit, OnDestroy {
  @ViewChild('ganttContainer') ganttContainer!: ElementRef<SVGElement>;

  readonly proyectoId     = input.required<string>();
  readonly proyectoCodigo = input<string>('');

  private readonly proyectoService  = inject(ProyectoService);
  private readonly tareaService     = inject(TareaService);
  private readonly schedulingService = inject(SchedulingService);
  private readonly baselineService  = inject(BaselineService);
  private readonly router           = inject(Router);
  private readonly route            = inject(ActivatedRoute);
  private readonly dialog           = inject(MatDialog);
  private readonly toast       = inject(ToastService);
  private readonly cdr              = inject(ChangeDetectorRef);

  readonly loading          = signal(true);
  readonly hasData          = signal(false);
  readonly hideCompleted    = signal(false);
  readonly compactMode      = signal(false);
  viewMode: ViewMode = 'Week';

  toggleHideCompleted(): void {
    this.hideCompleted.set(!this.hideCompleted());
    this.rerenderGantt();
  }

  toggleCompactMode(): void {
    this.compactMode.set(!this.compactMode());
    this.rerenderGantt();
  }


  // ── SK-41: Scheduling overlays ────────────────────────────────────────────
  readonly showCriticalPath  = signal(false);
  readonly showFloat         = signal(false);
  readonly showBaseline      = signal(false);
  readonly loadingOverlay    = signal(false);

  private criticalTaskIds    = new Set<string>();
  private floatMap           = new Map<string, number | null>();
  readonly activeBaseline    = signal<ProjectBaselineList | null>(null);

  private ganttInstance: Gantt | null = null;
  private tasks: FrappeGanttTask[]    = [];
  /** Mapa ganttId → UUID original de la tarea (para navegación on_click) */
  private ganttIdToUuid      = new Map<string, string>();

  /** Flag para distinguir drag de click simple */
  private wasDragged = false;
  /** Timeout del debounce de on_date_change */
  private dateChangeTimer?: ReturnType<typeof setTimeout>;

  readonly LEGEND = [
    { clase: 'estado-todo',        label: 'Por hacer'   },
    { clase: 'estado-in_progress', label: 'En progreso' },
    { clase: 'estado-in_review',   label: 'En revisión' },
    { clase: 'estado-blocked',     label: 'Bloqueada'   },
    { clase: 'estado-completed',   label: 'Completada'  },
    { clase: 'estado-cancelled',   label: 'Cancelada'   },
  ];

  ngAfterViewInit(): void {
    this.cargarGantt();
  }

  ngOnDestroy(): void {
    this.ganttInstance = null;
    clearTimeout(this.dateChangeTimer);
  }

  cargarGantt(): void {
    this.loading.set(true);
    this.proyectoService.getGanttData(this.proyectoId()).subscribe({
      next: ({ tasks }) => {
        this.loading.set(false);
        if (!tasks.length) {
          this.hasData.set(false);
          this.cdr.detectChanges();
          return;
        }
        this.ganttIdToUuid.clear();
        this.tasks = tasks.map(t => {
          const ganttId = uuidToGanttId(t.id);
          this.ganttIdToUuid.set(ganttId, t.id);
          // Convert dependency UUIDs to ganttIds
          const deps = (t.dependencies ?? '')
            .split(',')
            .map(d => d.trim())
            .filter(d => d.length > 0)
            .map(uuidToGanttId)
            .join(', ');
          return {
            id:           ganttId,
            name:         t.name,
            start:        t.start,
            end:          t.end,
            progress:     t.progress,
            custom_class: t.custom_class,
            dependencies: deps,
          };
        });
        this.hasData.set(true);
        this.cdr.detectChanges();
        this.initGantt();
      },
      error: () => {
        this.loading.set(false);
        this.hasData.set(false);
        this.cdr.detectChanges();
      },
    });
  }

  // ── SK-41: Toggle ruta crítica ────────────────────────────────────────────

  toggleCriticalPath(): void {
    const next = !this.showCriticalPath();
    this.showCriticalPath.set(next);
    if (next && this.criticalTaskIds.size === 0) {
      this.loadCriticalPath();
    } else {
      this.applyCriticalPathClasses();
    }
  }

  private loadCriticalPath(): void {
    this.loadingOverlay.set(true);
    this.schedulingService.getCriticalPath(this.proyectoId()).subscribe({
      next: (data) => {
        this.criticalTaskIds = new Set(data.critical_path.map(uuidToGanttId));
        this.loadingOverlay.set(false);
        this.applyCriticalPathClasses();
      },
      error: () => {
        this.loadingOverlay.set(false);
        this.showCriticalPath.set(false);
        this.toast.error('No se pudo calcular la ruta crítica.');
      },
    });
  }

  // ── SK-41: Toggle float ───────────────────────────────────────────────────

  toggleFloat(): void {
    const next = !this.showFloat();
    this.showFloat.set(next);
    if (next && this.floatMap.size === 0) {
      this.loadFloatData();
    } else {
      this.rerenderGantt();
    }
  }

  private loadFloatData(): void {
    this.loadingOverlay.set(true);
    // UUIDs originales de todas las tareas visibles (máx 30 para no saturar la red)
    const taskUuids = [...this.ganttIdToUuid.values()].slice(0, 30);
    if (taskUuids.length === 0) {
      this.loadingOverlay.set(false);
      return;
    }

    // Cargar float de cada tarea en paralelo; si una tarea no tiene CPM devuelve null
    forkJoin(
      taskUuids.map(uuid =>
        this.schedulingService.getTaskFloat(uuid).pipe(
          catchError(() => of(null))
        )
      )
    ).subscribe({
      next: (results) => {
        this.floatMap.clear();
        results.forEach((fd, idx) => {
          const ganttId = uuidToGanttId(taskUuids[idx]);
          this.floatMap.set(ganttId, fd ? fd.total_float : null);
        });
        this.loadingOverlay.set(false);
        this.rerenderGantt();
      },
      error: () => {
        this.loadingOverlay.set(false);
        this.showFloat.set(false);
      },
    });
  }

  // ── SK-41: Toggle baseline ────────────────────────────────────────────────

  toggleBaseline(): void {
    const next = !this.showBaseline();
    this.showBaseline.set(next);
    if (next && !this.activeBaseline()) {
      this.loadActiveBaseline();
    }
  }

  private loadActiveBaseline(): void {
    this.loadingOverlay.set(true);
    this.baselineService.list(this.proyectoId()).subscribe({
      next: (list) => {
        const active = list.find(b => b.is_active_baseline) ?? list[0] ?? null;
        this.activeBaseline.set(active);
        this.loadingOverlay.set(false);
        this.cdr.detectChanges();
      },
      error: () => {
        this.loadingOverlay.set(false);
        this.showBaseline.set(false);
      },
    });
  }

  // ── Renderizado con overlays ──────────────────────────────────────────────

  private rerenderGantt(): void {
    const sourceTasks = this.hideCompleted()
      ? this.tasks.filter(t => !t.custom_class?.includes('estado-completed') && !t.custom_class?.includes('estado-cancelled'))
      : this.tasks;

    const renderTasks = sourceTasks.map(t => {
      let customClass = t.custom_class ?? '';
      let name        = t.name;

      if (this.showFloat()) {
        const f = this.floatMap.get(t.id);
        if (f === 0) {
          name = `${name} [CRÍTICA]`;
        } else if (f !== undefined && f !== null && f > 0) {
          name = `${name} [Holgura: ${f}d]`;
        }
      }
      return { ...t, custom_class: customClass, name };
    });

    const el = this.ganttContainer?.nativeElement;
    if (!el) return;

    // frappe-gantt wraps the SVG inside a .gantt-container div on init.
    // On re-render we must unwrap it first to avoid nested wrappers.
    const wrapper = el.closest('.gantt-container');
    if (wrapper && wrapper.parentElement) {
      wrapper.parentElement.insertBefore(el, wrapper);
      wrapper.remove();
    }
    el.innerHTML = '';

    this.ganttInstance = new Gantt(el, renderTasks, {
      view_mode:  this.viewMode,
      language:   'es',
      bar_height: this.compactMode() ? 12 : 20,
      padding:    this.compactMode() ? 4  : 8,
      on_date_change: (task: FrappeGanttTask, start: Date, end: Date) => {
        clearTimeout(this.dateChangeTimer);
        this.dateChangeTimer = setTimeout(() => {
          this.wasDragged = true;
          this.confirmarCambioFechas(task, start, end);
        }, 400);
      },
      on_click: (task: FrappeGanttTask) => {
        if (this.wasDragged) { this.wasDragged = false; return; }
        const taskUuid = this.ganttIdToUuid.get(task.id) ?? task.id;
        this.abrirTareaDialog(taskUuid);
      },
    });

    this.applyCriticalPathClasses();
  }

  /** Apply/remove critical-task CSS classes without re-rendering the Gantt */
  private applyCriticalPathClasses(): void {
    const el = this.ganttContainer?.nativeElement;
    if (!el) return;
    const svg = el.closest('.gantt-container')?.querySelector('svg') ?? el;
    // Clear existing
    svg.querySelectorAll('.critical-task').forEach(
      (barEl: Element) => barEl.classList.remove('critical-task'),
    );
    // Apply if enabled
    if (this.showCriticalPath() && this.criticalTaskIds.size > 0) {
      this.criticalTaskIds.forEach(ganttId => {
        const barEl = svg.querySelector(`.bar-wrapper[data-id="${ganttId}"]`);
        if (barEl) barEl.classList.add('critical-task');
      });
    }
  }

  private initGantt(): void {
    this.rerenderGantt();
  }

  private confirmarCambioFechas(task: FrappeGanttTask, start: Date, end: Date): void {
    const fmt = (d: Date) =>
      d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });

    const ref = this.dialog.open(ConfirmDialogComponent, {
      width: '420px',
      data: {
        header:      'Confirmar cambio de fechas',
        message:     `¿Actualizar las fechas de "${task.name}"?\n\nNuevo rango: ${fmt(start)} → ${fmt(end)}`,
        acceptLabel: 'Actualizar',
        acceptColor: 'primary',
      },
    });

    ref.afterClosed().subscribe(confirmed => {
      if (!confirmed) {
        // Revertir el Gantt al estado anterior
        this.cargarGantt();
        return;
      }

      const toISO = (d: Date) => d.toISOString().split('T')[0];

      // task.id es ganttId; recuperar UUID original para la API
      const taskUuid = this.ganttIdToUuid.get(task.id) ?? task.id;
      this.tareaService.update(taskUuid, {
        fecha_inicio: toISO(start),
        fecha_fin:    toISO(end),
      }).subscribe({
        next: () => {
          this.toast.success('Fechas actualizadas correctamente.');
        },
        error: () => {
          this.toast.error('No se pudieron actualizar las fechas.');
          this.cargarGantt();
        },
      });
    });
  }

  private abrirTareaDialog(tareaId: string): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { tarea: tareaId },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });

    const ref = this.dialog.open<TareaDialogComponent, unknown, TareaDialogResult>(
      TareaDialogComponent,
      {
        data: { tareaId },
        width: '820px',
        height: '88vh',
        maxWidth: '96vw',
        maxHeight: '96vh',
        panelClass: 'trd-dialog-panel',
      },
    );

    ref.afterClosed().subscribe((result) => {
      if (result?.navigateTo) {
        this.router.navigate(result.navigateTo!, {
          queryParams: result.navigateParams,
        });
        return;
      }

      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { tarea: null },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      });

      if (result?.updated) {
        this.cargarGantt();
      }
    });
  }

  onViewModeChange(): void {
    if (this.ganttInstance) {
      this.ganttInstance.change_view_mode(this.viewMode);
    }
  }

  refreshGantt(): void {
    this.cargarGantt();
  }

  exportarSVG(): void {
    const el = this.ganttContainer?.nativeElement as HTMLElement | SVGElement | undefined;
    if (!el) return;

    const wrapper = el.closest('.gantt-container') ?? el.parentElement;
    const svg = el instanceof SVGElement
      ? el
      : (el as HTMLElement).querySelector('svg');
    if (!svg) return;

    const clone = svg.cloneNode(true) as SVGElement;

    // 1. Resolve CSS variables in inline styles — they don't work in standalone SVGs.
    const origElements = svg.querySelectorAll('*');
    const cloneElements = clone.querySelectorAll('*');
    origElements.forEach((origEl, i) => {
      const cloneEl = cloneElements[i];
      if (!cloneEl) return;
      const inlineStyle = cloneEl.getAttribute('style');
      if (inlineStyle && inlineStyle.includes('var(--')) {
        const computed = getComputedStyle(origEl as Element);
        const resolved = inlineStyle.replace(
          /var\(--[^)]+\)/g,
          (match) => {
            const varName = match.slice(4, -1).split(',')[0].trim();
            return computed.getPropertyValue(varName).trim() || 'transparent';
          },
        );
        cloneEl.setAttribute('style', resolved);
      }
    });

    // 2. Remove drag handles — not useful in exported image.
    clone.querySelectorAll('.handle-group').forEach(h => h.remove());

    // 3. Inject header texts from the HTML overlay into the SVG.
    const headerDiv = wrapper?.querySelector('.grid-header') as HTMLElement | null;
    if (headerDiv) {
      const ns = 'http://www.w3.org/2000/svg';
      const headerG = document.createElementNS(ns, 'g');
      headerG.setAttribute('class', 'export-header');

      // Header background
      const headerBg = document.createElementNS(ns, 'rect');
      headerBg.setAttribute('x', '0');
      headerBg.setAttribute('y', '0');
      headerBg.setAttribute('width', clone.getAttribute('width') ?? '100%');
      headerBg.setAttribute('height', '85');
      headerBg.setAttribute('fill', '#f5f5f5');
      headerG.appendChild(headerBg);

      headerDiv.querySelectorAll('.upper-text').forEach(el => {
        const left = parseInt((el as HTMLElement).style.left, 10) || 0;
        const text = document.createElementNS(ns, 'text');
        text.setAttribute('x', String(left + 4));
        text.setAttribute('y', '30');
        text.setAttribute('fill', '#333');
        text.setAttribute('font-size', '14');
        text.setAttribute('font-weight', '600');
        text.setAttribute('font-family', 'sans-serif');
        text.textContent = el.textContent?.trim() ?? '';
        headerG.appendChild(text);
      });

      headerDiv.querySelectorAll('.lower-text').forEach(el => {
        const left = parseInt((el as HTMLElement).style.left, 10) || 0;
        const text = document.createElementNS(ns, 'text');
        text.setAttribute('x', String(left + 4));
        text.setAttribute('y', '65');
        text.setAttribute('fill', '#888');
        text.setAttribute('font-size', '11');
        text.setAttribute('font-family', 'sans-serif');
        text.textContent = el.textContent?.trim() ?? '';
        headerG.appendChild(text);
      });

      // Insert header after background but before grid content
      const gridEl = clone.querySelector('.grid');
      if (gridEl) {
        clone.insertBefore(headerG, gridEl);
      } else {
        clone.appendChild(headerG);
      }
    }

    // 4. Inject white background rect as the first child
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('width', '100%');
    bg.setAttribute('height', '100%');
    bg.setAttribute('fill', '#ffffff');
    clone.insertBefore(bg, clone.firstChild);

    // 5. Inject inline styles so the SVG is self-contained
    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    style.textContent = `
      text { fill: #333; }
      .grid-background { fill: none; }
      .grid-row { fill: #ffffff; }
      .row-line { stroke: #e0e0e0; }
      .tick { stroke: #e0e0e0; }
      .today-highlight { fill: rgba(25, 118, 210, 0.08); }
      .bar-label { fill: #333 !important; font-size: 11px; font-weight: 600; }
      .arrow path { fill: none; stroke: #718096; stroke-width: 1.5; }
      .bar-wrapper.estado-todo .bar { fill: #64b5f6; }
      .bar-wrapper.estado-todo .bar-progress { fill: #2196f3; }
      .bar-wrapper.estado-in_progress .bar { fill: #42a5f5; }
      .bar-wrapper.estado-in_progress .bar-progress { fill: #1976d2; }
      .bar-wrapper.estado-in_review .bar { fill: #ab47bc; }
      .bar-wrapper.estado-in_review .bar-progress { fill: #8e24aa; }
      .bar-wrapper.estado-blocked .bar { fill: #ef5350; }
      .bar-wrapper.estado-blocked .bar-progress { fill: #c62828; }
      .bar-wrapper.estado-completed .bar { fill: #66bb6a; }
      .bar-wrapper.estado-completed .bar-progress { fill: #388e3c; }
      .bar-wrapper.estado-cancelled .bar { fill: #bdbdbd; }
      .bar-wrapper.estado-cancelled .bar-progress { fill: #9e9e9e; }
      .bar-wrapper.critical-task .bar { fill: #e53935; }
      .bar-wrapper.critical-task .bar-progress { fill: #b71c1c; }
    `;
    clone.insertBefore(style, clone.firstChild);

    const serializer = new XMLSerializer();
    const svgStr = serializer.serializeToString(clone);
    const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const code = this.proyectoCodigo() || this.proyectoId();
    const ts = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
    a.download = `gantt-${code}-${ts}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
