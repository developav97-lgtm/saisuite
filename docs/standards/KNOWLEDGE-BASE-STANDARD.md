# Estándar de Base de Conocimiento — SaiCloud AI

> **Fecha:** 2026-04-07
> **Aplica a:** Todos los archivos que alimentan el asistente de IA
> **Responsable:** Equipo SaiCloud — ValMen Tech

---

## 1. Visión General

La base de conocimiento (Knowledge Base, KB) es el conjunto de documentos que el
asistente de IA de SaiCloud usa para responder preguntas de los usuarios. Incluye:

- Manuales de usuario de cada módulo
- Norma colombiana (PUC, NIIF, tributaria)
- FAQ aprendidas del feedback positivo
- Guías y documentación personalizada

Los documentos se procesan automáticamente: se convierten a Markdown, se dividen en
fragmentos (~500 tokens), se generan embeddings vectoriales, y se almacenan en
PostgreSQL (pgvector) para búsqueda semántica.

---

## 2. Formatos de Archivo Aceptados

| Formato | Extensión | Conversión | Calidad |
|---------|-----------|------------|---------|
| **Markdown** | `.md` | Ninguna (directo) | Excelente |
| **Texto plano** | `.txt` | Ninguna (directo) | Buena |
| **Word** | `.docx` | Automática (mammoth) | Buena |
| **PDF** | `.pdf` | Automática (pdfplumber) | Variable (*) |

(*) Los PDF con mucho contenido visual (tablas complejas, diagramas, imágenes con texto)
pueden perder formato. Para estos casos, se recomienda convertir manualmente a Markdown.

**Formato preferido: Markdown (`.md`)**. Si tienes el documento en otro formato y puedes
exportar o escribir en Markdown, hazlo. La calidad del chunking y la búsqueda es mejor.

### Formatos NO soportados

- `.xlsx`, `.csv` — datos tabulares no se indexan como conocimiento
- `.pptx` — presentaciones no se procesan
- Imágenes (`.png`, `.jpg`) — no se indexan (no hay OCR en el pipeline)

---

## 3. Estructura de Carpetas

### Google Drive (Canal principal)

```
SaiCloud Knowledge Base/                   ← Carpeta raíz compartida
├── manuales/                              ← module: inferido del contenido
│   ├── MANUAL-PROYECTOS-SAICLOUD.md
│   ├── MANUAL-DASHBOARD-SAICLOUD.md
│   └── ...
├── norma-colombiana/                      ← module: contabilidad
│   ├── puc-plan-unico-cuentas.md
│   ├── niif-pymes-resumen.md
│   ├── impuestos-iva-retencion.md
│   └── obligaciones-tributarias.md
├── faq/                                   ← module: inferido del contenido
│   └── faq-proyectos-comunes.md
├── guias/                                 ← module: inferido del contenido
│   └── guia-onboarding-usuario.md
└── custom/                                ← module: general (a menos que se especifique)
    └── politicas-empresa-x.md
```

### Repositorio local (Canal CLI)

```
docs/
├── manuales/                              ← Ya existe, 7 manuales
│   ├── MANUAL-PROYECTOS-SAICLOUD.md
│   └── ...
└── knowledge/                             ← Nuevo
    ├── norma-colombiana/
    │   ├── puc-plan-unico-cuentas.md
    │   └── ...
    └── faq/
        └── (generadas automáticamente)
```

### Mapeo de carpeta → módulo y categoría

| Carpeta Drive | Módulo (inferido) | Categoría |
|---------------|-------------------|-----------|
| `manuales/` | Se lee del frontmatter o del nombre del archivo | `manual` |
| `norma-colombiana/` | `contabilidad` | `norma` |
| `faq/` | Se lee del frontmatter o se infiere del contenido | `faq` |
| `guias/` | Se lee del frontmatter o `general` | `guia` |
| `custom/` | `general` (a menos que tenga frontmatter) | `custom` |

---

## 4. Frontmatter YAML (Opcional pero Recomendado)

Si el archivo es Markdown, incluir metadata al inicio para mejor clasificación:

```yaml
---
module: proyectos
category: manual
version: "1.1"
last_updated: "2026-04-07"
title: "Manual de Proyectos SaiCloud"
description: "Guía completa del módulo de gestión de proyectos"
---

# Manual de Proyectos SaiCloud

## 1. Introducción
...
```

### Campos del frontmatter

| Campo | Requerido | Valores | Default |
|-------|-----------|---------|---------|
| `module` | No | `proyectos`, `dashboard`, `terceros`, `contabilidad`, `chat`, `general` | Inferido de carpeta |
| `category` | No | `manual`, `norma`, `faq`, `guia`, `custom` | Inferido de carpeta |
| `version` | No | Semver (`"1.0"`, `"2.1"`) | `"1.0"` |
| `last_updated` | No | Fecha ISO (`"2026-04-07"`) | Fecha de indexación |
| `title` | No | Texto libre | Primer `#` header del archivo |
| `description` | No | Texto libre | — |

Si no hay frontmatter, el sistema infiere `module` y `category` de la carpeta donde está
el archivo (ver tabla de mapeo arriba).

---

## 5. Reglas de Escritura para Archivos `.md`

### Estructura recomendada

```markdown
---
module: contabilidad
category: norma
---

# Título Principal del Documento

Párrafo introductorio breve.

## Sección 1: Nombre descriptivo

Contenido de la sección. Usar listas para conceptos:

- Concepto A: explicación
- Concepto B: explicación

### Subsección 1.1

Detalle adicional.

## Sección 2: Otra sección

...
```

### Reglas del chunker

El sistema divide el documento en fragmentos (chunks) respetando estas reglas:

1. **Cada sección `##` es un chunk** (si cabe en ~500 tokens)
2. Si una sección es **muy larga** (>500 tokens), se subdivide por párrafos
3. El **header de la sección se repite** en cada chunk para contexto
4. **Nunca se corta** en medio de una lista o tabla
5. Subsecciones `###` se mantienen dentro del chunk de su `##` padre

### Buenas prácticas

- Usar `##` para secciones principales (el chunker las respeta)
- Máximo ~3000 palabras por archivo (si es más largo, dividir en archivos)
- Usar listas con `-` para conceptos clave (mejor para búsqueda semántica)
- Incluir cifras y datos específicos (el IA los puede citar)
- Evitar imágenes embebidas (no se indexan)
- Usar tablas Markdown para datos tabulares (se indexan como texto)

### Malas prácticas

- Archivos de >5000 palabras sin secciones `##` → chunks de baja calidad
- Solo títulos sin contenido → chunks vacíos
- Contenido duplicado entre archivos → chunks redundantes
- Usar `#` (H1) para cada sección → el chunker espera `##`

---

## 6. Cómo Agregar o Actualizar Conocimiento

### Método 1: Google Drive (recomendado)

**Para agregar un documento nuevo:**

1. Ir a la carpeta compartida `SaiCloud Knowledge Base` en Google Drive
2. Navegar a la subcarpeta correspondiente (`manuales/`, `norma-colombiana/`, etc.)
3. Subir el archivo (`.md`, `.pdf`, `.docx` o `.txt`)
4. En ~5 minutos el sistema detecta el archivo nuevo, lo procesa y lo indexa
5. Verificar en SaiCloud → Admin → Base de Conocimiento IA que aparece

**Para actualizar un documento existente:**

1. Subir el archivo actualizado con **el mismo nombre** a la misma carpeta
2. El sistema detecta que el hash del archivo cambió
3. Borra los chunks anteriores y crea los nuevos (upsert)
4. El contenido actualizado está disponible en ~5 minutos

**Para eliminar un documento:**

1. Eliminar el archivo de Google Drive
2. Ir a SaiCloud → Admin → Base de Conocimiento IA
3. Buscar la fuente y click "Eliminar" (elimina la fuente y todos sus chunks)

### Método 2: Panel de Administración SaiCloud

1. Ir a SaiCloud → Administración → Base de Conocimiento IA
2. Click "Subir Documento"
3. Seleccionar el archivo
4. Elegir módulo y categoría (o dejar en "auto-detectar")
5. Click "Procesar"
6. El sistema muestra: "Documento indexado: X chunks, Y tokens"

### Método 3: Línea de Comandos (solo desarrollo)

```bash
# Indexar toda la carpeta docs/knowledge/ y docs/manuales/
python manage.py index_knowledge_base

# Indexar un archivo específico
python manage.py index_knowledge_base --file docs/knowledge/norma-colombiana/puc.md

# Re-indexar todo desde cero (borra todos los chunks primero)
python manage.py index_knowledge_base --reindex

# Solo archivos que cambiaron desde la última indexación
python manage.py index_knowledge_base --incremental
```

---

## 7. Cómo Exportar desde NotebookLM

Si tienes contenido en Google NotebookLM que quieres agregar a la KB:

1. Abrir el cuaderno en NotebookLM
2. Seleccionar la sección/fuente a exportar
3. Copiar el contenido relevante
4. Crear un nuevo archivo `.md` con:
   - Frontmatter YAML (module, category)
   - Contenido organizado con `##` headers
5. Subir a Google Drive (`SaiCloud Knowledge Base/norma-colombiana/`)

**Tip:** No copiar todo el cuaderno en un solo archivo. Dividir por temas:
- Un archivo para PUC
- Un archivo para NIIF PyMEs
- Un archivo para impuestos (IVA, retención, ICA)
- Un archivo para estados financieros

---

## 8. Conversión Automática de Formatos

### PDF → Markdown

El sistema usa `pdfplumber` para extraer texto de PDFs:

- **Texto simple:** se extrae correctamente
- **Tablas simples:** se convierten a texto tabulado
- **Tablas complejas/anidadas:** pueden perder formato → convertir manualmente
- **Imágenes con texto (escaneados):** NO se procesan (no hay OCR)
- **PDFs protegidos:** NO se pueden procesar

**Si el PDF tiene mala calidad de extracción:** convertir manualmente a `.md` y subir el
`.md` en su lugar.

### Word (.docx) → Markdown

El sistema usa `mammoth` para convertir Word:

- **Headers:** se convierten a `#`, `##`, `###`
- **Listas:** se convierten a `-` items
- **Negritas/cursivas:** se preservan como `**bold**` / `*italic*`
- **Tablas:** se convierten a tablas Markdown
- **Imágenes:** se ignoran (no se indexan)
- **Estilos personalizados:** pueden no traducirse correctamente

---

## 9. Verificación y Troubleshooting

### Verificar que un archivo se indexó correctamente

1. Ir a SaiCloud → Admin → Base de Conocimiento IA
2. Buscar el archivo por nombre en la lista de fuentes
3. Verificar: `chunks`, `tokens`, `último indexado`
4. Si no aparece → revisar logs de n8n o del endpoint

### Problemas comunes

| Problema | Causa | Solución |
|----------|-------|----------|
| Archivo no se detecta en Drive | n8n polling cada 5 min | Esperar o subir via panel admin |
| Chunks con contenido cortado | Archivo sin `##` headers | Agregar headers para dividir secciones |
| PDF con texto ilegible | PDF escaneado (imagen) | Convertir manualmente a `.md` |
| Documento duplicado | Mismo archivo subido 2 veces con nombres diferentes | Eliminar uno de los dos desde Admin |
| "0 chunks creados" | Archivo vacío o formato no soportado | Verificar contenido y extensión |
| Hash no cambió (no re-indexa) | Archivo subido es idéntico al anterior | Contenido no cambió; no hay nada que actualizar |

### Logs

```bash
# Ver logs de indexación en Django
docker logs saisuite-api | grep "knowledge_"

# Eventos loggeados:
# knowledge_ingest_started — archivo recibido
# knowledge_convert_complete — conversión a markdown
# knowledge_chunks_created — chunks guardados
# knowledge_ingest_complete — proceso terminado
# knowledge_ingest_error — error en el proceso
```

---

## 10. Límites y Consideraciones

| Concepto | Límite |
|----------|--------|
| Tamaño máximo por archivo | 10 MB |
| Máximo de archivos por empresa | 500 |
| Máximo de chunks totales | 50,000 |
| Tokens máximos por chunk | ~500 (target) |
| Dimensiones del embedding | 1536 (text-embedding-3-small) |
| Polling Google Drive | Cada 5 minutos |
| Costo de re-indexación completa (~200 chunks) | ~$0.01 (embeddings OpenAI) |

---

**Última actualización:** 2026-04-07
**Mantenido por:** Equipo Saicloud — ValMen Tech
