from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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


# --- Block 4: confirmación de orden (persistencia) ---


class PiezaConfirmar(BaseModel):
    """Una pieza del payload de confirmación (Block 4). A diferencia de `PiezaExtraida`
    (solo lectura del borrador), este schema es el que efectivamente arma cada
    `PiezaOrden` persistida — el cliente puede haber editado los valores extraídos
    antes de confirmar."""

    model_config = ConfigDict(extra="forbid")

    ref: str | None
    cantidad: int = Field(gt=0, le=100000)
    pieza: str
    descripcion: str
    es_recorte: bool = False
    largo_mm: float | None = None
    ancho_mm: float | None = None


class OrdenConfirmarRequest(BaseModel):
    """Payload de `POST /api/ordenes/confirmar` (Block 4)."""

    model_config = ConfigDict(extra="forbid")

    indice_formato: str | None
    multiplicidad: int = Field(gt=0, le=10000)
    material: str
    espesor: float = Field(gt=0, le=100000)
    largo: float = Field(gt=0, le=100000)
    ancho: float = Field(gt=0, le=100000)
    tiempo_ejecucion_estimado: str | None
    piezas: list[PiezaConfirmar]
    crear_producto_automaticamente: bool = False


class PiezaResponse(BaseModel):
    """Representación de una `PiezaOrden` persistida en las respuestas de la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ref: str | None
    cantidad: int
    pieza: str
    descripcion: str
    es_recorte: bool
    largo_mm: float | None
    ancho_mm: float | None


class OrdenResponse(BaseModel):
    """Respuesta de `POST /api/ordenes/confirmar` (Block 4)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nest_code: str
    estado: str
    multiplicidad: int
    material: str
    espesor: float
    largo: float
    ancho: float
    tiempo_ejecucion_estimado: str | None
    indice_formato: str | None
    product_id: int
    created_at: datetime
    piezas: list[PiezaResponse]
    alerta_stock_bajo: bool


class OrdenListItem(BaseModel):
    """Un elemento del listado de `GET /api/ordenes` (Block 4)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nest_code: str | None
    estado: str
    material: str
    espesor: float
    largo: float
    ancho: float
    multiplicidad: int
    created_at: datetime
