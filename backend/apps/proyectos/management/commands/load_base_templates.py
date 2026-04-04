"""
Management command: load_base_templates
Carga las 5 plantillas base de proyecto para una empresa dada.

Uso:
    python manage.py load_base_templates --company <company_id>
    python manage.py load_base_templates --company <company_id> --overwrite

Las plantillas creadas son:
  1. Construcción (3 fases, 9 tareas)
  2. Desarrollo de Software (3 fases, 9 tareas)
  3. Evento (2 fases, 6 tareas)
  4. Marketing Campaign (3 fases, 9 tareas)
  5. Lanzamiento de Producto (3 fases, 9 tareas)
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

logger = logging.getLogger(__name__)

PLANTILLAS = [
    {
        'nombre': 'Proyecto de Construcción',
        'descripcion': 'Plantilla base para proyectos de obra civil y construcción.',
        'categoria': 'construccion',
        'icono': 'construction',
        'duracion_estimada': 180,
        'fases': [
            {
                'nombre': 'Diseño y Planeación',
                'descripcion': 'Elaboración de planos, diseños técnicos y obtención de permisos.',
                'orden': 1,
                'porcentaje_duracion': '15.00',
                'tareas': [
                    {'nombre': 'Levantamiento topográfico', 'orden': 1, 'duracion_dias': 5, 'prioridad': 3},
                    {'nombre': 'Diseño arquitectónico', 'orden': 2, 'duracion_dias': 15, 'prioridad': 3},
                    {'nombre': 'Obtención de licencias y permisos', 'orden': 3, 'duracion_dias': 7, 'prioridad': 4},
                ],
            },
            {
                'nombre': 'Construcción',
                'descripcion': 'Ejecución de la obra civil.',
                'orden': 2,
                'porcentaje_duracion': '70.00',
                'tareas': [
                    {'nombre': 'Movimiento de tierras y cimentación', 'orden': 1, 'duracion_dias': 20, 'prioridad': 4},
                    {'nombre': 'Estructura y mampostería', 'orden': 2, 'duracion_dias': 45, 'prioridad': 4},
                    {'nombre': 'Instalaciones hidráulicas y eléctricas', 'orden': 3, 'duracion_dias': 20, 'prioridad': 3},
                ],
            },
            {
                'nombre': 'Acabados y Entrega',
                'descripcion': 'Terminados, inspecciones y entrega al cliente.',
                'orden': 3,
                'porcentaje_duracion': '15.00',
                'tareas': [
                    {'nombre': 'Acabados interiores y exteriores', 'orden': 1, 'duracion_dias': 15, 'prioridad': 2},
                    {'nombre': 'Inspección técnica final', 'orden': 2, 'duracion_dias': 3, 'prioridad': 3},
                    {'nombre': 'Acta de entrega y cierre', 'orden': 3, 'duracion_dias': 2, 'prioridad': 4},
                ],
            },
        ],
    },
    {
        'nombre': 'Desarrollo de Software',
        'descripcion': 'Plantilla estándar para proyectos de desarrollo de software ágil.',
        'categoria': 'software',
        'icono': 'code',
        'duracion_estimada': 90,
        'fases': [
            {
                'nombre': 'Análisis y Diseño',
                'descripcion': 'Levantamiento de requisitos, diseño de arquitectura y prototipos.',
                'orden': 1,
                'porcentaje_duracion': '20.00',
                'tareas': [
                    {'nombre': 'Levantamiento de requisitos', 'orden': 1, 'duracion_dias': 5, 'prioridad': 4},
                    {'nombre': 'Diseño de arquitectura', 'orden': 2, 'duracion_dias': 5, 'prioridad': 3},
                    {'nombre': 'Diseño UX/UI y prototipos', 'orden': 3, 'duracion_dias': 8, 'prioridad': 3},
                ],
            },
            {
                'nombre': 'Desarrollo e Integración',
                'descripcion': 'Implementación de funcionalidades y pruebas técnicas.',
                'orden': 2,
                'porcentaje_duracion': '60.00',
                'tareas': [
                    {'nombre': 'Desarrollo de funcionalidades core', 'orden': 1, 'duracion_dias': 25, 'prioridad': 4},
                    {'nombre': 'Integración con sistemas externos', 'orden': 2, 'duracion_dias': 10, 'prioridad': 3},
                    {'nombre': 'Pruebas unitarias e integración', 'orden': 3, 'duracion_dias': 10, 'prioridad': 3},
                ],
            },
            {
                'nombre': 'QA y Despliegue',
                'descripcion': 'Pruebas de aceptación, correcciones y despliegue en producción.',
                'orden': 3,
                'porcentaje_duracion': '20.00',
                'tareas': [
                    {'nombre': 'Pruebas de aceptación del usuario (UAT)', 'orden': 1, 'duracion_dias': 5, 'prioridad': 4},
                    {'nombre': 'Corrección de defectos', 'orden': 2, 'duracion_dias': 5, 'prioridad': 4},
                    {'nombre': 'Despliegue en producción y capacitación', 'orden': 3, 'duracion_dias': 3, 'prioridad': 3},
                ],
            },
        ],
    },
    {
        'nombre': 'Organización de Evento',
        'descripcion': 'Plantilla para la planificación y ejecución de eventos corporativos.',
        'categoria': 'evento',
        'icono': 'event',
        'duracion_estimada': 60,
        'fases': [
            {
                'nombre': 'Planificación del Evento',
                'descripcion': 'Definición de objetivos, logística, invitaciones y contratación de proveedores.',
                'orden': 1,
                'porcentaje_duracion': '60.00',
                'tareas': [
                    {'nombre': 'Definir concepto y presupuesto del evento', 'orden': 1, 'duracion_dias': 3, 'prioridad': 4},
                    {'nombre': 'Reservar venue y contratar proveedores', 'orden': 2, 'duracion_dias': 7, 'prioridad': 3},
                    {'nombre': 'Envío de invitaciones y gestión de registros', 'orden': 3, 'duracion_dias': 5, 'prioridad': 2},
                ],
            },
            {
                'nombre': 'Ejecución y Cierre',
                'descripcion': 'Realización del evento, coordinación logística y cierre.',
                'orden': 2,
                'porcentaje_duracion': '40.00',
                'tareas': [
                    {'nombre': 'Coordinación día del evento', 'orden': 1, 'duracion_dias': 2, 'prioridad': 4},
                    {'nombre': 'Post-evento: encuestas y agradecimientos', 'orden': 2, 'duracion_dias': 3, 'prioridad': 2},
                    {'nombre': 'Liquidación de cuentas con proveedores', 'orden': 3, 'duracion_dias': 5, 'prioridad': 3},
                ],
            },
        ],
    },
    {
        'nombre': 'Campaña de Marketing',
        'descripcion': 'Plantilla para campañas de marketing digital e integrado.',
        'categoria': 'marketing',
        'icono': 'campaign',
        'duracion_estimada': 45,
        'fases': [
            {
                'nombre': 'Estrategia y Creatividad',
                'descripcion': 'Definición de audiencia, mensajes clave y creación de contenidos.',
                'orden': 1,
                'porcentaje_duracion': '35.00',
                'tareas': [
                    {'nombre': 'Investigación de audiencia y competencia', 'orden': 1, 'duracion_dias': 5, 'prioridad': 3},
                    {'nombre': 'Brief creativo y estrategia de contenido', 'orden': 2, 'duracion_dias': 3, 'prioridad': 3},
                    {'nombre': 'Producción de piezas gráficas y videos', 'orden': 3, 'duracion_dias': 7, 'prioridad': 3},
                ],
            },
            {
                'nombre': 'Implementación',
                'descripcion': 'Lanzamiento de campañas en canales digitales y medios.',
                'orden': 2,
                'porcentaje_duracion': '45.00',
                'tareas': [
                    {'nombre': 'Configurar campañas Google Ads / Meta Ads', 'orden': 1, 'duracion_dias': 2, 'prioridad': 4},
                    {'nombre': 'Lanzamiento de campaña email marketing', 'orden': 2, 'duracion_dias': 2, 'prioridad': 3},
                    {'nombre': 'Publicación en redes sociales y SEO', 'orden': 3, 'duracion_dias': 14, 'prioridad': 2},
                ],
            },
            {
                'nombre': 'Análisis y Optimización',
                'descripcion': 'Monitoreo de métricas, optimización y reporte final.',
                'orden': 3,
                'porcentaje_duracion': '20.00',
                'tareas': [
                    {'nombre': 'Monitoreo diario de métricas', 'orden': 1, 'duracion_dias': 7, 'prioridad': 3},
                    {'nombre': 'Optimización de campañas activas', 'orden': 2, 'duracion_dias': 3, 'prioridad': 3},
                    {'nombre': 'Reporte final de resultados', 'orden': 3, 'duracion_dias': 2, 'prioridad': 2},
                ],
            },
        ],
    },
    {
        'nombre': 'Lanzamiento de Producto',
        'descripcion': 'Plantilla para el go-to-market de un nuevo producto o servicio.',
        'categoria': 'product_launch',
        'icono': 'rocket_launch',
        'duracion_estimada': 120,
        'fases': [
            {
                'nombre': 'Preparación del Producto',
                'descripcion': 'Validación final del producto, materiales de soporte y capacitación.',
                'orden': 1,
                'porcentaje_duracion': '30.00',
                'tareas': [
                    {'nombre': 'Pruebas de aceptación del producto final', 'orden': 1, 'duracion_dias': 10, 'prioridad': 4},
                    {'nombre': 'Preparación de materiales de ventas', 'orden': 2, 'duracion_dias': 7, 'prioridad': 3},
                    {'nombre': 'Capacitación del equipo comercial', 'orden': 3, 'duracion_dias': 3, 'prioridad': 3},
                ],
            },
            {
                'nombre': 'Lanzamiento al Mercado',
                'descripcion': 'Ejecución del lanzamiento: comunicados, demos y primeras ventas.',
                'orden': 2,
                'porcentaje_duracion': '40.00',
                'tareas': [
                    {'nombre': 'Comunicado de prensa y relaciones públicas', 'orden': 1, 'duracion_dias': 3, 'prioridad': 3},
                    {'nombre': 'Demo day y eventos de lanzamiento', 'orden': 2, 'duracion_dias': 5, 'prioridad': 4},
                    {'nombre': 'Inicio de campaña comercial', 'orden': 3, 'duracion_dias': 30, 'prioridad': 4},
                ],
            },
            {
                'nombre': 'Seguimiento Post-Lanzamiento',
                'descripcion': 'Análisis de adopción, soporte a primeros clientes y ajustes.',
                'orden': 3,
                'porcentaje_duracion': '30.00',
                'tareas': [
                    {'nombre': 'Soporte a primeros clientes (onboarding)', 'orden': 1, 'duracion_dias': 14, 'prioridad': 4},
                    {'nombre': 'Análisis de métricas de adopción', 'orden': 2, 'duracion_dias': 7, 'prioridad': 3},
                    {'nombre': 'Informe de lecciones aprendidas', 'orden': 3, 'duracion_dias': 3, 'prioridad': 2},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = (
        'Carga las 5 plantillas base de proyecto (construcción, software, evento, '
        'marketing, product_launch) para la empresa especificada.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            required=True,
            help='UUID o ID de la empresa donde se cargarán las plantillas.',
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Si se especifica, elimina las plantillas existentes de esa empresa antes de cargar.',
        )

    def handle(self, *args, **options):
        from apps.companies.models import Company
        from apps.proyectos.models import PlantillaProyecto, PlantillaFase, PlantillaTarea
        from decimal import Decimal

        company_id = options['company']
        overwrite  = options['overwrite']

        # Resolver empresa
        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            raise CommandError(f'Empresa con id={company_id!r} no encontrada.')

        if overwrite:
            deleted, _ = PlantillaProyecto.all_objects.filter(company=company).delete()
            self.stdout.write(
                self.style.WARNING(f'Se eliminaron {deleted} plantillas existentes.')
            )

        creadas = 0
        with transaction.atomic():
            for plantilla_data in PLANTILLAS:
                fases_data = plantilla_data.pop('fases')

                plantilla = PlantillaProyecto.objects.create(
                    company=company,
                    **plantilla_data,
                )
                logger.info(
                    'Plantilla base creada',
                    extra={'plantilla_id': str(plantilla.id), 'nombre': plantilla.nombre},
                )

                for fase_data in fases_data:
                    tareas_data = fase_data.pop('tareas')
                    fase = PlantillaFase.objects.create(
                        company=company,
                        plantilla_proyecto=plantilla,
                        **{k: Decimal(v) if k == 'porcentaje_duracion' else v for k, v in fase_data.items()},
                    )

                    for tarea_data in tareas_data:
                        PlantillaTarea.objects.create(
                            company=company,
                            plantilla_fase=fase,
                            **tarea_data,
                        )

                # Restore fases_data for potential re-use (not really needed but clean)
                plantilla_data['fases'] = fases_data
                creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Se cargaron exitosamente {creadas} plantillas base para la empresa "{company}".'
            )
        )
