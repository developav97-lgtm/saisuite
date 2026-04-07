"""
Management command: sqs_worker
Inicia el worker que consume mensajes SQS del agente Go y los procesa.

Uso:
    python manage.py sqs_worker
    python manage.py sqs_worker --max-cycles 5   # para tests

En producción se corre como contenedor separado en ECS Fargate.
En desarrollo se puede correr en una terminal aparte.
"""
from django.core.management.base import BaseCommand

from apps.contabilidad.sqs_consumer import SQSWorker


class Command(BaseCommand):
    help = 'Consume mensajes SQS del agente Go y sincroniza datos contables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-cycles',
            type=int,
            default=0,
            help='Número máximo de ciclos de polling (0 = infinito)',
        )

    def handle(self, *args, **options):
        max_cycles = options['max_cycles']
        self.stdout.write(self.style.SUCCESS('Iniciando SQS worker...'))
        if max_cycles:
            self.stdout.write(f'Modo test: máximo {max_cycles} ciclos')

        worker = SQSWorker()
        worker.run(max_cycles=max_cycles)
