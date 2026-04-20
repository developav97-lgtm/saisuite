# Orden de generación de archivos — Features SaiSuite

Al implementar una feature vertical (backend + frontend), seguir este orden estricto:

## Backend (Django)

1. `models.py` — modelos con BaseModel (UUID pk, company FK)
2. `python manage.py makemigrations <app>` — crear migración
3. `serializers.py` — DRF serializers
4. `services.py` — **TODA la lógica de negocio vive aquí**
5. `views.py` + `urls.py` — ViewSets delgados, URLs del app
6. `tests/` — pytest junto con código (≥80% coverage en services)

## Frontend (Angular)

7. `model.ts` — interfaces TypeScript strict
8. `service.ts` — servicios Angular (OnPush compatibles)
9. `components/` — Angular Material, `@if`/`@for`, variables `var(--sc-*)`
10. Rutas con lazy loading
11. Tests Jasmine/Karma (services =100%, components ≥70%)

## Validación final

12. **Validación 4x4** — checklist de UI/UX según `docs/base-reference/CHECKLIST-VALIDACION.md`

---

## Reglas no negociables

- Nunca `print()` en backend — usar `logger`.
- Nunca secrets hardcodeados — solo `settings.py` + variables de entorno.
- Nunca lógica en views/modelos — siempre en `services.py`.
- Nunca PrimeNG/Bootstrap/Tailwind — solo Angular Material.
- Nunca `*ngIf`/`*ngFor` — usar `@if`/`@for`.
- Nunca `any` en TypeScript — tipar estricto.
- Nunca suscripciones sin `takeUntilDestroyed()` o `async pipe`.
- Nunca hardcodear colores — usar variables CSS `var(--sc-*)`.
- Nunca olvidar `company_id` — todo modelo multi-tenant.
- Nunca `sai_key` sin `unique_together` con `company_id`.

---

**Lista completa de errores frecuentes:** `ERRORS.md`
