from sqlalchemy.orm import Session

from app.models.configuracion import Configuracion

# RF-02: valor por defecto cuando nunca se configuró el margen — no requiere seed
# en la base de datos.
DEFAULT_MARGEN_TOLERANCIA = 1.0

# Clave fija del singleton (mitigación del threat model,
# docs/daw/security/threat-FEAT-003.md): en vez de "la primera fila por orden de
# inserción", se opera siempre sobre id=1, lo que elimina la ambigüedad de
# concurrencia del upsert sin agregar ningún control de concurrencia adicional.
_CONFIGURACION_ID = 1


def get_margen_tolerancia(db: Session) -> float:
    config = db.get(Configuracion, _CONFIGURACION_ID)
    if config is None:
        return DEFAULT_MARGEN_TOLERANCIA
    return config.margen_tolerancia_dimensional


def update_margen_tolerancia(db: Session, valor: float) -> float:
    config = db.get(Configuracion, _CONFIGURACION_ID)
    if config is None:
        config = Configuracion(id=_CONFIGURACION_ID, margen_tolerancia_dimensional=valor)
        db.add(config)
    else:
        config.margen_tolerancia_dimensional = valor
    db.commit()
    db.refresh(config)
    return config.margen_tolerancia_dimensional
