import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.orden import Orden, PiezaOrden
from app.models.product import Product


@pytest.fixture()
def db(initialized_db):
    """Sesión de SQLAlchemy contra el engine de test aislado (mismo patrón que
    `test_product_service.py`), sin pasar por el TestClient/HTTP.
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=initialized_db)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _crear_producto(db):
    product = Product(
        material="SAE_1010",
        espesor=2.1,
        largo=3000,
        ancho=1500,
        stock=10,
        stock_comprometido=0,
        punto_pedido=5,
    )
    db.add(product)
    db.flush()
    return product


def test_crea_orden_con_piezas(db):
    product = _crear_producto(db)

    orden = Orden(
        nest_code=None,
        estado="vigente",
        multiplicidad=1,
        material="SAE_1010",
        espesor=2.1,
        largo=3000,
        ancho=1500,
        tiempo_ejecucion_estimado="00:10:00",
        indice_formato="1/1",
        product_id=product.id,
    )
    db.add(orden)
    db.flush()

    pieza1 = PiezaOrden(
        orden_id=orden.id,
        ref="1",
        cantidad=2,
        pieza="PIEZA-A",
        descripcion="Descripcion A",
        es_recorte=False,
    )
    pieza2 = PiezaOrden(
        orden_id=orden.id,
        ref=None,
        cantidad=1,
        pieza="800x400_RECT_SCRAP",
        descripcion="Saved scrap",
        es_recorte=True,
        largo_mm=800.0,
        ancho_mm=400.0,
    )
    db.add_all([pieza1, pieza2])
    db.commit()

    piezas = db.query(PiezaOrden).filter(PiezaOrden.orden_id == orden.id).all()

    assert len(piezas) == 2
    assert {p.pieza for p in piezas} == {"PIEZA-A", "800x400_RECT_SCRAP"}


def test_nest_code_se_asigna_post_flush(db):
    product = _crear_producto(db)

    orden = Orden(
        nest_code=None,
        estado="vigente",
        multiplicidad=1,
        material="SAE_1010",
        espesor=2.1,
        largo=3000,
        ancho=1500,
        product_id=product.id,
    )
    db.add(orden)

    assert orden.id is None

    db.flush()

    assert orden.id is not None
    assert orden.nest_code is None

    orden.nest_code = f"NEST-{orden.id:06d}"
    db.commit()

    assert orden.nest_code == f"NEST-{orden.id:06d}"

    otra_orden = Orden(
        nest_code=None,
        estado="vigente",
        multiplicidad=1,
        material="SAE_1010",
        espesor=2.1,
        largo=3000,
        ancho=1500,
        product_id=product.id,
    )
    db.add(otra_orden)
    db.flush()
    otra_orden.nest_code = f"NEST-{otra_orden.id:06d}"
    db.commit()

    assert otra_orden.nest_code != orden.nest_code


def test_tablas_registradas_en_metadata(test_engine):
    Base.metadata.create_all(bind=test_engine)

    inspector = inspect(test_engine)
    tablas = inspector.get_table_names()

    assert "ordenes" in tablas
    assert "piezas_orden" in tablas
