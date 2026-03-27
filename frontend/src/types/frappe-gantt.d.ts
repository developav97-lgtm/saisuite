/**
 * Declaraciones de tipos para frappe-gantt (sin tipos oficiales).
 * Solo se exponen las APIs que realmente usamos.
 */
declare module 'frappe-gantt' {
  export interface FrappeGanttTask {
    id: string;
    name: string;
    start: string;
    end: string;
    progress: number;
    custom_class?: string;
    dependencies?: string;
  }

  export type ViewMode = 'Quarter Day' | 'Half Day' | 'Day' | 'Week' | 'Month' | 'Year';

  export interface FrappeGanttOptions {
    view_mode?: ViewMode;
    language?: string;
    on_click?: (task: FrappeGanttTask) => void;
    on_date_change?: (task: FrappeGanttTask, start: Date, end: Date) => void;
    on_progress_change?: (task: FrappeGanttTask, progress: number) => void;
    on_view_change?: (mode: ViewMode) => void;
    header_height?: number;
    column_width?: number;
    step?: number;
    bar_height?: number;
    bar_corner_radius?: number;
    arrow_curve?: number;
    padding?: number;
    date_format?: string;
    popup_trigger?: string;
    custom_popup_html?: ((task: FrappeGanttTask) => string) | null;
  }

  export default class Gantt {
    constructor(
      element: string | SVGElement,
      tasks: FrappeGanttTask[],
      options?: FrappeGanttOptions,
    );

    change_view_mode(mode: ViewMode): void;
    refresh(tasks: FrappeGanttTask[]): void;
  }
}
