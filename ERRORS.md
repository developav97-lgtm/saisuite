# ERRORS.md — Registro de Errores Resueltos
# SaiSuite | ValMen Tech
#
# INSTRUCCIONES PARA CLAUDE:
# - Leer este archivo al inicio de cada sesión.
# - Cuando resuelvas un error nuevo, agregarlo aquí ANTES de continuar.
# - El objetivo es que cada error se resuelva UNA SOLA VEZ en todo el proyecto.
# - Formato: ver sección de ejemplo al final.

---

## Cómo usar este archivo

Este archivo es la memoria de errores del proyecto. Cada vez que se resuelve
un problema técnico significativo, se registra aquí con su causa y fix para
que no vuelva a ocurrir en sesiones futuras.

**Claude debe:**
1. Leerlo al inicio de cada sesión
2. Consultarlo antes de solucionar cualquier error (puede que ya esté resuelto)
3. Agregarlo al final cuando resuelva algo nuevo

---

## Índice de categorías

- [Django / Backend](#django--backend)
- [Angular / Frontend](#angular--frontend)
- [Base de datos / Migraciones](#base-de-datos--migraciones)
- [Sincronización Firebird / SQS](#sincronización-firebird--sqs)
- [AWS / Infraestructura](#aws--infraestructura)
- [Tests](#tests)

---

## Django / Backend

*— Sin entradas aún. Se irán agregando durante el desarrollo. —*

---

## Angular / Frontend

*— Sin entradas aún. —*

---

## Base de datos / Migraciones

*— Sin entradas aún. —*

---

## Sincronización Firebird / SQS

*— Sin entradas aún. —*

---

## AWS / Infraestructura

*— Sin entradas aún. —*

---

## Tests

*— Sin entradas aún. —*

---

## Formato de entrada (copiar y completar)

```
## [YYYY-MM-DD] ERROR: [descripción corta en una línea]
**Categoría:** Django | Angular | BD | Sync | AWS | Tests
**Síntoma:** Qué mensaje de error aparecía o qué comportamiento incorrecto se observó.
**Causa:** Por qué ocurría el error. La causa raíz, no solo el síntoma.
**Fix:** Código o pasos exactos para resolverlo.
**Prevención:** Qué regla o patrón evita que vuelva a ocurrir.
**Archivos afectados:** Lista de archivos que se modificaron.
```

---

*Última actualización: Marzo 2026*

---

## [2026-03-09] ERROR: AUTH_USER_MODEL refers to model 'users.User' that has not been installed
**Categoría:** Django
**Síntoma:** Django no arranca. Error `ImproperlyConfigured: AUTH_USER_MODEL refers to model 'users.User' that has not been installed`.
**Causa:** `settings.py` apunta a `AUTH_USER_MODEL = 'users.User'` pero `apps/users/models.py` estaba vacío — el modelo no existía aún.
**Fix:** Crear el modelo `User` en `apps/users/models.py` heredando de `AbstractBaseUser` y `PermissionsMixin`. También requiere que `apps/companies/models.py` tenga el modelo `Company` porque `User` tiene FK a `Company`.
**Prevención:** Siempre generar los modelos `Company` y `User` antes de hacer el primer `docker-compose up` del backend. Orden obligatorio: Company → User → migraciones → arranque.
**Archivos afectados:** `apps/users/models.py`, `apps/companies/models.py`

---

## [2026-03-09] ERROR: No module named 'apps.users.urls.auth'; 'apps.users.urls' is not a package
**Categoría:** Django
**Síntoma:** Django no arranca al correr makemigrations. Error `ModuleNotFoundError: No module named 'apps.users.urls.auth'`.
**Causa:** `config/urls.py` tenía `include('apps.users.urls.auth')` tratando `urls.py` como si fuera una carpeta con subpaquetes. Un archivo `.py` no puede tener submodules.
**Fix:** Cambiar a `include('apps.users.urls')` en `config/urls.py`. Si se necesitan URLs separadas por funcionalidad, crear una carpeta `urls/` con `__init__.py` dentro de la app.
**Prevención:** Al generar `config/urls.py`, usar siempre `include('apps.<nombre>.urls')` apuntando al archivo `urls.py` directo de la app.
**Archivos afectados:** `config/urls.py`

---

## [2026-03-09] ERROR: URLconf does not appear to have any patterns — module not iterable
**Categoría:** Django
**Síntoma:** `ImproperlyConfigured: The included URLconf does not appear to have any patterns. 'module' object is not iterable`.
**Causa:** Los archivos `urls.py` de las apps tenían texto plano como comentario (`# users URLs`) en lugar de código Python válido con `urlpatterns = []`. Django los importó pero no encontró la lista `urlpatterns`.
**Fix:** Todo `urls.py` debe tener mínimo `from django.urls import path` y `urlpatterns = []` aunque esté vacío.
**Prevención:** Al generar `urls.py` placeholder para una app nueva, siempre incluir `urlpatterns = []` explícito. Nunca dejar solo un comentario.
**Archivos afectados:** `apps/users/urls.py`, `apps/companies/urls.py`, `apps/sync_agent/urls.py`, `apps/integrations/urls.py`

---

## [2026-03-09] ERROR: makemigrations no detecta cambios — falta carpeta migrations/
**Categoría:** Django
**Síntoma:** `makemigrations` dice "No changes detected" aunque los modelos son nuevos.
**Causa:** Las apps no tenían la carpeta `migrations/` con su `__init__.py`. Django requiere esa carpeta para saber que una app puede tener migraciones.
**Fix:** Crear `migrations/__init__.py` en cada app: `mkdir -p apps/<nombre>/migrations && touch apps/<nombre>/migrations/__init__.py`
**Prevención:** Al generar la estructura base de cualquier app nueva, siempre incluir la carpeta `migrations/` con su `__init__.py`. Nunca omitirla aunque los modelos estén vacíos.
**Archivos afectados:** `apps/companies/migrations/__init__.py`, `apps/users/migrations/__init__.py`, `apps/sync_agent/migrations/__init__.py`, `apps/integrations/migrations/__init__.py`