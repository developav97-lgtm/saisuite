import { Injectable, inject } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';

const MAX_HISTORY = 10;

@Injectable({ providedIn: 'root' })
export class NavigationHistoryService {
  private readonly router = inject(Router);
  private readonly history: string[] = [];

  constructor() {
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe((e) => {
        const url = e.urlAfterRedirects;
        if (this.history[this.history.length - 1] !== url) {
          this.history.push(url);
          if (this.history.length > MAX_HISTORY) {
            this.history.shift();
          }
        }
      });
  }

  /**
   * Navigate to the previous in-app URL, or to the fallback if there is
   * no meaningful history (direct access, first page, etc.).
   */
  goBack(
    fallback: string | string[],
    fallbackQueryParams?: Record<string, string | number>,
  ): void {
    if (this.history.length >= 2) {
      this.history.pop();
      const previousUrl = this.history.pop()!;
      this.router.navigateByUrl(previousUrl);
    } else {
      const route = Array.isArray(fallback) ? fallback : [fallback];
      this.router.navigate(route, { queryParams: fallbackQueryParams });
    }
  }

  get previousUrl(): string | null {
    return this.history.length >= 2
      ? this.history[this.history.length - 2]
      : null;
  }

  get canGoBack(): boolean {
    return this.history.length >= 2;
  }
}
