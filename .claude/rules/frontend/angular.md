---
paths:
  - "frontend/**/*.ts"
  - "frontend/**/*.html"
  - "frontend/**/*.scss"
---

# Reglas Frontend Angular — Se cargan SOLO al trabajar en archivos del frontend

## TypeScript
- `strict: true` obligatorio. Si no compila con strict, el código está mal.
- Nunca `any`. Usar `unknown` con narrowing si no se conoce el tipo.
- JWT se añade via interceptor. Nunca añadir headers manualmente.

## Componentes
- Presentacionales: `ChangeDetectionStrategy.OnPush`.
- Nunca suscripción manual sin `unsubscribe`. Usar `async pipe`.
- Servicios globales en `core/`. Servicios de feature en `features/[x]/services/`.

## UI Framework: Angular Material (DEC-011)
- **NUNCA** PrimeNG, Bootstrap ni Tailwind.
- Iconos: `mat-icon`. Notificaciones: `MatSnackBar` (nunca `alert()`).
- Confirmaciones: `MatDialog` + `ConfirmDialogComponent` (nunca `confirm()`).
- Tablas: `mat-table` + `MatPaginatorModule` server-side.
- Dark mode: `.dark-theme` en `<body>`, `ThemeService`.
- Tema: M3 paleta azul corporativo ValMen Tech.
- Sintaxis Angular 18: `@if` / `@for` / `@switch` — NUNCA `*ngIf` / `*ngFor`.
- SCSS: variables `var(--sc-*)`. Sin colores hardcodeados.

## Estándares UI/UX
- Tablas vacías: `sc-empty-state` fuera del `mat-table`.
- Loading: `mat-progress-bar` encima de tabla (nunca spinner en listados).
- Feedback: `MatSnackBar` con `panelClass`.
- Responsive: class `table-responsive` en TODAS las tablas.
- Referencia canónica: `proyecto-list` component.
- Leer: `docs/standards/UI-UX-STANDARDS.md`

## Tests
- Services: 100% cobertura. Components: ≥70%.
- Comando: `ng test --watch=false`

## Validación 4x4
1. Desktop (1920x1080) + Light
2. Desktop + Dark
3. Mobile (375px) + Light
4. Mobile + Dark
- Touch targets ≥44px, tablas con scroll horizontal mobile.
- Referencia: `docs/base-reference/CHECKLIST-VALIDACION.md`
