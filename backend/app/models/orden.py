from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)

from app.db.base import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # nullable=True a propósito: nest_code se deriva del id autoincremental de la
    # propia fila (f"NEST-{id:06d}"), que solo se conoce después del INSERT. El flujo
    # correcto (Block 4) es db.add() -> db.flush() -> asignar nest_code -> db.commit().
    nest_code = Column(String(255), unique=True, nullable=True, index=True)
    estado = Column(String(50), nullable=False, default="vigente")
    multiplicidad = Column(Integer, nullable=False)
    material = Column(String(255), nullable=False)
    espesor = Column(Float, nullable=False)
    largo = Column(Float, nullable=False)
    ancho = Column(Float, nullable=False)
    tiempo_ejecucion_estimado = Column(String(255), nullable=True)
    indice_formato = Column(String(50), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())


class PiezaOrden(Base):
    __tablename__ = "piezas_orden"

    id = Column(Integer, primary_key=True, autoincrement=True)
    orden_id = Column(Integer, ForeignKey("ordenes.id"), nullable=False, index=True)
    ref = Column(String(255), nullable=True)
    cantidad = Column(Integer, nullable=False)
    pieza = Column(String(255), nullable=False)
    descripcion = Column(String(255), nullable=False)
    es_recorte = Column(Boolean, nullable=False, default=False)
    largo_mm = Column(Float, nullable=True)
    ancho_mm = Column(Float, nullable=True)
