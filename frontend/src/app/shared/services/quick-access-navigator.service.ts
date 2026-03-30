/**
 * QuickAccessNavigatorService
 * Cuando un QuickAccessDialog está activo, intercepta las navegaciones
 * del router y las redirige al sistema de navegación interna del dialog.
 */
import { Injectable, Type } from '@angular/core';
import { Subject } from 'rxjs';

export interface QuickAccessRoute {
  /** Patrón de URL (soporta :param) */
  pattern: string;
  /** Cargador lazy del componente */
  loader: () => Promise<Type<unknown>>;
}

@Injectable({ providedIn: 'root' })
export class QuickAccessNavigatorService {
  /** true mientras algún QuickAccessDialog está activo */
  isActive = false;

  /** Rutas que este servicio puede manejar internamente */
  private routes: QuickAccessRoute[] = [];

  /** Emite la URL interceptada para que el dialog la procese */
  private readonly interceptedSubject = new Subject<string>();
  readonly intercepted$ = this.interceptedSubject.asObservable();

  /** Emite cuando un componente interno solicita retroceder en el historial */
  private readonly goBackSubject = new Subject<void>();
  readonly goBack$ = this.goBackSubject.asObservable();

  register(routes: QuickAccessRoute[]): void {
    this.routes = routes;
    this.isActive = true;
  }

  unregister(): void {
    this.isActive = false;
    this.routes = [];
  }

  /** Emite si la URL puede manejarse dentro del dialog; retorna true si la absorbe */
  tryIntercept(url: string): boolean {
    if (!this.isActive) return false;
    const path = url.split('?')[0];
    const canHandle = this.routes.some(r => this.matchPattern(r.pattern, path));
    if (canHandle) {
      this.interceptedSubject.next(url);
      return true;
    }
    return false;
  }

  /** Resuelve el componente para una URL dada */
  async resolveComponent(url: string): Promise<Type<unknown> | null> {
    const path = url.split('?')[0];
    const route = this.routes.find(r => this.matchPattern(r.pattern, path));
    return route ? route.loader() : null;
  }

  /**
   * Solicita retroceder dentro del dialog activo.
   * Los componentes internos deben llamar esto en lugar de router.navigate(listUrl)
   * cuando están dentro de un QuickAccessDialog.
   */
  requestGoBack(): void {
    this.goBackSubject.next();
  }

  private matchPattern(pattern: string, path: string): boolean {
    const patternParts = pattern.split('/').filter(Boolean);
    const pathParts   = path.split('/').filter(Boolean);
    if (patternParts.length !== pathParts.length) return false;
    return patternParts.every((part, i) => part.startsWith(':') || part === pathParts[i]);
  }
}
