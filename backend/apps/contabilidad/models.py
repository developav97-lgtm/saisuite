"""
SaiSuite -- Contabilidad: Models
Modelos espejo de la contabilidad de Saiopen. READ-ONLY desde Saicloud.
MovimientoContable NO hereda BaseModel (usa company+conteo como clave unica).
"""
import logging
from django.db import models

logger = logging.getLogger(__name__)


class MovimientoContable(models.Model):
    """
    Espejo desnormalizado de la tabla GL de Firebird.
    Cada registro es un asiento contable individual.
    READ-ONLY desde Saicloud: solo se escribe via sync desde el agente.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.PROTECT,
        related_name='movimientos_contables',
        db_index=True,
    )
    conteo = models.IntegerField(
        help_text='PK del asiento en Firebird (GL.CONTEO)',
    )

    # -- Cuenta contable (PUC) desnormalizada --
    auxiliar = models.DecimalField(
        max_digits=18, decimal_places=4, db_index=True,
        help_text='Codigo auxiliar contable completo',
    )
    auxiliar_nombre = models.CharField(max_length=120)

    titulo_codigo = models.IntegerField(
        null=True, blank=True,
        help_text='PUC Nivel 1 - Titulo (1=Activo, 2=Pasivo, etc.)',
    )
    titulo_nombre = models.CharField(max_length=120, blank=True, default='')

    grupo_codigo = models.IntegerField(
        null=True, blank=True,
        help_text='PUC Nivel 2 - Grupo',
    )
    grupo_nombre = models.CharField(max_length=120, blank=True, default='')

    cuenta_codigo = models.IntegerField(
        null=True, blank=True,
        help_text='PUC Nivel 3 - Cuenta',
    )
    cuenta_nombre = models.CharField(max_length=120, blank=True, default='')

    subcuenta_codigo = models.IntegerField(
        null=True, blank=True,
        help_text='PUC Nivel 4 - Subcuenta',
    )
    subcuenta_nombre = models.CharField(max_length=120, blank=True, default='')

    # -- Tercero --
    tercero_id = models.CharField(
        max_length=30, db_index=True,
        help_text='Identificacion del tercero (NIT/CC)',
    )
    tercero_nombre = models.CharField(max_length=35, blank=True, default='')

    # -- Valores monetarios --
    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # -- Clasificacion del asiento --
    tipo = models.CharField(max_length=3, blank=True, default='')
    batch = models.IntegerField(null=True, blank=True)
    invc = models.CharField(
        max_length=15, blank=True, default='',
        help_text='Numero de factura/documento',
    )
    descripcion = models.CharField(max_length=120, blank=True, default='')

    # -- Fechas --
    fecha = models.DateField(db_index=True)
    duedate = models.DateField(
        null=True, blank=True,
        help_text='Fecha de vencimiento (para CxC y CxP)',
    )
    periodo = models.CharField(
        max_length=7, db_index=True,
        help_text='Periodo contable YYYY-MM',
    )

    # -- Dimensiones opcionales --
    departamento_codigo = models.SmallIntegerField(null=True, blank=True)
    departamento_nombre = models.CharField(max_length=40, blank=True, default='')

    centro_costo_codigo = models.SmallIntegerField(null=True, blank=True)
    centro_costo_nombre = models.CharField(max_length=40, blank=True, default='')

    proyecto_codigo = models.CharField(
        max_length=10, null=True, blank=True, db_index=True,
    )
    proyecto_nombre = models.CharField(max_length=60, blank=True, default='')

    actividad_codigo = models.CharField(max_length=3, null=True, blank=True)
    actividad_nombre = models.CharField(max_length=60, blank=True, default='')

    # -- Metadata de sincronizacion --
    sincronizado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cont_movimiento'
        unique_together = [('company', 'conteo')]
        indexes = [
            models.Index(fields=['company', 'fecha'], name='idx_cont_mov_fecha'),
            models.Index(fields=['company', 'periodo'], name='idx_cont_mov_periodo'),
            models.Index(fields=['company', 'auxiliar'], name='idx_cont_mov_auxiliar'),
            models.Index(fields=['company', 'titulo_codigo'], name='idx_cont_mov_titulo'),
            models.Index(fields=['company', 'tercero_id'], name='idx_cont_mov_tercero'),
            models.Index(fields=['company', 'proyecto_codigo'], name='idx_cont_mov_proyecto'),
            models.Index(fields=['company', 'departamento_codigo'], name='idx_cont_mov_depto'),
            models.Index(fields=['company', 'fecha', 'titulo_codigo'], name='idx_cont_mov_fecha_tit'),
        ]
        verbose_name = 'Movimiento contable'
        verbose_name_plural = 'Movimientos contables'
        ordering = ['-fecha', '-conteo']

    def __str__(self):
        return f'[{self.periodo}] {self.auxiliar} D={self.debito} C={self.credito}'


class ConfiguracionContable(models.Model):
    """
    Configuracion contable por empresa. OneToOne.
    Controla estado de sincronizacion y features habilitadas.
    """
    company = models.OneToOneField(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='config_contable',
        primary_key=True,
    )
    usa_departamentos_cc = models.BooleanField(
        default=False,
        help_text='La empresa usa departamentos y centros de costo en Saiopen',
    )
    usa_proyectos_actividades = models.BooleanField(
        default=False,
        help_text='La empresa usa proyectos y actividades en Saiopen',
    )
    ultimo_conteo_gl = models.BigIntegerField(
        default=0,
        help_text='Ultimo conteo GL sincronizado (watermark incremental)',
    )
    ultima_sync_gl = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha/hora de la ultima sincronizacion de GL exitosa',
    )
    ultima_sync_acct = models.DateTimeField(
        null=True, blank=True,
        help_text='Fecha/hora de la ultima sincronizacion de ACCT exitosa',
    )
    sync_activo = models.BooleanField(
        default=False,
        help_text='True si la sincronizacion esta configurada y activa',
    )
    sync_error = models.TextField(
        blank=True, default='',
        help_text='Ultimo error de sincronizacion (vacio si OK)',
    )

    class Meta:
        db_table = 'cont_configuracion'
        verbose_name = 'Configuracion contable'
        verbose_name_plural = 'Configuraciones contables'

    def __str__(self):
        status = 'activo' if self.sync_activo else 'inactivo'
        return f'Config contable {self.company.name} ({status})'


class CuentaContable(models.Model):
    """
    Espejo del plan de cuentas (ACCT) de Saiopen.
    Se sincroniza completo en cada sync de cuentas.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='cuentas_contables',
        db_index=True,
    )
    codigo = models.DecimalField(
        max_digits=18, decimal_places=4,
        help_text='Codigo contable auxiliar',
    )
    descripcion = models.CharField(max_length=120)
    nivel = models.SmallIntegerField(
        default=0,
        help_text='Nivel jerarquico en el PUC (1=titulo, 2=grupo, etc.)',
    )
    clase = models.CharField(
        max_length=1, blank=True, default='',
        help_text='Clase de la cuenta (A=activo, P=pasivo, etc.)',
    )
    tipo = models.CharField(
        max_length=3, blank=True, default='',
        help_text='Tipo de cuenta en Saiopen',
    )
    titulo_codigo = models.IntegerField(default=0)
    grupo_codigo = models.IntegerField(default=0)
    cuenta_codigo = models.IntegerField(default=0)
    subcuenta_codigo = models.IntegerField(default=0)
    posicion_financiera = models.IntegerField(
        default=0,
        help_text='Posicion en el estado financiero',
    )

    class Meta:
        db_table = 'cont_cuenta_contable'
        unique_together = [('company', 'codigo')]
        verbose_name = 'Cuenta contable'
        verbose_name_plural = 'Cuentas contables'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descripcion}'
