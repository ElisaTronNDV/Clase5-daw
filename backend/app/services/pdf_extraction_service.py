"""Extracción de datos del archivo de corte (PDF de Salvagnini) en memoria.

Cada página del PDF se trata como un borrador de orden independiente (FR-03 a FR-07).
No toca la base de datos ni persiste nada: devuelve `OrdenBorrador` de solo lectura.
"""

import io
import re

import pdfplumber

from app.core.exceptions import ArchivoCorteInvalidoError
from app.schemas.orden import OrdenBorrador, PiezaExtraida

# Límite duro de páginas (mitigación DoS del threat model, NFR-01).
MAX_PAGINAS = 50

_DATOS_GENERALES_HEADER = "Datos generales"
_PIEZAS_HEADER = "Ref. Cant. Pieza Descripción"

# Los campos de "Datos generales" vienen como texto plano "Clave Valor" en una misma
# línea (a veces con ruido numérico del diagrama de piezas superpuesto delante de la
# clave) — se busca la clave como substring y se toma el resto de la línea como valor.
_CAMPOS_GENERALES_PATRONES: dict[str, re.Pattern[str]] = {
    "indice_formato": re.compile(r"Índice formato\s+(.+)$"),
    "multiplicidad": re.compile(r"Multiplicidad\s+(.+)$"),
    "material": re.compile(r"Material\s+(.+)$"),
    "espesor": re.compile(r"Espesor \[mm\]\s+(.+)$"),
    "dimensiones": re.compile(r"Dimensiones \[mm\]\s+(.+)$"),
    "tiempo_ejecucion_estimado": re.compile(r"Tiempo de ejecución estimado\s+(.+)$"),
}

# Fila de la tabla de piezas: Ref. es opcional (las filas "Saved scrap" no lo traen),
# Cant. y Pieza son un único token cada uno, Descripción es el resto de la línea.
_FILA_PIEZA = re.compile(r"^(?:(\d+)\s+)?(\d+)\s+(\S+)\s+(.+)$")

_SAVED_SCRAP_DESCRIPCION = "Saved scrap"
_SAVED_SCRAP_PIEZA = re.compile(
    r"^(?P<largo>[\d.]+)x(?P<ancho>[\d.]+)_RECT_SCRAP$", re.IGNORECASE
)


def extraer_paginas(contenido: bytes) -> list[OrdenBorrador]:
    """Extrae un `OrdenBorrador` por cada página del archivo de corte.

    Nunca propaga una excepción interna de `pdfplumber`: cualquier fallo de parseo,
    memoria o formato se remapea a `ArchivoCorteInvalidoError` con mensaje genérico
    (mitigación de Information Disclosure del threat model).
    """
    try:
        with pdfplumber.open(io.BytesIO(contenido)) as pdf:
            if len(pdf.pages) > MAX_PAGINAS:
                raise ArchivoCorteInvalidoError(
                    f"El archivo de corte supera el límite de {MAX_PAGINAS} páginas."
                )
            return [_extraer_pagina(pagina) for pagina in pdf.pages]
    except ArchivoCorteInvalidoError:
        raise
    except Exception as exc:
        raise ArchivoCorteInvalidoError(
            "No se pudo procesar el archivo de corte: formato no reconocido."
        ) from exc


def _extraer_pagina(pagina) -> OrdenBorrador:
    texto = pagina.extract_text() or ""
    lineas = texto.splitlines()

    if not any(linea.strip() == _DATOS_GENERALES_HEADER for linea in lineas):
        raise ArchivoCorteInvalidoError(
            "No se encontró la tabla 'Datos generales' en el archivo de corte."
        )

    header_idx = next(
        (i for i, linea in enumerate(lineas) if linea.strip() == _PIEZAS_HEADER),
        None,
    )
    if header_idx is None:
        raise ArchivoCorteInvalidoError(
            "No se encontró la tabla de piezas (Ref./Cant./Pieza/Descripción) en el "
            "archivo de corte."
        )

    valores = _extraer_campos_generales(lineas)

    dimensiones = valores.get("dimensiones")
    if not dimensiones or " x " not in dimensiones:
        raise ArchivoCorteInvalidoError(
            "No se pudo interpretar el campo 'Dimensiones [mm]'."
        )
    largo_str, ancho_str = dimensiones.split(" x ", 1)

    multiplicidad = _parsear_entero(valores.get("multiplicidad"), "Multiplicidad")
    espesor = _parsear_float(valores.get("espesor"), "Espesor [mm]")
    largo = _parsear_float(largo_str, "Dimensiones [mm] (largo)")
    ancho = _parsear_float(ancho_str, "Dimensiones [mm] (ancho)")

    material = valores.get("material")
    if not material:
        raise ArchivoCorteInvalidoError("No se encontró el campo 'Material'.")

    piezas = _extraer_piezas(lineas[header_idx + 1 :])

    return OrdenBorrador(
        indice_formato=valores.get("indice_formato"),
        multiplicidad=multiplicidad,
        material=material,
        espesor=espesor,
        largo=largo,
        ancho=ancho,
        tiempo_ejecucion_estimado=valores.get("tiempo_ejecucion_estimado"),
        piezas=piezas,
    )


def _extraer_campos_generales(lineas: list[str]) -> dict[str, str]:
    valores: dict[str, str] = {}
    patrones = dict(_CAMPOS_GENERALES_PATRONES)

    for linea in lineas:
        if not patrones:
            break
        encontrados = []
        for campo, patron in patrones.items():
            match = patron.search(linea)
            if match:
                valores[campo] = match.group(1).strip()
                encontrados.append(campo)
        for campo in encontrados:
            del patrones[campo]

    return valores


def _extraer_piezas(lineas: list[str]) -> list[PiezaExtraida]:
    piezas: list[PiezaExtraida] = []

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            break

        match = _FILA_PIEZA.match(linea)
        if not match:
            break

        ref, cantidad_str, pieza, descripcion = match.groups()
        cantidad = _parsear_entero(cantidad_str, "Cantidad de pieza")
        descripcion = descripcion.strip()
        es_recorte = descripcion == _SAVED_SCRAP_DESCRIPCION

        largo_mm: float | None = None
        ancho_mm: float | None = None
        if es_recorte:
            scrap_match = _SAVED_SCRAP_PIEZA.match(pieza)
            if not scrap_match:
                raise ArchivoCorteInvalidoError(
                    "Fila 'Saved scrap' con formato de pieza inválido: "
                    f"'{pieza}'."
                )
            largo_mm = float(scrap_match.group("largo"))
            ancho_mm = float(scrap_match.group("ancho"))

        piezas.append(
            PiezaExtraida(
                ref=ref,
                cantidad=cantidad,
                pieza=pieza,
                descripcion=descripcion,
                es_recorte=es_recorte,
                largo_mm=largo_mm,
                ancho_mm=ancho_mm,
            )
        )

    return piezas


def _parsear_entero(valor: str | None, nombre_campo: str) -> int:
    if valor is None:
        raise ArchivoCorteInvalidoError(f"No se encontró el campo '{nombre_campo}'.")
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ArchivoCorteInvalidoError(
            f"El campo '{nombre_campo}' no es un número entero válido: '{valor}'."
        ) from None


def _parsear_float(valor: str | None, nombre_campo: str) -> float:
    if valor is None:
        raise ArchivoCorteInvalidoError(f"No se encontró el campo '{nombre_campo}'.")
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ArchivoCorteInvalidoError(
            f"El campo '{nombre_campo}' no es un número válido: '{valor}'."
        ) from None
