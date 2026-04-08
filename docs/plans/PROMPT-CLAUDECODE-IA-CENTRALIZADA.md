# Prompt de Ejecución — IA Centralizada SaiCloud

> **Copiar en Claude Code para ejecutar cada sprint.**  
> **Leer primero:** `docs/plans/PLAN-IA-CENTRALIZADA.md`

---

## SPRINT 1 — Infraestructura IA + RAG + Pipeline Knowledge Base

### Agente Backend 1: pgvector + Modelos + Servicios + Pipeline Ingesta

```
Contexto: Estamos construyendo un asistente de IA centralizado para SaiCloud.
Leer docs/plans/PLAN-IA-CENTRALIZADA.md para entender la arquitectura completa.
NOTA: La base de datos corre en Docker local (aún no en producción, estamos en pruebas).

TAREAS:

1. Cambiar imagen de PostgreSQL en docker-compose.yml:
   - De: `postgres:16-alpine` → A: `pgvector/pgvector:pg16`
   - Ejecutar: docker compose down -v && docker compose up -d db
   - Verificar: docker exec saisuite-db psql -U saisuite -d saisuite_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"

2. Instalar dependencias en requirements.txt:
   - pgvector (Python client)
   - tiktoken (conteo de tokens)
   - mammoth (conversión .docx → markdown)
   - pdfplumber (conversión .pdf → texto)
   - markdownify (HTML → markdown, backup para mammoth)

3. Crear app Django: backend/apps/ai/
   - __init__.py, apps.py (AIConfig)
   - Agregar 'apps.ai' en config/settings/base.py INSTALLED_APPS

4. Crear modelos (backend/apps/ai/models.py):
   - KnowledgeChunk: source_type, source_file, module, title, content,
     token_count, embedding (VectorField 1536), metadata (JSON),
     source (FK a KnowledgeSource, nullable para FAQ aprendidas)
   - KnowledgeSource: file_name, source_channel (drive/upload/cli),
     original_format, module, category, file_hash (SHA-256),
     chunk_count, total_tokens, last_indexed_at, drive_file_id, metadata
   - AIFeedback: company (FK), user (FK), mensaje (FK), rating,
     module_context, question, answer
   - HNSW index en embedding para búsqueda rápida
   - Migración: makemigrations ai && migrate

5. Crear DocumentConverter (backend/apps/ai/converters.py):
   - convert(file_path) → str: auto-detecta formato y convierte a markdown
   - _pdf_to_markdown(file_path) → str: pdfplumber extrae texto + headers
   - _docx_to_markdown(file_path) → str: mammoth convierte preservando estructura
   - extract_frontmatter(content) → (dict, str): extrae YAML frontmatter si existe
   - Formatos soportados: .md, .txt, .pdf, .docx

6. Crear EmbeddingService (backend/apps/ai/services.py):
   - embed(text) → list[float] usando OpenAI text-embedding-3-small
   - embed_batch(texts) → list[list[float]] con batching
   - Usar settings.OPENAI_API_KEY

7. Crear RAGService (backend/apps/ai/services.py):
   - search(query, module='', top_k=5) → busca en pgvector por cosine similarity
   - Filtra por module si se especifica
   - Retorna [{title, content, score, source_file}]

8. Crear KnowledgeIngestionService (backend/apps/ai/services.py):
   - ingest(file_content, file_name, module, category, source_channel, drive_file_id=''):
     1. Calcular hash SHA-256 del archivo
     2. Verificar si ya existe en KnowledgeSource (upsert por file_name+source_channel)
     3. Convertir a markdown con DocumentConverter
     4. Extraer frontmatter si existe (override de module/category)
     5. Dividir en chunks de ~500 tokens respetando ## headers
     6. Generar embeddings en batch con EmbeddingService
     7. Borrar chunks anteriores del mismo source (si es update)
     8. Guardar chunks nuevos en KnowledgeChunk
     9. Crear/actualizar KnowledgeSource con stats
     Retorna: {chunks_created, total_tokens, file_name, status}
   - _chunk_markdown(content, max_tokens=500):
     Divide por ## headers, subdivide secciones largas por párrafos,
     mantiene header en cada chunk

9. Crear management command index_knowledge_base:
   - Lee todos los archivos en docs/manuales/ y docs/knowledge/
   - Soporta .md, .txt, .pdf, .docx (usa DocumentConverter)
   - Para cada archivo: llama KnowledgeIngestionService.ingest()
   - Flags: --reindex (borra todo primero), --file (solo un archivo),
            --incremental (solo archivos con hash diferente)
   - Output: tabla resumen con archivos procesados, chunks, tokens

10. Crear endpoints de ingesta (backend/apps/ai/views.py + urls.py):
    - POST /api/v1/ai/knowledge/ingest/ — llamado por n8n (auth: X-N8N-Secret header)
    - POST /api/v1/ai/knowledge/upload/ — llamado desde panel admin (auth: JWT, admin only)
    - GET  /api/v1/ai/knowledge/sources/ — listar fuentes indexadas (auth: JWT, admin only)
    - DELETE /api/v1/ai/knowledge/sources/{id}/ — eliminar fuente y chunks
    - Incluir en config/urls.py: path('api/v1/ai/', include('apps.ai.urls'))

11. Tests:
    - Test DocumentConverter con archivos .md, .pdf, .docx de prueba
    - Test KnowledgeIngestionService (mock embeddings)
    - Test upsert: subir mismo archivo 2 veces → no duplica chunks
    - Test EmbeddingService (mock OpenAI)
    - Test RAGService con datos de prueba
    - Test management command con archivo de prueba
    - Test endpoints ingesta (auth, validación)

REGLAS:
- BaseModel para todos los modelos (UUID pk, company FK donde aplique)
- Lógica en services.py, nunca en views
- Logging con logger.info/error, nunca print()
- Estricto con types: nunca `any`
- KnowledgeSource.file_hash detecta duplicados — no re-procesar si hash no cambió
```

### Agente Backend 2: Data Collectors

```
Contexto: Estamos construyendo DataCollectors que extraen datos del sistema
para alimentar al asistente de IA. SOLO LECTURA — nunca create/update/delete.
Leer docs/plans/PLAN-IA-CENTRALIZADA.md sección 4, Fase 1.2.

TAREAS:

1. Crear backend/apps/ai/collectors.py con:

   BaseDataCollector:
   - collect(company, query, user=None) → str (contexto formateado)
   - Todos los queries filtran por company (multi-tenant)

   DashboardCollector:
   - Resumen año en curso: ingresos, costos, gastos, utilidad, activo, pasivo
   - Desglose mensual (12 meses, débito/crédito por título)
   - Top 10 cuentas por movimiento total
   - Comparativo año anterior vs actual
   - Fuentes: MovimientoContable, CuentaContable

   ProyectosCollector:
   - Proyectos activos con % avance, presupuesto, estado
   - Tareas del usuario (pendientes, bloqueadas, vencidas)
   - Hitos próximos 30 días
   - Horas registradas vs estimadas (global)
   - Resumen de fases por proyecto
   - Fuentes: Project, Task, Phase, Milestone, WorkSession

   TercerosCollector:
   - Total terceros activos/inactivos
   - Terceros por tipo (cliente/proveedor/empleado)
   - Últimos 10 terceros creados
   - Fuentes: Tercero

   ContabilidadCollector:
   - Balance de prueba resumido (clase 1-6)
   - Top 10 cuentas con mayor saldo
   - Movimientos del mes actual
   - Fuentes: MovimientoContable, CuentaContable

   GeneralCollector:
   - Info empresa (nombre, NIT, módulos activos)
   - Usuarios activos
   - Estado de licencia y uso IA
   - Fuentes: Company, CompanyModule, CompanyLicense, User

2. COLLECTORS registry (dict module → collector instance)

3. Tests unitarios para cada collector

REGLAS:
- NUNCA usar .create(), .update(), .delete(), .save() — SOLO LECTURA
- select_related/prefetch_related para evitar N+1
- Cada collector retorna un string formateado legible (no JSON)
- Formato: secciones con ## headers, listas con -, cifras con $ formateado
- Max ~1500 tokens por collector (medir con tiktoken)
```

### Agente Integración: Knowledge Base + n8n Workflow + Estándar

```
Contexto: Preparar la base de conocimiento para el asistente de IA y crear
el pipeline de actualización semi-automática.
Leer docs/plans/PLAN-IA-CENTRALIZADA.md sección 3.3 para el diseño completo.
Leer docs/standards/KNOWLEDGE-BASE-STANDARD.md para el estándar ya creado.

TAREAS:

1. Crear estructura de directorios:
   docs/knowledge/norma-colombiana/
   docs/knowledge/faq/

2. Crear archivos .md base de norma colombiana con frontmatter YAML:
   - puc-plan-unico-cuentas.md (estructura del PUC colombiano, clases 1-9,
     grupos principales, cuentas más usadas en PyMEs)
   - niif-pymes-resumen.md (normas NIIF para PyMEs colombianas, secciones
     clave: reconocimiento, medición, presentación)
   - impuestos-iva-retencion.md (IVA, retención en la fuente, ICA, tarifas
     vigentes, bases gravables)
   - obligaciones-tributarias.md (calendario tributario, declaraciones,
     obligaciones de PyMEs)
   Cada archivo debe tener:
     ---
     module: contabilidad
     category: norma
     version: "1.0"
     last_updated: "2026-04-07"
     ---

3. Verificar que docs/manuales/ tiene los 7 manuales existentes

4. Crear n8n workflow: n8n/workflows/knowledge-base-watcher.json
   - Trigger: Google Drive Trigger (polling cada 5 min)
   - Carpeta: "SaiCloud Knowledge Base" (configurable por folder ID)
   - Evento: archivo creado o modificado
   - Node 1: Download File del Drive
   - Node 2: Extract Metadata (folder → module, MIME → format, file_id)
   - Node 3: HTTP POST a http://backend:8000/api/v1/ai/knowledge/ingest/
     con file + metadata + header X-N8N-Secret
   - Node 4: Error Handler → log + notificación
   NOTA: El folder ID de Google Drive se configura después de crear la
   carpeta compartida. Dejar como variable de entorno N8N_GDRIVE_KB_FOLDER_ID.

5. Agregar variable de entorno al servicio n8n en docker-compose.yml:
   - N8N_GDRIVE_KB_FOLDER_ID (folder ID de Google Drive)

6. Agregar variable de entorno al backend .env:
   - N8N_WEBHOOK_SECRET (clave compartida para autenticar calls de n8n)

7. Ejecutar: python manage.py index_knowledge_base
   Verificar: los chunks se crearon correctamente en la DB.
   Verificar: KnowledgeSource tiene un registro por cada archivo procesado.

8. Test de pipeline completo:
   - Subir un .pdf de prueba via endpoint /api/v1/ai/knowledge/upload/
   - Verificar: se convirtió a markdown, se crearon chunks, KnowledgeSource registrado
   - Subir el mismo archivo modificado → verificar que hizo upsert (no duplicó)
```

---

## SPRINT 2 — AI Orchestrator + UI

### Agente Backend: Orquestador + Refactoring

```
Contexto: Construir el orquestador central de IA y refactorizar BotResponseService.
Leer docs/plans/PLAN-IA-CENTRALIZADA.md sección 5.

TAREAS:

1. Crear AIOrchestrator en backend/apps/ai/services.py:
   - process(question, company, user, module_context) → dict
   - _build_prompt() construye array de messages optimizado
   - _detect_intent() clasifica sin LLM (regex + keywords)
   - _get_chat_history() últimos 5 mensajes de la conversación
   - Llama OpenAI directamente (gpt-4o-mini)
   - Combina: DataCollector + RAGService + chat history
   - Retorna: {response, module, tokens_used, sources}

2. Refactorizar BotResponseService:
   - Eliminar routing manual por bot_context
   - Usar AIOrchestrator.process() para TODOS los contextos
   - Mantener quota check con AIUsageService

3. Crear endpoint feedback:
   - POST /api/v1/ai/feedback/ con {mensaje_id, rating}
   - View en backend/apps/ai/views.py
   - URL en backend/apps/ai/urls.py
   - Incluir en config/urls.py

4. Eliminar CfoVirtualService (ya no necesario, reemplazado por AIOrchestrator)
   - Mover _build_financial_context a DashboardCollector

5. Tests del AIOrchestrator (mock OpenAI)

REGLAS:
- System prompt max 200 tokens
- Contexto total max 3500 tokens
- Respuesta max 1024 tokens
- Si intent es 'general_chat' (saludo) → responder sin OpenAI
```

### Agente Frontend: UI del Asistente

```
Contexto: Actualizar la UI del chat para el asistente IA centralizado.
Leer docs/plans/PLAN-IA-CENTRALIZADA.md sección 5, Fase 2.3.
Leer docs/standards/UI-UX-STANDARDS.md para estándares de componentes.

TAREAS:

1. Chat bot siempre fijado arriba en la lista de chats:
   - En chat-list, ordenar conversaciones poniendo la del bot primero
   - Mostrar icono especial (smart_toy) y nombre "SaiCloud AI"
   - Mostrar siempre como "En línea" (no usar PresenceService para el bot)
   - Si no existe conversación bot, mostrar botón "Iniciar chat con IA"

2. Indicador de contexto activo en el header del chat bot:
   - Chip con ícono del módulo actual (dashboard, assignment, people, etc.)
   - Texto: "Dashboard", "Proyectos", "Terceros", "General"
   - Detectar módulo desde Router.url automáticamente
   - El módulo se envía como parámetro adicional al backend

3. Actualizar bot_context dinámicamente:
   - ChatStateService.openBot() → detecta módulo actual
   - Cuando usuario navega a otro módulo y vuelve al chat, actualiza contexto
   - PATCH /api/v1/chat/conversaciones/{id}/ con nuevo bot_context

4. Feedback thumbs up/down:
   - Solo en mensajes del bot (remitente_email = 'ai-assistant@saicloud.co')
   - Botones mat-icon-button con thumb_up / thumb_down
   - POST /api/v1/ai/feedback/ al hacer clic
   - Visual: botón seleccionado se ilumina

5. Sugerencias contextuales:
   - Cuando la conversación bot está vacía o al inicio
   - Chips clickeables con preguntas sugeridas según módulo
   - Al hacer clic, se envía como mensaje normal

6. Angular Material, OnPush, signals, @if/@for
7. Responsive: funcionar en mobile y desktop
8. Dark mode: usar variables CSS del tema
```

---

## SPRINT 3 — Learning + Optimización

### Agente Backend: Aprendizaje + Cache

```
Contexto: Implementar sistema de aprendizaje y optimización de costos.
Leer docs/plans/PLAN-IA-CENTRALIZADA.md sección 6.

TAREAS:

1. LearningService:
   - process_feedback() analiza feedback positivo/negativo
   - Si 3+ thumbs_up en pregunta similar → crear FAQ aprendida en pgvector
   - Cache en Redis: ai:cache:{module}:{hash_query} con TTL 30 días

2. Cache de respuestas:
   - Antes de llamar OpenAI, verificar cache Redis
   - Hash de query normalizada (lowercase, sin puntuación)
   - Si cache hit y similarity > 0.92 → retornar sin OpenAI

3. Token optimization:
   - Medir tokens con tiktoken antes de enviar
   - Si contexto > 3500 tokens → truncar inteligentemente
   - Si intent es saludo/despedida → template response sin OpenAI
   - Logging de tokens ahorrados por cache vs gastados

4. Tests del LearningService
5. Benchmark: medir costo promedio por mensaje con datos reales
```

### Agente Integración: E2E + Documentación

```
Contexto: Validación end-to-end del asistente IA.

TAREAS:

1. Tests E2E en navegador real:
   - Abrir chat IA desde Dashboard → preguntar sobre ingresos
   - Navegar a Proyectos → preguntar sobre tareas → verificar contexto cambia
   - Dar feedback thumbs_up → verificar se guarda
   - Verificar sugerencias cambian según módulo

2. Validación 4x4:
   - Desktop + Light: chat bot, indicador, sugerencias, feedback
   - Desktop + Dark: mismos elementos
   - Mobile + Light: responsive, touch targets 44px
   - Mobile + Dark: contraste, legibilidad

3. Actualizar manual del chat (docs/manuales/MANUAL-CHAT-SAICLOUD.md):
   - Sección nueva: "Asistente IA SaiCloud"
   - Cómo usarlo, qué puede responder, feedback

4. Validar pipeline de Knowledge Base end-to-end:
   - Subir archivo .pdf via panel admin → verificar chunks creados
   - Subir archivo .docx via panel admin → verificar conversión correcta
   - Subir archivo .md con frontmatter → verificar module/category inferidos
   - Re-subir archivo modificado → verificar upsert (no duplica)
   - Eliminar fuente desde admin → verificar chunks eliminados
   - (Si Google Drive configurado) Subir archivo a Drive → esperar 5 min → verificar indexación

5. Actualizar CONTEXT.md con el nuevo estado
6. Actualizar DECISIONS.md con DEC-036 a DEC-043
```
