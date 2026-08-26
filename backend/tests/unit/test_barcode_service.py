from app.services import barcode_service

_PNG_MAGIC_BYTES = b"\x89PNG\r\n\x1a\n"


def test_genera_imagen_png_valida():
    resultado = barcode_service.generar_codigo_barras("NEST-000001")

    assert isinstance(resultado, bytes)
    assert resultado.startswith(_PNG_MAGIC_BYTES)


def test_codigo_decodificable_por_pyzbar_a_300dpi():
    # Crítico (NFR-02/AC-17): no basta con que se genere una imagen, tiene que ser
    # legible por un lector de código de barras independiente a resolución de
    # impresión típica.
    from io import BytesIO

    from PIL import Image
    from pyzbar import pyzbar

    nest_code = "NEST-000042"
    resultado = barcode_service.generar_codigo_barras(nest_code)

    imagen = Image.open(BytesIO(resultado))
    decodificados = pyzbar.decode(imagen)

    assert len(decodificados) == 1
    assert decodificados[0].data.decode() == nest_code
