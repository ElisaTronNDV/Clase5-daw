import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.orden import Orden, PiezaOrden
from app.services import barcode_service

_PIEZAS_HEADER = ["Ref.", "Cantidad", "Pieza", "Descripción"]


def generar_documento_orden(orden: Orden, piezas: list[PiezaOrden]) -> bytes:
    """Compone el documento PDF descargable de una orden: encabezado, tabla de
    piezas y el código de barras del nest_code embebido desde bytes en memoria.
    Devuelve bytes; no persiste nada en disco."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph(f"Orden {orden.nest_code}", styles["Title"]))
    elementos.append(Spacer(1, 6 * mm))

    encabezado_data = [
        ["Material", orden.material],
        ["Espesor (mm)", str(orden.espesor)],
        ["Dimensiones (mm)", f"{orden.largo} x {orden.ancho}"],
        ["Multiplicidad", str(orden.multiplicidad)],
    ]
    tabla_encabezado = Table(encabezado_data, colWidths=[50 * mm, 100 * mm])
    tabla_encabezado.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(tabla_encabezado)
    elementos.append(Spacer(1, 8 * mm))

    elementos.append(Paragraph("Piezas", styles["Heading2"]))
    piezas_data = [_PIEZAS_HEADER] + [
        [pieza.ref or "", str(pieza.cantidad), pieza.pieza, pieza.descripcion]
        for pieza in piezas
    ]
    tabla_piezas = Table(piezas_data, colWidths=[25 * mm, 25 * mm, 50 * mm, 60 * mm])
    tabla_piezas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(tabla_piezas)
    elementos.append(Spacer(1, 10 * mm))

    barcode_bytes = barcode_service.generar_codigo_barras(orden.nest_code)
    barcode_buffer = io.BytesIO(barcode_bytes)
    elementos.append(Image(barcode_buffer, width=80 * mm, height=25 * mm))

    doc.build(elementos)
    return buffer.getvalue()
