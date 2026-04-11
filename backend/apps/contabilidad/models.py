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


class TerceroSaiopen(models.Model):
    """
    Espejo de la tabla CUST de Saiopen (clientes, proveedores, empleados).
    Sync incremental por campo Version cada gl_interval_minutes.
    READ-ONLY desde Saicloud.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='terceros_saiopen',
        db_index=True,
    )
    id_n = models.CharField(
        max_length=30,
        help_text='Identificador interno Saiopen (ID_N)',
    )
    nit = models.CharField(max_length=30, blank=True, default='')
    nombre = models.CharField(max_length=120, blank=True, default='')
    direccion = models.CharField(max_length=120, blank=True, default='')
    ciudad = models.CharField(max_length=60, blank=True, default='')
    departamento = models.CharField(max_length=100, blank=True, default='')
    telefono = models.CharField(max_length=30, blank=True, default='')
    telefono2 = models.CharField(max_length=30, blank=True, default='')
    email = models.CharField(max_length=100, blank=True, default='')
    es_cliente = models.BooleanField(default=False)
    es_proveedor = models.BooleanField(default=False)
    es_empleado = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    # Cuentas contables del tercero
    acct = models.CharField(max_length=30, blank=True, default='',
                            help_text='Cuenta contable cliente (ACCT)')
    acctp = models.CharField(max_length=30, blank=True, default='',
                             help_text='Cuenta contable proveedor (ACCTP)')
    regimen = models.CharField(max_length=10, blank=True, default='')
    fecha_creacion = models.DateField(null=True, blank=True)
    descuento = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    creditlmt = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    version_saiopen = models.BigIntegerField(
        default=0,
        help_text='Version field from CUST trigger (change detection)',
    )
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cont_tercero_saiopen'
        unique_together = [('company', 'id_n')]
        verbose_name = 'Tercero Saiopen'
        verbose_name_plural = 'Terceros Saiopen'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.nit or self.id_n})'


class ListaSaiopen(models.Model):
    """
    Espejo de la tabla LISTA de Saiopen (departamentos y centros de costo).
    Tipo: 'DP' = departamento, 'CC' = centro de costo.
    """
    class Tipo(models.TextChoices):
        DEPARTAMENTO = 'DP', 'Departamento'
        CENTRO_COSTO = 'CC', 'Centro de costo'

    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='listas_saiopen',
        db_index=True,
    )
    tipo = models.CharField(max_length=2, choices=Tipo.choices, db_index=True)
    codigo = models.IntegerField()
    descripcion = models.CharField(max_length=80)
    activo = models.BooleanField(default=True)
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cont_lista_saiopen'
        unique_together = [('company', 'tipo', 'codigo')]
        verbose_name = 'Lista Saiopen (DP/CC)'
        verbose_name_plural = 'Listas Saiopen (DP/CC)'
        ordering = ['tipo', 'codigo']

    def __str__(self):
        return f'[{self.tipo}] {self.codigo} - {self.descripcion}'


class ProyectoSaiopen(models.Model):
    """
    Espejo de la tabla PROYECTOS de Saiopen.
    Permite relacionar movimientos GL con proyectos contables.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='proyectos_saiopen',
        db_index=True,
    )
    codigo = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=120, blank=True, default='')
    cliente_nit = models.CharField(max_length=30, blank=True, default='')
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_estimada_fin = models.DateField(null=True, blank=True)
    costo_estimado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, blank=True, default='')
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cont_proyecto_saiopen'
        unique_together = [('company', 'codigo')]
        verbose_name = 'Proyecto Saiopen'
        verbose_name_plural = 'Proyectos Saiopen'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descripcion}'


class ActividadSaiopen(models.Model):
    """
    Espejo de la tabla ACTIVIDADES de Saiopen.
    Actividades asociadas a proyectos.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='actividades_saiopen',
        db_index=True,
    )
    codigo = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=120, blank=True, default='')
    proyecto_codigo = models.CharField(max_length=10, blank=True, default='')
    departamento_codigo = models.IntegerField(default=0)
    centro_costo_codigo = models.IntegerField(default=0)
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cont_actividad_saiopen'
        unique_together = [('company', 'codigo', 'proyecto_codigo')]
        verbose_name = 'Actividad Saiopen'
        verbose_name_plural = 'Actividades Saiopen'
        ordering = ['proyecto_codigo', 'codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descripcion} (Proy: {self.proyecto_codigo})'


class ShipToSaiopen(models.Model):
    """
    Espejo de la tabla SHIPTO de Saiopen — direcciones de envío del tercero.
    PK compuesta: (ID_N, SUCCLIENTE). SUCCLIENTE=0 es la dirección principal.
    Se sincroniza atómicamente junto con CUST.
    READ-ONLY desde Saicloud.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='shipto_saiopen',
        db_index=True,
    )
    id_n = models.CharField(
        max_length=30,
        help_text='ID_N del tercero en CUST',
        db_index=True,
    )
    succliente = models.IntegerField(
        default=0,
        help_text='Número de sucursal. 0 = dirección principal.',
    )
    descripcion = models.CharField(max_length=120, blank=True, default='')
    nombre = models.CharField(max_length=120, blank=True, default='')
    addr1 = models.CharField(max_length=120, blank=True, default='')
    addr2 = models.CharField(max_length=120, blank=True, default='')
    ciudad = models.CharField(max_length=60, blank=True, default='')
    departamento = models.CharField(max_length=100, blank=True, default='')
    cod_dpto = models.CharField(max_length=3, blank=True, default='')
    cod_municipio = models.CharField(max_length=6, blank=True, default='')
    pais = models.CharField(max_length=60, blank=True, default='')
    telefono = models.CharField(max_length=30, blank=True, default='')
    email = models.CharField(max_length=100, blank=True, default='')
    zona = models.IntegerField(default=0)
    id_vend = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, blank=True, default='')
    es_principal = models.BooleanField(
        default=False,
        help_text='True si succliente == 0',
    )
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cont_shipto_saiopen'
        unique_together = [('company', 'id_n', 'succliente')]
        verbose_name = 'ShipTo Saiopen'
        verbose_name_plural = 'ShipTos Saiopen'
        ordering = ['id_n', 'succliente']

    def __str__(self):
        return f'{self.id_n} [{self.succliente}] {self.descripcion or self.nombre}'


class TributariaSaiopen(models.Model):
    """
    Espejo de la tabla TRIBUTARIA de Saiopen — info tributaria del tercero.
    Relación 1:1 con TerceroSaiopen. Se sincroniza atómicamente junto con CUST.
    READ-ONLY desde Saicloud.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='tributaria_saiopen',
        db_index=True,
    )
    id_n = models.CharField(
        max_length=30,
        help_text='ID_N del tercero en CUST',
    )
    tdoc = models.SmallIntegerField(
        default=0,
        help_text='Tipo de documento (FK a TRIBUTARIA_TIPODOCUMENTO)',
    )
    tipo_contribuyente = models.SmallIntegerField(
        default=0,
        help_text='1=persona jurídica, 2=persona natural',
    )
    primer_nombre = models.CharField(max_length=100, blank=True, default='')
    segundo_nombre = models.CharField(max_length=100, blank=True, default='')
    primer_apellido = models.CharField(max_length=100, blank=True, default='')
    segundo_apellido = models.CharField(max_length=100, blank=True, default='')
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cont_tributaria_saiopen'
        unique_together = [('company', 'id_n')]
        verbose_name = 'Tributaria Saiopen'
        verbose_name_plural = 'Tributarias Saiopen'
        ordering = ['id_n']

    def __str__(self):
        nombre = ' '.join(filter(None, [
            self.primer_nombre, self.segundo_nombre,
            self.primer_apellido, self.segundo_apellido,
        ]))
        return f'{self.id_n} - {nombre or "(jurídica)"}'


class FacturaEncabezado(models.Model):
    """
    Espejo denormalizado de OE (encabezados de facturación).
    READ-ONLY desde Saicloud: solo se escribe via sync desde el agente.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='facturas_encabezado',
        db_index=True,
    )

    # PK Firebird compuesta
    number = models.IntegerField()
    tipo = models.CharField(max_length=3, db_index=True)
    id_sucursal = models.SmallIntegerField(default=1)

    # Tercero
    tercero_id = models.CharField(max_length=30, db_index=True)
    tercero_nombre = models.CharField(max_length=120, blank=True, default='')

    # Vendedor
    salesman = models.SmallIntegerField(null=True, blank=True)
    salesman_nombre = models.CharField(max_length=60, blank=True, default='')

    # Fechas
    fecha = models.DateField(db_index=True)
    duedate = models.DateField(null=True, blank=True)
    periodo = models.CharField(max_length=7, db_index=True)

    # Montos
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    descuento_global = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Estado
    posted = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)

    # Moneda
    cod_moneda = models.CharField(max_length=5, blank=True, default='COP')

    # Dimensiones
    comentarios = models.TextField(blank=True, default='')

    # Metadata de sincronizacion
    sincronizado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cont_factura_encabezado'
        unique_together = [('company', 'number', 'tipo', 'id_sucursal')]
        indexes = [
            models.Index(fields=['company', 'periodo'], name='idx_fact_enc_periodo'),
            models.Index(fields=['company', 'tipo', 'fecha'], name='idx_fact_enc_tipo_fecha'),
            models.Index(fields=['company', 'tercero_id'], name='idx_fact_enc_tercero'),
            models.Index(fields=['company', 'salesman'], name='idx_fact_enc_salesman'),
        ]
        verbose_name = 'Factura encabezado'
        verbose_name_plural = 'Facturas encabezado'
        ordering = ['-fecha', '-number']

    def __str__(self):
        return f'[{self.tipo}] #{self.number} {self.tercero_nombre} ${self.total}'


class FacturaDetalle(models.Model):
    """
    Espejo denormalizado de OEDET (líneas de factura).
    READ-ONLY desde Saicloud: solo se escribe via sync desde el agente.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='facturas_detalle',
        db_index=True,
    )
    factura = models.ForeignKey(
        FacturaEncabezado,
        on_delete=models.CASCADE,
        related_name='detalles',
    )

    conteo = models.IntegerField(help_text='PK del detalle en Firebird (OEDET.CONTEO)')

    # Producto
    item_codigo = models.CharField(max_length=30, db_index=True)
    item_descripcion = models.CharField(max_length=120, blank=True, default='')
    location = models.CharField(max_length=3, blank=True, default='')

    # Cantidades
    qty_order = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    qty_ship = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Precios
    precio_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    precio_extendido = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    costo_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)

    # Impuestos y descuentos
    valor_iva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    porc_iva = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Márgenes
    margen_valor = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    margen_porcentaje = models.DecimalField(max_digits=7, decimal_places=2, default=0)

    # Proyecto
    proyecto_codigo = models.CharField(max_length=10, blank=True, default='')

    # Metadata de sincronizacion
    sincronizado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cont_factura_detalle'
        unique_together = [('company', 'conteo')]
        indexes = [
            models.Index(fields=['company', 'item_codigo'], name='idx_fact_det_item'),
        ]
        verbose_name = 'Factura detalle'
        verbose_name_plural = 'Facturas detalle'
        ordering = ['conteo']

    def __str__(self):
        return f'[{self.conteo}] {self.item_codigo} x{self.qty_ship} ${self.precio_extendido}'


class MovimientoCartera(models.Model):
    """
    Espejo de CARPRO — saldos de cuentas por cobrar y pagar.
    READ-ONLY desde Saicloud: solo se escribe via sync desde el agente.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='movimientos_cartera',
        db_index=True,
    )

    conteo = models.IntegerField(help_text='PK del registro en Firebird (CARPRO.CONTEO)')

    tercero_id = models.CharField(max_length=30, db_index=True)
    tercero_nombre = models.CharField(max_length=120, blank=True, default='')

    cuenta_contable = models.DecimalField(max_digits=18, decimal_places=4)
    tipo = models.CharField(max_length=3, blank=True, default='')
    batch = models.IntegerField(null=True, blank=True)
    invc = models.CharField(max_length=15, blank=True, default='')
    descripcion = models.CharField(max_length=120, blank=True, default='')

    fecha = models.DateField(db_index=True)
    duedate = models.DateField(null=True, blank=True)
    periodo = models.CharField(max_length=7, db_index=True)

    debito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    departamento = models.SmallIntegerField(null=True, blank=True)
    centro_costo = models.SmallIntegerField(null=True, blank=True)
    proyecto_codigo = models.CharField(max_length=10, blank=True, default='')

    tipo_cartera = models.CharField(
        max_length=3,
        choices=[('CXC', 'Cuentas por Cobrar'), ('CXP', 'Cuentas por Pagar')],
        db_index=True,
    )

    # Metadata de sincronizacion
    sincronizado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cont_movimiento_cartera'
        unique_together = [('company', 'conteo')]
        indexes = [
            models.Index(
                fields=['company', 'tercero_id', 'tipo_cartera'],
                name='idx_cart_tercero_tipo',
            ),
            models.Index(fields=['company', 'periodo'], name='idx_cart_periodo'),
            models.Index(fields=['company', 'duedate'], name='idx_cart_duedate'),
        ]
        verbose_name = 'Movimiento de cartera'
        verbose_name_plural = 'Movimientos de cartera'
        ordering = ['-fecha', '-conteo']

    def __str__(self):
        return f'[{self.tipo_cartera}] {self.tercero_nombre} D={self.debito} C={self.credito} S={self.saldo}'


class MovimientoInventario(models.Model):
    """
    Espejo de ITEMACT — movimientos transaccionales de inventario.
    READ-ONLY desde Saicloud: solo se escribe via sync desde el agente.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='movimientos_inventario',
        db_index=True,
    )

    conteo = models.IntegerField(help_text='PK del registro en Firebird (ITEMACT.CONTEO)')

    item_codigo = models.CharField(max_length=30, db_index=True)
    item_descripcion = models.CharField(max_length=120, blank=True, default='')
    location = models.CharField(max_length=3, db_index=True, default='')

    tercero_id = models.CharField(max_length=30, blank=True, default='')
    tipo = models.CharField(max_length=3, blank=True, default='')
    batch = models.IntegerField(null=True, blank=True)

    fecha = models.DateField(db_index=True)
    periodo = models.CharField(max_length=7, db_index=True)

    cantidad = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    valor_unitario = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    costo_peps = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_unidades = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    saldo_pesos = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    lote = models.CharField(max_length=30, blank=True, default='')
    serie = models.CharField(max_length=50, blank=True, default='')
    lote_vencimiento = models.DateField(null=True, blank=True)

    # Metadata de sincronizacion
    sincronizado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cont_movimiento_inventario'
        unique_together = [('company', 'conteo')]
        indexes = [
            models.Index(
                fields=['company', 'item_codigo', 'fecha'],
                name='idx_inv_item_fecha',
            ),
            models.Index(fields=['company', 'location'], name='idx_inv_location'),
            models.Index(fields=['company', 'periodo'], name='idx_inv_periodo'),
        ]
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-fecha', '-conteo']

    def __str__(self):
        return f'[{self.periodo}] {self.item_codigo} qty={self.cantidad} ${self.total}'


class TipdocSaiopen(models.Model):
    """
    Espejo de la tabla TIPDOC de Saiopen (catálogo de tipos de documento).
    PK Firebird: (CLASE, E, S).
    CLASE (3 chars) es el mismo valor que aparece en GL.TIPO / MovimientoContable.tipo.
    READ-ONLY desde Saicloud: solo escribe el agente Go vía SQS.
    """
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='tipdocs_saiopen',
        db_index=True,
    )
    # PK compuesta Firebird: CLASE + E + S
    clase        = models.CharField(max_length=3, help_text='TIPDOC.CLASE = GL.TIPO (ej: FAC, CE)')
    e            = models.SmallIntegerField(default=0, help_text='Entidad (E en Firebird)')
    s            = models.SmallIntegerField(default=0, help_text='Serie (S en Firebird)')
    tipo         = models.CharField(max_length=2, blank=True, default='')
    consecutivo  = models.IntegerField(default=0)
    descripcion  = models.CharField(max_length=35, blank=True, default='')
    sigla        = models.CharField(max_length=10, blank=True, default='',
                                    help_text='Abreviatura del tipo (ej: FACT, CE)')
    operar       = models.CharField(max_length=2, blank=True, default='')
    enviafacelect = models.CharField(max_length=1, blank=True, default='')
    prefijo_dian  = models.CharField(max_length=5, blank=True, default='')
    sincronizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'cont_tipdoc_saiopen'
        unique_together = [('company', 'clase', 'e', 's')]
        verbose_name    = 'Tipo de documento Saiopen'
        verbose_name_plural = 'Tipos de documento Saiopen'
        ordering        = ['clase', 'e', 's']

    def __str__(self):
        return f'{self.clase} ({self.sigla}) — {self.descripcion}'
