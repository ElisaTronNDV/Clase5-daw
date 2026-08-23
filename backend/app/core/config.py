from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación, leída exclusivamente de variables de entorno / .env.

    DATABASE_URL y JWT_SECRET no tienen default: deben venir siempre del entorno
    (mitigación del threat model — nunca un secreto hardcodeado en el código).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 1440
    PASSWORD_MIN_LENGTH: int = 8
    # NoDecode: pydantic-settings intenta JSON.loads por defecto en tipos list;
    # se desactiva para poder aceptar una cadena separada por comas en .env.
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode]
    DEBUG: bool = False

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_allowed_origins(cls, value: object) -> object:
        """Acepta tanto una lista JSON como una cadena separada por comas en .env."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
