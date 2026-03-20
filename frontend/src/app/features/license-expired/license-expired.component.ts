import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-license-expired',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './license-expired.component.html',
  styleUrl: './license-expired.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LicenseExpiredComponent {
  private readonly authService = inject(AuthService);

  logout(): void {
    this.authService.logout();
  }
}
