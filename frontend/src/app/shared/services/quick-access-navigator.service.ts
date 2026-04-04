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

  /** URL de la última navegación interceptada (para extraer params) */
  private currentInterceptedUrl = '';

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
    this.currentInterceptedUrl = '';
  }

  /** Emite si la URL puede manejarse dentro del dialog; retorna true si la absorbe */
  tryIntercept(url: string): boolean {
    if (!this.isActive) return false;
    const path = url.split('?')[0];
    const canHandle = this.routes.some(r => this.matchPattern(r.pattern, path));
    if (canHandle) {
      this.currentInterceptedUrl = url;
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
   * Extrae un param nombrado de la última URL interceptada.
   * Útil para componentes cargados con NgComponentOutlet que no tienen ActivatedRoute.
   * Ej: getParam('id') en la URL /terceros/abc-123/editar → 'abc-123'
   */
  getParam(name: string): string | null {
    const path = this.currentInterceptedUrl.split('?')[0];
    for (const route of this.routes) {
      const params = this.extractParams(route.pattern, path);
      if (params && name in params) return params[name];
    }
    return null;
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

  private extractParams(pattern: string, path: string): Record<string, string> | null {
    const patternParts = pattern.split('/').filter(Boolean);
    const pathParts   = path.split('/').filter(Boolean);
    if (patternParts.length !== pathParts.length) return null;
    const params: Record<string, string> = {};
    for (let i = 0; i < patternParts.length; i++) {
      if (patternParts[i].startsWith(':')) {
        params[patternParts[i].slice(1)] = pathParts[i];
      } else if (patternParts[i] !== pathParts[i]) {
        return null;
      }
    }
    return params;
  }
}
