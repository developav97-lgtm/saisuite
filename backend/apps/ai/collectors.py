"""
SaiSuite — AI: Data Collectors
Recolectan datos del sistema para alimentar el contexto del AI Orchestrator.

REGLA INQUEBRANTABLE:
  NUNCA usar .create(), .update(), .delete(), .save() — SOLO LECTURA.
  Todos los queries filtran por company (multi-tenant).

Formato de salida:
  - String legible con secciones ## y listas -
  - Cifras monetarias con formato $ COP
  - Máximo ~1500 tokens por collector
"""
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

# Mapa de título PUC → nombre para contexto del IA
TITULOS_PUC = {
    1: 'Activos',
    2: 'Pasivos',
    3: 'Patrimonio',
    4: 'Ingresos',
    5: 'Costos de ventas',
    6: 'Gastos',
    7: 'Costos de producción',
    8: 'Costo de producción de lo vendido',
    9: 'Cuentas de orden',
}


def _fmt_currency(value) -> str:
    """Formatea un valor Decimal/float como moneda COP."""
    if value is None:
        return '$0'
    try:
        v = float(value)
        sign = '-' if v < 0 else ''
        return f'{sign}${abs(v):,.0f}'
    except (TypeError, ValueError):
        return '$0'


def _safe_ratio(numerador, denominador) -> float:
    """División segura que evita ZeroDivisionError."""
    try:
        d = float(denominador)
        if d == 0:
            return 0.0
        return float(numerador) / d
    except (TypeError, ValueError):
        return 0.0


# ══════════════════════════════════════════════════════════════════
# Base
# ══════════════════════════════════════════════════════════════════


class BaseDataCollector:
    """
    Clase base para recolectores de datos por módulo.
    SOLO LECTURA — nunca create/update/delete.
    """

    def collect(self, company, query: str, user=None) -> str:
        """
        Retorna contexto como string formateado para el prompt del IA.
        Implementar en cada subclase.
        """
        raise NotImplementedError


# ══════════════════════════════════════════════════════════════════
# DashboardCollector
# ══════════════════════════════════════════════════════════════════


class DashboardCollector(BaseDataCollector):
    """
    Recolecta datos financieros/contables de MovimientoContable.
    Fuentes: MovimientoContable, ConfiguracionContable
    """

    def collect(self, company, query: str, user=None) -> str:
        from apps.contabilidad.models import ConfiguracionContable, MovimientoContable

        anio = date.today().year
        anio_anterior = anio - 1

        qs = MovimientoContable.objects.filter(company=company)
        qs_anio = qs.filter(periodo__startswith=str(anio))
        qs_anterior = qs.filter(periodo__startswith=str(anio_anterior))

        # Estado de sync
        sync_status = 'No configurada'
        try:
            config = ConfiguracionContable.objects.get(company=company)
            if config.sync_activo:
                sync_status = f'Activa — última sync: {config.ultima_sync_gl.strftime("%d/%m/%Y %H:%M") if config.ultima_sync_gl else "nunca"}'
            else:
                sync_status = 'Inactiva'
        except ConfiguracionContable.DoesNotExist:
            pass

        # Resumen por título (año en curso) — 1 query
        totales = (
            qs_anio
            .filter(titulo_codigo__isnull=False, titulo_codigo__in=[1, 2, 3, 4, 5, 6])
            .values('titulo_codigo', 'titulo_nombre')
            .annotate(total_debito=Sum('debito'), total_credito=Sum('credito'))
            .order_by('titulo_codigo')
        )

        # Calcular saldos netos por título
        saldos: dict[int, dict] = {}
        for row in totales:
            cod = row['titulo_codigo']
            deb = row['total_debito'] or Decimal('0')
            cre = row['total_credito'] or Decimal('0')
            saldos[cod] = {
                'nombre': TITULOS_PUC.get(cod, row['titulo_nombre'] or f'Título {cod}'),
                'debito': deb,
                'credito': cre,
                'neto': deb - cre,
            }

        # Ingresos (título 4) = saldo crédito
        ingresos = float(saldos.get(4, {}).get('credito', 0))
        # Costos (título 5) = saldo débito
        costos = float(saldos.get(5, {}).get('debito', 0))
        # Gastos (título 6) = saldo débito
        gastos = float(saldos.get(6, {}).get('debito', 0))
        utilidad = ingresos - costos - gastos

        # Comparativo año anterior — 1 query
        ant_agg = qs_anterior.filter(titulo_codigo=4).aggregate(ing_ant=Sum('credito'))
        ingresos_ant = float(ant_agg['ing_ant'] or 0)
        variacion = _safe_ratio(ingresos - ingresos_ant, ingresos_ant) * 100 if ingresos_ant else 0

        # Top 10 cuentas por movimiento total — 1 query
        top_cuentas = (
            qs_anio
            .filter(cuenta_codigo__isnull=False)
            .values('cuenta_codigo', 'cuenta_nombre')
            .annotate(
                total=Sum('debito') + Sum('credito'),
            )
            .order_by('-total')
            [:10]
        )

        # Activos y pasivos
        activos = float(saldos.get(1, {}).get('debito', 0)) - float(saldos.get(1, {}).get('credito', 0))
        pasivos = float(saldos.get(2, {}).get('credito', 0)) - float(saldos.get(2, {}).get('debito', 0))
        patrimonio = float(saldos.get(3, {}).get('credito', 0)) - float(saldos.get(3, {}).get('debito', 0))

        margen = _safe_ratio(utilidad, ingresos) * 100

        lines = [
            f'## Resumen Financiero {anio}',
            f'- Sincronización contable: {sync_status}',
            f'- Ingresos: {_fmt_currency(ingresos)}',
            f'- Costos de ventas: {_fmt_currency(costos)}',
            f'- Gastos operacionales: {_fmt_currency(gastos)}',
            f'- Utilidad neta: {_fmt_currency(utilidad)} (margen {margen:.1f}%)',
            '',
            f'## Balance General {anio}',
            f'- Activos totales: {_fmt_currency(activos)}',
            f'- Pasivos totales: {_fmt_currency(pasivos)}',
            f'- Patrimonio: {_fmt_currency(patrimonio)}',
            '',
            f'## Comparativo vs {anio_anterior}',
            f'- Ingresos {anio_anterior}: {_fmt_currency(ingresos_ant)}',
            f'- Ingresos {anio}: {_fmt_currency(ingresos)}',
            f'- Variación: {variacion:+.1f}%',
        ]

        if top_cuentas:
            lines.append('')
            lines.append('## Top 10 Cuentas por Movimiento')
            for i, c in enumerate(top_cuentas, 1):
                nombre = c['cuenta_nombre'] or f'Cuenta {c["cuenta_codigo"]}'
                lines.append(f'- {i}. [{c["cuenta_codigo"]}] {nombre}: {_fmt_currency(c["total"])}')

        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════
# ProyectosCollector
# ══════════════════════════════════════════════════════════════════


class ProyectosCollector(BaseDataCollector):
    """
    Recolecta datos de proyectos, fases, tareas e hitos.
    Fuentes: Project, Phase, Task, Milestone, TimesheetEntry
    """

    def collect(self, company, query: str, user=None) -> str:
        from apps.proyectos.models import Milestone, Project, Task

        hoy = date.today()
        en_30_dias = hoy + timedelta(days=30)

        # Proyectos activos — 1 query con prefetch de fases
        proyectos = list(
            Project.all_objects
            .filter(company=company, activo=True)
            .exclude(estado__in=['closed', 'cancelled'])
            .select_related('gerente')
            .prefetch_related('phases')
            [:20]
        )

        lines = [
            f'## Proyectos Activos ({len(proyectos)} en total)',
        ]

        if not proyectos:
            lines.append('- Sin proyectos activos en este momento.')
        else:
            for p in proyectos:
                avance = float(p.porcentaje_avance)
                presupuesto = float(p.presupuesto_total)
                fases_total = p.phases.count()
                fases_activas = p.phases.filter(estado='active').count()
                lines.append(
                    f'- [{p.codigo}] {p.nombre}: {avance:.0f}% avance | '
                    f'Estado: {p.get_estado_display()} | '
                    f'Presupuesto: {_fmt_currency(presupuesto)} | '
                    f'Fases: {fases_activas}/{fases_total} activas'
                )

        # Tareas del usuario (pendientes, bloqueadas, vencidas) — 1 query
        user_tasks_qs = (
            Task.all_objects
            .filter(
                company=company,
                estado__in=['todo', 'in_progress', 'blocked'],
            )
            .select_related('proyecto', 'fase')
        )
        if user:
            user_tasks_qs = user_tasks_qs.filter(responsable=user)

        user_tasks = list(user_tasks_qs[:15])

        vencidas = [t for t in user_tasks if t.fecha_limite and t.fecha_limite < hoy]
        bloqueadas = [t for t in user_tasks if t.estado == 'blocked']
        pendientes = [t for t in user_tasks if t.estado in ('todo', 'in_progress') and (not t.fecha_limite or t.fecha_limite >= hoy)]

        lines.append('')
        if user:
            lines.append(f'## Mis Tareas ({getattr(user, 'full_name', None) or user.email})')
        else:
            lines.append('## Tareas del equipo')

        lines.append(f'- Pendientes/En progreso: {len(pendientes)}')
        lines.append(f'- Bloqueadas: {len(bloqueadas)}')
        lines.append(f'- Vencidas: {len(vencidas)}')

        if vencidas:
            lines.append('')
            lines.append('### Tareas vencidas (requieren atención inmediata):')
            for t in vencidas[:5]:
                dias = (hoy - t.fecha_limite).days
                lines.append(
                    f'  - [{t.codigo or t.id}] {t.nombre} — '
                    f'{t.proyecto.codigo}/{t.fase.nombre} — '
                    f'vencida hace {dias} día(s)'
                )

        if bloqueadas:
            lines.append('')
            lines.append('### Tareas bloqueadas:')
            for t in bloqueadas[:5]:
                lines.append(
                    f'  - [{t.codigo or t.id}] {t.nombre} — {t.proyecto.codigo}'
                )

        # Hitos próximos 30 días — 1 query
        hitos = list(
            Milestone.all_objects
            .filter(
                company=company,
                facturado=False,
                facturable=True,
            )
            .select_related('proyecto')
            .order_by('created_at')
            [:10]
        )

        lines.append('')
        lines.append(f'## Hitos próximos (facturable, sin facturar)')
        if not hitos:
            lines.append('- Sin hitos pendientes de facturación.')
        else:
            for h in hitos:
                lines.append(
                    f'- {h.proyecto.codigo}: {h.nombre} — '
                    f'{_fmt_currency(h.valor_facturar)} ({h.porcentaje_proyecto}%)'
                )

        # Horas globales — 1 query
        horas_agg = (
            Task.all_objects
            .filter(company=company)
            .aggregate(
                est=Sum('horas_estimadas'),
                reg=Sum('horas_registradas'),
            )
        )
        horas_est = float(horas_agg['est'] or 0)
        horas_reg = float(horas_agg['reg'] or 0)
        eficiencia = _safe_ratio(horas_reg, horas_est) * 100

        lines.append('')
        lines.append('## Resumen de Horas')
        lines.append(f'- Estimadas: {horas_est:,.1f} h')
        lines.append(f'- Registradas: {horas_reg:,.1f} h')
        lines.append(f'- Uso: {eficiencia:.1f}%')

        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════
# TercerosCollector
# ══════════════════════════════════════════════════════════════════


class TercerosCollector(BaseDataCollector):
    """
    Recolecta datos de terceros de SaiCloud (Tercero) y Saiopen (TerceroSaiopen).
    Fuentes: Tercero, TerceroSaiopen
    """

    def collect(self, company, query: str, user=None) -> str:
        from apps.contabilidad.models import TerceroSaiopen
        from apps.terceros.models import Tercero, TipoTercero

        # Conteos por tipo — 1 query cada uno
        total_saicloud = Tercero.all_objects.filter(company=company).count()
        activos = Tercero.all_objects.filter(company=company, activo=True).count()
        inactivos = total_saicloud - activos

        por_tipo = (
            Tercero.all_objects
            .filter(company=company)
            .values('tipo_tercero')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        # Últimos 10 creados — 1 query
        ultimos = list(
            Tercero.all_objects
            .filter(company=company)
            .only('nombre_completo', 'tipo_tercero', 'created_at', 'activo')
            .order_by('-created_at')
            [:10]
        )

        # Terceros Saiopen (contabilidad) — conteo rápido
        saiopen_count = TerceroSaiopen.objects.filter(company=company).count()
        saiopen_clientes = TerceroSaiopen.objects.filter(company=company, es_cliente=True).count()
        saiopen_proveedores = TerceroSaiopen.objects.filter(company=company, es_proveedor=True).count()

        tipo_labels = {t.value: t.label for t in TipoTercero}

        lines = [
            '## Resumen de Terceros (SaiCloud)',
            f'- Total: {total_saicloud}',
            f'- Activos: {activos}',
            f'- Inactivos: {inactivos}',
            '',
            '## Por tipo:',
        ]

        for row in por_tipo:
            tipo = tipo_labels.get(row['tipo_tercero'], row['tipo_tercero'] or 'Sin tipo')
            lines.append(f'- {tipo}: {row["total"]}')

        lines.append('')
        lines.append('## Terceros Saiopen (contabilidad):')
        lines.append(f'- Total en Saiopen: {saiopen_count}')
        lines.append(f'- Clientes: {saiopen_clientes}')
        lines.append(f'- Proveedores: {saiopen_proveedores}')

        if ultimos:
            lines.append('')
            lines.append('## Últimos 10 terceros creados:')
            for t in ultimos:
                tipo = tipo_labels.get(t.tipo_tercero, t.tipo_tercero or 'N/A')
                estado = 'Activo' if t.activo else 'Inactivo'
                fecha = t.created_at.strftime('%d/%m/%Y')
                lines.append(f'- {t.nombre_completo} ({tipo}) — {estado} — creado {fecha}')

        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════
# ContabilidadCollector
# ══════════════════════════════════════════════════════════════════


class ContabilidadCollector(BaseDataCollector):
    """
    Recolecta datos contables detallados (balance de prueba, movimientos recientes).
    Fuentes: MovimientoContable, CuentaContable
    """

    def collect(self, company, query: str, user=None) -> str:
        from apps.contabilidad.models import MovimientoContable

        hoy = date.today()
        periodo_actual = hoy.strftime('%Y-%m')
        anio = hoy.year

        qs = MovimientoContable.objects.filter(company=company)

        # Balance de prueba resumido (clase 1-6) — 1 query
        balance = (
            qs
            .filter(titulo_codigo__isnull=False)
            .values('titulo_codigo')
            .annotate(
                total_debito=Sum('debito'),
                total_credito=Sum('credito'),
            )
            .order_by('titulo_codigo')
        )

        lines = [
            '## Balance de Prueba (Acumulado)',
        ]

        for row in balance:
            cod = row['titulo_codigo']
            nombre = TITULOS_PUC.get(cod, f'Título {cod}')
            deb = float(row['total_debito'] or 0)
            cre = float(row['total_credito'] or 0)
            saldo = deb - cre
            lines.append(
                f'- {cod} - {nombre}: '
                f'Débito {_fmt_currency(deb)} | Crédito {_fmt_currency(cre)} | Saldo {_fmt_currency(saldo)}'
            )

        # Top 10 cuentas con mayor movimiento — 1 query
        top_cuentas = (
            qs
            .filter(cuenta_codigo__isnull=False)
            .values('cuenta_codigo', 'cuenta_nombre')
            .annotate(
                movimiento=Sum('debito') + Sum('credito'),
                saldo=Sum('debito') - Sum('credito'),
            )
            .order_by('-movimiento')
            [:10]
        )

        lines.append('')
        lines.append('## Top 10 Cuentas por Movimiento Total')
        for c in top_cuentas:
            nombre = c['cuenta_nombre'] or f'Cuenta {c["cuenta_codigo"]}'
            lines.append(
                f'- [{c["cuenta_codigo"]}] {nombre}: '
                f'Movimiento {_fmt_currency(c["movimiento"])} | Saldo {_fmt_currency(c["saldo"])}'
            )

        # Movimientos del mes actual — estadísticas — 1 query
        mes_agg = qs.filter(periodo=periodo_actual).aggregate(
            total_mov=Count('conteo'),
            total_debito=Sum('debito'),
            total_credito=Sum('credito'),
        )

        lines.append('')
        lines.append(f'## Movimientos del mes ({periodo_actual})')
        lines.append(f'- Asientos registrados: {mes_agg["total_mov"] or 0}')
        lines.append(f'- Total débito: {_fmt_currency(mes_agg["total_debito"])}')
        lines.append(f'- Total crédito: {_fmt_currency(mes_agg["total_credito"])}')

        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════
# GeneralCollector
# ══════════════════════════════════════════════════════════════════


class GeneralCollector(BaseDataCollector):
    """
    Recolecta información general de la empresa, módulos y licencia.
    Fuentes: Company, CompanyModule, CompanyLicense, User
    """

    def collect(self, company, query: str, user=None) -> str:
        from django.contrib.auth import get_user_model

        from apps.companies.models import AIUsageLog, CompanyLicense, CompanyModule

        User = get_user_model()

        # Módulos activos
        modulos = list(
            CompanyModule.objects.filter(company=company, is_active=True)
            .values_list('module', flat=True)
        )

        # Licencia
        try:
            licencia = CompanyLicense.objects.get(company=company)
            lic_info = (
                f'Estado: {licencia.get_status_display()} | '
                f'Mensajes IA usados: {licencia.messages_used} | '
                f'Tokens IA: {licencia.ai_tokens_used}'
            )
            lic_vence = licencia.expires_at.strftime('%d/%m/%Y') if licencia.expires_at else 'N/A'
        except CompanyLicense.DoesNotExist:
            lic_info = 'Sin licencia registrada'
            lic_vence = 'N/A'

        # Usuarios activos
        usuarios_activos = User.objects.filter(
            company=company,
            is_active=True,
        ).count()

        lines = [
            '## Información de la Empresa',
            f'- Nombre: {company.name}',
            f'- NIT: {company.nit}',
            f'- Plan: {company.get_plan_display()}',
            f'- Saiopen integrado: {"Sí" if company.saiopen_enabled else "No"}',
            '',
            '## Módulos Activos',
            f'- {", ".join(modulos) if modulos else "Sin módulos configurados"}',
            '',
            '## Licencia y Uso IA',
            f'- {lic_info}',
            f'- Vence: {lic_vence}',
            '',
            '## Usuarios',
            f'- Usuarios activos: {usuarios_activos}',
        ]

        if user:
            lines.append('')
            lines.append('## Usuario actual')
            lines.append(f'- Nombre: {getattr(user, 'full_name', None) or user.email}')
            lines.append(f'- Email: {user.email}')
            lines.append(f'- Rol: {getattr(user, "role", "N/A")}')

        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════
# Registry
# ══════════════════════════════════════════════════════════════════

COLLECTORS: dict[str, BaseDataCollector] = {
    'dashboard': DashboardCollector(),
    'contabilidad': ContabilidadCollector(),
    'proyectos': ProyectosCollector(),
    'terceros': TercerosCollector(),
    'general': GeneralCollector(),
}
