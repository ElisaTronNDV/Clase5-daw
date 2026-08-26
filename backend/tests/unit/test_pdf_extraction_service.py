import io
from pathlib import Path
from unittest.mock import patch

import pytest
import pypdfium2 as pdfium

from app.core.exceptions import ArchivoCorteInvalidoError
from app.services import pdf_extraction_service

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "docs" / "Archivos de Corte"


def _leer_fixture(nombre: str) -> bytes:
    return (FIXTURES_DIR / nombre).read_bytes()


def _pdf_vacio(num_paginas: int = 1) -> bytes:
    """Construye un PDF sintético válido (sin las tablas esperadas) con N páginas
    en blanco, usando pypdfium2 (ya es una dependencia transitiva de pdfplumber, no
    se agrega ninguna librería nueva solo para tests).
    """
    doc = pdfium.PdfDocument.new()
    for _ in range(num_paginas):
        doc.new_page(200, 200)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestExtraeEjemplo1:
    def test_extrae_ejemplo_1(self):
        contenido = _leer_fixture("Ejemplo 1.pdf")

        paginas = pdf_extraction_service.extraer_paginas(contenido)

        assert len(paginas) == 1
        pagina = paginas[0]
        assert pagina.multiplicidad == 1
        assert pagina.largo == 1310.000
        assert pagina.ancho == 580.000
        assert pagina.espesor == 12.700
        assert pagina.material == "SAE_1010"
        assert pagina.tiempo_ejecucion_estimado == "00:26:19"
        assert pagina.indice_formato == "1/1"

        assert len(pagina.piezas) == 4

        p1, p2, p3, p4 = pagina.piezas

        assert p1.ref == "1"
        assert p1.cantidad == 3
        assert p1.pieza == "139394-00.lsr"
        assert p1.descripcion == "PC 1368 (CO) X3"
        assert p1.es_recorte is False

        assert p2.ref == "2"
        assert p2.cantidad == 3
        assert p2.pieza == "139346-00.lsr"
        assert p2.descripcion == "PC 1368 (CO) X3"

        assert p3.ref == "3"
        assert p3.cantidad == 6
        assert p3.pieza == "139396-00.lsr"
        assert p3.descripcion == "PC 1368 (CO) X6"

        assert p4.ref == "4"
        assert p4.cantidad == 3
        assert p4.pieza == "139213-00.lsr"
        assert p4.descripcion == "PC 1362 (CO) X3"

        assert all(not p.es_recorte for p in pagina.piezas)


class TestExtraeEjemplo2:
    def test_extrae_ejemplo_2_multipagina(self):
        contenido = _leer_fixture("Ejemplo 2.pdf")

        paginas = pdf_extraction_service.extraer_paginas(contenido)

        assert len(paginas) == 3

        pagina1, pagina2, pagina3 = paginas

        assert pagina1.indice_formato == "1/3"
        assert pagina1.multiplicidad == 1
        assert pagina1.largo == 3000.000
        assert pagina1.ancho == 1500.000
        assert pagina1.espesor == 0.910
        assert pagina1.material == "SAE_1010"
        assert pagina1.tiempo_ejecucion_estimado == "00:01:44"
        assert len(pagina1.piezas) == 6

        assert pagina2.indice_formato == "2/3"
        assert pagina2.multiplicidad == 1
        assert pagina2.largo == 3000.000
        assert pagina2.ancho == 1500.000
        assert pagina2.espesor == 0.910
        assert pagina2.material == "SAE_1010"
        assert pagina2.tiempo_ejecucion_estimado == "00:02:29"
        assert len(pagina2.piezas) == 5

        assert pagina3.indice_formato == "3/3"
        assert pagina3.multiplicidad == 1
        assert pagina3.largo == 3000.000
        assert pagina3.ancho == 1500.000
        assert pagina3.espesor == 0.910
        assert pagina3.material == "SAE_1010"
        assert pagina3.tiempo_ejecucion_estimado == "00:02:13"
        assert len(pagina3.piezas) == 5

        assert all(not p.es_recorte for pagina in paginas for p in pagina.piezas)


class TestExtraeEjemplo3:
    def test_extrae_ejemplo_3_con_saved_scrap(self):
        contenido = _leer_fixture("Ejemplo 3.pdf")

        paginas = pdf_extraction_service.extraer_paginas(contenido)

        assert len(paginas) == 1
        pagina = paginas[0]
        assert pagina.multiplicidad == 1
        assert pagina.largo == 3000.000
        assert pagina.ancho == 1500.000
        assert pagina.espesor == 8.000
        assert pagina.material == "SAE_1010"
        assert pagina.tiempo_ejecucion_estimado == "00:26:51"
        assert pagina.indice_formato == "1/1"

        assert len(pagina.piezas) == 4

        p1, p2, scrap1, scrap2 = pagina.piezas

        assert p1.ref == "1"
        assert p1.cantidad == 7
        assert p1.pieza == "141005-02.lsr"
        assert p1.descripcion == "PC 1388 X1/ PC 1363 X1/ PC 1362 X5 (C/P) BOUNOUS"
        assert p1.es_recorte is False

        assert p2.ref == "2"
        assert p2.cantidad == 24
        assert p2.pieza == "200055-00.lsr"
        assert p2.descripcion == "PC 1363 X24 (CO) BOUNOUS"
        assert p2.es_recorte is False

        assert scrap1.ref is None
        assert scrap1.cantidad == 1
        assert scrap1.descripcion == "Saved scrap"
        assert scrap1.es_recorte is True
        assert scrap1.largo_mm == 1085.00
        assert scrap1.ancho_mm == 1500.00

        assert scrap2.ref is None
        assert scrap2.cantidad == 1
        assert scrap2.descripcion == "Saved scrap"
        assert scrap2.es_recorte is True
        assert scrap2.largo_mm == 955.00
        assert scrap2.ancho_mm == 559.16


class TestSadPaths:
    def test_rechaza_pdf_sin_tablas_esperadas(self):
        contenido = _pdf_vacio(num_paginas=1)

        with pytest.raises(ArchivoCorteInvalidoError):
            pdf_extraction_service.extraer_paginas(contenido)

    def test_rechaza_mas_de_50_paginas(self):
        contenido = _pdf_vacio(num_paginas=51)

        with pytest.raises(ArchivoCorteInvalidoError):
            pdf_extraction_service.extraer_paginas(contenido)

    def test_captura_excepcion_interna_pdfplumber(self):
        with patch("app.services.pdf_extraction_service.pdfplumber.open") as mock_open:
            mock_open.side_effect = RuntimeError(
                "detalle interno sensible de pdfminer que no debe propagarse"
            )

            with pytest.raises(ArchivoCorteInvalidoError) as exc_info:
                pdf_extraction_service.extraer_paginas(b"contenido-cualquiera")

            assert "detalle interno sensible" not in str(exc_info.value)
