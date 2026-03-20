"""
SaiSuite — Módulo de Terceros
Personas naturales y jurídicas relacionadas con proyectos (clientes, proveedores, etc.)
"""
import logging
from django.db import models
from apps.core.models import BaseModel

logger = logging.getLogger(__name__)


class TipoIdentificacion(models.TextChoices):
    NIT    = 'nit',    'NIT'
    CC     = 'cc',     'Cédula de ciudadanía'
    CE     = 'ce',     'Cédula de extranjería'
    PAS    = 'pas',    'Pasaporte'
    OTRO   = 'otro',   'Otro'


class TipoPersona(models.TextChoices):
    NATURAL  = 'natural',  'Persona natural'
    JURIDICA = 'juridica', 'Persona jurídica'


class TipoTercero(models.TextChoices):
    CLIENTE        = 'cliente',        'Cliente'
    PROVEEDOR      = 'proveedor',      'Proveedor'
    SUBCONTRATISTA = 'subcontratista', 'Subcontratista'
    INTERVENTOR    = 'interventor',    'Interventor'
    CONSULTOR      = 'consultor',      'Consultor'
    EMPLEADO       = 'empleado',       'Empleado'
    OTRO           = 'otro',           'Otro'


class TipoDireccion(models.TextChoices):
    PRINCIPAL  = 'principal',  'Principal'
    SUCURSAL   = 'sucursal',   'Sucursal'
    BODEGA     = 'bodega',     'Bodega'
    FACTURACION = 'facturacion', 'Facturación'
    OTRO       = 'otro',       'Otro'


class Tercero(BaseModel):
    """
    Persona natural o jurídica vinculada a proyectos.
    Puede sincronizarse con el tercero equivalente en Saiopen.
    """
    codigo = models.CharField(max_length=50, db_index=True)

    tipo_identificacion   = models.CharField(max_length=20, choices=TipoIdentificacion.choices)
    numero_identificacion = models.CharField(max_length=50)

    # Campos para persona natural
    primer_nombre    = models.CharField(max_length=100, blank=True)
    segundo_nombre   = models.CharField(max_length=100, blank=True)
    primer_apellido  = models.CharField(max_length=100, blank=True)
    segundo_apellido = models.CharField(max_length=100, blank=True)

    # Campo para persona jurídica
    razon_social = models.CharField(max_length=255, blank=True)

    # Calculado automáticamente al guardar
    nombre_completo = models.CharField(max_length=512, db_index=True, editable=False)

    tipo_persona = models.CharField(max_length=10, choices=TipoPersona.choices)
    tipo_tercero = models.CharField(
        max_length=20, choices=TipoTercero.choices, blank=True,
        help_text='Clasificación principal. Un tercero puede tener varios roles via TerceroProyecto.',
    )

    # Contacto principal
    email    = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    celular  = models.CharField(max_length=30, blank=True)

    # Sincronización con Saiopen (gestionada por el agente)
    saiopen_id     = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    sai_key        = models.CharField(max_length=100, null=True, blank=True)
    saiopen_synced = models.BooleanField(default=False)

    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name        = 'Tercero'
        verbose_name_plural = 'Terceros'
        ordering            = ['nombre_completo']
        unique_together     = [('company', 'tipo_identificacion', 'numero_identificacion')]

    def __str__(self):
        return f'{self.nombre_completo} ({self.numero_identificacion})'

    def save(self, *args, **kwargs):
        self.nombre_completo = self._build_nombre_completo()
        super().save(*args, **kwargs)

    def _build_nombre_completo(self) -> str:
        if self.tipo_persona == TipoPersona.JURIDICA:
            return self.razon_social.strip()
        partes = [
            self.primer_nombre, self.segundo_nombre,
            self.primer_apellido, self.segundo_apellido,
        ]
        return ' '.join(p.strip() for p in partes if p.strip()) or self.razon_social.strip()


class TerceroDireccion(BaseModel):
    """
    Dirección de un tercero. Un tercero puede tener múltiples direcciones.
    Solo una puede ser es_principal=True por tercero.
    """
    tercero = models.ForeignKey(Tercero, on_delete=models.CASCADE, related_name='direcciones')

    tipo           = models.CharField(max_length=20, choices=TipoDireccion.choices, default=TipoDireccion.PRINCIPAL)
    nombre_sucursal = models.CharField(max_length=255, blank=True)

    pais            = models.CharField(max_length=100, default='Colombia')
    departamento    = models.CharField(max_length=100)
    ciudad          = models.CharField(max_length=100)
    direccion_linea1 = models.CharField(max_length=255)
    direccion_linea2 = models.CharField(max_length=255, blank=True)
    codigo_postal   = models.CharField(max_length=20, blank=True)

    nombre_contacto  = models.CharField(max_length=255, blank=True)
    telefono_contacto = models.CharField(max_length=30, blank=True)
    email_contacto   = models.EmailField(blank=True)

    # Referencia Saiopen
    saiopen_linea_id = models.CharField(max_length=50, null=True, blank=True)

    activa      = models.BooleanField(default=True)
    es_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Dirección de tercero'
        verbose_name_plural = 'Direcciones de tercero'
        ordering            = ['-es_principal', 'tipo']

    def __str__(self):
        return f'{self.tercero.nombre_completo} — {self.direccion_linea1}, {self.ciudad}'
