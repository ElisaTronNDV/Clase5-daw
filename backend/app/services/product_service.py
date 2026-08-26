from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.core.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def _normalize_material(material: str) -> str:
    return material.strip().lower()


def get_product_by_id(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise ProductNotFoundError(product_id)
    return product


def list_products(db: Session) -> list[Product]:
    return db.query(Product).all()


def _find_duplicate(
    db: Session, data: ProductCreate | ProductUpdate, exclude_id: int | None = None
) -> Product | None:
    """Busca un producto existente con el mismo material (case-insensitive) + espesor +
    largo + ancho exactos. Excluye `exclude_id` para que update_product no se compare
    contra sí mismo (FR-02)."""
    normalized_material = _normalize_material(data.material)
    query = db.query(Product).filter(
        Product.espesor == data.espesor,
        Product.largo == data.largo,
        Product.ancho == data.ancho,
    )
    if exclude_id is not None:
        query = query.filter(Product.id != exclude_id)

    for candidate in query.all():
        if _normalize_material(candidate.material) == normalized_material:
            return candidate
    return None


def create_product(db: Session, data: ProductCreate) -> Product:
    if _find_duplicate(db, data) is not None:
        raise ProductAlreadyExistsError(data.material)

    product = Product(
        material=data.material,
        espesor=data.espesor,
        largo=data.largo,
        ancho=data.ancho,
        stock=data.stock,
        stock_comprometido=0,
        punto_pedido=data.punto_pedido,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)

    if _find_duplicate(db, data, exclude_id=product_id) is not None:
        raise ProductAlreadyExistsError(data.material)

    product.material = data.material
    product.espesor = data.espesor
    product.largo = data.largo
    product.ancho = data.ancho
    product.stock = data.stock
    product.punto_pedido = data.punto_pedido
    db.commit()
    db.refresh(product)
    return product


def buscar_por_tolerancia(
    db: Session, material: str, espesor: float, largo: float, ancho: float, margen: float
) -> Product | None:
    """Matching por tolerancia dimensional (FR-12/FR-13 de FEAT-004): mismo material
    (case-insensitive, vía `_normalize_material`) y espesor exacto, pero largo/ancho
    dentro de `margen` mm en vez de exactos. Acota candidatos por espesor exacto en la
    query y resuelve material/tolerancia en Python (SQLite no ofrece comparación
    case-insensitive trivial para esto)."""
    normalized_material = _normalize_material(material)
    candidates = db.query(Product).filter(Product.espesor == espesor).all()

    for candidate in candidates:
        if _normalize_material(candidate.material) != normalized_material:
            continue
        if abs(candidate.largo - largo) <= margen and abs(candidate.ancho - ancho) <= margen:
            return candidate
    return None


def comprometer_stock(db: Session, product: Product, cantidad: int) -> Product:
    """Incrementa el stock comprometido del maestro al confirmar una orden. Sin
    commit: la transacción completa (incluida la creación de la `Orden`) la cierra
    `orden_service` con un único commit (Block 4)."""
    product.stock_comprometido += cantidad
    db.flush()
    return product


def crear_producto_automatico(
    db: Session, material: str, espesor: float, largo: float, ancho: float
) -> Product:
    """Alta automática de un producto maestro cuando no hubo match por tolerancia y el
    cliente confirmó `crear_producto_automaticamente=True` (FR-15). No pasa por el
    schema HTTP `ProductCreate` (exige `stock > 0` para el alta manual de FEAT-002);
    acá el stock inicial es siempre 0 por definición. Reutiliza `_find_duplicate` como
    chequeo defensivo de condición de carrera contra un `SimpleNamespace` que expone
    los mismos atributos que `ProductCreate`/`ProductUpdate` (duck typing), sin generar
    una instancia de esos schemas -que traen sus propias validaciones de stock/punto de
    pedido, ajenas a este flujo-."""
    candidate_data = SimpleNamespace(material=material, espesor=espesor, largo=largo, ancho=ancho)
    if _find_duplicate(db, candidate_data) is not None:
        raise ProductAlreadyExistsError(material)

    product = Product(
        material=material,
        espesor=espesor,
        largo=largo,
        ancho=ancho,
        stock=0,
        stock_comprometido=0,
        punto_pedido=0,
    )
    db.add(product)
    db.flush()
    return product
