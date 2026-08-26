import io

import barcode
from barcode.writer import ImageWriter

# Opciones de generación deliberadas (mitigación NFR-02 / AC-17, ver AGENTS.md): un
# `module_width` por debajo de ~0.3mm vuelve el código ilegible aunque se vea bien en
# pantalla. Se verifica con un lector independiente (pyzbar) en los tests.
_MODULE_WIDTH_MM = 0.3
_MODULE_HEIGHT_MM = 15.0
_QUIET_ZONE_MM = 6.5
_DPI = 300


def generar_codigo_barras(nest_code: str) -> bytes:
    """Genera un código de barras Code128 en memoria (PNG, bytes) a partir del
    nest_code de una orden. Nunca escribe a disco."""
    codigo = barcode.get("code128", nest_code, writer=ImageWriter())

    buffer = io.BytesIO()
    codigo.write(
        buffer,
        options={
            "module_width": _MODULE_WIDTH_MM,
            "module_height": _MODULE_HEIGHT_MM,
            "quiet_zone": _QUIET_ZONE_MM,
            "dpi": _DPI,
        },
    )
    return buffer.getvalue()
