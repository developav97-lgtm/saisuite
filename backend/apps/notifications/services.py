"""
SaiSuite — Notifications: Services
Toda la lógica de negocio de notificaciones y comentarios.
Regla: NUNCA lógica de negocio en views o modelos.
"""
import re
import logging
from collections import defaultdict
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from .models import Notificacion, Comentario, PreferenciaNotificacion

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificacionService:
    """
    Servicio para crear y gestionar notificaciones genéricas.
    Punto único de creación: cualquier módulo que necesite notificar
    llama a NotificacionService.crear().
    """

    @staticmethod
    def crear(
        usuario: User,
        tipo: str,
        titulo: str,
        mensaje: str,
        objeto_relacionado: models.Model,
        url_accion: str = '',
        ancla: str = '',
        metadata: Optional[dict] = None,
    ) -> Optional[Notificacion]:
        """
        Crea una notificación respetando las preferencias del usuario.

        Returns:
            Notificacion creada, o None si está desactivada en preferencias
            o el usuario no tiene company (valmen_admin sin tenant).
        """
        if not getattr(usuario, 'company_id', None):
            # valmen_admin / usuarios sin tenant no reciben notificaciones in-app
            return None

        preferencia, _ = PreferenciaNotificacion.objects.get_or_create(
            company=usuario.company,
            usuario=usuario,
            tipo=tipo,
            defaults={'habilitado_app': True},
        )

        if not preferencia.habilitado_app:
            return None

        content_type = ContentType.objects.get_for_model(objeto_relacionado)

        notificacion = Notificacion.objects.create(
            company=usuario.company,
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            content_type=content_type,
            object_id=objeto_relacionado.pk,
            url_accion=url_accion,
            ancla=ancla,
            metadata=metadata or {},
        )
        logger.info(
            'notificacion_creada',
            extra={'tipo': tipo, 'usuario': str(usuario.id), 'notificacion': str(notificacion.id)},
        )
        return notificacion

    @staticmethod
    def marcar_leida(notificacion_id: str, usuario: User) -> Notificacion:
        """Marca una notificación del usuario como leída."""
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=usuario)
        if not notificacion.leida:
            notificacion.leida    = True
            notificacion.leida_en = timezone.now()
            notificacion.save(update_fields=['leida', 'leida_en', 'updated_at'])
        return notificacion

    @staticmethod
    def marcar_no_leida(notificacion_id: str, usuario: User) -> 'Notificacion':
        """Marca una notificación del usuario como no leída."""
        from django.utils import timezone  # noqa: F401 — already imported at module level
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=usuario)
        if notificacion.leida:
            notificacion.leida    = False
            notificacion.leida_en = None
            notificacion.save(update_fields=['leida', 'leida_en', 'updated_at'])
        return notificacion

    @staticmethod
    def marcar_todas_leidas(usuario: User) -> int:
        """Marca todas las notificaciones sin leer del usuario como leídas."""
        count = Notificacion.objects.filter(usuario=usuario, leida=False).update(
            leida=True, leida_en=timezone.now(),
        )
        logger.info('notificaciones_marcadas_leidas', extra={'usuario': str(usuario.id), 'count': count})
        return count

    @staticmethod
    def listar_sin_leer(usuario: User):
        ahora = timezone.now()
        return (
            Notificacion.objects
            .filter(usuario=usuario, leida=False)
            .exclude(snoozed_until__gt=ahora)
            .filter(
                models.Q(recordatorio_en__isnull=True) |
                models.Q(recordatorio_en__lte=ahora)
            )
            .select_related('content_type')
            .order_by('-created_at')
        )

    @staticmethod
    def contar_sin_leer(usuario: User) -> int:
        ahora = timezone.now()
        return (
            Notificacion.objects
            .filter(usuario=usuario, leida=False)
            .exclude(snoozed_until__gt=ahora)
            .filter(
                models.Q(recordatorio_en__isnull=True) |
                models.Q(recordatorio_en__lte=ahora)
            )
            .count()
        )

    @staticmethod
    def agrupar_notificaciones(usuario: User) -> list:
        """
        Agrupa notificaciones no leídas del mismo tipo sobre el mismo objeto.
        Excluye snoozed y recordatorios futuros.
        """
        from .serializers import NotificacionSerializer

        ahora = timezone.now()
        notificaciones = (
            Notificacion.objects
            .filter(usuario=usuario, leida=False)
            .exclude(snoozed_until__gt=ahora)
            .filter(
                models.Q(recordatorio_en__isnull=True) |
                models.Q(recordatorio_en__lte=ahora)
            )
            .select_related('content_type')
            .order_by('-created_at')
        )

        # Agrupar por (tipo, content_type_id, object_id)
        grupos: dict = defaultdict(list)
        for notif in notificaciones:
            key = f"{notif.tipo}_{notif.content_type_id}_{notif.object_id}"
            grupos[key].append(notif)

        resultado = []
        for key, notifs in grupos.items():
            if len(notifs) > 1:
                primera = notifs[0]
                objeto_nombre = ''
                try:
                    obj = primera.objeto_relacionado
                    if obj is not None:
                        objeto_nombre = getattr(obj, 'nombre', None) or getattr(obj, 'titulo', None) or str(obj)
                except Exception:
                    objeto_nombre = primera.metadata.get('objeto_nombre', '')

                if not objeto_nombre:
                    objeto_nombre = primera.metadata.get('objeto_nombre', '')

                autores = []
                for n in notifs[:3]:
                    nombre = n.metadata.get('autor_nombre', '')
                    if nombre and nombre not in autores:
                        autores.append(nombre)

                tipo_display = primera.get_tipo_display().lower()
                titulo = f"{len(notifs)} {tipo_display}s en {objeto_nombre}" if objeto_nombre else f"{len(notifs)} {tipo_display}s"

                resultado.append({
                    'tipo': 'grupo',
                    'id': key,
                    'cantidad': len(notifs),
                    'tipo_notificacion': primera.tipo,
                    'titulo': titulo,
                    'autores': autores,
                    'notificaciones_ids': [str(n.id) for n in notifs],
                    'url_accion': primera.url_accion,
                    'ancla': primera.ancla,
                    'created_at': primera.created_at.isoformat(),
                    'metadata': {
                        'objeto_nombre': objeto_nombre,
                        'objeto_codigo': primera.metadata.get('objeto_codigo', ''),
                        'proyecto_nombre': primera.metadata.get('proyecto_nombre', ''),
                    },
                })
            else:
                resultado.append({
                    'tipo': 'individual',
                    'notificacion': NotificacionSerializer(notifs[0]).data,
                })

        resultado.sort(
            key=lambda x: x.get('created_at') if x['tipo'] == 'grupo'
            else x['notificacion']['created_at'],
            reverse=True,
        )
        return resultado

    @staticmethod
    def marcar_grupo_leidas(notificaciones_ids: list, usuario: User) -> int:
        """Marca leídas todas las notificaciones del grupo que pertenecen al usuario."""
        count = Notificacion.objects.filter(
            id__in=notificaciones_ids,
            usuario=usuario,
            leida=False,
        ).update(leida=True, leida_en=timezone.now())
        return count

    @staticmethod
    def snooze(notificacion_id: str, usuario: User, minutos: int) -> Notificacion:
        """Pospone una notificación por N minutos."""
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=usuario)
        notificacion.snoozed_until = timezone.now() + timezone.timedelta(minutes=minutos)
        notificacion.save(update_fields=['snoozed_until', 'updated_at'])
        return notificacion

    @staticmethod
    def remind_me(notificacion_id: str, usuario: User, minutos: int) -> Notificacion:
        """
        Marca la notificación original como leída y crea un recordatorio
        para N minutos en el futuro usando el mismo objeto relacionado.
        """
        original = Notificacion.objects.get(id=notificacion_id, usuario=usuario)

        # Marcar original como leída
        if not original.leida:
            original.leida = True
            original.leida_en = timezone.now()
            original.save(update_fields=['leida', 'leida_en', 'updated_at'])

        recordatorio_en = timezone.now() + timezone.timedelta(minutes=minutos)

        recordatorio = Notificacion.objects.create(
            company=usuario.company,
            usuario=usuario,
            tipo='recordatorio',
            titulo=f'Recordatorio: {original.titulo}',
            mensaje=original.mensaje,
            content_type=original.content_type,
            object_id=original.object_id,
            url_accion=original.url_accion,
            ancla=original.ancla,
            metadata={**original.metadata, 'recordatorio_original_id': str(original.id)},
            recordatorio_en=recordatorio_en,
        )
        logger.info(
            'recordatorio_creado',
            extra={'original': str(original.id), 'recordatorio': str(recordatorio.id), 'minutos': minutos},
        )
        return recordatorio


class ComentarioService:
    """
    Servicio para gestionar comentarios con notificaciones automáticas.
    Soporta threading y menciones @username.
    """

    # Profundidad máxima de anidación permitida
    MAX_NIVEL = 2

    @staticmethod
    def crear_comentario(
        autor: User,
        objeto_relacionado: models.Model,
        texto: str,
        padre: Optional[Comentario] = None,
    ) -> Comentario:
        """
        Crea un comentario y dispara notificaciones automáticas.

        Notifica a:
        - Usuarios mencionados (@username)
        - Autor del comentario padre (si es respuesta)
        - Responsable del objeto (si tiene campo 'responsable')
        - Seguidores del objeto (si tiene campo 'followers')
        """
        if padre and ComentarioService._nivel_anidacion(padre) >= ComentarioService.MAX_NIVEL:
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f'No se permiten más de {ComentarioService.MAX_NIVEL} niveles de anidación.'
            )

        content_type = ContentType.objects.get_for_model(objeto_relacionado)

        comentario = Comentario.objects.create(
            company=autor.company,
            autor=autor,
            content_type=content_type,
            object_id=objeto_relacionado.pk,
            padre=padre,
            texto=texto,
        )

        # Detectar y vincular menciones (@prefijo_email, ej: @juan.perez para juan.perez@empresa.com)
        menciones_texto = re.findall(r'@([\w.]+)', texto)
        logger.info(
            'menciones_detectadas',
            extra={'menciones': menciones_texto, 'company_id': str(getattr(autor, 'company_id', None))},
        )
        if menciones_texto and getattr(autor, 'company_id', None):
            from django.db.models import Q
            filtro = Q()
            for m in menciones_texto:
                filtro |= Q(email__istartswith=f'{m}@')
            mencionados = list(User.objects.filter(filtro, company=autor.company))
            logger.info(
                'mencionados_encontrados',
                extra={'count': len(mencionados), 'usuarios': [str(u.id) for u in mencionados]},
            )
            comentario.menciones.set(mencionados)

        # Disparar notificaciones (en misma transacción, sin Celery por ahora)
        ComentarioService._notificar(comentario, objeto_relacionado)

        logger.info(
            'comentario_creado',
            extra={
                'comentario': str(comentario.id),
                'autor': str(autor.id),
                'objeto': f'{content_type.model}:{objeto_relacionado.pk}',
            },
        )
        return comentario

    @staticmethod
    def editar_comentario(comentario: Comentario, texto: str) -> Comentario:
        """Edita el texto de un comentario. Solo el autor debe llamar esto."""
        comentario.texto      = texto
        comentario.editado    = True
        comentario.editado_en = timezone.now()
        comentario.save(update_fields=['texto', 'editado', 'editado_en', 'updated_at'])
        return comentario

    # ── Helpers internos ──────────────────────────────────────────

    @staticmethod
    def _nivel_anidacion(comentario: Comentario) -> int:
        """Cuenta niveles de anidación sin recursión infinita (máx 10 pasos)."""
        nivel   = 0
        actual  = comentario
        visitados = set()
        while actual.padre_id and nivel < 10:
            if actual.id in visitados:
                break
            visitados.add(actual.id)
            actual = actual.padre
            nivel += 1
        return nivel

    @staticmethod
    def _construir_url(objeto: models.Model) -> str:
        """Construye URL frontend para el objeto."""
        rutas = {
            'tarea':    f'/proyectos/tareas/{objeto.pk}',
            'proyecto': f'/proyectos/{objeto.pk}',
        }
        model_name = objeto._meta.model_name
        return rutas.get(model_name, f'/{objeto._meta.app_label}/{model_name}/{objeto.pk}')

    @staticmethod
    def _construir_metadata(objeto: models.Model) -> dict:
        """
        Construye metadata de contexto para las notificaciones de comentario.
        Permite al frontend mostrar detalles del objeto sin una llamada adicional.
        """
        meta: dict = {
            'objeto_model': objeto._meta.model_name,
            'objeto_id':    str(objeto.pk),
        }
        if hasattr(objeto, 'nombre'):
            meta['objeto_nombre'] = str(objeto.nombre)
        if hasattr(objeto, 'codigo'):
            meta['objeto_codigo'] = str(objeto.codigo)
        # Contexto de proyecto para tareas
        if hasattr(objeto, 'proyecto') and objeto.proyecto is not None:  # type: ignore[union-attr]
            proyecto = objeto.proyecto  # type: ignore[union-attr]
            if hasattr(proyecto, 'nombre'):
                meta['proyecto_nombre'] = str(proyecto.nombre)
            if hasattr(proyecto, 'codigo'):
                meta['proyecto_codigo'] = str(proyecto.codigo)
        return meta

    @staticmethod
    def _notificar(comentario: Comentario, objeto_relacionado: models.Model) -> None:
        """Genera notificaciones para el comentario. Silencia errores para no romper el flujo."""
        try:
            ComentarioService._notificar_inner(comentario, objeto_relacionado)
        except Exception:
            logger.exception('error_generando_notificaciones_comentario',
                             extra={'comentario': str(comentario.id)})

    @staticmethod
    def _notificar_inner(comentario: Comentario, objeto_relacionado: models.Model) -> None:
        url_base   = ComentarioService._construir_url(objeto_relacionado)
        ancla      = f'#comentario-{comentario.id}'
        autor      = comentario.autor
        metadata   = ComentarioService._construir_metadata(objeto_relacionado)
        notificados: set = set()

        # 1. Usuarios mencionados
        for mencionado in comentario.menciones.all():
            if mencionado.id == autor.id:
                continue
            NotificacionService.crear(
                usuario=mencionado,
                tipo='mencion',
                titulo=f'{autor.get_full_name() or autor.email} te mencionó',
                mensaje=comentario.texto[:200],
                objeto_relacionado=objeto_relacionado,
                url_accion=url_base,
                ancla=ancla,
                metadata=metadata,
            )
            notificados.add(mencionado.id)

        # 2. Autor del comentario padre (respuesta)
        if comentario.padre_id and comentario.padre.autor_id != autor.id:
            padre_autor = comentario.padre.autor
            if padre_autor.id not in notificados:
                NotificacionService.crear(
                    usuario=padre_autor,
                    tipo='comentario',
                    titulo=f'{autor.get_full_name() or autor.email} respondió tu comentario',
                    mensaje=comentario.texto[:200],
                    objeto_relacionado=objeto_relacionado,
                    url_accion=url_base,
                    ancla=ancla,
                    metadata=metadata,
                )
                notificados.add(padre_autor.id)

        verbose = objeto_relacionado._meta.verbose_name.capitalize()

        # 3. Responsable del objeto
        responsable = getattr(objeto_relacionado, 'responsable', None)
        if responsable and responsable.id not in notificados and responsable.id != autor.id:
            NotificacionService.crear(
                usuario=responsable,
                tipo='comentario',
                titulo=f'Nuevo comentario en {verbose}',
                mensaje=comentario.texto[:200],
                objeto_relacionado=objeto_relacionado,
                url_accion=url_base,
                ancla=ancla,
                metadata=metadata,
            )
            notificados.add(responsable.id)

        # 4. Seguidores del objeto
        followers_mgr = getattr(objeto_relacionado, 'followers', None)
        if followers_mgr is not None:
            for follower in followers_mgr.all():
                if follower.id in notificados or follower.id == autor.id:
                    continue
                NotificacionService.crear(
                    usuario=follower,
                    tipo='comentario',
                    titulo=f'Nuevo comentario en {verbose}',
                    mensaje=comentario.texto[:200],
                    objeto_relacionado=objeto_relacionado,
                    url_accion=url_base,
                    ancla=ancla,
                    metadata=metadata,
                )
                notificados.add(follower.id)
