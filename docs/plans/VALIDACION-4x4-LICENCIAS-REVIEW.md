# Re-validación 4×4 — Sistema de Solicitudes de Licencia

**Ticket origen:** IMP-VAL-002 (reporte original `VALIDACION-4x4-LICENCIAS.md`)
**Tickets aplicados:** BUGFIX-LIC-201, 202, 203, 204, 205 + IMP-LIC-206, 207
**Fecha:** 2026-04-20
**Ejecutado por:** Orquestador SaiSuite (live preview — backend Docker + `ng serve` local)
**Build:** `ng build --configuration=development` limpio (warnings sólo pre-existentes en otros módulos).

---

## Resumen ejecutivo

**Veredicto:** ✅ **PASS** — todos los issues críticos del reporte original resueltos y verificados visualmente.

**Score por componente (post-fix):**
| Componente | Score previo | Score actual | Estado |
|------------|--------------|--------------|--------|
| `license-requests` (tabla admin) | 5.5/10 | **9.0/10** | ✅ PASS |
| `license-request-dialog` (modal) | 6.0/10 | **9.0/10** | ✅ PASS |
| `license-expired` (página 403) | 4.5/10 | **9.0/10** | ✅ PASS |

Escenarios verificados en live preview (Chromium, viewport 1280×800 y 375×812):

| Escenario | license-requests | license-request-dialog | license-expired |
|-----------|:----------------:|:-----------------------:|:---------------:|
| Desktop · Light | ✅ | ✅ | ✅ |
| Desktop · Dark  | ✅ | ✅ | ✅ |
| Mobile · Light  | ✅ | ✅ | ✅ |
| Mobile · Dark   | ✅ | —  | ✅ |

Además verificado: `/license-expired?reason=session_expired` (variante sesión cerrada) con icono `devices_off` y CTA "Volver a iniciar sesión" ✅.

---

## Evidencia por ticket

### BUGFIX-LIC-201 — Tokens CSS inexistentes
- `license-requests`: chip `APROBADO` se pinta con `--sc-success-light` + `--sc-success` en light y dark (verdes coherentes en ambas paletas).
- `license-request-dialog`: hint del modal usa `--sc-text-muted` (antes `--sc-text-secondary` inexistente).
- `license-expired`: todos los tokens resuelven a valores reales de `styles.scss`; ya no hay "congelamiento" en light-mode.

### BUGFIX-LIC-202 — mat-table + MatPaginator
- 2 tablas separadas (Pendientes / Historial), cada una con paginator independiente (`pageSize=10`, options `[10,25,50]`).
- Responsive mobile: columnas `requester`/`reviewer` ocultas <960px; `date`/`price` ocultas <680px; scroll horizontal dentro de `.table-responsive`.
- Acciones por fila con `mat-icon-button` + tooltip (`check_circle`, `cancel`) y touch target 44px automático por la regla global `.mat-mdc-icon-button` en mobile.

### BUGFIX-LIC-203 — Feedback + submit lock
- Error de `load()` ahora llama a `toast.error(...)` (MatSnackBar) — el usuario ya no queda a ciegas.
- Dialog con `submitting = signal(false)` + botón con `[disabled]="form.invalid || submitting()"`. El `submit()` retorna antes de cerrar si ya está en curso.

### BUGFIX-LIC-204 — Homogeneización `license-expired`
- Eliminados los 6 `--mat-sys-*` y los 4 fallbacks hex en tokens `--sc-*`.
- `role="alert"` + `aria-live="assertive"` en el contenedor.
- `<a href="mailto:…">` y `<a href="tel:…">` con `min-height: 44px`, color `--sc-primary` en hover (tap-to-call en mobile funcional).
- `position: fixed; inset: 0; z-index: 9999` reemplazados por `min-height: 100vh` + flex.

### BUGFIX-LIC-205 — DX/a11y
- `subscriptSizing="dynamic"` en los dos campos del modal (sin saltos de altura al aparecer/desaparecer el contador).
- `Validators.maxLength(500)` en `notes` + contador `{{ notesLength }} / 500` visible.
- Opciones del select con `aria-label` generado (`optionAriaLabel(pkg)`) — verificado por DOM: `+200K tokens IA, 200000 tokens, 280000.00 COP mensuales`.
- Nullish chains removidos donde el modelo garantiza non-null (`req.package.name`).
- `mat-icon` decorativos con `aria-hidden="true"`.

### IMP-LIC-206 — Primitivas canónicas
- Nuevas variantes `.sc-status-chip--pending/--approved/--rejected` añadidas a `styles.scss` con tokens dark-mode aware (`--sc-warning-light`, `--sc-success-light`, `--sc-error-light`).
- Tabla de historial usa la primitiva global en lugar de chip custom; padding override de `.sc-card` removido del componente.

### IMP-LIC-207 — Pulidos
- `CommonModule` reemplazado por `DatePipe` / `DecimalPipe` directos (bundle-friendly).
- Fallbacks hex (`#666`, `#1565c0`, `#f5f5f5`, `#fff`) removidos de los 3 componentes.
- Contador de caracteres en la nota.
- Touch targets ≥44px en enlaces de contacto (mailto/tel).

---

## Observaciones menores detectadas durante la revisión

1. **Email con wrap** — en viewports muy estrechos (<300px) el email `ventas@valmentech.com` puede empujar el icono de sobre fuera del card porque la cadena no tiene puntos de corte naturales. Se vio en el viewport de 277px generado por el resize pre-Dark. Solución mínima: agregar `min-width: 0; overflow-wrap: anywhere;` a `.le-contact-item span` o `word-break: break-all`. **No bloquea** — los viewports objetivo (≥375px) renderizan correctamente.

2. **Botón Historial en mobile** — el tab bar es estrecho; pese a `flex-wrap: nowrap` del estilo global, los headers de tabla se hacen horizontales con scroll (comportamiento correcto según patrón canónico `proyecto-list`). Validado.

3. **Panel admin** — el listado de Pendientes mostró 2 solicitudes reales y el Historial 1 aprobada, suficiente para validar ambas variantes. No se disparó el flujo end-to-end de aprobación (reuso de datos existentes).

---

## Flujos pendientes (out of scope de esta re-validación)

- **E2E real**: crear solicitud → aprobar → company activa → email enviado. No se ejecutó para no alterar datos de la sesión de QA (requiere cliente con licencia vencida).
- **Test de doble-click** en botón "Enviar solicitud": el lock aplica por `submitting` signal, pero faltaría test unitario Jasmine que lo cubra.
- **100+ solicitudes** para estresar el paginator client-side: no hay fixtures con ese volumen. A considerar si el uso real supera ~50 solicitudes activas — evaluar migrar a paginator server-side.

---

## Trazabilidad

- **Archivos tocados:** `styles.scss`, `license-requests.component.{ts,html,scss}`, `license-request-dialog.component.ts` (monolito), `license-expired.component.{ts,html,scss}`.
- **Build:** OK en `development` (ver `CONTEXT.md` sección 20 abr 2026).
- **Screenshots:** capturados durante la sesión (no persistidos a disco — sesión en vivo). Si se requieren artefactos, re-ejecutar con `qa-evidence/` script similar al de 2026-04-09.

**Siguiente acción:** cerrar los 7 tickets BUGFIX-LIC-201/207 como resueltos. Mantener observación 1 (email wrap) como nota para la próxima iteración de UI-UX.
