from pydantic import BaseModel, ConfigDict


class PiezaExtraida(BaseModel):
    """Una fila de la tabla de piezas extraída de una página del archivo de corte.

    Solo lectura: se arma en memoria a partir del PDF, nunca se persiste tal cual (Block 4
    la usa como base para construir `PiezaOrden` recién en la confirmación).
    """

    model_config = ConfigDict(extra="forbid")

    ref: str | None
    cantidad: int
    pieza: str
    descripcion: str
    es_recorte: bool = False
    largo_mm: float | None = None
    ancho_mm: float | None = None


class OrdenBorrador(BaseModel):
    """Borrador de orden extraído de una página del archivo de corte, sin persistir."""

    model_config = ConfigDict(extra="forbid")

    indice_formato: str | None
    multiplicidad: int
    material: str
    espesor: float
    largo: float
    ancho: float
    tiempo_ejecucion_estimado: str | None
    piezas: list[PiezaExtraida]
