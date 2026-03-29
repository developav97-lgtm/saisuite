import { Injectable } from '@angular/core';
import { toast } from 'ngx-sonner';

@Injectable({ providedIn: 'root' })
export class ToastService {
  success(message: string, description?: string): void {
    toast.success(message, { description, duration: 5000 });
  }

  error(message: string, description?: string): void {
    toast.error(message, { description, duration: 5000 });
  }

  warning(message: string, description?: string): void {
    toast.warning(message, { description, duration: 5000 });
  }

  info(message: string, description?: string): void {
    toast.info(message, { description, duration: 5000 });
  }
}
