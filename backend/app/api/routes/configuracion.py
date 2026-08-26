from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.configuracion import ConfiguracionOut, ConfiguracionUpdate
from app.services import configuracion_service

router = APIRouter()


@router.get("", response_model=ConfiguracionOut)
def get_configuracion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConfiguracionOut:
    valor = configuracion_service.get_margen_tolerancia(db)
    return ConfiguracionOut(margen_tolerancia_dimensional=valor)


@router.put("", response_model=ConfiguracionOut)
def update_configuracion(
    data: ConfiguracionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConfiguracionOut:
    valor = configuracion_service.update_margen_tolerancia(
        db, data.margen_tolerancia_dimensional
    )
    return ConfiguracionOut(margen_tolerancia_dimensional=valor)
