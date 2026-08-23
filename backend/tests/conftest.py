import os

import pytest

# Los settings requeridos (DATABASE_URL, JWT_SECRET, ALLOWED_ORIGINS) se leen al importar
# app.core.config. Se fijan ANTES de cualquier import de la app para que los tests nunca
# dependan de un .env real ni toquen la base de datos de producción (dyp_lasercore.db).
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:4200")
os.environ.setdefault("DEBUG", "false")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402,F401  (registra los modelos en Base.metadata)


@pytest.fixture()
def test_engine():
    """Motor SQLite en memoria, aislado por test, que persiste entre conexiones
    (StaticPool) para que todas las sesiones del mismo test vean el mismo esquema/datos.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


@pytest.fixture()
def initialized_db(test_engine):
    """Crea el esquema en el engine de test aislado y lo limpia al terminar."""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(initialized_db):
    """TestClient con la dependencia de DB de la app apuntando a la base de test aislada.

    No se usa init_db() aquí para no acoplarse a la DB real: el startup event queda
    neutralizado (monkeypatch de init_db) y, además, get_db (Block 2) se sobreescribe
    para que cada sesión de request se abra contra el engine de test aislado en vez de
    tocar el archivo dyp_lasercore.db — nunca se opera contra datos reales (Rule #0).
    """
    from app.main import app

    def override_init_db():
        # El esquema ya está creado por el fixture initialized_db sobre el engine de test.
        pass

    import app.main as main_module

    original_init_db = main_module.init_db
    main_module.init_db = override_init_db

    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=initialized_db
    )

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from app.api.deps import get_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        main_module.init_db = original_init_db
        app.dependency_overrides.pop(get_db, None)
