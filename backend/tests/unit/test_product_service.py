import pytest
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import product_service


@pytest.fixture()
def db(initialized_db):
    """Sesión de SQLAlchemy contra el engine de test aislado (mismo patrón que la
    fixture `client` de conftest.py, pero sin pasar por el TestClient/HTTP).
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=initialized_db)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _payload(**overrides):
    payload = {
        "material": "SAE_1010",
        "espesor": 2.1,
        "largo": 3000,
        "ancho": 1500,
        "stock": 10,
        "punto_pedido": 5,
    }
    payload.update(overrides)
    return payload


def test_normalize_material_trims_and_lowercases():
    assert product_service._normalize_material("  SAE_1010  ") == "sae_1010"


def test_create_product_success(db):
    product = product_service.create_product(db, ProductCreate(**_payload()))

    assert product.id is not None
    assert product.material == "SAE_1010"
    assert product.stock_comprometido == 0


def test_create_product_duplicate_case_insensitive_raises(db):
    product_service.create_product(db, ProductCreate(**_payload(material="SAE_1010")))

    with pytest.raises(ProductAlreadyExistsError):
        product_service.create_product(db, ProductCreate(**_payload(material="  sae_1010  ")))


def test_create_product_different_espesor_not_duplicate(db):
    product_service.create_product(db, ProductCreate(**_payload(espesor=2.1)))

    product = product_service.create_product(db, ProductCreate(**_payload(espesor=3.0)))

    assert product.id is not None


def test_update_product_duplicate_against_other_product_raises(db):
    product_service.create_product(db, ProductCreate(**_payload(material="Acero A")))
    product_b = product_service.create_product(db, ProductCreate(**_payload(material="Acero B")))

    with pytest.raises(ProductAlreadyExistsError):
        product_service.update_product(
            db, product_b.id, ProductUpdate(**_payload(material="acero a"))
        )


def test_update_product_no_false_positive_against_itself(db):
    product = product_service.create_product(db, ProductCreate(**_payload()))

    updated = product_service.update_product(
        db, product.id, ProductUpdate(**_payload(stock=20))
    )

    assert updated.stock == 20


def test_get_product_by_id_not_found_raises(db):
    with pytest.raises(ProductNotFoundError):
        product_service.get_product_by_id(db, 9999)
