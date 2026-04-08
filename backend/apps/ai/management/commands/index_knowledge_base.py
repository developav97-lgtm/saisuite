"""
SaiSuite — Management Command: index_knowledge_base
Indexa archivos de conocimiento en la base vectorial (pgvector).

Uso:
    python manage.py index_knowledge_base                  # indexar todo
    python manage.py index_knowledge_base --file PATH      # un archivo
    python manage.py index_knowledge_base --reindex         # borrar y re-indexar
    python manage.py index_knowledge_base --incremental     # solo archivos con hash diferente
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.ai.models import KnowledgeChunk, KnowledgeSource
from apps.ai.services import KnowledgeIngestionService
from apps.companies.models import Company

logger = logging.getLogger(__name__)

# Carpetas a indexar (relativas a la raíz del proyecto)
KNOWLEDGE_DIRS = [
    'docs/manuales',
    'docs/knowledge',
]

# Extensiones soportadas
SUPPORTED_EXTENSIONS = {'.md', '.txt', '.pdf', '.docx'}

# Mapeo carpeta → module/category defaults
FOLDER_DEFAULTS = {
    'manuales': {'module': 'general', 'category': 'manual'},
    'norma-colombiana': {'module': 'contabilidad', 'category': 'norma'},
    'faq': {'module': 'general', 'category': 'faq'},
    'guias': {'module': 'general', 'category': 'guia'},
    'knowledge': {'module': 'general', 'category': 'custom'},
}


class Command(BaseCommand):
    help = 'Indexa archivos de conocimiento en la base vectorial (pgvector)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Ruta a un archivo específico para indexar',
        )
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='Borrar TODOS los chunks e indexar desde cero',
        )
        parser.add_argument(
            '--incremental',
            action='store_true',
            help='Solo indexar archivos con hash diferente al registrado',
        )
        parser.add_argument(
            '--company-id',
            type=str,
            help='ID de la empresa (UUID). Si no se especifica, usa la primera empresa.',
        )

    def handle(self, *args, **options):
        company = self._get_company(options.get('company_id'))
        if not company:
            self.stderr.write(self.style.ERROR('No se encontró empresa.'))
            return

        self.stdout.write(
            self.style.NOTICE(f'Empresa: {company.name} ({company.id})')
        )

        if options['reindex']:
            self._reindex(company)

        if options['file']:
            self._index_single_file(options['file'], company)
        else:
            self._index_all(company, incremental=options['incremental'])

    def _get_company(self, company_id=None):
        """Obtiene la empresa para la indexación."""
        if company_id:
            return Company.objects.filter(id=company_id).first()
        # Default: primera empresa
        return Company.objects.first()

    def _reindex(self, company):
        """Borra todos los chunks y fuentes de la empresa."""
        chunk_count = KnowledgeChunk.all_objects.filter(
            company=company,
        ).count()
        source_count = KnowledgeSource.all_objects.filter(
            company=company,
        ).count()

        KnowledgeChunk.all_objects.filter(company=company).delete()
        KnowledgeSource.all_objects.filter(company=company).delete()

        self.stdout.write(self.style.WARNING(
            f'Re-index: eliminados {chunk_count} chunks y {source_count} fuentes.'
        ))

    def _index_single_file(self, file_path: str, company):
        """Indexa un solo archivo."""
        path = Path(file_path)
        if not path.exists():
            self.stderr.write(self.style.ERROR(f'Archivo no encontrado: {file_path}'))
            return

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            self.stderr.write(self.style.ERROR(
                f'Formato no soportado: {path.suffix}. '
                f'Válidos: {", ".join(SUPPORTED_EXTENSIONS)}'
            ))
            return

        module, category = self._infer_module_category(path)
        result = self._process_file(path, company, module, category)
        self._print_result(result)

    def _index_all(self, company, incremental: bool = False):
        """Indexa todos los archivos de las carpetas de conocimiento."""
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        files = []

        for dir_name in KNOWLEDGE_DIRS:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                self.stdout.write(self.style.WARNING(
                    f'Directorio no encontrado: {dir_name}'
                ))
                continue

            for ext in SUPPORTED_EXTENSIONS:
                files.extend(dir_path.rglob(f'*{ext}'))

        if not files:
            self.stdout.write(self.style.WARNING('No se encontraron archivos.'))
            return

        self.stdout.write(f'Encontrados {len(files)} archivos para indexar.')

        results = []
        for file_path in sorted(files):
            module, category = self._infer_module_category(file_path)

            if incremental:
                # Verificar si el hash ya existe
                content = file_path.read_bytes()
                import hashlib
                file_hash = hashlib.sha256(content).hexdigest()
                existing = KnowledgeSource.all_objects.filter(
                    company=company,
                    file_name=file_path.name,
                    source_channel='cli',
                    file_hash=file_hash,
                ).exists()
                if existing:
                    self.stdout.write(f'  [skip] {file_path.name} (sin cambios)')
                    continue

            result = self._process_file(file_path, company, module, category)
            results.append(result)

        self._print_summary(results)

    def _process_file(self, file_path: Path, company, module: str, category: str) -> dict:
        """Procesa un archivo individual."""
        try:
            content = file_path.read_bytes()
            result = KnowledgeIngestionService.ingest(
                file_content=content,
                file_name=file_path.name,
                company_id=company.id,
                module=module,
                category=category,
                source_channel='cli',
            )
            status_icon = {
                'created': '+',
                'updated': '~',
                'unchanged': '=',
                'empty': '!',
            }.get(result['status'], '?')
            self.stdout.write(
                f'  [{status_icon}] {file_path.name}: '
                f'{result["chunks_created"]} chunks, '
                f'{result["total_tokens"]} tokens '
                f'({result["status"]})'
            )
            return result
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                f'  [x] Error procesando {file_path.name}: {e}'
            ))
            return {
                'file_name': file_path.name,
                'chunks_created': 0,
                'total_tokens': 0,
                'status': 'error',
                'is_update': False,
            }

    def _infer_module_category(self, file_path: Path) -> tuple[str, str]:
        """Infiere module y category según la ruta del archivo."""
        parts = file_path.parts
        for part in parts:
            if part in FOLDER_DEFAULTS:
                defaults = FOLDER_DEFAULTS[part]
                return defaults['module'], defaults['category']
        return 'general', 'custom'

    def _print_result(self, result: dict):
        """Imprime resultado de un solo archivo."""
        self.stdout.write(self.style.SUCCESS(
            f'\nResultado: {result["file_name"]}\n'
            f'  Status: {result["status"]}\n'
            f'  Chunks: {result["chunks_created"]}\n'
            f'  Tokens: {result["total_tokens"]}'
        ))

    def _print_summary(self, results: list[dict]):
        """Imprime tabla resumen de indexación."""
        if not results:
            self.stdout.write(self.style.WARNING('No se procesaron archivos.'))
            return

        total_chunks = sum(r['chunks_created'] for r in results)
        total_tokens = sum(r['total_tokens'] for r in results)
        created = sum(1 for r in results if r['status'] == 'created')
        updated = sum(1 for r in results if r['status'] == 'updated')
        unchanged = sum(1 for r in results if r['status'] == 'unchanged')
        errors = sum(1 for r in results if r['status'] == 'error')

        self.stdout.write(self.style.SUCCESS(
            f'\n{"=" * 50}\n'
            f'Resumen de indexación\n'
            f'{"=" * 50}\n'
            f'  Archivos procesados: {len(results)}\n'
            f'  Creados: {created}\n'
            f'  Actualizados: {updated}\n'
            f'  Sin cambios: {unchanged}\n'
            f'  Errores: {errors}\n'
            f'  Total chunks: {total_chunks}\n'
            f'  Total tokens: {total_tokens}\n'
            f'{"=" * 50}'
        ))
