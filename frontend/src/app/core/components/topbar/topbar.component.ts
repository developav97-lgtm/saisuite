import { ChangeDetectionStrategy, Component, EventEmitter, Output, inject, input } from '@angular/core';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ThemeService } from '../../services/theme.service';
import { AuthService } from '../../auth/auth.service';

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [RouterModule, MatIconModule, MatButtonModule, MatTooltipModule],
  templateUrl: './topbar.component.html',
  styleUrls: ['./topbar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TopbarComponent {
  readonly sidebarVisible = input(true);
  @Output() toggleSidebar = new EventEmitter<void>();

  readonly themeService = inject(ThemeService);
  readonly authService  = inject(AuthService);
  readonly currentUser  = inject(AuthService).currentUser;
}
