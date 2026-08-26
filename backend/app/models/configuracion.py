from sqlalchemy import Column, Float, Integer

from app.db.base import Base


class Configuracion(Base):
    __tablename__ = "configuracion"

    # Sin UNIQUE ni constraint de "una sola fila" a nivel de DB: el singleton lo
    # garantiza configuracion_service mediante la clave fija id=1 (mitigación del
    # threat model, docs/daw/security/threat-FEAT-003.md).
    id = Column(Integer, primary_key=True)
    margen_tolerancia_dimensional = Column(Float, nullable=False)
