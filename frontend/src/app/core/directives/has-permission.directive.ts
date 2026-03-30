import {
  Directive,
  TemplateRef,
  ViewContainerRef,
  effect,
  inject,
  input,
} from '@angular/core';
import { AuthService } from '../auth/auth.service';

/**
 * Directiva estructural que muestra/oculta contenido según permiso granular.
 *
 * Uso:
 *   <button *hasPermission="'proyectos.edit'">Editar</button>
 *
 * SuperAdmin y soporte siempre tienen acceso.
 * Si el usuario no tiene rol granular asignado, el elemento NO se muestra.
 * Reactiva: se re-evalúa automáticamente cuando cambia currentUser (ej: refresh de perfil).
 */
@Directive({
  selector: '[hasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  readonly hasPermission = input.required<string>();

  private readonly auth          = inject(AuthService);
  private readonly templateRef   = inject(TemplateRef<unknown>);
  private readonly viewContainer = inject(ViewContainerRef);

  constructor() {
    effect(() => {
      const user = this.auth.currentUser();

      // SuperAdmin y staff tienen todos los permisos
      if (user?.is_superadmin || user?.is_superuser || user?.is_staff) {
        if (!this.viewContainer.length) {
          this.viewContainer.createEmbeddedView(this.templateRef);
        }
        return;
      }

      const permisos = user?.rol_granular?.permisos ?? [];
      const tiene    = permisos.some(p => p.codigo === this.hasPermission());

      if (tiene) {
        if (!this.viewContainer.length) {
          this.viewContainer.createEmbeddedView(this.templateRef);
        }
      } else {
        this.viewContainer.clear();
      }
    });
  }
}
