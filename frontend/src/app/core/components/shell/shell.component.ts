// frontend/src/app/core/components/shell/shell.component.ts
import {
    Component,
    OnInit,
    ChangeDetectionStrategy,
    ChangeDetectorRef,
} from '@angular/core';
import { TopbarComponent } from '../topbar/topbar.component';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from '../../services/theme.service';

@Component({
    selector: 'app-shell',
    standalone: true,
    imports: [RouterOutlet, TopbarComponent, SidebarComponent],
    templateUrl: './shell.component.html',
    styleUrls: ['./shell.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShellComponent implements OnInit {
    sidebarVisible = true;

    constructor(
        private themeService: ThemeService,
        private cdr: ChangeDetectorRef,
    ) { }

    ngOnInit(): void {
        this.themeService.initTheme();
        // En móvil el sidebar arranca cerrado
        this.sidebarVisible = window.innerWidth >= 992;
        this.cdr.markForCheck();
    }

    toggleSidebar(): void {
        this.sidebarVisible = !this.sidebarVisible;
        this.cdr.markForCheck();
    }
}