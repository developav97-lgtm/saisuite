# FIX BUG #1: PDF Export Module

## Problema
```json
{
    "error": "El módulo de exportación PDF no está disponible."
}
```

## Causa
WeasyPrint no instalado o importación fallida.

## Solución

### 1. Verificar instalación de WeasyPrint

```bash
# En el contenedor Django
pip install weasyprint==60.1

# Verificar instalación
python -c "import weasyprint; print(weasyprint.__version__)"
```

### 2. Instalar dependencias del sistema (si no están)

```bash
# Ubuntu/Debian
apt-get update
apt-get install -y \
    python3-dev \
    python3-pip \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info
```

### 3. Modificar `apps/proyectos/services.py`

Cambiar el import lazy por import directo:

```python
# ANTES (import lazy - puede fallar silenciosamente)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# DESPUÉS (import directo con error claro)
from weasyprint import HTML, CSS

class ProyectoExportService:
    
    @staticmethod
    def generate_pdf(proyecto, user, options):
        """
        Genera PDF del proyecto usando WeasyPrint.
        """
        # Preparar datos
        context = ProyectoExportService._prepare_context(proyecto, user, options)
        
        # Renderizar HTML
        html_string = render_to_string('proyectos/export/pdf_report.html', context)
        
        # CSS
        css_string = ProyectoExportService._get_pdf_css()
        
        # Generar PDF
        pdf = HTML(string=html_string).write_pdf(
            stylesheets=[CSS(string=css_string)]
        )
        
        return pdf
```

### 4. Actualizar `requirements.txt`

Verificar que esté:
```
weasyprint==60.1
```

### 5. Rebuild del contenedor

```bash
docker-compose down
docker-compose build backend
docker-compose up -d
```

### 6. Test manual

```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/proyectos/<proyecto_id>/export/pdf/ \
     --output test.pdf
```

## Validación
- [ ] WeasyPrint instalado correctamente
- [ ] Dependencias sistema instaladas
- [ ] Endpoint devuelve PDF (no error JSON)
- [ ] PDF se abre correctamente
