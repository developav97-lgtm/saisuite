"""
SaiSuite — AI: Document Converters
Convierte documentos (.pdf, .docx, .txt, .md) a Markdown para indexación RAG.
Estándar: docs/standards/KNOWLEDGE-BASE-STANDARD.md
"""
import io
import logging
import re
from pathlib import Path

import mammoth
import pdfplumber
import yaml

logger = logging.getLogger(__name__)


class DocumentConverter:
    """
    Convierte documentos a Markdown para indexación en la knowledge base.

    Formatos soportados:
      .md   — se usa directamente (sin conversión)
      .txt  — se usa directamente (sin conversión)
      .pdf  — pdfplumber extrae texto + detecta estructura
      .docx — mammoth convierte a markdown preservando headers y listas
    """

    SUPPORTED_EXTENSIONS = {'.md', '.txt', '.pdf', '.docx'}

    @staticmethod
    def convert(file_content: bytes, file_name: str) -> str:
        """
        Auto-detecta formato y convierte a markdown.

        Args:
            file_content: Contenido del archivo en bytes.
            file_name: Nombre del archivo (usado para detectar extensión).

        Returns:
            Contenido en formato markdown.

        Raises:
            ValueError: Si el formato no es soportado.
        """
        ext = Path(file_name).suffix.lower()

        if ext not in DocumentConverter.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f'Formato no soportado: {ext}. '
                f'Formatos válidos: {", ".join(DocumentConverter.SUPPORTED_EXTENSIONS)}'
            )

        if ext in ('.md', '.txt'):
            return file_content.decode('utf-8', errors='replace')

        if ext == '.pdf':
            return DocumentConverter._pdf_to_markdown(file_content)

        if ext == '.docx':
            return DocumentConverter._docx_to_markdown(file_content)

        return file_content.decode('utf-8', errors='replace')

    @staticmethod
    def _pdf_to_markdown(file_content: bytes) -> str:
        """
        Extrae texto de un PDF y lo estructura como markdown.
        Usa pdfplumber para extraer texto preservando layout básico.
        """
        lines = []
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        lines.append(text)
                    else:
                        logger.warning(
                            'pdf_page_empty',
                            extra={'page': page_num},
                        )
        except Exception:
            logger.exception('pdf_conversion_error')
            raise ValueError('No se pudo procesar el archivo PDF.')

        full_text = '\n\n'.join(lines)
        return DocumentConverter._clean_extracted_text(full_text)

    @staticmethod
    def _docx_to_markdown(file_content: bytes) -> str:
        """
        Convierte un archivo .docx a markdown usando mammoth.
        Preserva headers, listas, negritas y cursivas.
        """
        try:
            result = mammoth.convert_to_markdown(io.BytesIO(file_content))
            if result.messages:
                for msg in result.messages:
                    logger.info(
                        'docx_conversion_warning',
                        extra={'message': str(msg)},
                    )
            return result.value
        except Exception:
            logger.exception('docx_conversion_error')
            raise ValueError('No se pudo procesar el archivo .docx.')

    @staticmethod
    def _clean_extracted_text(text: str) -> str:
        """Limpia texto extraído de PDF: normaliza whitespace, preserva estructura."""
        # Colapsar líneas vacías múltiples a máximo 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Normalizar espacios dentro de líneas (no newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def extract_frontmatter(content: str) -> tuple[dict, str]:
        """
        Extrae metadata YAML del inicio del archivo si existe.

        El frontmatter debe estar entre dos líneas '---':
        ---
        module: proyectos
        category: manual
        ---

        Returns:
            Tupla (metadata_dict, contenido_sin_frontmatter).
            Si no hay frontmatter, retorna ({}, contenido_original).
        """
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return {}, content

        try:
            metadata = yaml.safe_load(match.group(1))
            if not isinstance(metadata, dict):
                return {}, content
            body = content[match.end():]
            return metadata, body
        except yaml.YAMLError:
            logger.warning('frontmatter_parse_error')
            return {}, content

    @staticmethod
    def get_format_from_name(file_name: str) -> str:
        """Extrae la extensión limpia de un nombre de archivo."""
        ext = Path(file_name).suffix.lower().lstrip('.')
        return ext if ext else 'txt'
