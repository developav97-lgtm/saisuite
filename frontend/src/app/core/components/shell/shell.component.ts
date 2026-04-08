import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, OnDestroy, inject, computed, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { TopbarComponent } from '../topbar/topbar.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { ThemeService } from '../../services/theme.service';
import { AuthService } from '../../auth/auth.service';
import { NotificationSocketService, WsNotification } from '../../services/notification-socket.service';
import { ChatStateService } from '../../services/chat-state.service';
import { NavigationHistoryService } from '../../services/navigation-history.service';
import { NgxSonnerToaster, toast } from 'ngx-sonner';
import { ChatFabComponent } from '../../../features/chat/components/chat-fab/chat-fab.component';
import { ChatPanelComponent } from '../../../features/chat/components/chat-panel/chat-panel.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, CommonModule, TopbarComponent, SidebarComponent, NgxSonnerToaster, MatIconModule, MatButtonModule, ChatFabComponent, ChatPanelComponent],
  templateUrl: './shell.component.html',
  styleUrls: ['./shell.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShellComponent implements OnInit, OnDestroy {
  private readonly themeService   = inject(ThemeService);
  private readonly authService    = inject(AuthService);
  private readonly socketService  = inject(NotificationSocketService);
  readonly chatState              = inject(ChatStateService);
  private readonly _navHistory     = inject(NavigationHistoryService);
  private readonly router         = inject(Router);
  private readonly destroyRef     = inject(DestroyRef);

  constructor() {
    // Clean orphaned CDK overlays after route path changes.
    // The CDK overlay container lives in <body> outside the component tree.
    // When a dialog-opening component is destroyed by navigation, the overlay
    // can persist as an orphan. This handler sweeps those after each navigation
    // to a different path (ignoring query-param-only changes).
    let previousPath = '';
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe((e) => {
      const currentPath = e.urlAfterRedirects.split('?')[0];
      if (currentPath === previousPath) { previousPath = currentPath; return; }
      previousPath = currentPath;
      // Path changed — sweep orphaned overlay DOM after a frame to let CDK
      // finish its own cleanup first.
      requestAnimationFrame(() => {
        const container = document.querySelector('.cdk-overlay-container');
        if (container && container.children.length > 0) {
          container.innerHTML = '';
        }
      });
    });

    // Use toObservable instead of effect() so the toast call runs in a plain
    // RxJS subscription — outside any reactive context — avoiding interactions
    // between ngx-sonner's internal signal store and Angular's effect scheduler.
    toObservable(this.socketService.latestNotification).pipe(
      filter((notif): notif is WsNotification => notif !== null),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(notif => {
      toast(notif.titulo, {
        description: notif.mensaje,
        duration: 5000,
        action: {
          label: 'Ver',
          onClick: () => {
            if (notif.tipo === 'chat' && notif.metadata?.['conversacion_id']) {
              this.chatState.open(notif.metadata['conversacion_id'] as string);
            } else if (notif.url_accion) {
              const url = notif.ancla
                ? `${notif.url_accion}${notif.ancla}`
                : notif.url_accion;
              this.router.navigateByUrl(url);
            }
          },
        },
      });
    });
  }

  /** Cuando soporte está en un tenant sin licencia válida. */
  readonly soporteNoLicense = computed(() => {
    const user = this.authService.currentUser();
    if (!user?.is_staff || user.is_superadmin || user.role === 'valmen_admin') return false;
    const ec = user.effective_company;
    if (!ec) return false;
    const lic = ec.license;
    return !lic || !lic.is_active_and_valid;
  });

  /** Info de licencia para mostrar la alerta. null = sin advertencia. */
  readonly licenseWarningInfo = computed(() => {
    const user = this.authService.currentUser();
    if (!user || user.is_superadmin || user.is_staff) return null;
    const lic = (user.effective_company ?? user.company)?.license;
    if (!lic) return null;
    const days = lic.days_until_expiry;
    if (days === undefined || days === null) return null;

    const isTrial = lic.status === 'trial';

    // Para prueba: mostrar siempre que quedan <= 30 días
    // Para activa: mostrar solo cuando quedan <= 5 días
    const threshold = isTrial ? 30 : 5;
    if (days > threshold) return null;

    return { days, isTrial };
  });

  /** @deprecated use licenseWarningInfo */
  readonly licenseWarning = computed(() => this.licenseWarningInfo()?.days ?? null);

  readonly licenseWarningClass = computed(() => {
    const d = this.licenseWarning();
    if (d === null) return '';
    if (d <= 1)  return 'sc-license-banner--critical';
    if (d <= 7)  return 'sc-license-banner--danger';
    return 'sc-license-banner--warning';
  });

  dismissedWarning = false;

  /** Total unread messages — fed by ChatPanelComponent via output */
  readonly chatUnreadCount = signal(0);

  private readonly SIDEBAR_EXPANDED_KEY = 'saisuite.sidebarExpanded';

  sidebarVisible = false;

  ngOnInit(): void {
    this.themeService.initTheme();
    if (window.innerWidth < 992) {
      // Mobile: drawer cerrado por defecto
      this.sidebarVisible = false;
    } else {
      // Desktop: leer preferencia guardada; si no hay nada guardado, contraído (false)
      const saved = localStorage.getItem(this.SIDEBAR_EXPANDED_KEY);
      this.sidebarVisible = saved === 'true';
    }

    // Connect WebSocket for real-time notifications
    if (this.authService.getAccessToken()) {
      this.socketService.connect();
    }
  }

  ngOnDestroy(): void {
    this.socketService.disconnect();
  }

  toggleSidebar(): void {
    this.sidebarVisible = !this.sidebarVisible;
    if (window.innerWidth >= 992) {
      localStorage.setItem(this.SIDEBAR_EXPANDED_KEY, String(this.sidebarVisible));
    }
  }
}
