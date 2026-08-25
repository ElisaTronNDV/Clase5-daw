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
