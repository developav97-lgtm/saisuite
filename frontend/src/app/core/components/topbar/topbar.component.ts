// frontend/src/app/core/components/topbar/topbar.component.ts
import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { BadgeModule } from 'primeng/badge';
import { RippleModule } from 'primeng/ripple';
import { ThemeService } from '../../services/theme.service';

@Component({
    selector: 'app-topbar',
    standalone: true,
    imports: [CommonModule, RouterModule, ButtonModule, AvatarModule, BadgeModule, RippleModule],
    templateUrl: './topbar.component.html',
    styleUrls: ['./topbar.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TopbarComponent {
    @Input() sidebarVisible = true;
    @Output() toggleSidebar = new EventEmitter<void>();

    constructor(public themeService: ThemeService) { }
}