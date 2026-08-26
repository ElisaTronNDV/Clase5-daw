import pytest
from sqlalchemy.orm import sessionmaker

from app.models.configuracion import Configuracion
from app.services import configuracion_service


@pytest.fixture()
def db(initialized_db):
    """Sesión de SQLAlchemy contra el engine de test aislado (mismo patrón que
    test_product_service.py)."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=initialized_db)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_get_margen_tolerancia_returns_default_when_no_row(db):
    valor = configuracion_service.get_margen_tolerancia(db)

    assert valor == configuracion_service.DEFAULT_MARGEN_TOLERANCIA
    assert db.get(Configuracion, 1) is None


def test_get_margen_tolerancia_returns_persisted_value_when_row_exists(db):
    db.add(Configuracion(id=1, margen_tolerancia_dimensional=2.5))
    db.commit()

    valor = configuracion_service.get_margen_tolerancia(db)

    assert valor == 2.5


def test_update_margen_tolerancia_creates_row_when_none_exists(db):
    valor = configuracion_service.update_margen_tolerancia(db, 3.0)

    assert valor == 3.0
    row = db.get(Configuracion, 1)
    assert row is not None
    assert row.margen_tolerancia_dimensional == 3.0


def test_update_margen_tolerancia_updates_existing_row_without_duplicating(db):
    configuracion_service.update_margen_tolerancia(db, 3.0)

    valor = configuracion_service.update_margen_tolerancia(db, 4.5)

    assert valor == 4.5
    rows = db.query(Configuracion).all()
    assert len(rows) == 1
    assert rows[0].id == 1
    assert rows[0].margen_tolerancia_dimensional == 4.5
