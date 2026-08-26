from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import (
    ArchivoCorteInvalidoError,
    OrdenNotFoundError,
    ProductAlreadyExistsError,
    ProductoSinCoincidenciaError,
)
from app.models.user import User
from app.schemas.orden import OrdenBorrador, OrdenConfirmarRequest, OrdenListItem, OrdenResponse
from app.services import orden_service, pdf_document_service, pdf_extraction_service

router = APIRouter()

_EXTENSION_INVALIDA_DETAIL = "el archivo debe tener extensión .pdf"
_MAGIC_BYTES_INVALIDOS_DETAIL = "el archivo no es un PDF válido"
_TAMANO_EXCEDIDO_DETAIL = "el archivo supera el tamaño máximo permitido de 10 MB"
_DUPLICATE_DETAIL = "product already registered with this material, thickness and dimensions"
_ORDEN_NOT_FOUND_DETAIL = "orden not found"

_MAX_BYTES = 10 * 1024 * 1024
_PDF_MAGIC_BYTES = b"%PDF-"


class ExtraerResponse(BaseModel):
    """Wrapper de respuesta de `POST /ordenes/extraer`, local a este router (no forma
    parte de los schemas de persistencia de `schemas/orden.py`)."""

    model_config = ConfigDict(extra="forbid")

    paginas: list[OrdenBorrador]


class ListarOrdenesResponse(BaseModel):
    """Wrapper de respuesta de `GET /ordenes`, local a este router por la misma razón
    que `ExtraerResponse`."""

    model_config = ConfigDict(extra="forbid")

    ordenes: list[OrdenListItem]


@router.post("/extraer", response_model=ExtraerResponse)
async def extraer_orden(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtraerResponse:
    if archivo.filename is None or not archivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_EXTENSION_INVALIDA_DETAIL
        )

    contenido = await archivo.read()

    if not contenido.startswith(_PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_MAGIC_BYTES_INVALIDOS_DETAIL
        )

    if len(contenido) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=_TAMANO_EXCEDIDO_DETAIL,
        )

    try:
        paginas = pdf_extraction_service.extraer_paginas(contenido)
    except ArchivoCorteInvalidoError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )

    return ExtraerResponse(paginas=paginas)


@router.post("/confirmar", response_model=OrdenResponse, status_code=status.HTTP_201_CREATED)
def confirmar_orden(
    data: OrdenConfirmarRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrdenResponse:
    try:
        return orden_service.confirmar_orden(db, data)
    except ProductoSinCoincidenciaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.args[0])
    except ProductAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_DUPLICATE_DETAIL)


@router.get("", response_model=ListarOrdenesResponse)
def listar_ordenes(
    estado: Literal["vigente", "cerrada"] | None = None,
    nest: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListarOrdenesResponse:
    ordenes = orden_service.listar_ordenes(db, estado=estado, nest=nest)
    return ListarOrdenesResponse(ordenes=ordenes)


@router.get("/{id}/documento")
def descargar_documento_orden(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        orden, piezas = orden_service.obtener_orden_con_piezas(db, id)
    except OrdenNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=_ORDEN_NOT_FOUND_DETAIL
        )

    documento = pdf_document_service.generar_documento_orden(orden, piezas)
    return Response(content=documento, media_type="application/pdf")
