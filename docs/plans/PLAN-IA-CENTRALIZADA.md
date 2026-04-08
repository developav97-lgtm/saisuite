# PLAN: IA Centralizada — SaiCloud Assistant

> **Fecha:** 2026-04-07  
> **Módulo:** Chat / IA / Todos  
> **Modelo sugerido:** Opus (arquitectura) → Sonnet (implementación)  
> **Estimación total:** 70-90h (3 sprints)  
> **Estado:** 🟡 Planificado

---

## 1. VISIÓN

Transformar el chat con IA de un asistente financiero aislado (CFO Virtual) a un **asistente centralizado de toda la plataforma SaiCloud** que:

- Lee datos de TODOS los módulos (solo lectura — PROHIBIDO escritura)
- Conoce los manuales de usuario y guía a los usuarios en cada proceso
- Tiene contexto de la norma colombiana (via NotebookLM)
- Se adapta al módulo donde está el usuario (routing por contexto)
- Aprende de interacciones útiles para mejorar respuestas futuras
- Optimiza costos con el modelo más eficiente de OpenAI

---

## 2. ARQUITECTURA DE ALTO NIVEL

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│                                                          │
│  ┌────────────┐    ┌──────────────────────────────────┐  │
│  │ Cualquier  │    │       Chat Panel                  │  │
│  │ módulo     │───►│  [🤖 SaiCloud AI — Proyectos]   │  │
│  │            │    │  Indicador de contexto activo     │  │
│  │ Proyectos  │    │  Conversación siempre fijada      │  │
│  │ Dashboard  │    │  arriba en lista de chats         │  │
│  │ Terceros   │    └──────────┬───────────────────────┘  │
│  │ CRM (fut.) │               │                          │
│  └────────────┘               │ POST /mensajes/enviar/   │
│                               │ + module_context signal  │
└───────────────────────────────┼──────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────┐
│                    BACKEND                                │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │               AI Orchestrator Service                │  │
│  │                                                      │  │
│  │  1. Detectar módulo (bot_context)                    │  │
│  │  2. Recolectar contexto (DataCollectors)             │  │
│  │  3. Buscar conocimiento relevante (RAG)              │  │
│  │  4. Construir prompt optimizado                      │  │
│  │  5. Llamar OpenAI                                    │  │
│  │  6. Registrar feedback + uso                         │  │
│  └──────┬──────────┬───────────┬───────────────────────┘  │
│         │          │           │                           │
│  ┌──────▼───┐ ┌────▼─────┐ ┌──▼─────────────┐            │
│  │  Data    │ │   RAG    │ │  Knowledge     │            │
│  │Collectors│ │  Engine  │ │  Base (pgvector)│            │
│  │          │ │          │ │                  │            │
│  │Dashboard │ │ Query    │ │ Manuales .md    │            │
│  │Proyectos │ │ embedder │ │ Norma colombiana│            │
│  │Terceros  │ │ Retriever│ │ FAQ aprendidas  │            │
│  │Contabil. │ │ Ranker   │ │ Interacciones   │            │
│  └──────────┘ └──────────┘ └─────────────────┘            │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           AI Usage + Learning Service                │  │
│  │  - Cuota por empresa/mes                             │  │
│  │  - Feedback thumbs up/down por mensaje               │  │
│  │  - Cache de respuestas frecuentes (Redis)            │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

---

## 3. DECISIONES TÉCNICAS

### 3.1 Base de datos vectorial: PostgreSQL + pgvector

**Decisión:** Usar `pgvector` (extensión de PostgreSQL), no un servicio externo.

**Razón:**
- Ya tenemos PostgreSQL 16 en el stack (Docker local en fase de pruebas; misma extensión aplica cuando se despliegue a producción)
- pgvector es gratuito, sin servicio adicional
- Para <50k documentos es más que suficiente
- Sin latencia de red extra (misma DB)
- Alternativas descartadas:

| Servicio | Costo/mes | Por qué no |
|----------|-----------|------------|
| Pinecone | $70+ (Starter) | Costoso para nuestro volumen |
| Supabase Vector | $25+ (Pro) | Otra DB más que mantener |
| Weaviate Cloud | $25+ | Complejidad innecesaria |
| Cloudflare Vectorize | $0.04/M queries | No tiene SDK Python maduro |
| **pgvector** | **$0 (ya pagamos PG)** | **✅ Seleccionado** |

**Modelo de embeddings:** `text-embedding-3-small` de OpenAI
- $0.02 / 1M tokens (el más barato de OpenAI)
- 1536 dimensiones (buen balance calidad/costo)
- Suficiente para búsqueda semántica en español

### 3.2 Modelo LLM: gpt-4o-mini (confirmar)

| Modelo | Costo input/1M | Costo output/1M | Calidad | Decisión |
|--------|----------------|-----------------|---------|----------|
| gpt-4o-mini | $0.15 | $0.60 | Buena | ✅ Actual |
| gpt-4.1-mini | $0.40 | $1.60 | Mejor | Considerar si calidad no basta |
| gpt-4.1-nano | $0.10 | $0.40 | Básica | Para FAQ simples (cache hits) |
| gpt-4o | $2.50 | $10.00 | Excelente | Solo si necesario |

**Estrategia:** gpt-4o-mini por defecto. Si la pregunta es compleja (detectada por tokens/longitud), escalar a gpt-4.1-mini. Cache Redis para respuestas frecuentes.

### 3.3 Knowledge Base: Pipeline Dinámico de Actualización

**Decisión:** Pipeline semi-automático con 3 canales de ingesta + conversión automática de formatos.

**Problema original:**
- NotebookLM no tiene API pública — no se puede conectar en tiempo real
- Exportar manualmente y re-indexar cada vez es tedioso y propenso a errores
- Necesitamos que actualizar la base de conocimiento sea fácil y casi automático
- Los archivos fuente pueden venir en PDF, Word o Markdown

**Solución — 3 canales de ingesta:**

#### Canal 1: Google Drive + n8n (recomendado — usuarios no técnicos)

```
┌──────────────────┐       ┌───────────────────┐       ┌────────────────────────┐
│  Google Drive     │       │      n8n           │       │    Django Backend       │
│                   │       │                    │       │                         │
│ SaiCloud KB/      │──────►│ Google Drive       │──────►│ POST /api/v1/ai/       │
│  ├── manuales/    │trigger│ Trigger (polling   │webhook│   knowledge/ingest/    │
│  ├── norma/       │       │ cada 5 min)        │       │                         │
│  ├── faq/         │       │                    │       │ 1. Descarga archivo     │
│  └── custom/      │       │ ► Download file    │       │ 2. Convierte a .md      │
│                   │       │ ► POST webhook     │       │ 3. Chunking (~500 tok)  │
│ Drop .md/.pdf/.docx       │ ► Log resultado    │       │ 4. Embeddings batch     │
└──────────────────┘       └───────────────────┘       │ 5. Upsert pgvector      │
                                                        └────────────────────────┘
```

- Carpeta compartida en Google Drive: `SaiCloud Knowledge Base/`
- Subcarpetas por categoría: `manuales/`, `norma-colombiana/`, `faq/`, `custom/`
- n8n Google Drive Trigger detecta archivos nuevos o modificados
- n8n descarga el archivo y llama al endpoint Django con el contenido + metadata
- Django procesa, convierte, chunka, genera embeddings, almacena en pgvector
- Tiempo de propagación: ~5 minutos desde el upload

#### Canal 2: Panel de Administración SaiCloud (usuarios técnicos)

```
SaiCloud → Admin → Base de Conocimiento IA → Subir Documento
  - Seleccionar archivo (.md, .pdf, .docx, .txt)
  - Elegir módulo (proyectos, dashboard, terceros, contabilidad, general)
  - Elegir categoría (manual, norma, faq, guía)
  - Procesamiento inmediato con feedback visual
```

- Endpoint: `POST /api/v1/ai/knowledge/upload/`
- Solo accesible para `company_admin` y `valmen_admin`
- Feedback inmediato: "Documento indexado: 12 chunks, 3400 tokens"

#### Canal 3: Management command (desarrollo/migración)

```bash
# Indexar toda la carpeta docs/knowledge/ y docs/manuales/
python manage.py index_knowledge_base

# Indexar un archivo específico
python manage.py index_knowledge_base --file docs/knowledge/norma-colombiana/puc.md

# Re-indexar todo (borra chunks existentes y re-crea)
python manage.py index_knowledge_base --reindex

# Solo archivos modificados desde última indexación
python manage.py index_knowledge_base --incremental
```

#### Pipeline de conversión automática

```python
# apps/ai/converters.py — Convierte cualquier formato a Markdown

Formatos soportados:
  .md   → se usa directamente (sin conversión)
  .txt  → se usa directamente (sin conversión)
  .pdf  → pdfplumber extrae texto + detecta headers por tamaño de fuente
  .docx → mammoth convierte a markdown preservando headers y listas

Dependencias nuevas en requirements.txt:
  mammoth        # .docx → markdown (ligero, sin pandoc)
  pdfplumber     # .pdf → texto con metadata de layout
  markdownify    # HTML → markdown (backup para mammoth)
```

#### Estándar de archivos para la Knowledge Base

> **Documento completo:** `docs/standards/KNOWLEDGE-BASE-STANDARD.md`

Reglas clave:
- **Formato preferido:** Markdown (.md) — se indexa sin conversión
- **Headers `##`** dividen las secciones — el chunker los respeta
- **Máximo ~3000 palabras por archivo** — para chunking eficiente
- **Metadata YAML frontmatter** en cada archivo:
  ```yaml
  ---
  module: proyectos          # proyectos|dashboard|terceros|contabilidad|general
  category: manual           # manual|norma|faq|guia
  version: "1.0"
  last_updated: "2026-04-07"
  ---
  ```
- Si el archivo es PDF o Word, la metadata se infiere del nombre de carpeta
- Re-subir un archivo con el mismo nombre **actualiza** los chunks existentes (upsert, no duplica)

#### Modelo de datos: KnowledgeSource (nuevo)

```python
class KnowledgeSource(BaseModel):
    """Registro de cada archivo fuente indexado en la knowledge base."""
    file_name = models.CharField(max_length=255)
    source_channel = models.CharField(max_length=20)  # 'drive', 'upload', 'cli'
    original_format = models.CharField(max_length=10)  # 'md', 'pdf', 'docx', 'txt'
    module = models.CharField(max_length=50)
    category = models.CharField(max_length=30)
    file_hash = models.CharField(max_length=64)  # SHA-256 para detectar cambios
    chunk_count = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    last_indexed_at = models.DateTimeField()
    drive_file_id = models.CharField(max_length=255, blank=True)  # Google Drive ID
    metadata = models.JSONField(default=dict)

    class Meta:
        unique_together = ('company', 'file_name', 'source_channel')
```

#### n8n workflow: `knowledge-base-watcher.json`

```
Trigger: Google Drive Trigger
  - Folder ID: [carpeta "SaiCloud Knowledge Base"]
  - Poll interval: 5 min
  - Event: File created or modified

Steps:
  1. Download file from Google Drive
  2. Extract metadata (folder → module, name, MIME type)
  3. HTTP POST to Django: /api/v1/ai/knowledge/ingest/
     Body: { file: binary, file_name, module, category, drive_file_id }
  4. IF success → log, IF error → notify admin (email/slack)
```

### 3.4 Seguridad: Solo lectura ABSOLUTA

```python
# REGLA INQUEBRANTABLE: El AI Orchestrator NUNCA recibe funciones que modifiquen datos.
# Los DataCollectors solo ejecutan SELECT / .filter() / .values()
# Ningún collector tiene acceso a .create(), .update(), .delete(), .save()
```

---

## 4. SPRINT 1 — Infraestructura IA + RAG + Pipeline Knowledge Base (28-35h)

### Fase 1.1: pgvector + Knowledge Base (8-10h)

**Backend Agent:**

```
Archivos a crear/modificar:
  backend/apps/ai/                       # Nueva app Django
  backend/apps/ai/__init__.py
  backend/apps/ai/apps.py
  backend/apps/ai/models.py              # KnowledgeChunk, KnowledgeSource, AIFeedback
  backend/apps/ai/services.py            # EmbeddingService, RAGService, KnowledgeIngestionService, AIOrchestrator
  backend/apps/ai/converters.py          # DocumentConverter (.pdf/.docx/.md → markdown)
  backend/apps/ai/collectors.py          # DataCollectors por módulo
  backend/apps/ai/views.py               # Endpoints ingesta + feedback
  backend/apps/ai/urls.py                # Rutas AI
  backend/apps/ai/management/commands/
    index_knowledge_base.py              # Comando para indexar manuales
  backend/config/settings/base.py        # agregar 'apps.ai' a INSTALLED_APPS
  requirements.txt                       # agregar pgvector, tiktoken, mammoth, pdfplumber, markdownify
  docs/knowledge/                        # Directorio para knowledge base local
  docs/standards/KNOWLEDGE-BASE-STANDARD.md  # Estándar de actualización KB
  n8n/workflows/knowledge-base-watcher.json  # Workflow Google Drive → Django
```

**Modelos:**

```python
# apps/ai/models.py

class KnowledgeChunk(BaseModel):
    """Fragmento de conocimiento indexado con embedding vectorial."""
    source_type = models.CharField(max_length=30)
    # Valores: 'manual', 'norma', 'faq_aprendida', 'help_text'
    source_file = models.CharField(max_length=255)
    # Ej: 'docs/manuales/MANUAL-PROYECTOS-SAICLOUD.md'
    module = models.CharField(max_length=50)
    # Ej: 'proyectos', 'dashboard', 'chat', 'general'
    title = models.CharField(max_length=255)
    content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    embedding = VectorField(dimensions=1536)
    # pgvector: vector(1536) para text-embedding-3-small
    metadata = models.JSONField(default=dict)
    # Ej: {'section': 'Fases', 'subsection': 'Crear fase'}

    class Meta:
        indexes = [
            # HNSW index para búsqueda rápida de vecinos
            HnswIndex(
                name='kb_embedding_idx',
                fields=['embedding'],
                m=16, ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]


class KnowledgeSource(BaseModel):
    """Registro de cada archivo fuente indexado en la knowledge base."""
    file_name = models.CharField(max_length=255)
    source_channel = models.CharField(max_length=20)
    # Valores: 'drive', 'upload', 'cli'
    original_format = models.CharField(max_length=10)
    # Valores: 'md', 'pdf', 'docx', 'txt'
    module = models.CharField(max_length=50)
    category = models.CharField(max_length=30)
    # Valores: 'manual', 'norma', 'faq', 'guia', 'custom'
    file_hash = models.CharField(max_length=64)
    # SHA-256 para detectar cambios y evitar re-procesar
    chunk_count = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    last_indexed_at = models.DateTimeField()
    drive_file_id = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        unique_together = ('company', 'file_name', 'source_channel')


class AIFeedback(BaseModel):
    """Feedback del usuario sobre respuestas de IA."""
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    mensaje = models.ForeignKey('chat.Mensaje', on_delete=models.CASCADE)
    rating = models.SmallIntegerField()  # 1 = thumbs up, -1 = thumbs down
    module_context = models.CharField(max_length=50)
    question = models.TextField()
    answer = models.TextField()

    class Meta:
        unique_together = ('user', 'mensaje')
```

**Servicio de Embeddings:**

```python
# apps/ai/services.py

class EmbeddingService:
    """Genera embeddings usando OpenAI text-embedding-3-small."""

    MODEL = 'text-embedding-3-small'
    DIMENSIONS = 1536

    @staticmethod
    def embed(text: str) -> list[float]:
        """Genera embedding para un texto."""

    @staticmethod
    def embed_batch(texts: list[str]) -> list[list[float]]:
        """Genera embeddings en batch (max 2048 por request)."""


class RAGService:
    """Retrieval-Augmented Generation — busca conocimiento relevante."""

    @staticmethod
    def search(query: str, module: str = '', top_k: int = 5) -> list[dict]:
        """
        Busca fragmentos relevantes en la knowledge base.
        1. Genera embedding de la query
        2. Busca vecinos más cercanos en pgvector (cosine similarity)
        3. Filtra por módulo si se especifica
        4. Retorna top_k resultados con score
        """

    @staticmethod
    def search_cached_answer(query: str, module: str) -> str | None:
        """Busca en Redis si hay una respuesta cacheada para query similar."""
```

### Fase 1.2: Data Collectors — Solo lectura (6-8h)

**Backend Agent:**

```python
# apps/ai/collectors.py

class BaseDataCollector:
    """Base class para recolectores de datos por módulo. SOLO LECTURA."""

    def collect(self, company, query: str, user=None) -> str:
        """Retorna contexto como string formateado para el prompt."""
        raise NotImplementedError


class DashboardCollector(BaseDataCollector):
    """
    Recolecta datos financieros/contables.
    - Resumen por título contable (clase 1-6)
    - Desglose mensual del año
    - Top 10 cuentas por movimiento
    - Comparativo año anterior
    - Saldos por tercero (top 20)
    """

class ProyectosCollector(BaseDataCollector):
    """
    Recolecta datos de proyectos y tareas.
    - Lista de proyectos activos con % avance
    - Tareas pendientes/bloqueadas del usuario
    - Hitos próximos (30 días)
    - Horas registradas vs estimadas
    - Presupuesto ejecutado vs aprobado
    - Fases y su estado
    - Dependencias críticas
    """

class TercerosCollector(BaseDataCollector):
    """
    Recolecta datos de terceros (clientes/proveedores).
    - Lista de terceros con tipo y estado
    - Cartera pendiente por tercero
    - Último movimiento contable
    """

class ContabilidadCollector(BaseDataCollector):
    """
    Recolecta datos contables detallados.
    - Balance de prueba
    - Movimientos por cuenta PUC (rango)
    - Movimientos por tercero
    - Estado de resultados
    """

class GeneralCollector(BaseDataCollector):
    """
    Recolecta datos generales del sistema.
    - Info de la empresa
    - Módulos activos
    - Usuarios activos
    - Estado de sincronización Saiopen
    """

# Registry de collectors
COLLECTORS: dict[str, BaseDataCollector] = {
    'dashboard': DashboardCollector(),
    'proyectos': ProyectosCollector(),
    'terceros': TercerosCollector(),
    'contabilidad': ContabilidadCollector(),
    'general': GeneralCollector(),
}
```

### Fase 1.3: Pipeline de conversión + Ingesta (5-7h)

```python
# apps/ai/converters.py

class DocumentConverter:
    """Convierte documentos a Markdown para indexación RAG."""

    SUPPORTED = {'.md', '.txt', '.pdf', '.docx'}

    @staticmethod
    def convert(file_path: str) -> str:
        """Auto-detecta formato y convierte a markdown."""
        # .md/.txt → leer directamente
        # .pdf → pdfplumber: extraer texto + detectar headers
        # .docx → mammoth: convertir a markdown preservando estructura

    @staticmethod
    def extract_frontmatter(content: str) -> tuple[dict, str]:
        """Extrae metadata YAML del inicio del archivo si existe."""
```

```python
# apps/ai/services.py — KnowledgeIngestionService

class KnowledgeIngestionService:
    """Procesa archivos nuevos/actualizados para la knowledge base."""

    @staticmethod
    def ingest(file_content: bytes, file_name: str, module: str,
               category: str, source_channel: str, drive_file_id: str = '') -> dict:
        """
        Pipeline completo:
        1. Calcular hash del archivo (SHA-256)
        2. Verificar si ya existe en KnowledgeSource (upsert)
        3. Convertir a markdown (DocumentConverter)
        4. Extraer frontmatter si existe
        5. Dividir en chunks de ~500 tokens (respetar ## headers)
        6. Generar embeddings (EmbeddingService.embed_batch)
        7. Borrar chunks anteriores del mismo source
        8. Guardar chunks nuevos en KnowledgeChunk
        9. Actualizar/crear KnowledgeSource
        Retorna: {chunks_created, total_tokens, file_name, status}
        """

    @staticmethod
    def _chunk_markdown(content: str, max_tokens: int = 500) -> list[dict]:
        """
        Divide markdown en chunks respetando:
        - Secciones ## (nunca corta en medio de una sección)
        - Si una sección > max_tokens → subdivide por párrafos
        - Mantiene el header de la sección en cada chunk
        Retorna: [{title, content, token_count}]
        """
```

```python
# apps/ai/management/commands/index_knowledge_base.py

# 1. Lee todos los archivos en docs/manuales/ y docs/knowledge/
# 2. Para cada archivo: llama KnowledgeIngestionService.ingest()
# 3. Soporta formatos: .md, .txt, .pdf, .docx
# 4. Flags:
#    --reindex    → borra TODOS los chunks y re-indexa desde cero
#    --file PATH  → indexa un solo archivo
#    --incremental → solo archivos con hash diferente al registrado
# 5. Output: tabla resumen con archivos procesados, chunks, tokens
```

### Fase 1.4: Endpoints de ingesta + n8n workflow (3-4h)

```python
# apps/ai/views.py

# POST /api/v1/ai/knowledge/ingest/  (llamado por n8n)
#   - Recibe: file (binary), file_name, module, category, drive_file_id
#   - Auth: API key del backend (N8N_WEBHOOK_SECRET)
#   - Llama KnowledgeIngestionService.ingest()
#   - Retorna: {status, chunks_created, total_tokens}

# POST /api/v1/ai/knowledge/upload/  (llamado desde panel admin)
#   - Recibe: file (multipart), module, category
#   - Auth: JWT (company_admin o valmen_admin)
#   - Misma lógica que ingest pero con auth JWT
#   - Retorna: {status, chunks_created, total_tokens}

# GET  /api/v1/ai/knowledge/sources/  (listar fuentes indexadas)
#   - Retorna lista de KnowledgeSource con chunk_count, total_tokens, last_indexed_at
#   - Auth: JWT (company_admin o valmen_admin)

# DELETE /api/v1/ai/knowledge/sources/{id}/  (eliminar fuente y sus chunks)
```

```
# n8n/workflows/knowledge-base-watcher.json

Workflow:
  Trigger: Google Drive Trigger
    - Carpeta: "SaiCloud Knowledge Base" (compartida con el equipo)
    - Poll: cada 5 minutos
    - Evento: archivo creado o modificado

  Node 1: Download File
    - Descarga el archivo del Drive

  Node 2: Extract Metadata
    - folder_name → module (manuales/ → general, norma/ → contabilidad)
    - MIME type → original_format
    - file_id → drive_file_id

  Node 3: HTTP POST → Django
    - URL: http://backend:8000/api/v1/ai/knowledge/ingest/
    - Body: multipart con file + metadata
    - Auth: header X-N8N-Secret

  Node 4: Error Handler
    - Si falla → log error + notificación
```

### Fase 1.5: Migración pgvector (1h)

```bash
# En docker-compose.yml cambiar imagen de db:
#   postgres:16-alpine → pgvector/pgvector:pg16
# Migración Django: CREATE EXTENSION IF NOT EXISTS vector;
```

### Fase 1.6: Estándar de Knowledge Base (1-2h)

Crear `docs/standards/KNOWLEDGE-BASE-STANDARD.md` con:
- Formatos aceptados y cuál es el preferido
- Estructura de carpetas en Google Drive
- Cómo nombrar archivos
- Frontmatter YAML estándar
- Guía paso a paso para cada canal de ingesta
- Troubleshooting (archivo no se indexa, chunks incorrectos, etc.)

---

## 5. SPRINT 2 — AI Orchestrator + UI (20-25h)

### Fase 2.1: AI Orchestrator Service (8-10h)

**Backend Agent:**

```python
# apps/ai/services.py

class AIOrchestrator:
    """
    Orquestador central de IA. Procesa preguntas del usuario
    combinando datos del sistema + knowledge base + historial.
    """

    SYSTEM_PROMPT = """
    Eres SaiCloud AI, el asistente inteligente de la plataforma SaiCloud.
    Ayudas a los usuarios con: proyectos, finanzas, contabilidad, terceros y uso del sistema.

    REGLAS ESTRICTAS:
    1. Solo responde con base en los datos y conocimiento proporcionados.
    2. Si no tienes información suficiente, dilo claramente.
    3. Respuestas concisas y directas (máximo 3 párrafos).
    4. Usa cifras específicas cuando las tengas disponibles.
    5. Si el usuario pregunta cómo hacer algo, guíalo paso a paso.
    6. NUNCA inventes datos, valores o métricas.
    7. Responde en español.
    """

    @staticmethod
    def process(question: str, company, user, module_context: str) -> dict:
        """
        Flujo completo:
        1. Detectar intención (datos vs guía vs análisis)
        2. Recolectar datos del módulo (DataCollector)
        3. Buscar conocimiento relevante (RAG → pgvector)
        4. Buscar respuesta cacheada (Redis)
        5. Construir prompt optimizado (system + context + knowledge + history + question)
        6. Llamar OpenAI (gpt-4o-mini)
        7. Registrar uso (AIUsageService)
        8. Retornar respuesta + metadata (módulo, tokens, fuentes)
        """

    @staticmethod
    def _build_prompt(
        question: str,
        module_context: str,
        data_context: str,        # del DataCollector
        knowledge_chunks: list,   # del RAG
        chat_history: list,       # últimos 5 mensajes de la conversación
    ) -> list[dict]:
        """
        Construye el array de messages para OpenAI.
        Optimiza tokens:
        - System prompt fijo (~200 tokens)
        - Contexto de datos: max 1500 tokens
        - Knowledge base: max 1000 tokens (top 3 chunks)
        - Historial: max 500 tokens (últimos 5 msgs)
        - Pregunta: tal cual
        Total max ~3500 tokens de input → ~$0.0005 por request
        """

    @staticmethod
    def _detect_intent(question: str) -> str:
        """
        Clasifica la intención sin usar LLM (regex + keywords).
        Retorna: 'data_query' | 'how_to_guide' | 'analysis' | 'general_chat'
        Ejemplo:
        - 'cuántos proyectos tengo' → 'data_query'
        - 'cómo creo una fase' → 'how_to_guide'
        - 'analiza mis ingresos' → 'analysis'
        - 'hola, quién eres' → 'general_chat'
        """
```

### Fase 2.2: Refactorizar BotResponseService (3-4h)

**Backend Agent:**

```python
# apps/chat/services.py — BotResponseService

class BotResponseService:
    @staticmethod
    def process_bot_message(conversacion, user_message_content: str, user):
        """
        ANTES: solo CFO Virtual (dashboard)
        AHORA: AI Orchestrator para TODOS los módulos
        """
        from apps.ai.services import AIOrchestrator

        bot_context = conversacion.bot_context or 'general'

        result = AIOrchestrator.process(
            question=user_message_content,
            company=conversacion.company,
            user=user,
            module_context=bot_context,
        )

        BotResponseService._create_bot_message(
            conversacion, bot_user, result['response'],
            metadata={'module': bot_context, 'sources': result.get('sources', [])},
        )
```

### Fase 2.3: Frontend — UI del asistente IA (8-10h)

**Frontend Agent:**

**2.3.1: Conversación IA siempre fijada arriba**

```typescript
// chat-list.component.ts
// La conversación con el bot siempre aparece primera en la lista
// Se muestra con un ícono especial 🤖 y nombre "SaiCloud AI"
// Siempre muestra estado "En línea"
// Si no existe conversación bot, mostrar botón "Iniciar chat con IA"
```

**2.3.2: Indicador de contexto activo**

```html
<!-- chat-window.component.html — dentro del header del chat bot -->
<div class="ai-context-indicator" *ngIf="isBot">
  <mat-icon>{{ contextIcon() }}</mat-icon>
  <span class="context-label">{{ contextLabel() }}</span>
  <mat-chip-set>
    <mat-chip [highlighted]="true" class="context-chip">
      {{ currentModule() }}
    </mat-chip>
  </mat-chip-set>
</div>
```

```typescript
// El contexto se detecta automáticamente del módulo actual via Router
// chat-panel.component.ts
private detectModule(): string {
  const url = this.router.url;
  if (url.includes('/proyectos')) return 'proyectos';
  if (url.includes('/saidashboard')) return 'dashboard';
  if (url.includes('/terceros')) return 'terceros';
  if (url.includes('/contabilidad')) return 'contabilidad';
  return 'general';
}

// Se envía como parámetro extra al enviar mensaje al bot
```

**2.3.3: Feedback (thumbs up/down) en mensajes del bot**

```html
<!-- message-bubble.component.html — solo para mensajes del bot -->
<div class="ai-feedback" @if (message.remitente_email === 'ai-assistant@saicloud.co') {
  <button mat-icon-button (click)="rateBotMessage(message.id, 1)"
          [class.active]="message.userRating === 1">
    <mat-icon>thumb_up</mat-icon>
  </button>
  <button mat-icon-button (click)="rateBotMessage(message.id, -1)"
          [class.active]="message.userRating === -1">
    <mat-icon>thumb_down</mat-icon>
  </button>
}
```

**2.3.4: Sugerencias rápidas según contexto**

```html
<!-- Chips de sugerencias debajo del input cuando la conversación está vacía -->
<div class="ai-suggestions" @if (isBot && messages().length === 0) {
  <span class="suggestion-label">Prueba preguntar:</span>
  <mat-chip-set>
    @for (suggestion of contextSuggestions(); track suggestion) {
      <mat-chip (click)="sendSuggestion(suggestion)">{{ suggestion }}</mat-chip>
    }
  </mat-chip-set>
}
```

```typescript
contextSuggestions = computed(() => {
  switch (this.moduleContext()) {
    case 'proyectos': return [
      '¿Cuáles son mis tareas pendientes?',
      '¿Cómo creo una nueva fase?',
      '¿Cuál es el avance de mis proyectos?',
    ];
    case 'dashboard': return [
      '¿Cuál es mi utilidad este año?',
      '¿Cómo agrego una tarjeta personalizada?',
      'Analiza mis ingresos vs gastos',
    ];
    case 'terceros': return [
      '¿Cuántos clientes activos tengo?',
      '¿Cómo registro un nuevo tercero?',
    ];
    default: return [
      '¿Qué módulos tengo disponibles?',
      '¿Cómo funciona SaiCloud?',
    ];
  }
});
```

---

## 6. SPRINT 3 — Learning + Knowledge Base + Optimización (15-20h)

### Fase 3.1: Validación Pipeline KB + Contenido adicional (3-4h)

**Integration Agent:**

NOTA: La infraestructura del pipeline (converters, endpoints, n8n workflow) se construye
en Sprint 1 Fase 1.3-1.6. Esta fase se enfoca en validar E2E y agregar contenido.

1. Validar pipeline E2E con archivos reales:
   - Subir .pdf, .docx, .md via cada canal (upload, CLI, Drive si configurado)
   - Verificar conversiones, chunks, embeddings, KnowledgeSource registros

2. Ampliar knowledge base con contenido adicional si se identifica:
   - FAQ comunes del equipo de soporte
   - Guías de onboarding de usuarios

3. Verificar búsqueda semántica con preguntas reales de cada módulo

### Fase 3.2: Sistema de aprendizaje (5-7h)

**Backend Agent:**

```python
# apps/ai/services.py

class LearningService:
    """
    Aprende de las interacciones con feedback positivo.
    Las respuestas con thumbs_up se cachean y se priorizan.
    """

    @staticmethod
    def process_feedback(mensaje_id: str, user, rating: int):
        """
        1. Guarda AIFeedback
        2. Si rating=1 (positivo):
           - Cachea pregunta+respuesta en Redis (TTL 30 días)
           - Si acumula 3+ positivos para la misma pregunta:
             → Crea KnowledgeChunk con source_type='faq_aprendida'
        3. Si rating=-1 (negativo):
           - Invalida cache
           - Log para revisión
        """

    @staticmethod
    def get_similar_answered(query: str, module: str) -> str | None:
        """
        Busca en Redis/pgvector si hay una respuesta previamente
        validada (feedback positivo) para una pregunta similar.
        Si existe y similarity > 0.92, retornarla directamente
        sin llamar a OpenAI → ahorro de tokens.
        """
```

### Fase 3.3: Historial de conversación como contexto (3-4h)

**Backend Agent:**

```python
# En AIOrchestrator._build_prompt():
# Incluir últimos 5 mensajes de la conversación actual
# para que el bot tenga memoria de corto plazo.

def _get_chat_history(conversacion_id: str, limit: int = 5) -> list[dict]:
    """
    Retorna últimos N mensajes como [{role: 'user'|'assistant', content: '...'}]
    Trunca cada mensaje a 200 tokens para no explotar el contexto.
    """
```

### Fase 3.4: Cache de respuestas + optimización de tokens (3-4h)

**Backend Agent:**

```python
# Redis cache strategy:
# Key: ai:cache:{module}:{hash_of_question}
# Value: JSON {response, tokens_saved, hits}
# TTL: 30 días
# Invalidar cuando: feedback negativo, datos actualizados

# Token optimization:
# 1. Medir contexto antes de enviar (tiktoken)
# 2. Si contexto > 3500 tokens → truncar inteligentemente
# 3. Si pregunta es FAQ → usar cache, no llamar OpenAI
# 4. Si pregunta es saludo → responder template, no llamar OpenAI
```

---

## 7. MODELO DE DATOS COMPLETO

```
┌──────────────────────────┐       ┌──────────────────────────┐
│     KnowledgeSource      │       │     KnowledgeChunk       │
├──────────────────────────┤       ├──────────────────────────┤
│ id (UUID)                │  1:N  │ id (UUID)                │
│ company_id (FK)          │──────►│ source_id (FK)           │
│ file_name                │       │ source_type (manual/     │
│ source_channel (drive/   │       │   norma/faq_aprendida)   │
│   upload/cli)            │       │ source_file              │
│ original_format          │       │ module                   │
│ module                   │       │ title                    │
│ category                 │       │ content                  │
│ file_hash (SHA-256)      │       │ token_count              │
│ chunk_count              │       │ embedding (vector 1536)  │
│ total_tokens             │       │ metadata (JSON)          │
│ last_indexed_at          │       │ created_at               │
│ drive_file_id            │       │ updated_at               │
│ metadata (JSON)          │       └──────────────────────────┘
│ created_at               │
│ updated_at               │
└──────────────────────────┘

┌──────────────────────────┐
│      AIFeedback          │
├──────────────────────────┤
│ id (UUID)                │
│ company_id (FK)          │
│ user_id (FK)             │
│ mensaje_id (FK)          │
│ rating (+1/-1)           │
│ module_context           │
│ question                 │
│ answer                   │
│ created_at               │
└──────────────────────────┘

# Existentes (sin cambios):
# - Conversacion.bot_context → ya soporta routing
# - AIUsageLog → ya registra tokens por módulo
# - CompanyLicense → ya tiene quota mensual
```

---

## 8. ENDPOINTS API NUEVOS

```
# ── Knowledge Base (ingesta y gestión) ────────────────────────────
POST   /api/v1/ai/knowledge/ingest/           # Ingesta desde n8n (API key auth)
POST   /api/v1/ai/knowledge/upload/           # Upload desde panel admin (JWT auth)
GET    /api/v1/ai/knowledge/sources/           # Listar fuentes indexadas
DELETE /api/v1/ai/knowledge/sources/{id}/      # Eliminar fuente y sus chunks
POST   /api/v1/ai/knowledge/reindex/           # Re-indexar toda la KB (admin)

# ── Feedback y sugerencias ────────────────────────────────────────
POST   /api/v1/ai/feedback/                    # Enviar feedback (thumbs up/down)
GET    /api/v1/ai/suggestions/{module}/        # Sugerencias por módulo

# ── Uso ───────────────────────────────────────────────────────────
GET    /api/v1/ai/usage/                       # Resumen de uso IA del usuario
```

Los mensajes al bot siguen usando el endpoint existente:
```
POST   /api/v1/chat/conversaciones/{id}/mensajes/enviar/
```

---

## 9. COSTOS ESTIMADOS MENSUALES

| Concepto | Costo/mes estimado |
|----------|-------------------|
| OpenAI gpt-4o-mini (500 msgs × ~4K tokens) | ~$1.50 |
| OpenAI embeddings (re-index ~200 chunks) | ~$0.01 (una vez) |
| pgvector en PostgreSQL existente | $0 |
| Redis cache (Upstash, ya existente) | $0 (incluido) |
| **Total** | **~$1.50/mes** |

vs. servicios externos: Pinecone ($70+), Weaviate ($25+), vector DB separada ($25+)

---

## 10. PLAN DE EJECUCIÓN MULTI-AGENTE

### Sprint 1 — Infraestructura + Pipeline KB (semana 1-2)

```
┌────────────────────────┐   ┌───────────────────────────┐
│   Backend Agent 1      │   │   Backend Agent 2         │
│                        │   │                           │
│ • pgvector setup       │   │ • DataCollectors (5)      │
│ • KnowledgeChunk model │   │   - DashboardCollector    │
│ • KnowledgeSource model│   │   - ProyectosCollector    │
│ • EmbeddingService     │   │   - TercerosCollector     │
│ • RAGService           │   │   - ContabilidadCollector │
│ • DocumentConverter    │   │   - GeneralCollector      │
│ • KnowledgeIngestion   │   │ • Tests unitarios         │
│   Service              │   │                           │
│ • Endpoints ingesta    │   └───────────────────────────┘
│ • index_knowledge_base │
│   management command   │   ┌───────────────────────────┐
│                        │   │   Integration Agent       │
└────────────────────────┘   │                           │
                             │ • Exportar NotebookLM a   │
                             │   .md (carga inicial)     │
                             │ • Organizar docs/knowledge│
                             │ • Crear n8n workflow      │
                             │   knowledge-base-watcher  │
                             │ • Crear estándar KB       │
                             │   (KNOWLEDGE-BASE-        │
                             │    STANDARD.md)           │
                             │ • Setup Google Drive      │
                             │   carpeta compartida      │
                             └───────────────────────────┘
```

### Sprint 2 — Orquestador + UI (semana 2)

```
┌────────────────────────┐   ┌───────────────────────────┐
│   Backend Agent        │   │   Frontend Agent          │
│                        │   │                           │
│ • AIOrchestrator       │   │ • AI chat siempre fijado  │
│ • Refactor BotResponse │   │ • Indicador de contexto   │
│ • Chat history context │   │ • Feedback thumbs up/down │
│ • Intent detection     │   │ • Sugerencias por módulo  │
│ • API feedback endpoint│   │ • Auto-detect módulo      │
│ • Tests               │   │ • Bot siempre "en línea"  │
└────────────────────────┘   └───────────────────────────┘
```

### Sprint 3 — Learning + Polish (semana 3)

```
┌────────────────────────┐   ┌───────────────────────────┐
│   Backend Agent        │   │   Integration Agent       │
│                        │   │                           │
│ • LearningService      │   │ • E2E tests en browser   │
│ • Redis cache answers  │   │ • Validación 4x4         │
│ • Token optimization   │   │ • Pruebas con datos reales│
│ • FAQ auto-generation  │   │ • Benchmark de costos    │
│                        │   │ • Documentación usuario  │
└────────────────────────┘   └───────────────────────────┘
```

---

## 11. CRITERIOS DE ACEPTACIÓN

### Sprint 1 ✓
- [ ] pgvector instalado y funcionando
- [ ] Los 7 manuales indexados (~200 chunks con embeddings)
- [ ] `RAGService.search("cómo creo una fase", module="proyectos")` retorna chunks relevantes
- [ ] 5 DataCollectors funcionando con datos reales
- [ ] Norma colombiana exportada e indexada
- [ ] Pipeline de conversión funcional: subir .pdf y .docx → se convierten a .md automáticamente
- [ ] Endpoint `POST /api/v1/ai/knowledge/upload/` funcional (subir archivo desde admin)
- [ ] Endpoint `POST /api/v1/ai/knowledge/ingest/` funcional (llamado desde n8n)
- [ ] n8n workflow `knowledge-base-watcher` creado y probado con Google Drive
- [ ] KnowledgeSource registra cada archivo indexado con hash para detectar cambios
- [ ] Re-subir un archivo actualizado reemplaza los chunks (no duplica)
- [ ] `docs/standards/KNOWLEDGE-BASE-STANDARD.md` creado con guía completa

### Sprint 2 ✓
- [ ] AIOrchestrator responde preguntas de todos los módulos con datos reales
- [ ] Pregunta en contexto proyectos → datos de proyectos + guía del manual
- [ ] Chat bot fijado arriba en lista de chats
- [ ] Indicador muestra módulo actual (ej: "📊 Dashboard")
- [ ] Feedback thumbs up/down funcional
- [ ] Sugerencias contextuales visibles

### Sprint 3 ✓
- [ ] Respuestas con feedback positivo se cachean
- [ ] FAQ aprendidas se indexan automáticamente
- [ ] Historial de 5 mensajes da contexto conversacional
- [ ] Costo promedio < $0.001 por mensaje (con cache)
- [ ] Validación 4x4 (Desktop/Mobile × Light/Dark)

---

## 12. RIESGOS Y MITIGACIÓN

| Riesgo | Mitigación |
|--------|-----------|
| pgvector no disponible en imagen Docker PG | Usar `pgvector/pgvector:pg16` como imagen base |
| Embeddings costosos en re-index masivo | Batch processing + solo re-indexar cambios |
| Respuestas lentas (>5s) | Cache Redis + intent detection para evitar llamadas innecesarias |
| Datos sensibles en prompt | Company isolation + no enviar datos de otras empresas |
| OpenAI quota de API | Rate limiting + fallback a respuesta genérica |
| Calidad de respuestas baja | Feedback loop + escalamiento a gpt-4.1-mini si necesario |
| Google Drive API token expira | n8n maneja refresh automático; alertar si falla 3 veces seguidas |
| PDF con imágenes/tablas complejas | pdfplumber extrae texto; para tablas muy complejas → subir como .md |
| Archivos duplicados en Drive | KnowledgeSource.file_hash detecta duplicados y hace upsert |

---

## 13. DECISIONES DE ARQUITECTURA A REGISTRAR

| ID | Decisión | Razón |
|----|----------|-------|
| DEC-036 | pgvector sobre servicios externos | Costo $0, misma DB, latencia mínima |
| DEC-037 | Llamada directa OpenAI (sin n8n) | Control total, sin intermediarios inestables |
| DEC-038 | NotebookLM exportación estática | No hay API pública, contenido estable |
| DEC-039 | gpt-4o-mini por defecto | Mejor relación costo/calidad para consultas |
| DEC-040 | DataCollectors solo lectura | Seguridad: IA nunca modifica datos |
| DEC-041 | App Django `ai` independiente | Separación de concerns, fácil de testear |
| DEC-042 | Pipeline dinámico KB (Drive+n8n+Django) | Actualización semi-automática, sin intervención técnica para agregar conocimiento |
| DEC-043 | Conversión automática PDF/DOCX→MD | mammoth+pdfplumber — ligeros, sin dependencia de pandoc |

---

**Última actualización:** 2026-04-07  
**Autor:** Equipo Saicloud — ValMen Tech
