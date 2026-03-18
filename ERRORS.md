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

---

## [2026-03-17] ERROR: ModuleNotFoundError al hacer makemigrations — urls.py inexistente
**Categoría:** Django
**Síntoma:** `makemigrations` falla con `ModuleNotFoundError: No module named 'apps.proyectos.urls'` porque Django carga `config/urls.py` antes de correr migraciones.
**Causa:** `config/urls.py` ya tenía el `include('apps.proyectos.urls')` pero el archivo `urls.py` de la app aún no existía.
**Fix:** Crear `apps/proyectos/urls.py` con `urlpatterns = []` como stub ANTES de agregar el `include` en `config/urls.py`, o al menos antes de correr `makemigrations`.
**Prevención:** Al hacer scaffolding de una app nueva, siempre crear `urls.py` con stub vacío en el mismo paso que `__init__.py` y `apps.py`. Nunca agregar `include()` en `config/urls.py` apuntando a un módulo que no existe.
**Archivos afectados:** `apps/proyectos/urls.py`

---

## [2026-03-17] ERROR: User.all_objects AttributeError en services.py y tests
**Categoría:** Django
**Síntoma:** `AttributeError: type object 'User' has no attribute 'all_objects'`
**Causa:** El modelo `User` hereda de `AbstractBaseUser` + `PermissionsMixin` (modelos de Django), NO de `BaseModel`. Por lo tanto no tiene el manager `all_objects` que provee `BaseModel`.
**Fix:** Usar `User.objects` en lugar de `User.all_objects` en cualquier lugar que necesite acceder a usuarios. Ejemplo: `User.objects.get(id=gerente_id, company=company)`.
**Prevención:** `all_objects` solo existe en modelos que heredan de `BaseModel`. Para modelos de Django (User, Group, etc.) siempre usar `.objects`.
**Archivos afectados:** `apps/proyectos/services.py`, `apps/proyectos/tests/test_services.py`

---

## [2026-03-17] ERROR: TypeError float/Decimal en get_estado_financiero — defaults incorrectos
**Categoría:** Django
**Síntoma:** `TypeError: unsupported operand type(s) for /: 'float' and 'decimal.Decimal'` al llamar `ProyectoService.get_estado_financiero()`.
**Causa:** Los campos `porcentaje_administracion`, `porcentaje_imprevistos` y `porcentaje_utilidad` tenían `default=10.00` (float de Python). Cuando se crea un objeto sin guardar en BD y luego se llama el servicio, los valores son floats. Dividir `float / Decimal` falla en Python.
**Fix:** Cambiar defaults a `default=Decimal('10.00')` usando `from decimal import Decimal`. Esto garantiza que el valor sea Decimal desde la creación.
**Prevención:** Nunca usar literales float (`10.00`, `5.0`) como defaults en `DecimalField`. Siempre usar `Decimal('10.00')` importando `from decimal import Decimal`.
**Archivos afectados:** `apps/proyectos/models.py`

---

## [2026-03-17] ERROR: codigo requerido en ProyectoCreateUpdateSerializer
**Categoría:** Django
**Síntoma:** POST a `/api/v1/proyectos/` falla con `{'codigo': ['This field is required.']}` aunque el servicio auto-genera el código.
**Causa:** `codigo` es un `CharField(max_length=50)` sin `blank=True` en el modelo. DRF infiere que es requerido en el serializer write.
**Fix:** Declarar explícitamente en el serializer: `codigo = serializers.CharField(max_length=50, required=False, allow_blank=True)`.
**Prevención:** Al generar serializers write (CreateUpdate), siempre revisar qué campos son opcionales en la lógica de negocio aunque el modelo los tenga como no-blank. Declarar explícitamente con `required=False`.
**Archivos afectados:** `apps/proyectos/serializers.py`

---

## [2026-03-17] ERROR: Aislamiento multi-tenant falla con DRF / JWT — CompanyMiddleware no aplica
**Categoría:** Django
**Síntoma:** Tests de aislamiento multi-tenant fallan. Proyecto de empresa A es visible para empresa B.
**Causa:** `CompanyMiddleware` setea `_thread_locals.company` leyendo `request.user.company`. Pero con autenticación DRF/JWT, el middleware Django se ejecuta ANTES de que DRF autentique el token. En el momento del middleware, `request.user` es `AnonymousUser` → no se setea el company → `CompanyManager` filtra por `None` → retorna todo o nada incorrectamente.
**Fix:** En `ProyectoViewSet.get_queryset()`, pasar el company explícitamente: `ProyectoService.list_proyectos(company=self.request.user.company)`. El service usa `Proyecto.all_objects` (sin filtro de manager) y aplica `filter(company=company)` manualmente.
**Prevención:** Para APIs DRF con JWT, NUNCA confiar en `CompanyManager` thread-local para filtrar QuerySets en views. Siempre pasar `company` explícitamente desde la view usando `self.request.user.company` (disponible después de que DRF autentica). Solo usar `Proyecto.objects` (manager con thread-local) en contextos con sesiones Django normales.
**Archivos afectados:** `apps/proyectos/services.py`, `apps/proyectos/views.py`

---

## [2026-03-17] ERROR: PrimeNG 21 — primeng/dropdown y primeng/tabview no existen
**Categoría:** Angular
**Síntoma:** Build Angular falla: `Could not resolve 'primeng/dropdown'` y `Could not resolve 'primeng/tabview'`.
**Causa:** PrimeNG 21.x eliminó `primeng/dropdown` (renombrado a `primeng/select`) y `primeng/tabview` (reemplazado por nueva API en `primeng/tabs`).
**Fix:**
- `import { DropdownModule } from 'primeng/dropdown'` → `import { SelectModule } from 'primeng/select'`
- Template: `<p-dropdown>` → `<p-select>`
- `import { TabViewModule } from 'primeng/tabview'` → `import { TabsModule } from 'primeng/tabs'`
- Template: Reemplazar `<p-tabview>/<p-tabpanel>` por nueva API: `<p-tabs><p-tablist><p-tab value="x">` / `<p-tabpanels><p-tabpanel value="x">`
**Prevención:** Al usar PrimeNG, verificar la versión instalada antes de importar módulos. PrimeNG 19+ usa nuevos nombres. En este proyecto usar SIEMPRE: `SelectModule` (no `DropdownModule`), `TabsModule` (no `TabViewModule`).
**Archivos afectados:** `proyecto-list.component.ts`, `proyecto-form.component.ts`, `proyecto-detail.component.ts/html`

---

## [2026-03-17] ERROR: PrimeNG 21.1.3 incompatible con Angular 20.3.x — ChangeDetectionStrategy.Eager
**Categoría:** Angular
**Síntoma:** Build Angular falla con `Cannot create property 'message' on string '...primeng-table.mjs: Unsupported change detection strategy'`.
**Causa:** PrimeNG 21.1.3 internamente usa `ChangeDetectionStrategy.Eager` (valor 2) en sus componentes de tabla. Esta estrategia fue introducida en una versión de Angular posterior a 20.3.17. Angular 20.3.x solo conoce `Default` (0) y `OnPush` (1).
**Fix:** Downgrade de PrimeNG a `20.5.0-lts` que es la versión LTS compatible con Angular 20.x: `npm install primeng@20.5.0-lts --legacy-peer-deps`. También instalar `@angular/animations` que es peerDependency de PrimeNG 20.
**Prevención:** PrimeNG versioning sigue Angular major versions: PrimeNG 20.x = Angular 20.x. Nunca instalar PrimeNG con major version mayor al major de Angular instalado. Verificar compatibilidad antes de actualizar PrimeNG.
**Archivos afectados:** `package.json` (frontend)

---

## [2026-03-17] ERROR: TS7053 strict mode — indexar Record con tipo 'any' desde p-table let-variable
**Categoría:** Angular
**Síntoma:** Build falla con `TS7053: Element implicitly has an 'any' type because expression of type 'any' can't be used to index type 'Record<EstadoProyecto, string>'` en template `[value]="ESTADO_LABELS[proyecto.estado]"`.
**Causa:** La variable `proyecto` declarada con `let-proyecto` en `<p-table>` tiene tipo inferido `any`. Con strict mode, `any` no puede indexar un `Record<EstadoProyecto, string>` tipado.
**Fix:** Crear métodos helper tipados en el componente:
```typescript
estadoLabel(estado: string): string {
  return ESTADO_LABELS[estado as EstadoProyecto] ?? estado;
}
estadoSeverity(estado: string): 'success' | 'info' | 'warn' | 'danger' | 'secondary' | 'contrast' {
  return ESTADO_SEVERITY[estado as EstadoProyecto] ?? 'secondary';
}
```
Y usar en template: `[value]="estadoLabel(proyecto.estado)"`.
**Prevención:** Cuando `let-variable` de PrimeNG sea `any`, no indexar Records tipados directamente en template. Usar métodos helper que acepten `string` y hagan cast interno.
**Archivos afectados:** `proyecto-list.component.ts/html`