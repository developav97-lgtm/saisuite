---
paths:
  - "backend/**/*.py"
---

# Reglas Backend Django — Se cargan SOLO al trabajar en archivos Python del backend

## Lógica de negocio
- TODA la lógica va en `services.py`. Nunca en views, nunca en modelos.
- Views solo orquestan: request → service → response.
- Serializers solo transforman datos. Sin cálculos, sin APIs, sin side effects.

## Modelos
- Heredar BaseModel (UUID pk, company FK, timestamps).
- Multi-tenant: company_id en TODAS las tablas de negocio.
- Dinero: `NUMERIC(15,2)`. Nunca float.
- Firebird: campo `sai_key` + `unique_together: (company, sai_key)`.
- Migraciones: solo `python manage.py makemigrations`. Nunca SQL manual.

## Código
- Logging: `logger.info("evento", extra={"key": "value"})`. Nunca `print()`.
- Nunca hardcodear secrets → variables de entorno o AWS Secrets Manager.
- `select_related` / `prefetch_related` donde aplique (evitar N+1).
- `@transaction.atomic` en operaciones críticas.

## Tests
- Tests JUNTO con código, nunca después.
- Cobertura: services ≥80%, auth/permisos/licencias =100%.
- Comando: `pytest apps/{modulo}/tests/ -v --cov=apps.{modulo}`

## Orden de generación
1. models.py → 2. makemigrations → 3. serializers.py → 4. services.py → 5. views.py + urls.py → 6. tests/

## Docs de referencia
- Modelos: `docs/base-reference/Esquema_BD_SaiSuite_v1.docx`
- Código: `docs/base-reference/Estandares_Codigo_SaiSuite_v1.docx`
