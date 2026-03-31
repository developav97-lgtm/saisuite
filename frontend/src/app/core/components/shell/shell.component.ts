import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, OnDestroy, inject, computed, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { Router, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { TopbarComponent } from '../topbar/topbar.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { ThemeService } from '../../services/theme.service';
import { AuthService } from '../../auth/auth.service';
import { NotificationSocketService, WsNotification } from '../../services/notification-socket.service';
import { ChatStateService } from '../../services/chat-state.service';
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
  private readonly router         = inject(Router);
  private readonly destroyRef     = inject(DestroyRef);

  constructor() {
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
    if (!user?.is_staff || user.is_superadmin || user.is_superuser) return false;
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
