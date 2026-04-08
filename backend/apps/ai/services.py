"""
SaiSuite — AI: Services
EmbeddingService, RAGService, KnowledgeIngestionService.
Regla: TODA la lógica de negocio va aquí, nunca en views ni modelos.
"""
import hashlib
import logging
import re

import tiktoken
from django.conf import settings
from django.utils import timezone
from openai import OpenAI
from pgvector.django import CosineDistance

from apps.ai.converters import DocumentConverter
from apps.ai.models import KnowledgeChunk, KnowledgeSource

logger = logging.getLogger(__name__)

# ── Tokenizer singleton ──────────────────────────────────────────
_tokenizer = tiktoken.get_encoding('cl100k_base')


def count_tokens(text: str) -> int:
    """Cuenta tokens usando cl100k_base (compatible con text-embedding-3-small)."""
    return len(_tokenizer.encode(text))


# ══════════════════════════════════════════════════════════════════
# EmbeddingService
# ══════════════════════════════════════════════════════════════════


class EmbeddingService:
    """Genera embeddings usando OpenAI text-embedding-3-small."""

    MODEL = 'text-embedding-3-small'
    DIMENSIONS = 1536
    MAX_BATCH_SIZE = 2048

    _client = None

    @classmethod
    def _get_client(cls) -> OpenAI:
        if cls._client is None:
            cls._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return cls._client

    @classmethod
    def embed(cls, text: str) -> list[float]:
        """Genera embedding para un texto."""
        client = cls._get_client()
        response = client.embeddings.create(
            model=cls.MODEL,
            input=text,
            dimensions=cls.DIMENSIONS,
        )
        return response.data[0].embedding

    @classmethod
    def embed_batch(cls, texts: list[str]) -> list[list[float]]:
        """
        Genera embeddings en batch.
        Si hay más de MAX_BATCH_SIZE textos, los divide en sub-batches.
        """
        if not texts:
            return []

        client = cls._get_client()
        all_embeddings = []

        for i in range(0, len(texts), cls.MAX_BATCH_SIZE):
            batch = texts[i:i + cls.MAX_BATCH_SIZE]
            response = client.embeddings.create(
                model=cls.MODEL,
                input=batch,
                dimensions=cls.DIMENSIONS,
            )
            # Los resultados vienen ordenados por index
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([item.embedding for item in sorted_data])

        return all_embeddings


# ══════════════════════════════════════════════════════════════════
# RAGService
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
# RAGCacheService
# ══════════════════════════════════════════════════════════════════


class RAGCacheService:
    """
    Cache Redis para búsquedas RAG frecuentes.

    Estrategia de invalidación por versión:
    - Cada (company_id, module) tiene una versión numérica en cache.
    - La versión forma parte de la clave de cada resultado cacheado.
    - Al invalidar, incrementamos la versión → las claves antiguas
      son inalcanzables y expiran naturalmente por TTL.
    """

    CACHE_TTL = 2 * 60 * 60   # 2 horas para resultados RAG
    VERSION_TTL = None         # Las versiones no expiran

    @staticmethod
    def _get_version(company_id, module: str) -> int:
        from django.core.cache import cache
        return cache.get(f'rag_v:{company_id}:{module}', 0)

    @staticmethod
    def _make_key(company_id, module: str, query: str) -> str:
        version = RAGCacheService._get_version(company_id, module)
        query_hash = hashlib.md5(query.lower().strip().encode()).hexdigest()
        return f'rag:{company_id}:{module}:{version}:{query_hash}'

    @classmethod
    def get(cls, company_id, module: str, query: str) -> list[dict] | None:
        from django.core.cache import cache
        return cache.get(cls._make_key(company_id, module, query))

    @classmethod
    def set(cls, company_id, module: str, query: str, results: list[dict]) -> None:
        from django.core.cache import cache
        cache.set(cls._make_key(company_id, module, query), results, cls.CACHE_TTL)

    @classmethod
    def invalidate_company_module(cls, company_id, module: str) -> None:
        """
        Invalida todo el cache RAG de un (company, module).
        Incrementa la versión → futuras búsquedas usan clave nueva.
        """
        from django.core.cache import cache
        version_key = f'rag_v:{company_id}:{module}'
        try:
            cache.incr(version_key)
        except ValueError:
            cache.set(version_key, 1, timeout=cls.VERSION_TTL)
        logger.info(
            'rag_cache_invalidated',
            extra={'company_id': str(company_id), 'kb_module': module},
        )


class RAGService:
    """Retrieval-Augmented Generation — busca conocimiento relevante en pgvector."""

    @staticmethod
    def search(
        query: str,
        company_id,
        module: str = '',
        top_k: int = 5,
    ) -> list[dict]:
        """
        Busca fragmentos relevantes en la knowledge base.

        1. Revisa cache Redis (TTL 2h)
        2. Si miss: genera embedding → pgvector cosine distance
        3. Guarda en cache y retorna top_k resultados con score

        Returns:
            Lista de dicts: [{title, content, score, source_file, module}]
        """
        # ── Cache lookup ──────────────────────────────────────────
        cached = RAGCacheService.get(company_id, module, query)
        if cached is not None:
            logger.debug('rag_cache_hit', extra={'kb_module': module})
            return cached

        # ── Búsqueda vectorial ────────────────────────────────────
        query_embedding = EmbeddingService.embed(query)

        qs = KnowledgeChunk.all_objects.filter(company_id=company_id)

        if module:
            # Busca en el módulo específico Y en 'general'
            qs = qs.filter(module__in=[module, 'general'])

        results = (
            qs
            .annotate(distance=CosineDistance('embedding', query_embedding))
            .order_by('distance')
            [:top_k]
        )

        output = [
            {
                'title': chunk.title,
                'content': chunk.content,
                'score': round(1 - chunk.distance, 4),
                'source_file': chunk.source_file,
                'module': chunk.module,
            }
            for chunk in results
        ]

        # ── Guardar en cache ──────────────────────────────────────
        RAGCacheService.set(company_id, module, query, output)
        return output


# ══════════════════════════════════════════════════════════════════
# KnowledgeIngestionService
# ══════════════════════════════════════════════════════════════════


class KnowledgeIngestionService:
    """
    Procesa archivos nuevos/actualizados para la knowledge base.
    Pipeline completo: hash → convert → chunk → embed → store.
    """

    DEFAULT_MAX_TOKENS = 500

    @staticmethod
    def ingest(
        file_content: bytes,
        file_name: str,
        company_id,
        module: str = '',
        category: str = '',
        source_channel: str = 'upload',
        drive_file_id: str = '',
    ) -> dict:
        """
        Pipeline completo de ingesta:

        1. Calcular hash SHA-256 del archivo
        2. Verificar si ya existe en KnowledgeSource (upsert)
        3. Convertir a markdown con DocumentConverter
        4. Extraer frontmatter si existe (override de module/category)
        5. Dividir en chunks de ~500 tokens respetando ## headers
        6. Generar embeddings en batch con EmbeddingService
        7. Borrar chunks anteriores del mismo source (si es update)
        8. Guardar chunks nuevos en KnowledgeChunk
        9. Crear/actualizar KnowledgeSource con stats

        Returns:
            {chunks_created, total_tokens, file_name, status, is_update}
        """
        # 1. Hash del archivo
        file_hash = hashlib.sha256(file_content).hexdigest()

        # 2. Verificar si ya existe (skip si hash idéntico)
        existing_source = KnowledgeSource.all_objects.filter(
            company_id=company_id,
            file_name=file_name,
            source_channel=source_channel,
        ).first()

        if existing_source and existing_source.file_hash == file_hash:
            logger.info(
                'knowledge_ingest_skipped',
                extra={'file_name': file_name, 'reason': 'hash_unchanged'},
            )
            return {
                'chunks_created': existing_source.chunk_count,
                'total_tokens': existing_source.total_tokens,
                'file_name': file_name,
                'status': 'unchanged',
                'is_update': False,
            }

        is_update = existing_source is not None

        logger.info(
            'knowledge_ingest_started',
            extra={'kb_file_name': file_name, 'is_update': is_update},
        )

        # 3. Convertir a markdown
        markdown_content = DocumentConverter.convert(file_content, file_name)

        # 4. Extraer frontmatter
        metadata, body = DocumentConverter.extract_frontmatter(markdown_content)
        original_format = DocumentConverter.get_format_from_name(file_name)

        # Frontmatter overrides
        if metadata.get('module'):
            module = metadata['module']
        if metadata.get('category'):
            category = metadata['category']

        # Defaults
        if not module:
            module = 'general'
        if not category:
            category = 'custom'

        # Determinar source_type desde category
        source_type_map = {
            'manual': KnowledgeChunk.SourceType.MANUAL,
            'norma': KnowledgeChunk.SourceType.NORMA,
            'faq': KnowledgeChunk.SourceType.FAQ_APRENDIDA,
            'guia': KnowledgeChunk.SourceType.HELP_TEXT,
            'custom': KnowledgeChunk.SourceType.CUSTOM,
        }
        source_type = source_type_map.get(category, KnowledgeChunk.SourceType.CUSTOM)

        # 5. Dividir en chunks
        chunks = KnowledgeIngestionService._chunk_markdown(body)

        if not chunks:
            logger.warning(
                'knowledge_ingest_no_chunks',
                extra={'file_name': file_name},
            )
            return {
                'chunks_created': 0,
                'total_tokens': 0,
                'file_name': file_name,
                'status': 'empty',
                'is_update': is_update,
            }

        # 6. Generar embeddings en batch
        texts = [c['content'] for c in chunks]
        embeddings = EmbeddingService.embed_batch(texts)

        total_tokens = sum(c['token_count'] for c in chunks)

        # 7. Borrar chunks anteriores si es update
        if existing_source:
            KnowledgeChunk.all_objects.filter(source=existing_source).delete()
            logger.info(
                'knowledge_chunks_deleted',
                extra={
                    'file_name': file_name,
                    'old_chunk_count': existing_source.chunk_count,
                },
            )

        # 9. Crear/actualizar KnowledgeSource
        now = timezone.now()
        if existing_source:
            source = existing_source
            source.file_hash = file_hash
            source.original_format = original_format
            source.module = module
            source.category = category
            source.chunk_count = len(chunks)
            source.total_tokens = total_tokens
            source.last_indexed_at = now
            source.drive_file_id = drive_file_id or source.drive_file_id
            source.metadata = metadata
            source.save(update_fields=[
                'file_hash', 'original_format', 'module', 'category',
                'chunk_count', 'total_tokens', 'last_indexed_at',
                'drive_file_id', 'metadata', 'updated_at',
            ])
        else:
            source = KnowledgeSource.all_objects.create(
                company_id=company_id,
                file_name=file_name,
                source_channel=source_channel,
                original_format=original_format,
                module=module,
                category=category,
                file_hash=file_hash,
                chunk_count=len(chunks),
                total_tokens=total_tokens,
                last_indexed_at=now,
                drive_file_id=drive_file_id,
                metadata=metadata,
            )

        # 8. Guardar chunks nuevos
        chunk_objects = [
            KnowledgeChunk(
                company_id=company_id,
                source=source,
                source_type=source_type,
                source_file=file_name,
                module=module,
                title=chunk['title'],
                content=chunk['content'],
                token_count=chunk['token_count'],
                embedding=embeddings[i],
                metadata=chunk.get('metadata', {}),
            )
            for i, chunk in enumerate(chunks)
        ]
        KnowledgeChunk.all_objects.bulk_create(chunk_objects)

        # Invalidar cache RAG del módulo afectado
        RAGCacheService.invalidate_company_module(company_id, module)

        logger.info(
            'knowledge_ingest_complete',
            extra={
                'file_name': file_name,
                'chunks_created': len(chunks),
                'total_tokens': total_tokens,
                'is_update': is_update,
            },
        )

        return {
            'chunks_created': len(chunks),
            'total_tokens': total_tokens,
            'file_name': file_name,
            'status': 'updated' if is_update else 'created',
            'is_update': is_update,
        }

    @staticmethod
    def _chunk_markdown(
        content: str,
        max_tokens: int = 500,
    ) -> list[dict]:
        """
        Divide markdown en chunks respetando:
        - Secciones ## (nunca corta en medio de una sección)
        - Si una sección > max_tokens → subdivide por párrafos
        - Mantiene el header de la sección en cada chunk

        Returns:
            [{title, content, token_count, metadata}]
        """
        if not content.strip():
            return []

        # Dividir por ## headers
        sections = re.split(r'(?=^## )', content, flags=re.MULTILINE)
        chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extraer título
            title_match = re.match(r'^##\s+(.+)', section)
            title = title_match.group(1).strip() if title_match else 'Introducción'

            tokens = count_tokens(section)

            if tokens <= max_tokens:
                chunks.append({
                    'title': title,
                    'content': section,
                    'token_count': tokens,
                    'metadata': {},
                })
            else:
                # Sección muy larga: subdividir por párrafos
                sub_chunks = KnowledgeIngestionService._split_long_section(
                    section, title, max_tokens,
                )
                chunks.extend(sub_chunks)

        return chunks

    @staticmethod
    def _split_long_section(
        section: str,
        title: str,
        max_tokens: int,
    ) -> list[dict]:
        """Subdivide una sección larga por párrafos, manteniendo el header."""
        header_line = f'## {title}\n\n'
        header_tokens = count_tokens(header_line)

        # Quitar el header de la sección para dividir solo el body
        body = re.sub(r'^##\s+.+\n*', '', section, count=1).strip()
        paragraphs = re.split(r'\n\n+', body)

        chunks = []
        current_content = header_line
        current_tokens = header_tokens

        for paragraph in paragraphs:
            para_tokens = count_tokens(paragraph)

            if current_tokens + para_tokens <= max_tokens:
                current_content += paragraph + '\n\n'
                current_tokens += para_tokens
            else:
                # Guardar chunk actual si tiene contenido
                if current_tokens > header_tokens:
                    chunks.append({
                        'title': title,
                        'content': current_content.strip(),
                        'token_count': count_tokens(current_content.strip()),
                        'metadata': {'part': len(chunks) + 1},
                    })
                # Empezar nuevo chunk con el header
                current_content = header_line + paragraph + '\n\n'
                current_tokens = header_tokens + para_tokens

        # Último chunk
        if current_tokens > header_tokens:
            chunks.append({
                'title': title,
                'content': current_content.strip(),
                'token_count': count_tokens(current_content.strip()),
                'metadata': {'part': len(chunks) + 1} if chunks else {},
            })

        return chunks

    @staticmethod
    def delete_source(source_id, company_id) -> dict:
        """Elimina una fuente y todos sus chunks."""
        source = KnowledgeSource.all_objects.filter(
            id=source_id,
            company_id=company_id,
        ).first()

        if not source:
            raise ValueError('Fuente no encontrada.')

        file_name = source.file_name
        chunk_count = source.chunk_count

        # Cascade delete borra los chunks automáticamente
        source.delete()

        logger.info(
            'knowledge_source_deleted',
            extra={'file_name': file_name, 'chunks_deleted': chunk_count},
        )

        return {
            'file_name': file_name,
            'chunks_deleted': chunk_count,
        }


# ══════════════════════════════════════════════════════════════════
# AIOrchestrator
# ══════════════════════════════════════════════════════════════════


class AIOrchestrator:
    """
    Orquestador central de IA para SaiBot.

    Pipeline por mensaje:
      1. DataCollector  → contexto estructurado del módulo (SOLO LECTURA)
      2. RAGService     → chunks relevantes de la knowledge base (cosine similarity)
      3. OpenAI GPT-4o-mini → respuesta final con contexto completo
      4. Registro de uso de tokens

    Soporta todos los módulos: dashboard, proyectos, terceros, contabilidad, general.
    """

    # Límites de contexto para optimizar tokens
    MAX_COLLECTOR_TOKENS = 1500
    MAX_RAG_CHUNKS = 5
    MAX_RAG_TOKENS = 2000
    MAX_COMPLETION_TOKENS = 1024

    # Prompt base del sistema
    SYSTEM_TEMPLATE = (
        'Eres SaiBot, el asistente inteligente de SaiSuite para {company_name}.\n'
        'Tienes acceso a los datos reales de la empresa y a la base de conocimiento de SaiSuite.\n\n'
        'ESTILO DE RESPUESTA — MUY IMPORTANTE:\n'
        '- Sé conversacional y conciso. Máximo 3-4 oraciones por turno salvo que el usuario pida más detalle.\n'
        '- Si el usuario pide ayuda para hacer algo en la app (crear, configurar, editar), guíalo PASO A PASO en turnos separados: un paso por mensaje. Empieza con el primer paso y espera confirmación antes de continuar.\n'
        '- NUNCA vuelques una guía completa de una sola vez. Prefiere el diálogo: "¿Listo? Avancemos al siguiente paso.".\n'
        '- Usa bullets solo cuando haya 3+ elementos que comparar o listar datos.\n'
        '- Responde siempre en español.\n'
        '- Usa los datos reales de la empresa cuando estén disponibles.\n'
        '- Si no tienes datos suficientes, dilo en una sola oración.\n'
        '- Para cifras monetarias usa formato COP con separadores de miles.\n'
        '- No inventes datos. Si no lo sabes, dilo brevemente.\n'
        '- Cuando cites una norma contable colombiana (PUC, NIIF, IVA) explica en una línea.\n'
    )

    @staticmethod
    def answer(
        question: str,
        company,
        module: str = 'general',
        user=None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        """
        Genera una respuesta completa usando RAG + DataCollector + GPT-4o-mini.

        Args:
            question: Pregunta del usuario
            company: Objeto Company (multi-tenant)
            module: Módulo de contexto (dashboard, proyectos, terceros, contabilidad, general)
            user: Usuario que pregunta (para collectors de proyectos y personalización)
            conversation_history: Últimos N mensajes [{role, content}] para contexto multi-turno

        Returns:
            {
                'answer': str,
                'prompt_tokens': int,
                'completion_tokens': int,
                'model': str,
                'rag_chunks_used': int,
                'collector_used': bool,
            }
        """
        from apps.ai.collectors import COLLECTORS

        openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not openai_api_key:
            return {
                'answer': 'El asistente de IA no está configurado. Contacta al administrador.',
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'model': '',
                'rag_chunks_used': 0,
                'collector_used': False,
            }

        # ── 1. DataCollector: contexto estructurado del módulo ────────
        collector_context = ''
        collector_used = False
        collector = COLLECTORS.get(module) or COLLECTORS.get('general')
        if collector:
            try:
                raw = collector.collect(company, question, user)
                # Truncar si supera el límite de tokens
                if count_tokens(raw) > AIOrchestrator.MAX_COLLECTOR_TOKENS:
                    lines = raw.splitlines()
                    truncated = []
                    tok = 0
                    for line in lines:
                        lt = count_tokens(line)
                        if tok + lt > AIOrchestrator.MAX_COLLECTOR_TOKENS:
                            truncated.append('... [truncado por límite de tokens]')
                            break
                        truncated.append(line)
                        tok += lt
                    raw = '\n'.join(truncated)
                collector_context = raw
                collector_used = True
            except Exception:
                logger.exception(
                    'ai_collector_failed',
                    extra={'kb_module': module, 'company_id': str(company.id)},
                )

        # ── 2. RAGService: chunks relevantes de knowledge base ────────
        rag_context = ''
        rag_chunks_used = 0
        try:
            chunks = RAGService.search(
                query=question,
                company_id=company.id,
                module=module,
                top_k=AIOrchestrator.MAX_RAG_CHUNKS,
            )
            # Solo incluir chunks con score > 0.40 (relevancia mínima)
            relevant_chunks = [c for c in chunks if c['score'] >= 0.40]
            if relevant_chunks:
                rag_lines = ['### Base de Conocimiento SaiSuite']
                total_rag_tokens = 0
                for chunk in relevant_chunks:
                    chunk_text = f'**{chunk["title"]}**\n{chunk["content"]}'
                    ct = count_tokens(chunk_text)
                    if total_rag_tokens + ct > AIOrchestrator.MAX_RAG_TOKENS:
                        break
                    rag_lines.append(chunk_text)
                    total_rag_tokens += ct
                    rag_chunks_used += 1
                rag_context = '\n\n'.join(rag_lines)
        except Exception:
            logger.exception(
                'ai_rag_search_failed',
                extra={'kb_module': module, 'company_id': str(company.id)},
            )

        # ── 3. Construir mensajes para GPT-4o-mini ────────────────────
        system_prompt = AIOrchestrator.SYSTEM_TEMPLATE.format(
            company_name=company.name,
        )

        # User turn: combina datos + RAG + pregunta
        context_parts = []
        if collector_context:
            context_parts.append(f'## Datos actuales de la empresa\n\n{collector_context}')
        if rag_context:
            context_parts.append(rag_context)

        if context_parts:
            user_content = (
                '\n\n---\n\n'.join(context_parts)
                + f'\n\n---\n\n**Pregunta del usuario:** {question}'
            )
        else:
            user_content = question

        # Construir historial de mensajes
        messages = [{'role': 'system', 'content': system_prompt}]

        if conversation_history:
            # Máximo 6 turnos de historial para no saturar el contexto
            messages.extend(conversation_history[-6:])

        messages.append({'role': 'user', 'content': user_content})

        # ── 4. Llamar a OpenAI ────────────────────────────────────────
        # Token optimization: ajustar completion tokens según longitud de pregunta.
        # Preguntas cortas → respuestas más cortas son suficientes.
        question_tokens = count_tokens(question)
        if question_tokens <= 50:
            completion_tokens = 512
        elif question_tokens <= 150:
            completion_tokens = 768
        else:
            completion_tokens = AIOrchestrator.MAX_COMPLETION_TOKENS

        client = OpenAI(api_key=openai_api_key)
        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                max_tokens=completion_tokens,
                temperature=0.3,
            )
            answer_text = response.choices[0].message.content
            usage = response.usage

            logger.info(
                'ai_orchestrator_complete',
                extra={
                    'kb_module': module,
                    'company_id': str(company.id),
                    'rag_chunks': rag_chunks_used,
                    'prompt_tokens': usage.prompt_tokens,
                    'completion_tokens': usage.completion_tokens,
                },
            )

            return {
                'answer': answer_text,
                'prompt_tokens': usage.prompt_tokens,
                'completion_tokens': usage.completion_tokens,
                'model': response.model,
                'rag_chunks_used': rag_chunks_used,
                'collector_used': collector_used,
            }

        except Exception as exc:
            logger.error(
                'ai_orchestrator_error',
                extra={'error': str(exc), 'kb_module': module, 'company_id': str(company.id)},
            )
            return {
                'answer': (
                    'Lo siento, no pude generar una respuesta en este momento. '
                    'Por favor intenta de nuevo.'
                ),
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'model': 'gpt-4o-mini',
                'rag_chunks_used': rag_chunks_used,
                'collector_used': collector_used,
            }


# ══════════════════════════════════════════════════════════════════
# LearningService
# ══════════════════════════════════════════════════════════════════


class LearningService:
    """
    Aprende de feedback positivo para mejorar la knowledge base.

    Cuando un usuario da thumbs up a una respuesta del bot,
    esa pregunta+respuesta se convierte automáticamente en un
    KnowledgeChunk de tipo FAQ_APRENDIDA para mejorar respuestas
    futuras a preguntas similares.

    Garantías:
    - Deduplicación via content_hash (MD5 del contenido normalizado)
    - Mínimo de tokens para filtrar respuestas triviales
    - Invalida cache RAG del módulo para que la FAQ sea inmediatamente buscable
    """

    MIN_ANSWER_TOKENS = 50  # Respuestas muy cortas no aportan valor

    @staticmethod
    def process_positive_feedback(feedback) -> bool:
        """
        Procesa un feedback con rating=+1: crea un chunk FAQ si no existe.

        Args:
            feedback: Instancia de AIFeedback con rating=1

        Returns:
            True si se creó un chunk nuevo, False si ya existía o se omitió.
        """
        if feedback.rating != 1:
            return False

        if not feedback.question or not feedback.answer:
            return False

        if count_tokens(feedback.answer) < LearningService.MIN_ANSWER_TOKENS:
            logger.debug(
                'learning_skipped_short_answer',
                extra={'feedback_id': str(feedback.id)},
            )
            return False

        # Normalizar y hashear el contenido para deduplicar
        faq_content = (
            f'**Pregunta frecuente:** {feedback.question.strip()}\n\n'
            f'**Respuesta:** {feedback.answer.strip()}'
        )
        content_hash = hashlib.md5(faq_content.encode()).hexdigest()[:16]

        # Verificar si ya existe un chunk idéntico
        already_exists = KnowledgeChunk.all_objects.filter(
            company_id=feedback.company_id,
            source_type=KnowledgeChunk.SourceType.FAQ_APRENDIDA,
            metadata__content_hash=content_hash,
        ).exists()

        if already_exists:
            logger.info(
                'learning_faq_duplicate',
                extra={'feedback_id': str(feedback.id), 'content_hash': content_hash},
            )
            return False

        # Generar embedding del par Q&A
        try:
            embedding = EmbeddingService.embed(faq_content)
        except Exception:
            logger.exception(
                'learning_embed_failed',
                extra={'feedback_id': str(feedback.id)},
            )
            return False

        KnowledgeChunk.all_objects.create(
            company_id=feedback.company_id,
            source=None,  # FAQ aprendida no proviene de un archivo
            source_type=KnowledgeChunk.SourceType.FAQ_APRENDIDA,
            source_file=f'learned/{feedback.module_context}',
            module=feedback.module_context,
            title=feedback.question[:200],
            content=faq_content,
            token_count=count_tokens(faq_content),
            embedding=embedding,
            metadata={
                'content_hash': content_hash,
                'feedback_id': str(feedback.id),
                'learned_from_rating': feedback.rating,
            },
        )

        # Invalida cache para que la nueva FAQ sea buscable inmediatamente
        RAGCacheService.invalidate_company_module(
            company_id=feedback.company_id,
            module=feedback.module_context,
        )

        logger.info(
            'learning_faq_created',
            extra={
                'feedback_id': str(feedback.id),
                'module': feedback.module_context,
                'company_id': str(feedback.company_id),
                'question_preview': feedback.question[:60],
            },
        )
        return True
