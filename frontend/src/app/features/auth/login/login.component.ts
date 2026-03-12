// frontend/src/app/features/auth/login/login.component.ts
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [CommonModule],
    template: `
    <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;">
      <p>Login — por implementar</p>
    </div>
  `,
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginComponent { }