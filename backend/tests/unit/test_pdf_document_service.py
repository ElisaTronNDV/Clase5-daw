from datetime import datetime

from app.models.orden import Orden, PiezaOrden
from app.services import pdf_document_service

_PDF_MAGIC_BYTES = b"%PDF"


def _orden():
    return Orden(
        id=1,
        nest_code="NEST-000001",
        estado="vigente",
        multiplicidad=2,
        material="SAE_1010",
        espesor=2.1,
        largo=3000.0,
        ancho=1500.0,
        tiempo_ejecucion_estimado="00:10:00",
        indice_formato="1/1",
        product_id=1,
        created_at=datetime.now(),
    )


def _piezas():
    return [
        PiezaOrden(
            id=1,
            orden_id=1,
            ref="1",
            cantidad=3,
            pieza="139394-00.lsr",
            descripcion="PC 1368 (CO) X3",
            es_recorte=False,
            largo_mm=None,
            ancho_mm=None,
        )
    ]


def test_genera_pdf_valido_con_barcode_embebido():
    resultado = pdf_document_service.generar_documento_orden(_orden(), _piezas())

    assert isinstance(resultado, bytes)
    assert resultado.startswith(_PDF_MAGIC_BYTES)
    assert len(resultado) > 0
