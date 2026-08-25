from sqlalchemy import Column, Float, Integer, String

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    material = Column(String(255), nullable=False)
    espesor = Column(Float, nullable=False)
    largo = Column(Float, nullable=False)
    ancho = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    stock_comprometido = Column(Integer, nullable=False, default=0)
    punto_pedido = Column(Integer, nullable=False)
