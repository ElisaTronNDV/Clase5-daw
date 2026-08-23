from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

# check_same_thread=False es necesario para SQLite: por defecto solo permite el hilo
# que abrió la conexión, y FastAPI puede servir requests desde otro hilo.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Crea las tablas declaradas en los modelos si todavía no existen.

    Sin Alembic: es el primer schema de una base nueva (decisión de Block 1).
    """
    import app.models  # noqa: F401  (registra los modelos en Base.metadata)

    Base.metadata.create_all(bind=engine)
