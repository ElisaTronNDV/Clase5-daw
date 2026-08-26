"""Lógica de negocio de las órdenes de trabajo (Block 4 de FEAT-004): confirmación
(persistencia con matching por tolerancia, compromiso de stock y generación de NEST) y
listado/búsqueda. La extracción del PDF (sin persistir) vive en `pdf_extraction_service`
(Block 2)."""

from sqlalchemy.orm import Session

from app.core.exceptions import ProductoSinCoincidenciaError
from app.models.orden import Orden, PiezaOrden
from app.schemas.orden import OrdenConfirmarRequest
from app.services import configuracion_service, product_service


def confirmar_orden(db: Session, payload: OrdenConfirmarRequest) -> Orden:
    """Confirma una orden de trabajo en una única transacción (FR-09 a FR-16):

    1. Busca un producto maestro que matchee por tolerancia dimensional.
    2. Si no hay match y no se pidió alta automática -> `ProductoSinCoincidenciaError`
       sin persistir nada.
    3. Si no hay match y se pidió alta automática -> crea el producto (stock=0).
    4. Compromete stock del maestro según la multiplicidad.
    5. Persiste la `Orden` (flush para obtener el id -> arma `nest_code` -> commit) y
       sus `PiezaOrden`.

    Cualquier excepción antes del commit deja la sesión sin cambios persistidos (rollback
    explícito por seguridad, aunque SQLAlchemy no comitea nada hasta el paso final).
    """
    margen = configuracion_service.get_margen_tolerancia(db)
    producto = product_service.buscar_por_tolerancia(
        db, payload.material, payload.espesor, payload.largo, payload.ancho, margen
    )

    if producto is None and not payload.crear_producto_automaticamente:
        raise ProductoSinCoincidenciaError(
            {
                "material": payload.material,
                "espesor": payload.espesor,
                "largo": payload.largo,
                "ancho": payload.ancho,
            }
        )

    try:
        if producto is None:
            producto = product_service.crear_producto_automatico(
                db, payload.material, payload.espesor, payload.largo, payload.ancho
            )

        product_service.comprometer_stock(db, producto, payload.multiplicidad)

        orden = Orden(
            nest_code=None,
            estado="vigente",
            product_id=producto.id,
            multiplicidad=payload.multiplicidad,
            material=payload.material,
            espesor=payload.espesor,
            largo=payload.largo,
            ancho=payload.ancho,
            tiempo_ejecucion_estimado=payload.tiempo_ejecucion_estimado,
            indice_formato=payload.indice_formato,
        )
        db.add(orden)
        db.flush()
        orden.nest_code = f"NEST-{orden.id:06d}"

        piezas_creadas: list[PiezaOrden] = []
        for pieza_payload in payload.piezas:
            pieza = PiezaOrden(
                orden_id=orden.id,
                ref=pieza_payload.ref,
                cantidad=pieza_payload.cantidad,
                pieza=pieza_payload.pieza,
                descripcion=pieza_payload.descripcion,
                es_recorte=pieza_payload.es_recorte,
                largo_mm=pieza_payload.largo_mm,
                ancho_mm=pieza_payload.ancho_mm,
            )
            db.add(pieza)
            piezas_creadas.append(pieza)

        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(orden)
    for pieza in piezas_creadas:
        db.refresh(pieza)

    # Atributos "de vista" que no son columnas mapeadas: `OrdenResponse` los lee vía
    # `from_attributes=True` pero no existen como relación ORM (Block 1 no define
    # `relationship()` entre Orden y PiezaOrden) ni como columna en la tabla.
    orden.piezas = piezas_creadas
    orden.alerta_stock_bajo = (
        producto.stock - producto.stock_comprometido
    ) <= producto.punto_pedido

    return orden


def listar_ordenes(
    db: Session, estado: str | None = None, nest: str | None = None
) -> list[Orden]:
    """Lista/busca órdenes (FR-18 a FR-20): filtro opcional por `estado` exacto y
    búsqueda parcial case-insensitive por `nest_code`, combinables entre sí."""
    query = db.query(Orden)
    if estado is not None:
        query = query.filter(Orden.estado == estado)
    if nest:
        query = query.filter(Orden.nest_code.ilike(f"%{nest}%"))
    return query.order_by(Orden.id).all()
