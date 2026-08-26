from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.configuracion import router as configuracion_router
from app.api.routes.products import router as products_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(
    configuracion_router, prefix="/configuracion", tags=["configuracion"]
)
