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


# --- Block 3 (FEAT-004): matching por tolerancia, compromiso de stock, alta automática ---


def test_buscar_por_tolerancia_encuentra_dentro_del_margen(db):
    product = product_service.create_product(
        db, ProductCreate(**_payload(material="SAE_1010", espesor=2.1, largo=3000, ancho=1500))
    )

    found = product_service.buscar_por_tolerancia(
        db, material="SAE_1010", espesor=2.1, largo=3000.8, ancho=1499.5, margen=1.0
    )

    assert found is not None
    assert found.id == product.id


def test_buscar_por_tolerancia_no_encuentra_fuera_del_margen(db):
    product_service.create_product(
        db, ProductCreate(**_payload(material="SAE_1010", espesor=2.1, largo=3000, ancho=1500))
    )

    found = product_service.buscar_por_tolerancia(
        db, material="SAE_1010", espesor=2.1, largo=3005, ancho=1500, margen=1.0
    )

    assert found is None


def test_buscar_por_tolerancia_material_case_insensitive(db):
    product = product_service.create_product(
        db, ProductCreate(**_payload(material="SAE_1010", espesor=2.1, largo=3000, ancho=1500))
    )

    found = product_service.buscar_por_tolerancia(
        db, material="  sae_1010  ", espesor=2.1, largo=3000, ancho=1500, margen=1.0
    )

    assert found is not None
    assert found.id == product.id


def test_comprometer_stock_incrementa_correctamente(db):
    product = product_service.create_product(db, ProductCreate(**_payload(stock=10)))

    # Caso sintético: multiplicidad > 1 (ningún PDF de ejemplo real lo cubre).
    multiplicidad = 4
    updated = product_service.comprometer_stock(db, product, multiplicidad)

    assert updated.stock_comprometido == 4

    # Confirmar una segunda orden sobre el mismo producto acumula el compromiso.
    updated = product_service.comprometer_stock(db, product, 1)
    assert updated.stock_comprometido == 5


def test_crear_producto_automatico_stock_cero(db):
    product = product_service.crear_producto_automatico(
        db, material="SAE_1010", espesor=2.1, largo=3000, ancho=1500
    )

    assert product.id is not None
    assert product.stock == 0
    assert product.stock_comprometido == 0
    assert product.punto_pedido == 0


def test_crear_producto_automatico_rechaza_duplicado(db):
    product_service.create_product(
        db, ProductCreate(**_payload(material="SAE_1010", espesor=2.1, largo=3000, ancho=1500))
    )

    with pytest.raises(ProductAlreadyExistsError):
        product_service.crear_producto_automatico(
            db, material="sae_1010", espesor=2.1, largo=3000, ancho=1500
        )
