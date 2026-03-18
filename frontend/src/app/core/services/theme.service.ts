import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private dark = false;

  initTheme(): void {
    this.dark = localStorage.getItem('theme') === 'dark';
    document.body.classList.toggle('dark-theme', this.dark);
  }

  toggleDarkMode(): void {
    this.dark = !this.dark;
    document.body.classList.toggle('dark-theme', this.dark);
    localStorage.setItem('theme', this.dark ? 'dark' : 'light');
  }

  get isDark(): boolean {
    return this.dark;
  }
}
