/**
 * Respuesta paginada de Django REST Framework.
 * Usado por todos los endpoints con paginación.
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
