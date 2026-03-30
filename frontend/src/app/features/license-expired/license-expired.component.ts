import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
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
  private readonly route = inject(ActivatedRoute);

  readonly reason = signal<string>(
    this.route.snapshot.queryParamMap.get('reason') ?? 'no_license'
  );

  get isSessionExpired(): boolean {
    return this.reason() === 'session_expired';
  }

  logout(): void {
    this.authService.logout();
  }
}
