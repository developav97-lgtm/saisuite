# Validación 4×4 — Sistema de Solicitudes de Licencia

**Ticket:** IMP-VAL-002
**Fecha:** 2026-04-20
**Ejecutado por:** Orquestador SaiSuite (Evidence Collector + UI Designer en paralelo)
**Alcance:** `features/admin/license-requests/`, `features/admin/company-settings/license-request-dialog/`, `features/license-expired/`
**Modo:** Review estático (sin browser).

---

## Resumen ejecutivo

**Veredicto:** ❌ **NEEDS WORK** — 9 críticos bloquean producción.

**Score por componente:**
| Componente | Score | Drift |
|------------|-------|-------|
| `license-requests` (tabla admin) | 5.5/10 | heavy drift |
| `license-request-dialog` (modal) | 6.0/10 | drift menor |
| `license-expired` (página 403) | 4.5/10 | heavy drift |
| **Global (weighted)** | **5.3/10** | **Basic** |

**Hallazgos totales:** 31 issues (9 🔴 + 13 🟡 + 9 🔵)

---

## Problemas sistémicos transversales

Los 3 componentes comparten estos anti-patrones:

### S-1 — Tokens CSS inexistentes (crítico, rompe dark mode)
Referencias a tokens que **NO existen** en `styles.scss:43-85`:
- `--sc-warning-bg`, `--sc-success-bg`, `--sc-error-bg` (reales: `--sc-warning-light`, `--sc-success-light`, `--sc-error-light`)
- `--sc-text-secondary` (real: `--sc-text-muted`)

Los fallbacks hex enmascaran el bug: el chip se renderiza con el hex hardcodeado y **no cambia en dark mode**.

### S-2 — Mezcla `--sc-*` con `--mat-sys-*`
`license-expired` usa ambos sistemas — rompe el contrato del proyecto ("variables CSS `var(--sc-*)`" — CLAUDE.md). Los overrides de dark-theme no aplican a `--mat-sys-*`.

### S-3 — Fallbacks hex en tokens que SÍ existen
`var(--sc-primary, #1565c0)`, `var(--sc-surface-ground, #f5f5f5)`, etc. Red flag del checklist. Los tokens siempre están definidos, el fallback solo congela light-mode.

### S-4 — Listado admin sin `mat-table` + `MatPaginator`
`license-requests` usa cards stackeadas con filtrado client-side. No escala, no sigue patrón canónico `proyecto-list`.

### S-5 — Magic numbers px en lugar de rem + tokens
Border radius, paddings, font-sizes fuera de la escala del design system.

---

## Críticos (9 — bloquean deploy)

| ID | Componente | Descripción | Archivo:línea |
|----|------------|-------------|---------------|
| CRIT-L1 | license-requests | Tokens `--sc-warning-bg`, `--sc-success-bg`, `--sc-error-bg` no existen | `scss:72-74` |
| CRIT-L2 | license-requests | Sin `mat-table` + `MatPaginator` server-side | `ts/html` completo |
| CRIT-L3 | license-requests | Error callback sin `MatSnackBar` feedback | `ts:57` |
| CRIT-L4 | license-requests | Empty state no sigue patrón canónico (falta CTA) | `html:26-31,98-103` |
| CRIT-L5 | license-request-dialog | Token `--sc-text-secondary` no existe (usar `--sc-text-muted`) | `ts:83` |
| CRIT-L6 | license-request-dialog | Sin `subscriptSizing="dynamic"` — saltos de altura en el modal | `ts:42,58` |
| CRIT-L7 | license-request-dialog | Submit sin lock — doble click genera doble solicitud | `ts:68-72` |
| CRIT-L8 | license-expired | Mezcla `--mat-sys-*` con `--sc-*` en 6 líneas | `scss:29,36,41,58,69,76` |
| CRIT-L9 | license-expired | 4 fallbacks hex hardcodeados en tokens `--sc-*` | `scss:7,16,29,48` |

---

## Mayores (13)

**license-requests (5):**
- Nullish chains innecesarios `req.package?.name` (modelo declara non-null)
- Precio mensual sin alineación derecha
- Iconos decorativos sin `aria-hidden`
- Filtro status en cliente en vez de `?status=` en server
- `.sc-card` con padding override (rompe contrato de la primitiva)

**license-request-dialog (4):**
- Coerción `+pkg.price_monthly` frágil (tipado)
- `notes` sin `Validators.maxLength(500)`
- Opciones sin `aria-label`
- Getters en lugar de `computed()`

**license-expired (4):**
- `get isSessionExpired()` getter en vez de `computed()`
- 4 iconos decorativos sin `aria-hidden`
- Teléfono/email hardcodeados (placeholder en producción)
- Sin `role="alert"` — error crítico invisible a screen readers

---

## Menores (9)

**license-requests (3):**
- `CommonModule` importado innecesariamente
- Fallback hex redundante en `var(--sc-primary, #1565c0)`
- Touch targets mobile solo en <480px (tablets quedan con ~36px)

**license-request-dialog (3):**
- `CommonModule` innecesario (solo usa `number` pipe)
- Icono sin `aria-hidden`
- Fallback hex `#666` redundante

**license-expired (3):**
- `z-index: 9999` magic number
- `position: fixed; inset: 0` innecesario para ruta completa
- Email escapado HTML en vez de `<a href="mailto:">`
- Teléfono sin `<a href="tel:">` (no tap-to-call mobile)

---

## Bugs clasificados para tickets separados

| ID sugerido | Sev | Título |
|-------------|-----|--------|
| BUGFIX-LIC-201 | 🔴 | `fix(licencias): corregir tokens CSS inexistentes en los 3 componentes` |
| BUGFIX-LIC-202 | 🔴 | `fix(licencias): migrar license-requests a mat-table + MatPaginator` |
| BUGFIX-LIC-203 | 🔴 | `fix(licencias): MatSnackBar feedback + submit lock en dialog` |
| BUGFIX-LIC-204 | 🔴 | `fix(licencias): homogeneizar tokens en license-expired (quitar --mat-sys-*)` |
| BUGFIX-LIC-205 | 🟡 | `fix(licencias): subscriptSizing, nullish chains, aria-hidden` |
| IMP-LIC-206 | 🟡 | `improvement(licencias): usar sc-status-chip + sc-card canónicos` |
| IMP-LIC-207 | 🔵 | `improvement(licencias): 9 mejoras menores del design system` |

**Recomendación:** ejecutar los 4 críticos en 1 sesión BUGFIX autónoma (~2-3 horas). Los mayores en 1-2 sesiones adicionales. Los menores agrupar en 1 IMPROVEMENT.

---

## ⏳ Pending (con backend + dev server)

- Validación visual 4×4 real (Desktop/Mobile × Light/Dark) — mismo approach que contabilidad
- Flujo end-to-end: crear solicitud → aparece en admin → aprobar → company activa → email enviado
- Test de doble-click submission (CRIT-L7)
- Validar scroll y render del listado con 100+ solicitudes (CRIT-L2 escalabilidad)

---

## Trazabilidad

**Subagentes invocados:**
- `Evidence Collector` — 59,821 tokens, 124s, reporte por componente + veredicto
- `UI Designer` — 72,895 tokens, 140s, audit DS + comparación con canónico `proyecto-list`

**Convergencia entre agents:** alta (ambos detectaron los mismos 4 problemas sistémicos top: tokens inexistentes, drift vs proyecto-list, sin paginator, fallbacks hex).

**Telemetría:** 4 eventos registrados en `.claude/telemetry.jsonl` (ticket_start, phase_start, 2× agent_invoked, phase_complete, ticket_complete).

---

**Siguiente acción:** PO prioriza BUGFIX-LIC-201 a 204 para próxima sesión BUGFIX autónoma.
