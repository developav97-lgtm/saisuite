import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TopbarComponent } from '../topbar/topbar.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { ThemeService } from '../../services/theme.service';
import { NgxSonnerToaster } from 'ngx-sonner';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, TopbarComponent, SidebarComponent, NgxSonnerToaster],
  templateUrl: './shell.component.html',
  styleUrls: ['./shell.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShellComponent implements OnInit {
  private readonly themeService = inject(ThemeService);

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
  }

  toggleSidebar(): void {
    this.sidebarVisible = !this.sidebarVisible;
    if (window.innerWidth >= 992) {
      localStorage.setItem(this.SIDEBAR_EXPANDED_KEY, String(this.sidebarVisible));
    }
  }
}
